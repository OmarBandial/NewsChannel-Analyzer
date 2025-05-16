import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import json

topic = input("Enter topic: ")

filename = f"BBC_articles_{topic}_final.csv"
df = pd.read_csv(filename)

article_links = np.array(df["Link"])

article_contents = []
authors = []

i = 1
print("Links...")
for link in article_links:
    try:
        response = requests.get(link)
        print(f"{i} Getting article from link: {link}")
        i += 1
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract article content
        article_tag = soup.find("article")
        if article_tag:
            paragraphs = article_tag.find_all("p")
            if paragraphs:
                article_text = " ".join([para.get_text() for para in paragraphs])
            else:
                article_text = "No article content found"
        else:
            article_text = "No article tag found"
        article_contents.append(article_text)

        # Extract author from JSON-LD
        author = "BBC"  # Default author
        script_tag = soup.find("script", type="application/ld+json")
        if script_tag:
            try:
                json_data = json.loads(script_tag.string)
                if isinstance(json_data, dict):
                    if "author" in json_data:
                        author_info = json_data["author"]
                        if isinstance(author_info, dict) and "name" in author_info:
                            author = author_info["name"]
                        elif isinstance(author_info, list) and "name" in author_info[0]:
                            author = author_info[0]["name"]
            except json.JSONDecodeError:
                pass
        authors.append(author)

    except Exception as e:
        print(f"Failed to scrape content for {link}: {e}")
        article_contents.append("Content could not be scraped")
        authors.append("BBC")

df["Article_Content"] = article_contents
df["Author"] = authors

output_filename = f"bbc_articles_dataset.csv"
df.to_csv(output_filename, index=False)

print(f"Updated file saved to {output_filename}")
