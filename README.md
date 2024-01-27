# **Tired of too much news?**
## You need Net News 😎 

NetNews is a simple solution to all the noisy news - let ChatGPT's AI summarize it for you.

Enter the RSS feeds you wish to summarize into the rssfeeds.ini file and tell ChatGPT how many summaries you want.

**IMPORTANT:** Remember to rename the dot.env file to .env and add your OPENAI API KEY and set the AI_MODEL to your preferred engine. 

Produces a simple text file called: `TodaysNetNews.txt`

Here's a sample of the output:

```Feed: cbc tops stories
Title: Cap on international study permits sparks fear of rising tuition, program cuts, layoffs on campus
Link: https://www.cbc.ca/news/canada/campus-impact-intl-students-cap-1.7094629?cmp=rss
Summary: The Canadian federal government is lifting the work limit for international students next month. This decision has been welcomed by those who believe it is long overdue.
---
Feed: cbc offbeat
Title: Hundreds of 'perfectly good boots' trashed at Yellowknife dump, people snatch them up
Link: https://www.cbc.ca/news/canada/north/yellowknife-dump-good-boots-1.4638760?cmp=rss
Summary: Crates of steel-toe boots mysteriously appeared at the Yellowknife dump, but have since been mostly removed. The origins and reasons for the boots being there remain unclear.
```

### NetNews is quick and can process multiple feeds at once!

The multithreaded aspect of this code is implemented using Python's built-in `threading` module. Here's how it works:

1. The code first retrieves all the RSS feeds from the configuration file and stores them in the `rss_feeds` list. Each item in this list is a tuple containing the name of the feed, the URL of the feed, and the number of stories to summarize.

2. The code then creates a new thread for each RSS feed using the `threading.Thread` class. The target function of each thread is `generate_summaries`, and the arguments passed to this function are the name of the feed, the URL of the feed, and the number of stories to summarize. Each thread is appended to the `threads` list.

3. Once all the threads have been created, the code starts each thread with the `start` method. This causes each thread to run concurrently, meaning that the program can fetch and parse multiple RSS feeds at the same time.

4. Finally, the code waits for all threads to finish using the `join` method. This ensures that the main program does not exit until all threads have completed their tasks.

**This multithreaded approach allows the program to fetch and parse multiple RSS feeds in parallel, which can significantly improve performance when dealing with a large number of feeds.**