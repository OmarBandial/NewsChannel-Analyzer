# scrapers.py

import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException
)

from webdriver_manager.chrome import ChromeDriverManager


def _init_driver(headless: bool = True):
    opts = ChromeOptions()
    if headless:
        opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--log-level=3")
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        " AppleWebKit/537.36 (KHTML, like Gecko)"
        " Chrome/91.0.4472.124 Safari/537.36"
    )
    driver = webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()), options=opts
    )
    driver.set_page_load_timeout(45)
    return driver


def scrape_bbc_links(topic: str, max_articles: int = 5, max_pages: int = 10) -> list[str]:
    query = topic.strip().replace(" ", "+")
    url = f"https://www.bbc.com/search?q={query}"
    card_sel = 'div[data-testid="newport-card"]'
    link_sel = "a[data-testid='internal-link']"
    next_btn_sel = "div.sc-faaff782-0 button:has(svg[icon='chevron-right']):not([disabled])"
    prefix = "https://www.bbc.com/news/articles"

    driver = _init_driver()
    driver.get(url)
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, card_sel)))

    links = []
    for _ in range(max_pages):
        cards = driver.find_elements(By.CSS_SELECTOR, card_sel)
        for card in cards:
            if len(links) >= max_articles:
                break
            try:
                href = card.find_element(By.CSS_SELECTOR, link_sel).get_attribute("href")
                if href.startswith(prefix) and href not in links:
                    links.append(href)
            except Exception:
                continue
        if len(links) >= max_articles:
            break
        try:
            btn = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, next_btn_sel))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", btn)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", btn)
            WebDriverWait(driver, 30).until(EC.staleness_of(cards[0]))
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, card_sel)))
            time.sleep(0.5)
        except Exception:
            break

    driver.quit()
    return links[:max_articles]


def scrape_bbc_article(url: str) -> str:
    try:
        resp = requests.get(url, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        art = soup.find("article")
        if not art:
            return ""
        paras = art.find_all("p")
        return " ".join(p.get_text().strip() for p in paras)
    except Exception:
        return ""


def scrape_cnn_links(topic: str, max_articles: int = 5, max_pages: int = 10) -> list[str]:
    q = topic.strip().replace(" ", "+")
    url = (
        "https://edition.cnn.com/search?"
        f"q={q}&from=0&size=10&page=1&sort=newest&types=article&section="
    )
    card_sel = 'div[data-component-name="card"]'
    link_sel = "a.container__link"
    next_btn_sel = "div.pagination-arrow-right"

    driver = _init_driver()
    driver.set_page_load_timeout(30)
    driver.get(url)

    links = []
    for _ in range(max_pages):
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, card_sel))
            )
        except TimeoutException:
            break
        cards = driver.find_elements(By.CSS_SELECTOR, card_sel)
        for card in cards:
            if len(links) >= max_articles:
                break
            try:
                href = card.find_element(By.CSS_SELECTOR, link_sel).get_attribute("href")
                if href and href not in links:
                    links.append(href)
            except Exception:
                continue
        if len(links) >= max_articles:
            break
        try:
            btn = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, next_btn_sel))
            )
            btn.click()
            time.sleep(2)
        except Exception:
            break

    driver.quit()
    return links[:max_articles]


def scrape_cnn_article(url: str) -> str:
    try:
        resp = requests.get(url, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        paras = soup.find_all("p")
        return " ".join(p.get_text().strip() for p in paras)
    except Exception:
        return ""


def scrape_dawn_links(topic: str, max_articles: int = 5, max_pages: int = 10) -> list[str]:
    q = topic.strip().replace(" ", "+")
    url = (
        "https://www.dawn.com/search?"
        "cx=016184311056644083324%3Aa1i8yd7zymy&cof=FORID%3A10&ie=UTF-8"
        f"&q={q}"
    )
    card_sel = "div.gsc-webResult.gsc-result"
    link_sel = "div.gs-title a.gs-title"
    page_btn_sel = "div.gsc-cursor-page"

    driver = _init_driver()
    driver.get(url)
    time.sleep(2)

    links = []
    for page in range(max_pages):
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, card_sel))
            )
        except TimeoutException:
            break
        cards = driver.find_elements(By.CSS_SELECTOR, card_sel)
        for card in cards:
            if len(links) >= max_articles:
                break
            try:
                href = card.find_element(By.CSS_SELECTOR, link_sel).get_attribute("href")
                if href and href not in links:
                    links.append(href)
            except Exception:
                continue
        if len(links) >= max_articles:
            break
        # click next page button
        buttons = driver.find_elements(By.CSS_SELECTOR, page_btn_sel)
        if page + 1 < len(buttons):
            try:
                driver.execute_script("arguments[0].click();", buttons[page + 1])
                time.sleep(2)
            except Exception:
                break
        else:
            break

    driver.quit()
    return links[:max_articles]


