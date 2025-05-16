# Import necessary libraries
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options as ChromeOptions # Renamed to avoid conflict
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
import pandas as pd
import time
from datetime import datetime
import logging # Added for better error logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- User Inputs ---
topic = input("Enter topic: ")
topic_formatted = topic.strip().replace(' ', '+')

url = f"https://www.bbc.com/search?q={topic_formatted}"
source = "BBC"

# --- Chrome Driver Setup ---
logging.info("Setting up Chrome options...")
chrome_options = ChromeOptions()
chrome_options.add_argument("--headless") # Run in headless mode (no GUI)
chrome_options.add_argument("--no-sandbox") # Bypass OS security model, required for some environments
chrome_options.add_argument("--disable-dev-shm-usage") # Overcome limited resource problems
chrome_options.add_argument("--disable-gpu") # Applicable to windows os only
chrome_options.add_argument("--disable-software-rasterizer") # Disable the software rasterizer
chrome_options.add_argument("--log-level=3") # Suppress unnecessary console logs from Chrome/ChromeDriver
chrome_options.add_argument("--disable-extensions") # Disable extensions
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36") # Set a common user agent

logging.info("Initializing Chrome WebDriver...")
try:
    # Use webdriver-manager to automatically handle driver installation/updates
    driver = webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()), options=chrome_options
    )
    # Set a reasonable page load timeout
    driver.set_page_load_timeout(45) # Increased page load timeout slightly
except Exception as e:
    logging.error(f"Failed to initialize WebDriver: {e}")
    exit() # Exit if the driver cannot be initialized

# --- Data Storage ---
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

# --- Constants ---
# Updated CSS Selectors based on bbc.txt analysis
ARTICLE_CONTAINER_SELECTOR = 'div[data-testid="newport-card"]'
HEADLINE_SELECTOR = "h2[data-testid='card-headline']"
LINK_SELECTOR = "a[data-testid='internal-link']"
DESCRIPTION_SELECTOR = "div.sc-cdecfb63-3.pGVVH" # Class for description div
DATE_SELECTOR = "span[data-testid='card-metadata-lastupdated']"
# *** Refined Next button selector: Target button with the right chevron icon ***
NEXT_BUTTON_SELECTOR = "div.sc-faaff782-0 button:has(svg[icon='chevron-right']):not([disabled])"
WAIT_TIMEOUT = 30 # *** Increased timeout for waits to 30 seconds ***
# *** Added Link Prefix Filter ***
LINK_PREFIX_FILTER = "https://www.bbc.com/news/articles"

# --- Scraping Function ---
def scrape_articles():
    """
    Finds and scrapes article data from the currently loaded page.
    Uses updated selectors and handles potential missing elements.
    Filters articles based on LINK_PREFIX_FILTER.
    Returns True if successful, False if no articles found, "stale" if staleness detected.
    """
    logging.info("Waiting for article containers to load...")
    try:
        # Wait for at least one article container to be present
        WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ARTICLE_CONTAINER_SELECTOR)
            )
        )
        logging.info("Article containers found. Scraping articles...")
    except TimeoutException:
        logging.warning("Timed out waiting for article containers on the page.")
        return False # Indicate that no articles were found/page might be empty

    # Find all article containers
    # Add a small delay before finding elements, sometimes helps with dynamic content
    time.sleep(0.5)
    articles = driver.find_elements(By.CSS_SELECTOR, ARTICLE_CONTAINER_SELECTOR)
    logging.info(f"Found {len(articles)} potential articles on this page.")

    if not articles:
        logging.warning("No article elements found with the selector.")
        return False

    articles_scraped_count = 0
    for article in articles:
        link, headline, description, date_str = None, None, None, "Unknown" # Default values

        try:
            # Find the link element within the article container
            # Need to find the 'a' tag first which wraps the whole card usually
            card_link_element = article.find_element(By.CSS_SELECTOR, LINK_SELECTOR)
            link = card_link_element.get_attribute("href")

            # Find the headline element within the card
            headline_element = article.find_element(By.CSS_SELECTOR, HEADLINE_SELECTOR)
            headline = headline_element.text

            # Find the description element (handle if it doesn't exist)
            try:
                description_element = article.find_element(By.CSS_SELECTOR, DESCRIPTION_SELECTOR)
                description = description_element.text
            except NoSuchElementException:
                description = "-" # Assign default if description is not found
                logging.debug(f"Description element not found for article: {headline[:50] if headline else 'N/A'}...")

            # Find the date element (handle if it doesn't exist)
            try:
                date_element = article.find_element(By.CSS_SELECTOR, DATE_SELECTOR)
                date_str = date_element.text
            except NoSuchElementException:
                date_str = "Unknown" # Assign default if date is not found
                logging.debug(f"Date element not found for article: {headline[:50] if headline else 'N/A'}...")

            # Append data if core elements (link, headline) were found AND link matches prefix
            if link and headline:
                # *** Apply the link prefix filter ***
                if link.startswith(LINK_PREFIX_FILTER):
                    data["Source"].append(source)
                    data["Link"].append(link)
                    data["Headline"].append(headline)
                    data["Description"].append(description)
                    data["Date"].append(date_str)
                    data["Timestamp"].append(datetime.now())
                    data["Topic"].append(topic)
                    data["Article_Content"].append("-") # Placeholder
                    data["Author"].append("-") # Placeholder
                    articles_scraped_count += 1
                else:
                    # Log skipped articles due to filter
                    logging.debug(f"Skipped article (link filter): {link}")
            else:
                # This case might indicate an ad or non-standard card structure
                logging.warning("Skipped an article container due to missing link or headline.")

        except StaleElementReferenceException:
            logging.warning("Encountered a stale element reference, skipping this article and retrying find_elements.")
            return "stale" # Signal to retry finding elements on the current page
        except NoSuchElementException as e:
             # This error is more critical if it's for link/headline within a found container
             logging.warning(f"Missing core element (link/headline) within an article container: {e}. Skipping this container.")
        except Exception as e:
            logging.error(f"Error scraping an individual article container: {e}")

    logging.info(f"Successfully scraped and filtered {articles_scraped_count} articles from this page.")
    if articles_scraped_count == 0 and len(articles) > 0:
        logging.warning("Found article containers but failed to extract/filter data from any.")
        # Optionally return False here if this should stop pagination
    return True # Indicate successful scraping of found articles

