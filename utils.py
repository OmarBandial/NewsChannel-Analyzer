# utils.py
import re
import string
from transformers import pipeline
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from transformers import AutoTokenizer


def preprocess_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r"http\S+|www\S+|https\S+", "", text)  # remove URLs
    text = re.sub(r"[^\w\s\.\,\!\?\:\;]", "", text)      # keep letters, numbers, whitespace, standard punctuation
    text = re.sub(r"\s+", " ", text).strip()
    return text

# Load pipelines/models once
sentiment_pipeline = pipeline(
    "sentiment-analysis",
    model="cardiffnlp/twitter-roberta-base-sentiment"
)
summarizer = pipeline(
    "summarization",
    model="facebook/bart-large-cnn"
)
keyword_model = SentenceTransformer('distilbert-base-nli-mean-tokens')

def classify_sentiment(text: str):
    text = preprocess_text(text)
    if not text:
        return "Neutral", 0.0

    try:
        result = sentiment_pipeline(text[:1024])[0]
        label_map = {"LABEL_0": "Negative", "LABEL_1": "Neutral", "LABEL_2": "Positive"}
        sentiment = label_map.get(result['label'], "Neutral")
        score_pct = result['score'] * 100
        return sentiment, score_pct
    except Exception:
        return "Neutral", 0.0

# def get_summary(text: str):
    # text = preprocess_text(text)
    # if not text:
    #     return "No summary available."
    # try:
    #     summ = summarizer(text, max_length=130, min_length=30, do_sample=False)[0]
    #     return summ['summary_text']
    # except Exception:
    #     return "Failed to generate summary."
tokenizer = AutoTokenizer.from_pretrained("facebook/bart-large-cnn")
def get_summary(text: str, max_chunk_tokens: int = 900):
    """
    If `text` token-length > model max (1024), split into chunks of
    roughly `max_chunk_tokens` tokens, summarize each, and concat results.
    """
    text = preprocess_text(text)
    if not text:
        return "No summary available."

    # Tokenize once to get total length
    tokens = tokenizer.encode(text, return_tensors="pt")[0]
    total_len = tokens.size(0)

    # If within limit, summarize in one go
    if total_len <= max_chunk_tokens:
        try:
            out = summarizer(text, max_length=130, min_length=30, do_sample=False)
            return out[0]["summary_text"]
        except Exception:
            return "Failed to generate summary."

    # Otherwise, split the text into overlapping chunks of words
    words = text.split()
    # estimate words per chunk: assume avg 1.3 tokens per word
    words_per_chunk = int(max_chunk_tokens / 1.3)
    summaries = []
    for i in range(0, len(words), words_per_chunk):
        chunk = " ".join(words[i : i + words_per_chunk])
        try:
            out = summarizer(chunk, max_length=130, min_length=30, do_sample=False)
            summaries.append(out[0]["summary_text"])
        except Exception:
            continue

    if summaries:
        return " ".join(summaries)
    else:
        return "Failed to generate summary."

def get_keywords(text: str, top_n: int = 50):
    text = preprocess_text(text)
    words = list({w for w in text.split() if w.isalpha() and len(w) > 2})
    if not words:
        return []
    try:
        embeddings = keyword_model.encode(words)
        text_emb = keyword_model.encode([text])[0]
        sims = cosine_similarity([text_emb], embeddings)[0]
        top_idxs = sims.argsort()[-top_n:][::-1]
        return [words[i] for i in top_idxs]
    except Exception:
        return []

def generate_wordcloud(keywords):
    if not keywords:
        return None
    kw_str = " ".join(keywords)
    wc = WordCloud(width=800, height=400, background_color="black").generate(kw_str)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    return fig