def scrape_dawn_article(url: str) -> str:
    try:
        resp = requests.get(url, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        container = soup.find("div", class_="story__content")
        if not container:
            return ""
        paras = container.find_all("p")
        return "\n".join(p.get_text(strip=True) for p in paras)
    except Exception:
        return ""


def scrape_fox_links(topic: str, max_articles: int = 5, max_pages: int = 5) -> list[str]:
    q = topic.strip().replace(" ", "%20")
    url = f"https://www.foxnews.com/search-results/search#q={q}"
    card_sel = "article.article"
    link_sel = "h2.title a"
    load_more_sel = "div.button.load-more a"

    driver = _init_driver()
    driver.get(url)

    links = []
    for _ in range(max_pages):
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, card_sel))
            )
        except TimeoutException:
            break
        cards = driver.find_elements(By.CSS_SELECTOR, card_sel)
        for card in cards:
            if len(links) >= max_articles:
                break
            try:
                elem = card.find_element(By.CSS_SELECTOR, link_sel)
                href = elem.get_attribute("href")
                if href and href not in links:
                    links.append(href)
            except Exception:
                continue
        if len(links) >= max_articles:
            break
        try:
            btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, load_more_sel))
            )
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(3)
        except Exception:
            break

    driver.quit()
    return links[:max_articles]


def scrape_fox_article(url: str) -> str:
    try:
        resp = requests.get(url, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        main = soup.find("main")
        if not main:
            return ""
        paras = main.find_all("p")
        return "\n".join(p.get_text(strip=True) for p in paras)
    except Exception:
        return ""


def scrape_trt_links(topic: str, max_articles: int = 5, max_pages: int = 10) -> list[str]:
    q = topic.strip().replace(" ", "%20")
    url = f"https://www.trtworld.com/search?q={q}"
    card_sel = "div.Card.Card-Search"
    load_more_sel = ".btn-loadmore"

    driver = _init_driver()
    driver.get(url)
    time.sleep(2)

    links = []
    for _ in range(max_pages):
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, card_sel))
            )
        except TimeoutException:
            break
        cards = driver.find_elements(By.CSS_SELECTOR, card_sel)
        for card in cards:
            if len(links) >= max_articles:
                break
            try:
                href = card.find_element(By.TAG_NAME, "a").get_attribute("href")
                if href and href not in links:
                    links.append(href)
            except Exception:
                continue
        if len(links) >= max_articles:
            break
        try:
            btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, load_more_sel))
            )
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(3)
        except Exception:
            break

    driver.quit()
    return links[:max_articles]


def scrape_trt_article(url: str) -> str:
    try:
        resp = requests.get(url, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        paras = soup.find_all("p")
        return " ".join(p.get_text().strip() for p in paras)
    except Exception:
        return ""


def scrape_aljazeera_links(topic: str, max_articles: int = 5, max_pages: int = 10) -> list[str]:
    q = topic.strip().replace(" ", "%20")
    url = f"https://www.aljazeera.com/search/{q}"
    card_sel = "article.gc.u-clickable-card"
    link_sel = "a.u-clickable-card__link"
    more_sel = "button.show-more-button.grid-full-width"
    cookie_sel = "button#onetrust-accept-btn-handler"

    driver = _init_driver()
    driver.get(url)
    time.sleep(2)

    # dismiss cookie popup if present
    try:
        btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, cookie_sel))
        )
        btn.click()
    except Exception:
        pass

    links = []
    for _ in range(max_pages):
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, card_sel))
            )
        except TimeoutException:
            break
        cards = driver.find_elements(By.CSS_SELECTOR, card_sel)
        for card in cards:
            if len(links) >= max_articles:
                break
            try:
                href = card.find_element(By.CSS_SELECTOR, link_sel).get_attribute("href")
                if href and href not in links:
                    links.append(href)
            except Exception:
                continue
        if len(links) >= max_articles:
            break
        try:
            btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, more_sel))
            )
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(5)
        except Exception:
            break

    driver.quit()
    return links[:max_articles]


def scrape_aljazeera_article(url: str) -> str:
    try:
        resp = requests.get(url, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        main = soup.find("main")
        if not main:
            return ""
        paras = main.find_all("p")
        return "\n".join(p.get_text(strip=True) for p in paras)
    except Exception:
        return ""


def scrape_links(channel: str, topic: str) -> list[str]:
    if channel == "BBC":
        return scrape_bbc_links(topic)
    elif channel == "CNN":
        return scrape_cnn_links(topic)
    elif channel == "Dawn News":
        return scrape_dawn_links(topic)
    elif channel == "Fox News":
        return scrape_fox_links(topic)
    elif channel == "TRT News":
        return scrape_trt_links(topic)
    elif channel == "Al Jazeera":
        return scrape_aljazeera_links(topic)
    else:
        return []


def scrape_article(url: str, channel: str) -> str:
    if channel == "BBC":
        return scrape_bbc_article(url)
    elif channel == "CNN":
        return scrape_cnn_article(url)
    elif channel == "Dawn News":
        return scrape_dawn_article(url)
    elif channel == "Fox News":
        return scrape_fox_article(url)
    elif channel == "TRT News":
        return scrape_trt_article(url)
    elif channel == "Al Jazeera":
        return scrape_aljazeera_article(url)
    else:
        return ""