# --- Main Execution ---
logging.info(f"Navigating to URL: {url}")
try:
    driver.get(url)
    # Initial wait for the first set of articles instead of fixed sleep
    logging.info("Waiting for initial page load and first articles...")
    WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ARTICLE_CONTAINER_SELECTOR))
    )
    logging.info("Initial articles loaded.")

except TimeoutException:
    logging.error(f"Timeout loading initial URL or finding first articles: {url}")
    driver.quit()
    exit()
except Exception as e:
    logging.error(f"Error navigating to URL {url}: {e}")
    driver.quit()
    exit()

# Scrape the first page
logging.info("Scraping first page...")
scrape_result = scrape_articles()
if scrape_result == "stale": # Handle potential initial staleness
    logging.info("Retrying scrape on first page due to staleness.")
    time.sleep(1) # Brief pause before retry
    scrape_articles()

# Pagination Loop
MAX_PAGES = 50 # Limit the number of pages to scrape
for i in range(MAX_PAGES):
    current_page = i + 1
    logging.info(f"--- Attempting to navigate from page {current_page} to {current_page + 1} ---")

    try:
        # Find the first article on the current page to check for staleness later
        logging.debug("Locating first article on current page for staleness check...")
        try:
            first_article_on_page = WebDriverWait(driver, 10).until( # Shorter wait here is ok
                EC.presence_of_element_located((By.CSS_SELECTOR, ARTICLE_CONTAINER_SELECTOR))
            )
        except TimeoutException:
            logging.warning(f"Could not find first article on page {current_page} for staleness check. Stopping pagination.")
            break

        # Find and wait for the 'Next' button to be clickable using the refined selector
        logging.debug("Waiting for 'Next' button to be clickable...")
        next_button = WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, NEXT_BUTTON_SELECTOR)
            )
        )
        logging.debug("'Next' button found and clickable.")

        # *** Scroll the button into view before clicking ***
        logging.debug("Scrolling 'Next' button into view...")
        driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
        time.sleep(0.5) # Brief pause after scroll

        # Click the 'Next' button
        logging.debug("Clicking 'Next' button using JavaScript...")
        driver.execute_script("arguments[0].click();", next_button)
        time.sleep(1) # *** Increased pause after click slightly ***

        # Wait for the page to update by checking if the old first article is stale
        logging.debug("Waiting for page content to update (staleness check)...")
        WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.staleness_of(first_article_on_page)
        )
        logging.info(f"Navigation to page {current_page + 1} likely successful (staleness confirmed).")

        # Add an extra wait for the *new* articles to appear after navigation
        logging.debug(f"Waiting for new articles to appear on page {current_page + 1}...")
        WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ARTICLE_CONTAINER_SELECTOR))
        )
        logging.debug(f"New articles detected on page {current_page + 1}.")


        # Scrape the new page
        logging.info(f"Scraping page {current_page + 1}...")
        scrape_result = scrape_articles()
        if scrape_result == "stale": # Handle staleness after navigation
             logging.info(f"Retrying scrape on page {current_page + 1} due to staleness.")
             time.sleep(1) # Brief pause
             scrape_articles()
        elif scrape_result == False:
            logging.warning(f"Scrape function reported no articles found on page {current_page + 1}, stopping pagination.")
            break


        # Save data periodically
        if (current_page + 1) % 5 == 0: # Save after page 5, 10, 15 etc.
            logging.info(f"Saving data batch after page {current_page + 1}...")
            try:
                # Filter out empty lists before creating DataFrame
                valid_data = {k: v for k, v in data.items() if v}
                if valid_data and len(valid_data.get("Link", [])) > 0 : # Ensure we have core data
                    # Ensure all lists have the same length for the batch
                    # Find the current length of the Link list (which represents collected items)
                    current_len = len(data.get("Link", []))
                    # Determine how many items were added in the last 5 pages (approx)
                    # This logic isn't perfect for batching *only* the last 5 pages,
                    # it saves *all* data collected so far. A different approach
                    # would be needed to save only the delta.
                    # For simplicity, we save all accumulated data.
                    if current_len > 0:
                        batch_data_aligned = {}
                        all_keys = list(data.keys())
                        for k in all_keys:
                            v = data.get(k, [])
                            padded_v = v + ['-'] * (current_len - len(v)) # Pad to current max length
                            batch_data_aligned[k] = padded_v

                        df_batch = pd.DataFrame(batch_data_aligned)
                        batch_filename = f"scraped_articles_batch_{source}_{topic}_page_{current_page + 1}.csv"
                        df_batch.to_csv(batch_filename, index=False)
                        logging.info(f"Batch data saved to {batch_filename}")
                    else:
                        logging.warning(f"No link data to save in batch for page {current_page + 1}.")
                else:
                    logging.warning(f"No valid data to save in batch for page {current_page + 1}.")

            except Exception as e:
                logging.error(f"Error saving batch file at page {current_page + 1}: {e}")


    except TimeoutException:
        # This timeout could be waiting for the button, staleness, or new articles
        logging.info(f"Timeout occurred during pagination sequence for page {current_page + 1}. Assuming end of results or page load issue.")
        break # Exit loop
    except StaleElementReferenceException:
        logging.warning(f"Stale element reference during pagination sequence for page {current_page + 1}. Attempting to continue.")
        time.sleep(1) # Pause before retrying the loop
        continue # Try the next iteration
    except Exception as e:
        logging.error(f"An unexpected error occurred during pagination or scraping on page {current_page + 1}: {e}")
        # Consider adding more specific error handling if needed
        import traceback
        logging.error(traceback.format_exc()) # Log the full traceback for debugging
        break # Exit loop on other errors

