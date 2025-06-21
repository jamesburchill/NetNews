import configparser
import os
import socket
import sqlite3
import time
import logging
import argparse
from datetime import datetime, timedelta

import feedparser
from dotenv import load_dotenv
from openai import OpenAI


def get_summary_from_AI(client, model, text, logger, max_retries=3, retry_delay=2):
    """
    This function uses OpenAI's GPT model to generate a summary of a given text.
    Includes retry logic and rate limiting.

    Parameters:
    client (openai.OpenAI): The OpenAI client with the API key.
    model (str): The model to use for the summary generation.
    text (str): The text to summarize.
    logger (logging.Logger): Logger instance for logging.
    max_retries (int): Maximum number of retry attempts.
    retry_delay (int): Delay between retries in seconds.

    Returns:
    str: The generated summary or None if all retries fail.
    """
    # Ensure text is not too long
    max_length = 4000  # Reasonable limit for API
    if len(text) > max_length:
        logger.warning(f"Text too long ({len(text)} chars), truncating to {max_length} chars")
        text = text[:max_length]

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system",
                     "content": "You are a highly skilled AI trained in language comprehension and summarization. I would "
                                "like you to read the following text and summarize it into a concise abstract paragraph. Aim "
                                "to retain the most important points, providing a coherent and readable summary that could "
                                "help a person understand the main points of the discussion without needing to read the "
                                "entire text. Please avoid unnecessary details or tangential points."},
                    {"role": "user", "content": text}
                ])
            return response.choices[0].message.content
        except Exception as e:
            logger.warning(f"API call failed (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                # Increase delay for next retry (exponential backoff)
                retry_delay *= 2
            else:
                logger.error(f"All {max_retries} attempts failed")
                return None


def generate_summaries(client, model, conn, feed_name, feed_url, num_stories, max_retries=3):
    """
    This function generates summaries for a given number of stories from a RSS feed and stores them in a SQLite
    database.

    Parameters:
    client (openai.OpenAI): The OpenAI client with the API key.
    model (str): The model to use for the summary generation.
    conn (sqlite3.Connection): The SQLite database connection.
    feed_name (str): The name of the RSS feed.
    feed_url (str): The URL of the RSS feed.
    num_stories (int): The number of stories to summarize.
    max_retries (int): Maximum number of API call retries.

    Returns:
    None
    """
    logger = logging.getLogger('NetNews')
    logger.info(f"Starting to process feed: {feed_name}")

    # Get timeout from environment or use default
    timeout = int(os.getenv('FEED_TIMEOUT', '30'))

    try:

        # Set a timeout for the socket operations
        original_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(timeout)

        logger.info(f"Fetching feed: {feed_url}")
        feed = feedparser.parse(feed_url)

        # Restore the original timeout
        socket.setdefaulttimeout(original_timeout)

        if hasattr(feed, 'status') and feed.status != 200:
            logger.warning(f"Feed returned non-200 status: {feed.status}")

        if not feed.entries:
            logger.warning(f"No entries found in feed: {feed_name}")
            return

        logger.info(f"Found {len(feed.entries)} entries in feed, processing up to {num_stories}")

        # Track statistics
        processed = 0
        skipped = 0
        failed = 0
        added = 0

        for i, entry in enumerate(feed.entries):
            if i >= num_stories:
                break

            processed += 1

            # Skip entries without titles or descriptions
            if not hasattr(entry, 'title') or not hasattr(entry, 'description'):
                logger.warning(f"Entry {i} in {feed_name} missing title or description, skipping")
                skipped += 1
                continue

            # Check if we already have this entry
            c = conn.cursor()
            c.execute("SELECT 1 FROM news WHERE title = ?", (entry.title,))
            if c.fetchone() is not None:
                logger.debug(f"Entry already exists: {entry.title}")
                skipped += 1
                continue

            # Get description text
            description = entry.description

            # Get link
            link = entry.link if hasattr(entry, 'link') else ""

            # Generate summary
            logger.debug(f"Generating summary for: {entry.title}")
            summary = get_summary_from_AI(client, model, description, logger, max_retries=max_retries)

            if summary is not None:
                try:
                    c.execute('''INSERT INTO news (feed, title, link, summary) VALUES (?, ?, ?, ?)''',
                              (feed_name, entry.title, link, summary))
                    conn.commit()
                    added += 1
                    logger.debug(f"Added summary for: {entry.title}")
                except sqlite3.Error as e:
                    logger.error(f"Database error when adding entry {entry.title}: {e}")
                    failed += 1
            else:
                logger.warning(f"Failed to generate summary for: {entry.title}")
                failed += 1

        logger.info(f"Feed {feed_name} stats: processed={processed}, added={added}, skipped={skipped}, failed={failed}")

    except (TimeoutError, socket.timeout) as e:
        logger.error(f"Timeout error when fetching feed {feed_name} from {feed_url}: {e}")
        # Continue with the next feed
    except Exception as e:
        logger.error(f"Error when processing feed {feed_name} from {feed_url}: {e}", exc_info=True)
        # Continue with the next feed


def setup_logging():
    """
    Configure logging for the application.

    Returns:
    logging.Logger: Configured logger instance
    """
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('netnews.log')
        ]
    )
    return logging.getLogger('NetNews')

