import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
from datetime import datetime

topic = input("Enter topic: ")

filename = f"cnn_articles_{topic}.csv"
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

        paragraphs = soup.find_all("p")

        article_text = None
        if paragraphs:
            article_text = " ".join([para.get_text() for para in paragraphs])
        else:
            print("Article not found")

        article_contents.append(article_text)

        author_element = soup.find("span", class_="byline__name")
        if author_element:
            author = author_element.get_text().strip()
        else:
            author = "CNN"
            print("Author not found...")

        authors.append(author)

    except Exception as e:
        print(f"Failed to scrape content for {link}: {e}")
        article_contents.append("Content could not be scraped")
        authors.append("CNN")

df["Article_Content"] = article_contents
df["Author"] = authors


output_filename = f"cnn_articles_{topic}.csv"
df.to_csv(output_filename, index=False)

print(f"Updated file saved to {output_filename}")
