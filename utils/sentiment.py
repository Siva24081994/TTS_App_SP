from transformers import pipeline
from typing import List, Dict, Union
from collections import Counter
import itertools

class SentimentAnalyzer:
    def __init__(self, model_name="nlptown/bert-base-multilingual-uncased-sentiment"):
        """
        Initialize the sentiment analysis pipeline using a lightweight pre-trained model.
        This model supports multiple languages and provides sentiment classification.
        """
        print("Loading sentiment analysis model...")
        self.sentiment_pipeline = pipeline("sentiment-analysis", model=model_name)
        print("\u2713 Sentiment analysis model loaded")

    def analyze_text(self, text: str) -> Dict[str, Union[str, float]]:
        """
        Analyze the sentiment of a given text input.
        If the text is too long (more than 512 characters), it is truncated.
        """
        max_length = 512
        if len(text) > max_length:
            text = text[:max_length]  # Truncate if too long
        
        try:
            result = self.sentiment_pipeline(text)[0]
            return {"label": result["label"].upper(), "score": float(result["score"])}
        except Exception as e:
            print(f"Error analyzing sentiment: {str(e)}")
            return {"label": "NEUTRAL", "score": 0.5}  # Default to neutral sentiment in case of an error

    def analyze_article(self, article: Dict[str, str]) -> Dict[str, Union[str, float]]:
        """
        Perform sentiment analysis on a news article.
        It considers both the title and summary (if available) for better accuracy.
        """
        title_sentiment = self.analyze_text(article.get("Title", ""))
        summary_sentiment = self.analyze_text(article.get("Summary", "")) if article.get("Summary") else None
        
        if summary_sentiment:
            # Weighted combination: title contributes 40% and summary contributes 60%
            combined_score = (title_sentiment["score"] * 0.4 + summary_sentiment["score"] * 0.6)
            label = "POSITIVE" if combined_score >= 0.6 else "NEGATIVE" if combined_score <= 0.4 else "NEUTRAL"
            return {"label": label, "score": combined_score, "title_sentiment": title_sentiment, "summary_sentiment": summary_sentiment}
        
        return {"label": title_sentiment["label"], "score": title_sentiment["score"], "title_sentiment": title_sentiment, "summary_sentiment": None}


def extract_topics(text: str) -> List[str]:
    """
    Mock function to extract topics from a given text.
    This function simply considers the first few words of the text as topics.
    """
    words = text.lower().split()
    return list(set(words[:5]))  # Pick first 5 words as topics (basic method)


def compare_articles(articles: List[Dict[str, str]]) -> Dict:
    """
    Analyze topic overlap and differences between articles.
    This helps in understanding variations in news coverage.
    """
    topic_data = {idx: extract_topics(article.get("Summary", "")) for idx, article in enumerate(articles)}
    
    common_topics = list(set(itertools.chain(*topic_data.values())))  # Find common topics across articles
    coverage_differences = []
    
    for (idx1, topics1), (idx2, topics2) in itertools.combinations(topic_data.items(), 2):
        unique_1 = set(topics1) - set(topics2)
        unique_2 = set(topics2) - set(topics1)
        comparison = f"Article {idx1+1} focuses on {', '.join(unique_1) or 'general news'}, whereas Article {idx2+1} discusses {', '.join(unique_2) or 'general news'}."
        impact = "These differences highlight varying perspectives on the topic."
        coverage_differences.append({"Comparison": comparison, "Impact": impact})
    
    return {"Coverage Differences": coverage_differences, "Topic Overlap": {"Common Topics": common_topics}}


def process_articles(articles: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Process a list of news articles by performing sentiment analysis on each one.
    This function modifies the input articles by adding a 'Sentiment' field.
    """
    analyzer = SentimentAnalyzer()
    
    for article in articles:
        print(f"\nAnalyzing sentiment for: {article['Title'][:100]}...")  # Display the first 100 characters of the title
        sentiment = analyzer.analyze_article(article)
        article["Sentiment"] = sentiment["label"]  # Store only the sentiment label
    
    return articles  # Return processed articles with sentiment labels
