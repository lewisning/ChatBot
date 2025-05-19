import os
import json
import re
from urllib.parse import urljoin, urlparse, urlunparse
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from dataclasses import dataclass
import requests
from typing import List, Dict

# Configuration
BASE_URL = "https://www.madewithnestle.ca"
MAX_DEPTH = 2
CONCURRENT_PAGES = 3
REQUEST_TIMEOUT = 15000


@dataclass
class Product:
    name: str
    subtitle: str
    spec: str
    description: str
    features: str
    nutrition: list
    ingredient: str
    link: str
    image: str
    status: str


@dataclass
class Brand:
    name: str
    category: str
    category_description: str
    url: str
    products: List[Product]


def normalize_url(url):
    parsed = urlparse(url)
    path = re.sub(r'/+', '/', parsed.path).rstrip('/').lower()
    query = '&'.join([q for q in parsed.query.split('&') if not q.startswith(('utm_', 'fbclid'))])
    return urlunparse(parsed._replace(path=path, query=query, fragment=""))


# Extract brand links from the homepage
def extract_brand_links(soup, base_url):
    brands = []
    menu_container = soup.select_one('.coh-container.sub-menu-container.coh-ce-e4150c72')
    if not menu_container:
        return brands

    for category_block in menu_container.select('.coh-menu-list-item.has-children'):
        category_elem = category_block.select_one('span.coh-link.js-coh-menu-item-link')

        if not category_elem:
            continue

        # Get the category name and description of the category
        category = category_elem.get_text(strip=True)
        description = category_elem.get('title', "No description provided").strip()

        sub_menu = category_block.select_one('.coh-container.sub-sub-menu-container.coh-ce-2ef0a8f3')
        if not sub_menu:
            continue

        for brand_item in sub_menu.select('a[href]'):
            brand_name = brand_item.get_text(strip=True)
            brand_url = urljoin(base_url, brand_item['href'])

            brands.append({
                "category": category,
                "category_description": description,
                "name": brand_name,
                "url": normalize_url(brand_url)
            })

    return brands


# Predict product cards from the page
def find_possible_product_cards(soup):
    candidates = []

    # Find product cards based on common classes and structure (e.g., .coh-column)
    for div in soup.select('div[class*="coh-column"]'):
        has_img = div.select_one('img')
        has_link = div.select_one('a[href]')
        has_name = div.select_one('.product-title, h3, .views-field-title span')

        if has_img and has_link and has_name:
            candidates.append(div)

    return candidates


# Preliminary product information extraction
def extract_structured_content(soup, url, seen):
    products = []
    containers_a = find_possible_product_cards(soup)

    for container in containers_a:
        try:
            # product name
            name_elem = container.select_one('.views-field.views-field-title, .product-title')
            name = name_elem.get_text(strip=True) if name_elem else None

            # product subtitle
            subtitle_elem = container.select_one('.product-subtitle')
            subtitle = subtitle_elem.get_text(strip=True) if subtitle_elem else None

            # product size
            size_elem = container.select_one('.views-field.views-field-field-size')
            spec = size_elem.get_text(strip=True) if size_elem else ""

            # product image
            img_elem = container.select_one('.views-field-field-package-image img, .product-image img')
            image = urljoin(url, img_elem['src']) if img_elem else None

            status_elem = container.select_one('.views-field.views-field-field-product-highlight, .product-highlight')
            status = status_elem.get_text(strip=True)[:20] if status_elem else "Regular Product"

            link_elem = container.select_one('.views-field.views-field-title a, .product-title')
            product_link = urljoin(url, link_elem['href']) if link_elem else url

            # Check for duplicate products
            seen_key = f"{name}|{spec}"
            if not name or seen_key in seen:
                print(f"!!!REPEAT PRODUCT FOUND: {name}")
                continue
            seen.add(seen_key)

            # Check for empty name
            print(f"Explored product: {name} | {spec}")
            products.append(Product(name=name,
                                    subtitle=subtitle,
                                    spec=spec,
                                    description="",
                                    features="",
                                    nutrition=[],
                                    ingredient="",
                                    link=normalize_url(product_link),
                                    image=image,
                                    status=status))

        except Exception as e:
            print("Couldn't extract product info:", e)
            print("HTML Preview:", container.prettify()[:300])
            continue

    return products


