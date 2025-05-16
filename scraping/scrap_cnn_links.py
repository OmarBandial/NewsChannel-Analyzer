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

# CNN search results URL
topic = input("Enter topic: ")
topic_formatted = topic.strip().replace(' ', '+')

url = f"https://edition.cnn.com/search?q={topic_formatted}&from=0&size=10&page=1&sort=newest&types=article&section="

# Setup Selenium WebDriver in headless mode
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run headless Chrome
chrome_options.add_argument("--no-sandbox")  # Bypass OS security model
chrome_options.add_argument(
    "--disable-dev-shm-usage"
)  # Overcome limited resource problems

driver = webdriver.Chrome(
    service=ChromeService(ChromeDriverManager().install()), options=chrome_options
)


driver.get(url)
time.sleep(3)  # Let the page load

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


# Function to scrape articles from the current page
def scrape_articles():
    # Wait until the articles are present
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, 'div[data-component-name="card"]')
        )
    )

    articles = driver.find_elements(By.CSS_SELECTOR, 'div[data-component-name="card"]')

    for article in articles:
        try:
            source = "CNN"

            link_element = article.find_element(By.CSS_SELECTOR, "a.container__link")
            link = link_element.get_attribute("href")

            print(link)

            headline_element = article.find_element(
                By.CSS_SELECTOR, "span.container__headline-text"
            )
            headline = headline_element.text if headline_element else None

            date_element = article.find_element(By.CSS_SELECTOR, "div.container__date")
            date = date_element.text if date_element else None

            # Description
            description_element = article.find_element(
                By.CSS_SELECTOR, "div.container__description"
            )
            description = description_element.text if description_element else None

            # Append data to the dictionary
            data["Source"].append(source)
            data["Link"].append(link)
            data["Headline"].append(headline)
            data["Description"].append(description)
            data["Date"].append(date)

        except Exception as e:
            print(f"Error scraping article: {e}")


scrape_articles()

# Pagination loop

for i in range(10):
    try:
        print(f"Page {i+1}...")
        # Wait for the "Next Page" button to be clickable (Check if it exists and click)
        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div.pagination-arrow-right"))
        )

        # Click the Next button to navigate to the next page
        next_button.click()
        time.sleep(3)  # Allow time for the next page to load

        # Scrape articles from the new page
        scrape_articles()

    except Exception as e:
        print(f"No more pages to scrape or unable to click the next button: {e}")
        break


size = len(data["Source"])
timestamps = [datetime.now() for i in range(size)]
topics = [topic for i in range(size)]

data["Timestamp"] = timestamps
data["Topic"] = topics
data["Article_Content"] = "-"
data["Author"] = "-"

df = pd.DataFrame(data)
df.to_csv(f"cnn_articles_{topic}.csv", index=False)
print("Articles scraped successfully!")


driver.quit()
