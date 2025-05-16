import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
from datetime import datetime

filename = "trt_articles_Merged.csv"
df = pd.read_csv(filename)
topic = input("Enter topic: ")

article_links = np.array(df["Link"])


article_contents = []
authors = []

i = 1
for link in article_links:
    try:
        response = requests.get(link)
        print(f"{i} Getting article from link: {link}")
        i += 1
        soup = BeautifulSoup(response.text, "html.parser")

        paragraphs = soup.find_all("p")

        article_text = None
        if paragraphs:
            article_text = " ".join([para.get_text() for para in paragraphs])
        else:
            print("Article not found")

        article_contents.append(article_text)

        author = "TRT World"

        authors.append(author)

    except Exception as e:
        print(f"Failed to scrape content for {link}: {e}")
        article_contents.append("Content could not be scraped")
        authors.append("Unknown")

df["Article_Content"] = article_contents
df["Author"] = authors


output_filename = f"trt_articles_{topic}.csv"
df.to_csv(output_filename, index=False)

print(f"Updated file saved to {output_filename}")
