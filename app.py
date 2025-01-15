import praw
import schedule
import time
from datetime import datetime, timedelta
import logging
from datetime import datetime
from dotenv import load_dotenv
import os
import re
from groq import Groq
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Groq API Authentication
groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])

# Initialize Reddit instance
reddit = praw.Reddit(
    client_id=os.environ['REDDIT_CLIENT_ID'],
    client_secret=os.environ['REDDIT_CLIENT_SECRET'],
    username=os.environ['REDDIT_USERNAME'],
    password=os.environ['REDDIT_PASSWORD'],
    user_agent=os.environ['REDDIT_USER_AGENT']
)

# Function to generate AI content using Groq
def generate_content(prompt):
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            max_tokens=1000
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        logging.error(f"Error generating content: {e}")
        return None

def extract_title(text):
    # Regex pattern to match the content after 'Title:' and within quotes
    pattern = r'\*\*Title:\*\*\s*"([^"]+)"'
    
    match = re.search(pattern, text)
    
    if match:
        title = match.group(1) 
        # Remove the title line from the text
        text = re.sub(r'\*\*Title:\*\*\s*"[^"]+"\s*', '', text).strip()          
        return title, text  # Return both the title and the modified text
    else:
        return None, text  # Return None if no title found

# Function to post on Reddit
def post_on_reddit(prompt, subreddit_name):
    content = generate_content(prompt)
    
    if content:
        # Generate title separately from content to avoid repetition
        title, body_content = extract_title(content)

        # Check if title was successfully extracted
        if title:
            # Ensure the title doesn't appear again in the body
            body_content = body_content.strip()

            try:
                subreddit = reddit.subreddit(subreddit_name)
                post = subreddit.submit(title, selftext=body_content)
                logging.info(f"Post successful: {post.url}")
            except Exception as e:
                logging.error(f"Error posting on Reddit: {e}")
        else:
            logging.warning("No title extracted, post skipped.")
    else:
        logging.warning("No content generated, post skipped.")

# Function to schedule the daily post
def schedule_daily_post(prompt, subreddit_name, time_of_day):
    schedule.every().day.at(time_of_day).do(post_on_reddit, prompt=prompt, subreddit_name=subreddit_name, time_of_day=time_of_day)

    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

## For Demonstration
# Function to schedule a post 15 seconds from the current time
def schedule_post_test(prompt, subreddit_name):
    now = datetime.now()
    post_time = now + timedelta(seconds=5)  # Current time + 15 seconds

    # Format the time in 'HH:MM' format for scheduling
    formatted_time = post_time.strftime("%H:%M:%S")
    
    logging.info(f"Scheduled post to Reddit at {formatted_time} (in 5 seconds from now)")

    schedule.every().day.at(formatted_time).do(post_on_reddit, prompt=prompt, subreddit_name=subreddit_name)

    while True:
        schedule.run_pending()
        time.sleep(1)  

# Function to generate comment on a post (Bonus Feature)
def comment_on_post(post_id, prompt):
    try:
        post = reddit.submission(id=post_id)
        comment_content = generate_content(prompt)
        
        if comment_content:
            post.reply(comment_content)
            logging.info(f"Comment posted on {post_id}: {comment_content}")
    except Exception as e:
        logging.error(f"Error commenting on post {post_id}: {e}")

if __name__ == "__main__":
    PROMPT = "Generate an engaging and interesting Reddit post on the topic of technology and innovation."
    SUBREDDIT = "testingground4bots"
    TIME_OF_DAY = "09:00"  # Set your preferred time of the day for the post

    try:
        logging.info("Reddit bot starting...")
        comment_on_post("1i23suk" , "Write a comment on a tech post related to new upcoming tech")
        # schedule_post_test(PROMPT, SUBREDDIT)  ## For Demonstration  or to use with task scheduler
        schedule_daily_post(PROMPT, SUBREDDIT, TIME_OF_DAY)
    except Exception as e:
        logging.error(f"Error in bot execution: {e}")