def discover_entry_urls(page, brand_info):
    # ---- Preliminary check for entry paths ----
    base_url = brand_info['url'].rstrip('/')
    entry_paths = brand_info.get('entry_paths', None)

    if entry_paths:
        return [f"{base_url}{path}" for path in entry_paths]

    # ---- If no entry paths are provided, try to discover them automatically ----
    print(f"Automatically discovering entry URLs for {brand_info['name']}...")
    try:
        page.goto(base_url, wait_until="domcontentloaded", timeout=REQUEST_TIMEOUT)
        soup = BeautifulSoup(page.content(), 'html.parser')

        submenu_links = soup.select("ul.brand-submenu-list a[href]")

        hrefs = [a['href'] for a in submenu_links if a['href'].startswith("http")]

        # Default to the base URL if no submenu links are found
        entry_urls = [base_url] + hrefs

        # Redirect checker
        for i, url in enumerate(entry_urls):
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            entry_urls[i] = response.url

        print(f"Discovered {len(entry_urls)} entry URLs: {entry_urls}")
        return entry_urls

    except Exception as e:
        print(f"Automatic discovery failed: {e}")
        return [base_url]


def extract_pages_for_brand(page, brand_info):
    all_products = []
    entry_urls = discover_entry_urls(page, brand_info)

    # Test commands
    # entry_urls = [brand_info['url']]
    #
    # soup = BeautifulSoup(page.content(), 'html.parser')
    #
    # products = find_possible_product_cards(soup)
    # if not products:
    #     entry_urls = discover_entry_urls(page, brand_info)

    seen_products = set()

    for base_url in entry_urls:
        page_num = 0
        seen_urls = set()

        while True:
            page_url = f"{base_url}?page={page_num}" if page_num > 0 else base_url

            if page_url in seen_urls:
                print(f"Already visited: {page_url}")
                break
            seen_urls.add(page_url)

            print(f"Extracting page: {page_url}")
            try:
                page.goto(page_url, wait_until="domcontentloaded", timeout=REQUEST_TIMEOUT)
                page.wait_for_selector(".coh-column, .product-column, .product-title", timeout=5000)

            except Exception as e:
                print(f"Failed to load page: {page_url} - {e}")
                break

            soup = BeautifulSoup(page.content(), 'html.parser')
            products = extract_structured_content(soup, page_url, seen_products)

            if not products:
                print("Products not found, stopping pagination.")
                break

            if page_num > 0 and products == all_products[-len(products):]:
                print("Repetitive products found, stopping pagination.")
                break

            all_products.extend(products)
            page_num += 1

            if page_num > 20:
                print("Maximum page limit reached, stopping pagination.")
                break

    for p in all_products:
        extract_product_details(page, p)

    return all_products


# Helper function for nutrition information
def extract_nutrition(soup):
    nutrition = []

    # Scrape nutrition information from two sections
    rows = soup.select('.primarynutrient .coh-row-inner, .secondarynutrient .coh-row-inner')

    for row in rows:
        cells = row.find_all('div', recursive=False)
        if not cells or len(cells) < 2:
            continue

        # Extract name, amount, and DV (if available)
        name = cells[0].get_text(strip=True)
        amount = cells[1].get_text(strip=True)
        dv = cells[2].get_text(strip=True) if len(cells) >= 3 else "Not Provided"

        if name and amount:
            nutrition.append({"type": name, "amount": amount, "dv": dv})

    return nutrition