def cleanup_old_entries(conn, days_to_keep=30):
    """
    Remove entries older than the specified number of days.

    Parameters:
    conn (sqlite3.Connection): Database connection
    days_to_keep (int): Number of days to keep entries for

    Returns:
    int: Number of entries removed
    """
    cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).strftime('%Y-%m-%d')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM news WHERE date(created_date) < date(?)", (cutoff_date,))
    deleted_count = cursor.rowcount
    conn.commit()
    return deleted_count

def parse_arguments():
    """
    Parse command-line arguments.

    Returns:
    argparse.Namespace: Parsed command-line arguments
    """
    parser = argparse.ArgumentParser(description='NetNews - RSS feed summarizer using AI')

    # Configuration options
    parser.add_argument('--config', type=str, help='Path to RSS feeds configuration file')
    parser.add_argument('--db', type=str, help='Path to SQLite database file')
    parser.add_argument('--env', type=str, help='Path to .env file')

    # Processing options
    parser.add_argument('--workers', type=int, help='Number of parallel workers (ignored, sequential processing is used)')
    parser.add_argument('--timeout', type=int, help='Timeout for RSS feed requests in seconds')
    parser.add_argument('--retention', type=int, help='Number of days to keep entries')
    parser.add_argument('--model', type=str, help='OpenAI model to use')
    parser.add_argument('--max-retries', type=int, help='Maximum number of API call retries')

    # Logging options
    parser.add_argument('--log-level', type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Logging level')
    parser.add_argument('--log-file', type=str, help='Path to log file')

    # Feed selection
    parser.add_argument('--feeds', type=str, nargs='+', help='Specific feeds to process (by name)')

    return parser.parse_args()

def main():
    """
    This is the main function that reads the RSS feeds from the configuration file, generates summaries for each feed
    and stores them in a SQLite database.

    Parameters:
    None

    Returns:
    None
    """
    # Parse command-line arguments
    args = parse_arguments()

    # Load environment variables
    env_path = args.env if args.env else None
    load_dotenv(dotenv_path=env_path)

    # Setup logging
    log_level = args.log_level if args.log_level else os.getenv('LOG_LEVEL', 'INFO')
    log_file = args.log_file if args.log_file else os.getenv('LOG_FILE', 'netnews.log')

    if os.path.exists('/netnews'):  # Running in deployment environment
        log_file = '/netnews/'+log_file
    else: # Running in local environment
        log_file = '../'+log_file


    # Configure logging
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=getattr(logging, log_level),
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file)
        ]
    )
    logger = logging.getLogger('NetNews')

    logger.info("Starting NetNews feed processor")

    # Read configuration
    config = configparser.ConfigParser()

    # Determine config path
    if args.config:
        config_path = args.config
    elif os.path.exists('/netnews/RSSFeeds.ini'):
        config_path = '/netnews/RSSFeeds.ini'
    else:
        config_path = '../RSSFeeds.ini'

    logger.info(f"Reading configuration from {config_path}")
    config.read(config_path)

    # Create an OpenAI client with default settings
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        logger.error("OPENAI_API_KEY not found in environment variables")
        return

    client = OpenAI(api_key=api_key)

    # Connect to database
    if args.db:
        db_path = args.db
    elif os.path.exists('/netnews/netnews.db'):
        db_path = '/netnews/netnews.db'
    else:
        db_path = '../netnews.db'

    logger.info(f"Connecting to database at {db_path}")
    conn = sqlite3.connect(db_path)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            feed TEXT,
            title TEXT,
            link TEXT,
            summary TEXT,
            created_date DATE DEFAULT CURRENT_DATE
        )
    ''')

    # Create index on title for faster duplicate checking if it doesn't exist
    try:
        conn.execute('CREATE INDEX IF NOT EXISTS idx_news_title ON news(title)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_news_date ON news(created_date)')
    except sqlite3.OperationalError as e:
        logger.warning(f"Could not create index: {e}")

    # Clean up old entries
    days_to_keep = args.retention if args.retention else int(os.getenv('RETENTION_DAYS', '30'))
    logger.info(f"Retention policy: keeping entries for {days_to_keep} days")
    deleted_count = cleanup_old_entries(conn, days_to_keep)
    if deleted_count > 0:
        logger.info(f"Cleaned up {deleted_count} entries older than {days_to_keep} days")

    # Process feeds
    model = args.model if args.model else os.getenv('AI_MODEL')
    if not model:
        logger.warning("AI_MODEL not specified, defaulting to gpt-3.5-turbo")
        model = "gpt-3.5-turbo"
    logger.info(f"Using AI model: {model}")

    # No longer using workers as we're processing feeds sequentially
    logger.info("Processing feeds sequentially")

    # Get timeout
    timeout = args.timeout if args.timeout else int(os.getenv('FEED_TIMEOUT', '30'))
    os.environ['FEED_TIMEOUT'] = str(timeout)
    logger.info(f"Feed timeout set to {timeout} seconds")

    # Get max retries
    max_retries = args.max_retries if args.max_retries else int(os.getenv('MAX_RETRIES', '3'))
    logger.info(f"API max retries set to {max_retries}")

    # Prepare feed processing tasks
    feed_tasks = []
    selected_feeds = [f.lower() for f in args.feeds] if args.feeds else None

    for key in config['RSS_FEEDS']:
        # Skip feeds not in the selected list if a selection was provided
        if selected_feeds and key not in selected_feeds:
            logger.info(f"Skipping feed {key} (not in selected feeds)")
            continue

        url, num_entries = config['RSS_FEEDS'][key].split(',')
        feed_tasks.append((key, url, int(num_entries)))

    if not feed_tasks:
        if selected_feeds:
            logger.error(f"None of the selected feeds {selected_feeds} were found in the configuration")
        else:
            logger.error("No feeds found in the configuration")
        return

    logger.info(f"Processing {len(feed_tasks)} feeds: {[task[0] for task in feed_tasks]}")

    # Process feeds sequentially
    for key, url, num_entries in feed_tasks:
        try:
            generate_summaries(client, model, conn, key, url, num_entries, max_retries=max_retries)
        except Exception as e:
            logger.error(f"Error processing feed {key}: {e}", exc_info=True)
            # Continue with the next feed

    # Close the database connection
    conn.close()
    logger.info('NetNews feed processing completed successfully')


if __name__ == '__main__':
    main()
