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

# Set the base URL for Fox News search
topic=input("Enter the topic you want to search for: ")
processed_topic = topic.strip().replace(' ', '%20')
url = f"https://www.foxnews.com/search-results/search#q={processed_topic}"
source = "Fox News"

# Setup Selenium WebDriver in headless mode
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run headless Chrome
chrome_options.add_argument("--no-sandbox")  # Bypass OS security model
chrome_options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(
    service=ChromeService(ChromeDriverManager().install()), options=chrome_options
)

# # Load the search page
# driver.get(url)
# time.sleep(3)  # Let the page load

# # Locate the search box and enter the search term
# search_box = WebDriverWait(driver, 10).until(
#     EC.presence_of_element_located((By.CSS_SELECTOR, "div.search-form input"))
# )
# search_box.send_keys(search_term)

# # Click the search button
# search_button = driver.find_element(By.CSS_SELECTOR, "div.search-form div.button a")
# search_button.click()

# time.sleep(3)  # Allow the search results to load

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
    # Wait for articles to be present on the search results page
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located(
            (
                By.CSS_SELECTOR,
                "article.article",
            )
        )
    )

    articles = driver.find_elements(By.CSS_SELECTOR, "article.article")

    for article in articles:
        try:
            # Fetch the article link correctly from the <h2 class="title"><a href="">
            link_element = article.find_element(By.CSS_SELECTOR, "h2.title a")
            link = link_element.get_attribute("href") if link_element else None
            print(f"Article Link: {link}")

            # Fetch the article headline
            headline = link_element.text if link_element else None

            # Fetch the article description
            description_element = article.find_element(
                By.CSS_SELECTOR, "div.content p.dek a"
            )
            description = description_element.text if description_element else None

            # Fetch the article date
            date_element = article.find_element(By.CSS_SELECTOR, "span.time")
            date = date_element.text if date_element else "Unknown"

            # Add the extracted data to the dictionary
            data["Source"].append(source)
            data["Link"].append(link)
            data["Headline"].append(headline)
            data["Description"].append(description)
            data["Date"].append(date)
            data["Timestamp"].append(datetime.now())
            data["Topic"].append(topic)
            data["Article_Content"].append("-")
            data["Author"].append("-")

        except Exception as e:
            print(f"Error scraping article: {e}")


scrape_articles()

# Loop for pagination or showing more content
for i in range(5):
    try:
        print(f"Page {i+1}...")

        # Wait for the "Load More" button to be clickable
        load_more_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div.button.load-more a"))
        )

        # Click the "Load More" button to load more content
        load_more_button.click()
        time.sleep(3)  # Allow time for the new content to load

        # Scrape articles or load more content
        scrape_articles()

    except Exception as e:
        print(f"No more content to load or unable to click the 'Load More' button: {e}")
        break

# Save the data to a CSV file
df = pd.DataFrame(data)
df.to_csv(f"{source}_articles_{topic}.csv", index=False)
print("Articles scraped successfully!")

# Close the driver
driver.quit()