# --- Final Save and Cleanup ---
logging.info("Scraping finished or max pages reached. Saving final data...")
try:
    # Ensure all lists in the data dictionary have the same length before creating the final DataFrame
    if data["Link"]: # Check if any data was actually collected
        max_final_len = 0
        try:
            # Find the length of the longest list (should ideally be the same after filtering)
             max_final_len = max(len(lst) for lst in data.values() if lst is not None)
        except ValueError: # Handles case where data might be completely empty after filtering
            logging.warning("Data dictionary appears empty or invalid for final save.")
            max_final_len = 0

        if max_final_len > 0:
            final_data_aligned = {}
            all_keys = list(data.keys()) # Get all expected keys
            for k in all_keys:
                v = data.get(k, []) # Get the list or an empty list if key missing
                 # Pad shorter lists with a default value (e.g., None or '-')
                padded_v = v + ['-'] * (max_final_len - len(v))
                final_data_aligned[k] = padded_v

            df = pd.DataFrame(final_data_aligned)
            final_filename = f"{source}_articles_{topic}_final.csv"
            df.to_csv(final_filename, index=False)
            logging.info(f"All scraped articles saved successfully to {final_filename}! Total rows: {len(df)}") # Log row count
        else:
             logging.warning("No data with positive length collected, skipping final save.")
    else:
        logging.warning("No data was collected (Link list is empty), skipping final save.")
except Exception as e:
    logging.error(f"Failed to save final CSV file: {e}")
    import traceback
    logging.error(traceback.format_exc()) # Log the full traceback

logging.info("Quitting WebDriver...")
driver.quit()
logging.info("Script finished.")
