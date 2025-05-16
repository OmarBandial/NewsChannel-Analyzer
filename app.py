import streamlit as st
import pandas as pd
import plotly.express as px
from utils import classify_sentiment, get_summary, generate_wordcloud, get_keywords
from scrapers import scrape_links, scrape_article

# Streamlit page config
st.set_page_config(page_title="News Channel Analyzer", layout="wide")
st.title("News Channel Analyzer")

st.markdown("""
This app will:
1. Scrape the latest articles on your chosen topic from multiple news channels
2. Classify each article's sentiment
3. Generate visualizations comparing sentiment across channels
4. Provide summaries and word clouds for each article
""")

# -- User inputs --
channels = ["BBC", "CNN", "Dawn News", "Fox News", "TRT News", "Al Jazeera"]
selected_channels = st.multiselect("Select news channels:", channels, default=["BBC", "CNN"])
topic = st.text_input("Enter topic:")
num_articles = st.slider("Number of articles per channel:", min_value=1, max_value=5, value=3)

# -- Analysis options --
st.subheader("Analysis Options")
col1, col2 = st.columns(2)
with col1:
    generate_summary = st.checkbox("Generate article summaries", value=True)
with col2:
    show_wordcloud = st.checkbox("Generate word clouds", value=True, disabled=not generate_summary)

# Helper function to truncate text
def truncate_text(text, max_tokens=900):
    words = text.split()
    if len(words) <= max_tokens:
        return text
    return " ".join(words[:max_tokens])

# -- Analyze button --
if st.button("Analyze"):
    if not topic.strip():
        st.warning("Please enter a topic.")
    elif not selected_channels:
        st.warning("Please select at least one news channel.")
    else:
        all_articles = []
        sentiment_data = []
        
        # Process each selected channel
        for channel in selected_channels:
            st.write(f"### Analyzing {channel}")
            
            # 1) Scrape article URLs
            with st.spinner("Scraping article links..."):
                links = scrape_links(channel, topic)
            
            if not links:
                st.warning(f"No articles found for {channel} on this topic.")
                continue
            
            st.success(f"Found {len(links)} articles. Processing top {min(num_articles, len(links))}.")
            
            # Process articles for this channel
            for i, url in enumerate(links[:num_articles], start=1):
                with st.expander(f"Article #{i} from {channel}"):
                    st.write(f"**URL:** {url}")
                    
                    try:
                        # Fetch and analyze article
                        with st.spinner("Fetching article content..."):
                            text = scrape_article(url, channel)
                        
                        if not text:
                            st.error("Failed to fetch article content.")
                            continue
                        
                        # Truncate text if needed
                        truncated_text = truncate_text(text)
                        if len(text.split()) > 900:
                            st.info("Note: Article was truncated to fit model limits.")
                        
                        with st.spinner("Analyzing sentiment..."):
                            sentiment, score = classify_sentiment(truncated_text)
                            st.write(f"**Sentiment:** {sentiment} ({score:.1f}%)")
                        
                        # Generate summary if requested
                        summary = None
                        if generate_summary:
                            with st.spinner("Generating summary..."):
                                summary = get_summary(truncated_text)
                                st.write("**Summary:**")
                                st.write(summary)
                            
                            # Generate word cloud if requested
                            if show_wordcloud:
                                with st.spinner("Generating word cloud..."):
                                    st.write("**Word Cloud:**")
                                    keywords = get_keywords(truncated_text)
                                    wordcloud = generate_wordcloud(keywords)
                                    if wordcloud:
                                        st.pyplot(wordcloud)
                        
                        # Store article data
                        article_data = {
                            "Channel": channel,
                            "URL": url,
                            "Sentiment": sentiment,
                            "Score": score,
                            "Summary": summary,
                            "Text": truncated_text
                        }
                        all_articles.append(article_data)
                        sentiment_data.append({
                            "Channel": channel,
                            "Sentiment": sentiment,
                            "Score": score
                        })
                        
                    except Exception as e:
                        st.error(f"Failed to analyze this article: {e}")
                        continue

        if not all_articles:
            st.error("No articles could be analyzed. Please try a different topic or channels.")
        else:
            # Convert to DataFrame for visualization
            df = pd.DataFrame(sentiment_data)
            
            # Create two columns for visualizations
            col1, col2 = st.columns(2)
            
            with col1:
                # Sentiment Score Bar Chart
                st.subheader("Average Sentiment Score by Channel")
                avg_scores = df.groupby("Channel")["Score"].mean().reset_index()
                fig = px.bar(avg_scores, x="Channel", y="Score", 
                           title="Average Sentiment Score by Channel",
                           color="Score",
                           color_continuous_scale=["red", "yellow", "green"])
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Sentiment Distribution Pie Chart
                st.subheader("Overall Sentiment Distribution")
                sentiment_counts = df["Sentiment"].value_counts().reset_index()
                sentiment_counts.columns = ["Sentiment", "Count"]
                fig2 = px.pie(sentiment_counts, values="Count", names="Sentiment",
                            title="Overall Sentiment Distribution",
                            color="Sentiment",
                            color_discrete_map={"Positive": "green", "Neutral": "yellow", "Negative": "red"})
                st.plotly_chart(fig2, use_container_width=True)
            
            # New Grouped Bar Chart for Sentiment Distribution by Channel
            st.subheader("Sentiment Distribution by Channel")
            # Create a pivot table for the grouped bar chart
            sentiment_by_channel = df.groupby(['Channel', 'Sentiment']).size().reset_index(name='Count')
            fig3 = px.bar(sentiment_by_channel, 
                         x="Channel", 
                         y="Count", 
                         color="Sentiment",
                         title="Number of Articles by Sentiment and Channel",
                         color_discrete_map={"Positive": "green", "Neutral": "yellow", "Negative": "red"},
                         barmode='group')
            st.plotly_chart(fig3, use_container_width=True)
