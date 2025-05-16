from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
import re
from datetime import datetime



topic = input("Enter topic: ")
topic_formatted = topic.strip().replace(' ', '+')

url = f"https://www.dawn.com/search?cx=016184311056644083324%3Aa1i8yd7zymy&cof=FORID%3A10&ie=UTF-8&q={topic_formatted}"
source = "Dawn News"

# Setup Selenium WebDriver in headless mode
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run headless Chrome
chrome_options.add_argument("--no-sandbox")  # Bypass OS security model
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
    # Wait until articles are present in the DOM
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located(
            (
                By.CSS_SELECTOR,
                "div.gsc-webResult.gsc-result",  # Selector for the article containers
            )
        )
    )

    # Find all article elements
    articles = driver.find_elements(By.CSS_SELECTOR, "div.gsc-webResult.gsc-result")

    for article in articles:
        try:
            # Extract link
            link_element = article.find_element(
                By.CSS_SELECTOR, "div.gs-title a.gs-title"
            )
            link = link_element.get_attribute("href")
            print(f"Article Link: {link}")

            # Extract headline
            headline_element = article.find_element(By.CSS_SELECTOR, "div.gs-title")
            headline = headline_element.text if headline_element else None

            # Extract description
            description_element = article.find_element(
                By.CSS_SELECTOR, "div.gs-snippet"
            )
            description = description_element.text if description_element else None

            # Extract date (this might be embedded in the snippet text)
            snippet_element = article.find_element(By.CSS_SELECTOR, "div.gs-snippet")
            date_match = re.search(r"\d{2}-[a-zA-Z]{3}-\d{4}", snippet_element.text)
            date = date_match.group(0) if date_match else "Unknown"

            # Append data to dictionary (you will need to define these variables before the loop)
            data["Source"].append("DAWN.COM")  # Assuming source is DAWN
            data["Link"].append(link)
            data["Headline"].append(headline)
            data["Description"].append(description)
            data["Date"].append(date)
            data["Timestamp"].append(datetime.now())
            data["Topic"].append(topic)  # Assuming topic is predefined
            data["Article_Content"].append("-")  # Article content is not fetched yet
            data["Author"].append("-")  # Author not available in the structure

        except Exception as e:
            print(f"Error scraping article: {e}")


scrape_articles()



for i in range(10):
    try:
        print(f"Page {i+1}...")

        # Wait for the page cursor elements to be clickable
        page_buttons = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "div.gsc-cursor-page")
            )
        )

        # Ensure we're not on the last page
        if i < len(page_buttons):
            # Click the next page button
            next_page_button = page_buttons[i + 1]  # Select the next page button
            driver.execute_script("arguments[0].click();", next_page_button)
            time.sleep(3)  # Allow time for the new page content to load

            # Scrape articles on the new page
            scrape_articles()
        else:
            print("No more pages to load.")
            break

    except Exception as e:
        print(f"No more content to load or unable to navigate to the next page: {e}")
        break


df = pd.DataFrame(data)
df.to_csv(f"{source}_articles_{topic}.csv", index=False)
print("Articles scraped successfully!")


driver.quit()
