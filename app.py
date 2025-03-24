import gradio as gr
import requests
from threading import Thread
import uvicorn
from fastapi import FastAPI, Query
import os
from collections import defaultdict
from deep_translator import GoogleTranslator
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from utils.scraper import fetch_news
from utils.sentiment import process_articles
from utils.tts import generate_hindi_tts

app = FastAPI()

# ✅ Serving audio files
AUDIO_DIR = "/tmp/audio"
os.makedirs(AUDIO_DIR, exist_ok=True)  
app.mount("/audio", StaticFiles(directory=AUDIO_DIR), name="audio")

@app.get("/get_audio")
def get_audio(filename: str):
    file_path = os.path.join(AUDIO_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="audio/mpeg", filename=filename)
    return {"error": "File not found"}

@app.get("/news")
def analyze_news(company: str = Query(..., description="Company name for news analysis")):
    articles = fetch_news(company)[:10]  
    processed_articles = process_articles(articles)

    for article in processed_articles:
        article.pop("Link", None)
        article.pop("Published Date", None)

    sentiment_distribution = defaultdict(int)
    topic_sets = []
    coverage_differences = []

    for idx, article in enumerate(processed_articles):
        sentiment = article.get("Sentiment", "Neutral").capitalize()
        if sentiment in ["Positive", "Negative", "Neutral"]:
            sentiment_distribution[sentiment] += 1  
        topic_sets.append(set(article.get("Topics", [])))  

    for i in range(len(processed_articles)):
        for j in range(i + 1, len(processed_articles)):
            title_i, sentiment_i = processed_articles[i].get("Title", "Unknown"), processed_articles[i].get("Sentiment", "Neutral")
            title_j, sentiment_j = processed_articles[j].get("Title", "Unknown"), processed_articles[j].get("Sentiment", "Neutral")

            comparison = f"Article {i+1} discusses '{title_i}', while Article {j+1} covers '{title_j}'."
            impact = f"'{title_i}' focuses on {sentiment_i}, whereas '{title_j}' presents a {sentiment_j} viewpoint."
            coverage_differences.append({"Comparison": comparison, "Impact": impact})

    common_topics = set.intersection(*topic_sets) if topic_sets else set()
    unique_topics = {f"Unique Topics in Article {i+1}": list(topic_sets[i] - common_topics) for i in range(len(topic_sets)) if topic_sets[i]}

    final_sentiment_en = f"{company}’s latest news coverage is "
    if sentiment_distribution["Positive"] > sentiment_distribution["Negative"] and sentiment_distribution["Positive"] > sentiment_distribution["Neutral"]:
        final_sentiment_en += "mostly positive. Market sentiment appears optimistic, with potential growth opportunities."
    elif sentiment_distribution["Negative"] > sentiment_distribution["Positive"] and sentiment_distribution["Negative"] > sentiment_distribution["Neutral"]:
        final_sentiment_en += "mostly negative. There are concerns impacting market confidence and stability."
    elif sentiment_distribution["Neutral"] > sentiment_distribution["Positive"] and sentiment_distribution["Neutral"] > sentiment_distribution["Negative"]:
        final_sentiment_en += "mostly neutral. The news coverage lacks strong opinions, indicating market uncertainty or balanced perspectives."
    else:
        final_sentiment_en += "a mix of opinions, with no clear dominance of positive, negative, or neutral sentiments."

    try:
        final_sentiment_hi = GoogleTranslator(source="auto", target="hi").translate(final_sentiment_en)
    except Exception:
        final_sentiment_hi = "त्रुटि: अनुवाद विफल।"

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
            "Audio Filename": audio_filename  
        }
    }

# ✅ FastAPI runs inside Gradio
def get_news_sentiment(company):
    api_url = "https://sivapurush-sankaripugal-app.hf.space/news"
    response = requests.get(api_url, params={"company": company})
    if response.status_code == 200:
        result = response.json()
        audio_filename = result.get("Final Sentiment Analysis", {}).get("Audio Filename", None)
        audio_path = f"https://sivapurush-sankaripugal-app.hf.space/audio/{audio_filename}" if audio_filename else None
        return result, audio_path
    return {"error": f"API request failed with status {response.status_code}"}, None

# ✅ Expose API under `/api`
with gr.Blocks() as demo:
    gr.Markdown("# 📰 News Sentiment Analysis")
    company_input = gr.Textbox(label="Enter Company Name")
    output_json = gr.JSON(label="Sentiment Analysis Result")
    audio_output = gr.Audio(label="Hindi Speech")
    analyze_btn = gr.Button("Analyze")
    analyze_btn.click(get_news_sentiment, inputs=company_input, outputs=[output_json, audio_output])

# ✅ Run Gradio with FastAPI inside it
app = gr.mount_gradio_app(app, demo, path="/")
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
