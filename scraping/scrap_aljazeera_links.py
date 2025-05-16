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
from selenium.common.exceptions import TimeoutException, NoSuchElementException

topic = input("Enter topic: ")
processed_topic = topic.strip().replace(' ', '%20')
url = f"https://www.aljazeera.com/search/{processed_topic}"
source = "Al Jazeera"

# Setup Selenium WebDriver in headless mode
chrome_options = Options()
chrome_options.add_argument("--log-level=3")  # Suppresses non-critical errors
chrome_options.add_argument("--disable-gpu")  # Disable GPU hardware acceleration
chrome_options.add_argument("--headless")  # Run headless Chrome
chrome_options.add_argument("--no-sandbox")  # Bypass OS security model
chrome_options.add_argument(
    "--disable-dev-shm-usage"
)  # Overcome limited resource problems

driver = webdriver.Chrome(
    service=ChromeService(ChromeDriverManager().install()), options=chrome_options
)

# Load the webpage
driver.get(url)
time.sleep(5)  # Let the page load, increase the time to let the content load

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
        # Wait until articles are located (increase wait time to 10 seconds)
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located(
                (
                    By.CSS_SELECTOR,
                    "article.gc.u-clickable-card",
                )  # Match this CSS class from structure
            )
        )

        # Find all articles on the page
        articles = driver.find_elements(By.CSS_SELECTOR, "article.gc.u-clickable-card")

        if len(articles) == 0:
            print("No articles found on the page.")
            return

        for article in articles:
            try:
                # Extract the article link
                link_element = article.find_element(
                    By.CSS_SELECTOR, "a.u-clickable-card__link"
                )
                link = link_element.get_attribute("href")
                print(f"Article Link: {link}")

                # Extract the headline
                headline_element = article.find_element(
                    By.CSS_SELECTOR, "h3.gc__title span"
                )
                headline = headline_element.text if headline_element else None

                # Extract the description
                description_element = article.find_element(
                    By.CSS_SELECTOR, "div.gc__excerpt p"
                )
                description = description_element.text if description_element else None

                # Extract the date
                date_element = article.find_element(
                    By.CSS_SELECTOR, "div.gc__date__date span[aria-hidden='true']"
                )
                date = date_element.text if date_element else "Unknown"

                # Append extracted data to the data dictionary
                data["Source"].append(source)
                data["Link"].append(link)
                data["Headline"].append(headline)
                data["Description"].append(description)
                data["Date"].append(date)
                data["Timestamp"].append(datetime.now())
                data["Region"].append(region)
                data["Topic"].append(topic)
                data["Article_Content"].append(
                    "-"
                )  # No content extraction in this structure
                data["Author"].append("-")  # No author extraction in this structure

            except NoSuchElementException as e:
                print(f"Error scraping article (element not found): {e}")
            except Exception as e:
                print(f"Error scraping article: {e}")

    except TimeoutException:
        print("Timeout: Could not find articles on the page.")
    except Exception as e:
        print(f"Error during scraping process: {e}")


def dismiss_cookie_banner():
    try:
        # Wait for the cookie consent banner to appear and click the "Accept" button
        accept_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "button#onetrust-accept-btn-handler")
            )
        )
        accept_button.click()
        print("Cookie banner dismissed.")
    except TimeoutException:
        print("Cookie banner not found or already dismissed.")
    except Exception as e:
        print(f"Error dismissing cookie banner: {e}")


# Dismiss the cookie banner if it exists
dismiss_cookie_banner()

# Loop for pagination or showing more content
for i in range(50):
    try:
        print(f"Page {i+1}...")

        # Scrape articles on the current page
        scrape_articles()

        # Wait for the "Show More" button to be clickable, increased wait time to 10 seconds
        show_more_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "button.show-more-button.grid-full-width")
            )
        )

        # Click the "Show More" button to load more content
        show_more_button.click()
        time.sleep(5)  # Allow time for the new content to load, increased wait time

    except TimeoutException:
        print(
            f"No more content to load or unable to click the 'Show More' button on page {i+1}."
        )
        break
    except Exception as e:
        print(f"Error during pagination: {e}")
        break

# Save data to CSV
df = pd.DataFrame(data)
df.to_csv(f"{source}_articles_{topic}.csv", index=False)
print("Articles scraped successfully!")

# Close the driver
driver.quit()
