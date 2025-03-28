import feedparser  # Library to fetch and parse RSS feeds
import re  # Regular expressions for text processing
from collections import Counter  # To find most common words in text


def extract_keywords(text, num_keywords=5):
    """
    Extract top keywords from the given text.
    
    Parameters:
    text (str): The input text from which keywords need to be extracted.
    num_keywords (int): Number of keywords to extract. Default is 5.
    
    Returns:
    list: A list of extracted keywords.
    """
    if not text:
        return []  # If text is empty or None, return an empty list
    
    words = re.findall(r'\b\w{4,}\b', text.lower())  # Extract words with 4 or more letters
    
    # Common words to ignore as they don't add much meaning
    common_words = {"the", "and", "with", "from", "this", "that", "said", "will", "have"}
    filtered_words = [word for word in words if word not in common_words]
    
    return [word for word, _ in Counter(filtered_words).most_common(num_keywords)]  # Return top keywords


def summarize_text(text, max_words=20):
    """
    Summarize a given text to a specified number of words.
    
    Parameters:
    text (str): The input text to be summarized.
    max_words (int): Maximum number of words in the summary. Default is 20.
    
    Returns:
    str: A summarized version of the text.
    """
    if not text:
        return "Summary not available"  # Return a default message if text is empty
    
    words = text.split()
    return " ".join(words[:max_words]) + ('...' if len(words) > max_words else '')  # Append '...' if text is truncated


def fetch_news(company_name, num_articles=10):
    """
    Fetch top news articles about a company from Bing News RSS feed.
    
    Parameters:
    company_name (str): The company name to search for in news articles.
    num_articles (int): Number of articles to fetch. Default is 10.
    
    Returns:
    list: A list of dictionaries, each containing article details.
    """
    search_url = f"https://www.bing.com/news/search?q={company_name}&format=rss"  # Bing News RSS feed URL
    
    try:
        feed = feedparser.parse(search_url)  # Fetch and parse the RSS feed
        
        if not feed.entries:
            print("No news articles found.")
            return []  # If no news found, return an empty list
        
        articles = []
        
        for entry in feed.entries[:num_articles]:  # Limit articles directly while iterating
            title = entry.get("title", "No Title")  # Fetch the article title, default to "No Title" if missing
            description = entry.get("summary", "Summary not available")  # Get the summary (description)
            link = entry.get("link", "#")  # Fetch the article link
            published_date = entry.get("published", "Unknown Date")  # Fetch the publication date
            
            topics = extract_keywords(description)  # Extract keywords from the description
            summary = summarize_text(description)  # Summarize the article description
            
            articles.append({
                "Title": title,
                "Summary": summary,
                "Topics": topics,
                "Link": link,
                "Published Date": published_date
            })
        
        return articles  # Return the list of articles
    
    except Exception as e:
        print(f"Error fetching news: {e}")  # Print the error message if fetching fails
        return []  # Return an empty list in case of an error
