# NetNews Docker Compose Setup

This repository contains a Docker Compose configuration for running the NetNews application, which consists of two components:

1. **NetNewsCore**: Fetches RSS feeds, summarizes articles using OpenAI's API, and stores the summaries in a SQLite database.
2. **NetNewsWeb**: A web interface for viewing the summarized news articles.

## Prerequisites

- Docker and Docker Compose installed on your Synology NAS
- An OpenAI API key
- Synology DS423+ NAS (or compatible model)

## Setup Instructions

1. Clone this repository to your Synology NAS or copy the files to a directory on your NAS.

2. Create the required directory for persistent data:
   ```bash
   mkdir -p /volume1/docker/netnews
   ```

3. Copy the RSSFeeds.ini file to the persistent data directory:
   ```bash
   cp RSSFeeds.ini /volume1/docker/netnews/
   ```

4. Configure your OpenAI API key:

   Option 1: Edit the .env file in the NetNewsCore directory:
   ```bash
   nano core/.env
   ```
   Replace `your_openai_api_key` with your actual OpenAI API key.

   Option 2: Provide the API key directly when starting the containers (see next step).

5. Build and start the containers:
   ```bash
   OPENAI_API_KEY=your_openai_api_key docker-compose up -d
   ```
   Replace `your_openai_api_key` with your actual OpenAI API key. This will override any key set in the .env file.

6. The NetNewsCore container will run once and stop, while the NetNewsWeb container will continue running.

7. Access the web interface by navigating to `http://your-nas-ip:8081` in your web browser.

## Scheduling NetNewsCore

To run NetNewsCore at 5am daily to gather new data:

1. Open the Task Scheduler in your Synology DSM.
2. Create a new scheduled task.
3. Select "User-defined script" as the task type.
4. Set the schedule to run at 5am daily.
5. In the "Run command" field, enter:
   ```bash
   cd /path/to/netnews && OPENAI_API_KEY=your_openai_api_key docker-compose run netnewscore
   ```
   Replace `/path/to/netnews` with the actual path to the directory containing the compose.yaml file, and `your_openai_api_key` with your actual OpenAI API key.

   For better security, consider creating a script file with restricted permissions:
   ```bash
   echo '#!/bin/bash' > /volume1/docker/netnews/run_netnewscore.sh
   echo 'cd /path/to/netnews && OPENAI_API_KEY=your_openai_api_key docker-compose run netnewscore' >> /volume1/docker/netnews/run_netnewscore.sh
   chmod 700 /volume1/docker/netnews/run_netnewscore.sh
   ```
   Then in the Task Scheduler, use:
   ```bash
   /volume1/docker/netnews/run_netnewscore.sh
   ```

## Customizing RSS Feeds

To add or remove RSS feeds:

1. Edit the RSSFeeds.ini file in the persistent data directory:
   ```bash
   nano /volume1/docker/netnews/RSSFeeds.ini
   ```

2. Add or remove feeds in the format:
   ```
   Feed Name = Feed URL, Number of Articles to Summarize
   ```

3. Save the file.

4. The changes will take effect the next time NetNewsCore runs.

## Advanced Configuration

### Environment Variables

The following environment variables can be set in the `.env` file or passed directly to the container:

#### Required Settings:
- `OPENAI_API_KEY`: Your OpenAI API key
- `AI_MODEL`: The OpenAI model to use (default: gpt-3.5-turbo)

#### Performance Settings:
- `MAX_WORKERS`: Number of parallel workers for processing feeds (default: 3)
- `FEED_TIMEOUT`: Timeout in seconds for RSS feed requests (default: 30)
- `MAX_RETRIES`: Maximum number of retry attempts for API calls (default: 3)

#### Data Retention Settings:
- `RETENTION_DAYS`: Number of days to keep entries in the database (default: 30)

#### Logging Settings:
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) (default: INFO)
- `LOG_FILE`: Path to log file (default: netnews.log)

### Command-Line Arguments

NetNewsCore now supports command-line arguments for more flexible configuration:

```bash
docker-compose run netnewscore python /app/main.py [OPTIONS]
```

Available options:

#### Configuration Options:
- `--config PATH`: Path to RSS feeds configuration file
- `--db PATH`: Path to SQLite database file
- `--env PATH`: Path to .env file

#### Processing Options:
- `--workers N`: Number of parallel workers
- `--timeout N`: Timeout for RSS feed requests in seconds
- `--retention N`: Number of days to keep entries
- `--model MODEL`: OpenAI model to use
- `--max-retries N`: Maximum number of API call retries

#### Logging Options:
- `--log-level LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `--log-file PATH`: Path to log file

#### Feed Selection:
- `--feeds FEED [FEED ...]`: Specific feeds to process (by name)

Example to process only specific feeds with increased timeout:
```bash
docker-compose run netnewscore python /app/main.py --feeds "NYT World News" "CBC Technology & Science" --timeout 60
```

## Network Configuration

The Docker Compose configuration includes a bridge network that allows the containers to access the internet. This is necessary for:

1. Fetching RSS feeds from external sources
2. Communicating with the OpenAI API for generating summaries

The bridge network is configured automatically when you start the containers with Docker Compose.

## New Features and Improvements

The NetNewsCore component has been enhanced with several new features and improvements:

### Performance Improvements
- **Parallel Processing**: Process multiple RSS feeds simultaneously for faster execution
- **Database Indexing**: Improved database performance with indexes on frequently queried fields
- **Configurable Timeouts**: Adjust timeouts to handle slow RSS feeds

### Reliability Enhancements
- **Retry Mechanism**: Automatically retry failed API calls with exponential backoff
- **Improved Error Handling**: Better handling of network issues, API errors, and malformed feeds
- **Data Validation**: Validate feed entries before processing to prevent errors

### New Features
- **Data Retention Policy**: Automatically clean up old entries to manage database size
- **Feed Selection**: Process only specific feeds when needed
- **Comprehensive Logging**: Detailed logs with configurable log levels
- **Command-Line Interface**: Flexible configuration through command-line arguments

### Maintenance Improvements
- **Environment Variable Configuration**: Easy configuration through environment variables
- **Code Organization**: Better structured code for easier maintenance
- **Documentation**: Comprehensive documentation of features and configuration options

## Troubleshooting

If you encounter issues:

1. Make sure the `/volume1/docker/netnews` directory exists and is writable.
2. Check that your OpenAI API key is valid.
3. Verify that your NAS can access the internet to fetch RSS feeds and communicate with the OpenAI API.
4. Ensure that your Synology NAS firewall settings allow outbound connections to the internet.
5. Check the logs of the containers:
   ```bash
   docker-compose logs netnewscore
   docker-compose logs netnewsweb
   ```
6. Review the log file specified in the LOG_FILE environment variable for detailed error information.
7. If you're having network connectivity issues, try restarting the Docker service on your Synology NAS.
