import os
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
from playwright.sync_api import sync_playwright


BASE_URL = "https://www.madewithnestle.ca"


# URL validation
def is_valid_url(href):
    if not href:
        return False
    # Skip URLs with no scheme
    if any(href.startswith(scheme) for scheme in ["mailto:", "tel:", "javascript:", "view::"]):
        return False

    SKIP_EXTS = [".pdf", ".svg", ".ico", ".jpg", ".jpeg", ".png", ".gif", ".mp4", ".webm", ".zip", ".exe", ".woff", ".ttf", ".css", ".js"]
    if any(href.lower().endswith(ext) for ext in SKIP_EXTS):
        return False
    parsed = urlparse(href)
    # Allow URLs with a scheme (http, https, etc.)
    if not parsed.netloc:
        return True
    return BASE_URL in href

def normalize_url(url):
    parsed = urlparse(url)
    normalized = parsed._replace(query="", fragment='', path=parsed.path.rstrip("/"))
    return urlunparse(normalized)

def extract_page_content(page, url):
    print(f"[.] Scraping {url}")
    try:
        # Wait for the page to load
        page.goto(url, timeout=20000)
        page.wait_for_selector("body", timeout=20000)  # More reliable than wait_for_load_state
        html = page.content()
        soup = BeautifulSoup(html, "html.parser")

        title = soup.title.string.strip() if soup.title else ""
        body = soup.body or soup  # fallback to soup if body is None
        text = body.get_text(separator="\n", strip=True)

        images = [urljoin(url, img['src']) for img in soup.find_all('img') if img.get('src')]
        tables = []
        for table in soup.find_all('table'):
            rows = []
            for tr in table.find_all('tr'):
                cells = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
                if cells:
                    rows.append(cells)
            if rows:
                tables.append(rows)

        return {
            "url": url,
            "title": title,
            # "text": text[:10000],  # limit excessively long pages
            "text": text,  # Keep full text
            "images": images,
            "tables": tables
        }
    except Exception as e:
        print(f"[!] Failed to scrape {url}: {e}")
        return None

def scrape_site(start_url):
    data_file = "rag/data.json"
    visited = set()
    data = []
    MAX_PAGES = 10

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
        page = browser.new_page()

        to_visit = [start_url]
        while to_visit and len(visited) < MAX_PAGES:
            # Get current URL
            url = to_visit.pop(0)
            normalized_url = normalize_url(url)
            if normalized_url in visited:
                continue
            visited.add(normalized_url)

            content = extract_page_content(page, url)
            if content:
                data.append(content)

                # Find more links
                soup = BeautifulSoup(page.content(), "html.parser")
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    full_url = urljoin(url, href)
                    if is_valid_url(full_url) and full_url not in visited:
                        to_visit.append(full_url)

            print(f"[DEBUG] Queue size: {len(to_visit)} | VISITED: {len(visited)}")

        browser.close()

    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[✔] Scrape complete. {len(data)} pages saved.")

if __name__ == "__main__":
    scrape_site(BASE_URL)