# Extract product details from the product page
def extract_product_details(page, product: Product):
    try:
        page.goto(product.link, wait_until="domcontentloaded", timeout=REQUEST_TIMEOUT)
        soup = BeautifulSoup(page.content(), 'html.parser')

        # spec
        spec_elem = soup.select_one('.field--name-field-size')
        product.spec = spec_elem.get_text(strip=True) if spec_elem else None

        # description
        desc_elem = soup.select_one('.field--name-field-description')
        product.description = desc_elem.get_text(strip=True) if desc_elem else None

        # features
        features_list = soup.select('.coh-list-container.coh-unordered-list .coh-list-item')
        product.features = '\n'.join([li.get_text(strip=True) for li in features_list]) if features_list else None

        # nutrition
        product.nutrition = extract_nutrition(soup)

        # ingredients
        ing_elem = soup.select_one('.sub-ingredients')
        product.ingredient = ing_elem.get_text(strip=True) if ing_elem else None

    except Exception as e:
        print(f"Details extraction failed for {product.name}: {e}")


# Main function to scrape the site
def scrape_site(start_url):
    visited = set()
    brand_data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
        context = browser.new_context()

        try:
            print("Scraping categories and brands...")
            home_page = context.new_page()
            home_page.goto(start_url, wait_until="networkidle", timeout=REQUEST_TIMEOUT)
            home_soup = BeautifulSoup(home_page.content(), 'html.parser')
            brands = extract_brand_links(home_soup, start_url)
            home_page.close()
            # Test data
            # for brand_info in brands:
            #     print(brand_info)
            #
            # brands = [
            # {'category': 'Coffee',
            #            'category_description': 'Our hot beverages are just what you need when<br>you want to warm up, or wake up.',
            #            'name': 'Coffee Mate',
            #            'url': 'https://www.madewithnestle.ca/coffee-mate'},
            #           {'category': 'Coffee',
            #            'category_description': 'Our hot beverages are just what you need when<br>you want to warm up, or wake up.',
            #            'name': 'NESCAFÉ',
            #            'url': 'https://www.madewithnestle.ca/nescafe'},
            #           {'category': 'Ice Cream & Frozen Treats',
            #            'category_description': 'Whether in a cone, on a stick, or in a bowl, our frozen treats are a fun and yummy way to serve up a smile, any time of year.',
            #            'name': 'Häagen-Dazs',
            #            'url': 'https://www.madewithnestle.ca/hd-en'}
            #           ]

            print(f"Discovered {len(brands)} brands, starting to scrape...")
            for brand_info in brands[:2]:
                if brand_info['url'] in visited:
                    continue

                print(f"\n=== Processing brand: {brand_info['name']} ===")
                brand_page = context.new_page()
                try:
                    products = extract_pages_for_brand(brand_page, brand_info)
                    brand_data.append(Brand(
                        name=brand_info['name'],
                        category=brand_info['category'],
                        category_description=brand_info['category_description'],
                        url=brand_info['url'],
                        products=products
                    ))
                    visited.add(brand_info['url'])
                    print(f"SUCCESS: {brand_info['name']} - {len(products)} products found")
                except Exception as e:
                    print(f"FAILURE: {brand_info['name']} - {e}")
                finally:
                    brand_page.close()

        finally:
            browser.close()

    save_results(brand_data)
    print(f"\nCOMPLETED: {len(brand_data)} brands scraped.")


def save_results(data):
    output = []
    for brand in data:
        brand_dict = {
            "brand": brand.name,
            "category": brand.category,
            "category_description": brand.category_description,
            "url": brand.url,
            "products": []
        }
        for product in brand.products:
            brand_dict["products"].append({
                "name": product.name,
                "specification": product.spec,
                "description": product.description,
                "features": product.features,
                "nutrition": product.nutrition,
                "ingredient": product.ingredient,
                "product_url": product.link,
                "image_url": product.image,
                "status": product.status
            })
        output.append(brand_dict)

    with open(os.path.join("rag/brand_products.json"), "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    scrape_site(BASE_URL)