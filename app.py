import requests  # Used to make API requests
from threading import Thread  # Enables running tasks in the background
import uvicorn  # Runs FastAPI server
from fastapi import FastAPI, Query  # FastAPI framework for creating APIs
import os  # Helps with file operations
from collections import defaultdict  # Used to count occurrences efficiently
from deep_translator import GoogleTranslator  # For translating text
from fastapi.staticfiles import StaticFiles  # Helps serve static files like audio
from fastapi.responses import FileResponse  # Sends files as HTTP responses
from utils.scraper import fetch_news  # Fetches news articles
from utils.sentiment import process_articles  # Processes and analyzes sentiment
from utils.tts import generate_hindi_tts  # Converts text to Hindi speech

app = FastAPI()  # Initialize FastAPI application

# ✅ Directory to store audio files
AUDIO_DIR = "/tmp/audio"
os.makedirs(AUDIO_DIR, exist_ok=True)  # Create directory if it doesn’t exist
app.mount("/audio", StaticFiles(directory=AUDIO_DIR), name="audio")  # Serve audio files

# ✅ API to get saved audio files
@app.get("/get_audio")
def get_audio(filename: str):
    file_path = os.path.join(AUDIO_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="audio/mpeg", filename=filename)
    return {"error": "File not found"}  # If file doesn't exist

# ✅ API to analyze news sentiment for a company
@app.get("/news")
def analyze_news(company: str = Query(..., description="Company name for news analysis")):
    articles = fetch_news(company)[:10]  # Fetch and limit news to 10 articles
    processed_articles = process_articles(articles)  # Process and analyze sentiment
    
    # Remove unnecessary details from the response
    for article in processed_articles:
        article.pop("Link", None)
        article.pop("Published Date", None)
    
    sentiment_distribution = defaultdict(int)  # Count of positive, negative, neutral news
    topic_sets = []  # Store topics covered in each article
    coverage_differences = []  # Store differences in coverage

    # ✅ Analyze each article
    for idx, article in enumerate(processed_articles):
        sentiment = article.get("Sentiment", "Neutral").capitalize()
        if sentiment in ["Positive", "Negative", "Neutral"]:
            sentiment_distribution[sentiment] += 1  # Count each sentiment occurrence
        topic_sets.append(set(article.get("Topics", [])))  # Extract topics
    
    # ✅ Compare articles for coverage differences
    for i in range(len(processed_articles)):
        for j in range(i + 1, len(processed_articles)):
            title_i, sentiment_i = processed_articles[i].get("Title", "Unknown"), processed_articles[i].get("Sentiment", "Neutral")
            title_j, sentiment_j = processed_articles[j].get("Title", "Unknown"), processed_articles[j].get("Sentiment", "Neutral")
            
            comparison = f"Article {i+1} discusses '{title_i}', while Article {j+1} covers '{title_j}'."
            impact = f"'{title_i}' focuses on {sentiment_i}, whereas '{title_j}' presents a {sentiment_j} viewpoint."
            coverage_differences.append({"Comparison": comparison, "Impact": impact})
    
    # ✅ Identify common and unique topics
    common_topics = set.intersection(*topic_sets) if topic_sets else set()
    unique_topics = {f"Unique Topics in Article {i+1}": list(topic_sets[i] - common_topics) for i in range(len(topic_sets)) if topic_sets[i]}
    
    # ✅ Generate final sentiment summary in English
    final_sentiment_en = f"{company}’s latest news coverage is "
    if sentiment_distribution["Positive"] > sentiment_distribution["Negative"] and sentiment_distribution["Positive"] > sentiment_distribution["Neutral"]:
        final_sentiment_en += "mostly positive. Market sentiment appears optimistic, with potential growth opportunities."
    elif sentiment_distribution["Negative"] > sentiment_distribution["Positive"] and sentiment_distribution["Negative"] > sentiment_distribution["Neutral"]:
        final_sentiment_en += "mostly negative. There are concerns impacting market confidence and stability."
    elif sentiment_distribution["Neutral"] > sentiment_distribution["Positive"] and sentiment_distribution["Neutral"] > sentiment_distribution["Negative"]:
        final_sentiment_en += "mostly neutral. The news coverage lacks strong opinions, indicating market uncertainty or balanced perspectives."
    else:
        final_sentiment_en += "a mix of opinions, with no clear dominance of positive, negative, or neutral sentiments."
    
    # ✅ Translate sentiment summary to Hindi
    try:
        final_sentiment_hi = GoogleTranslator(source="auto", target="hi").translate(final_sentiment_en)
    except Exception:
        final_sentiment_hi = "त्रुटि: अनुवाद विफल।"  # Error message if translation fails
    
    # ✅ Convert Hindi summary to speech
    audio_path = generate_hindi_tts(final_sentiment_hi)
    audio_filename = os.path.basename(audio_path) if audio_path else None
    audio_path = f"/audio/{audio_filename}" if audio_filename else None
    
    return {
        "Company": company,
        "Articles": processed_articles,
        "Comparative Sentiment Score": {
            "Sentiment Distribution": dict(sentiment_distribution),
            "Coverage Differences": coverage_differences,
            "Topic Overlap": {
                "Common Topics": list(common_topics),
                **unique_topics
            }
        },
        "Final Sentiment Analysis": {
            "English": final_sentiment_en,
            "Hindi": final_sentiment_hi,
            "Audio Filename": audio_filename  # Path to generated Hindi speech
        }
    }

# ✅ Function to fetch sentiment analysis from the API

def get_news_sentiment(company):
    api_url = "https://sivapurush-sankaripugal-app.hf.space/news"
    response = requests.get(api_url, params={"company": company})
    if response.status_code == 200:
        result = response.json()
        audio_filename = result.get("Final Sentiment Analysis", {}).get("Audio Filename", None)
        audio_path = f"https://sivapurush-sankaripugal-app.hf.space/audio/{audio_filename}" if audio_filename else None
        return result, audio_path
    return {"error": f"API request failed with status {response.status_code}"}, None

# ✅ FastAPI integrates with Gradio UI
import gradio as gr  # Used to build the user interface
with gr.Blocks() as demo:
    gr.Markdown("# 📰 News Sentiment Analysis")
    company_input = gr.Textbox(label="Enter Company Name")
    output_json = gr.JSON(label="Sentiment Analysis Result")
    audio_output = gr.Audio(label="Hindi Speech")
    analyze_btn = gr.Button("Analyze")
    analyze_btn.click(get_news_sentiment, inputs=company_input, outputs=[output_json, audio_output])

# ✅ Mount Gradio UI with FastAPI
app = gr.mount_gradio_app(app, demo, path="/")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)  # Run FastAPI server
