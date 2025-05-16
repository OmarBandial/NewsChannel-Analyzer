from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
from datetime import datetime
topic=input("Enter the topic you want to search for: ")
processed_topic = topic.strip().replace(' ', '%20')

url = f"https://www.trtworld.com/search?q={processed_topic}"


chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(
    service=ChromeService(ChromeDriverManager().install()), options=chrome_options
)

driver.get(url)
time.sleep(3)

data = {
    "Source": [],
    "Link": [],
    "Headline": [],
    "Description": [],
    "Date": [],
    "Timestamp": [],
    "Topic": [],
    "Author": [],
    "Article_Content": [],
}


def scrape_articles():
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "div.Card.Card-Search")
            )
        )
    except Exception as e:
        print(f"Timeout while waiting for articles: {e}")
        return

    articles = driver.find_elements(By.CSS_SELECTOR, "div.Card.Card-Search")

    for article in articles:
        try:
            source = "TRT World"

            link_element = article.find_element(By.TAG_NAME, "a")
            link = link_element.get_attribute("href")
            print(f"Article Link: {link}")

            headline_element = article.find_element(
                By.CSS_SELECTOR, "div.news-title h3"
            )
            headline = headline_element.text if headline_element else None

            date_element = article.find_element(By.CSS_SELECTOR, "span.news-date")
            date = date_element.text if date_element else None

            description_element = article.find_element(
                By.CSS_SELECTOR, "div.news-summary p"
            )
            description = description_element.text if description_element else None

            data["Source"].append(source)
            data["Link"].append(link)
            data["Headline"].append(headline)
            data["Description"].append(description)
            data["Date"].append(date)
            data["Timestamp"].append(datetime.now)
            data["Topic"].append(topic)
            data["Article_Content"].append("-")
            data["Author"].append("-")

        except Exception as e:
            print(f"Error scraping article: {e}")


scrape_articles()

for i in range(50):
    try:
        print(f"Loading more articles, attempt {i+1}...")

        load_more_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "btn-loadmore"))
        )

        load_more_button.click()

        time.sleep(3)

        scrape_articles()

    except Exception as e:
        print(f"No more content to load or unable to click the button: {e}")
        break

size = len(data["Source"])
timestamps = [datetime.now() for _ in range(size)]
topics = [topic for _ in range(size)]


df = pd.DataFrame(data)
df.to_csv(f"trt_articles_{topic}.csv", index=False)
print("Articles scraped successfully!")

driver.quit()
