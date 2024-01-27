import os

import feedparser
import logging
import threading
import configparser
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

# Read the configuration file
config = configparser.ConfigParser()
config.read('config.ini')

AI_MODEL = config['DEFAULT']['AI_MODEL']
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
rss_feed = config['DEFAULT']['RSS_Feed']

client = OpenAI(api_key=OPENAI_API_KEY)

# Initialize an empty list to store the summaries
summaries = []

# Set up logging
logging.basicConfig(filename='app.log', level=logging.INFO)

# Function to summarize a text using AI
def get_summary(text):
    try:
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system",
                 "content": "You are a highly skilled AI trained in language comprehension and summarization. I would like you to read the following text and summarize it into a concise abstract paragraph. Aim to retain the most important points, providing a coherent and readable summary that could help a person understand the main points of the discussion without needing to read the entire text. Please avoid unnecessary details or tangential points."},
                {"role": "user", "content": text}
            ])
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Error summarizing text: {e}")
        return None

# Function to fetch and parse RSS feed and generate summaries
def generate_summaries(feed_name, feed_url, num_stories):
    try:
        # Fetch and parse the RSS feed
        feed = feedparser.parse(feed_url)

        # Iterate through the entries in the fetched feed
        for i, entry in enumerate(feed.entries):
            # Break the loop after the specified number of stories
            if i >= num_stories:
                break

            # Summarize the story's description using GPT-3
            summary = get_summary(entry.description)
            if summary is not None:
                with open('TodaysNetNews.txt', 'a') as f:
                    f.write(f"Feed: {feed_name}\nTitle: {entry.title}\nLink: {entry.link}\nSummary: {summary}\n---\n")

                # Add the summary to the list
                summaries.append(f"Feed: {feed_name}\nTitle: {entry.title}\nLink: {entry.link}\nSummary: {summary}\n---\n")
    except Exception as e:
        logging.error(f"Error fetching and parsing RSS feed: {e}")

# Create a thread for each RSS feed
threads = []
for feed_name, feed_url, num_stories in rss_feed:
    thread = threading.Thread(target=generate_summaries, args=(feed_name, feed_url, num_stories))
    threads.append(thread)
    thread.start()

# Wait for all threads to finish
for thread in threads:
    thread.join()