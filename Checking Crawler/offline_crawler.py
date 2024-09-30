import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque
from urllib import robotparser

# Initialize URL frontier with the target website
url_frontier = deque(['https://webscraper.io/test-sites/e-commerce/static'])
visited_urls = set()

# Respect robots.txt
def can_fetch(url):
    return True
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    robots_txt_url = f"{base_url}/robots.txt"
    
    print(f"Checking robots.txt for: {robots_txt_url}")
    
    rp = robotparser.RobotFileParser()
    rp.set_url(robots_txt_url)
    try:
        rp.read()
        can_fetch = rp.can_fetch('*', url)
        print(f"Can fetch {url}: {can_fetch}")
        return can_fetch
    except Exception as e:
        print(f"Failed to read robots.txt: {e}")
        return True  # Default to allow if there's an error reading robots.txt

# Downloader Module
def download_url(url):
    headers = {'User-Agent': 'OfflineCrawler (http://mycrawler.com/contact)'}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.content, response.headers.get('Content-Type')
    except requests.RequestException as e:
        print(f"Error downloading {url}: {e}")
        return None, None

# Parser Module
def parse_html(html_content, base_url):
    soup = BeautifulSoup(html_content, 'html.parser')
    resources = set()
    
    # Extract links to other pages
    for link in soup.find_all('a', href=True):
        full_url = urljoin(base_url, link['href'])
        resources.add(full_url)
    
    # Extract links to CSS, JS, images
    for tag in soup.find_all(['link', 'script', 'img']):
        if tag.name == 'link' and 'href' in tag.attrs:
            full_url = urljoin(base_url, tag['href'])
        elif tag.name == 'script' and 'src' in tag.attrs:
            full_url = urljoin(base_url, tag['src'])
        elif tag.name == 'img' and 'src' in tag.attrs:
            full_url = urljoin(base_url, tag['src'])
        else:
            continue
        resources.add(full_url)

    return resources

# Data Storage
def save_resource(url, content, content_type):
    parsed_url = urlparse(url)
    path = parsed_url.path.lstrip('/')
    
    # Ensure path is not empty
    if not path:
        path = 'index.html'
    else:
        if path.endswith('/'):
            path += 'index.html'

    # Create necessary directories
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    # Determine file extension if missing
    if content_type and not os.path.splitext(path)[1]:
        if 'text/html' in content_type:
            path += '.html'
        elif 'text/css' in content_type:
            path += '.css'
        elif 'application/javascript' in content_type:
            path += '.js'

    with open(path, 'wb') as f:
        f.write(content)

    return path

# Scheduler
def crawl():
    while url_frontier:
        url = url_frontier.popleft()
        if url in visited_urls:
            continue

        visited_urls.add(url)
        if not can_fetch(url):
            print(f"Disallowed by robots.txt: {url}")
            continue

        content, content_type = download_url(url)
        if content:
            path = save_resource(url, content, content_type)
            print(f"Saved {url} to {path}")

            if 'text/html' in content_type:
                resources = parse_html(content, url)
                for resource in resources:
                    if resource not in visited_urls:
                        url_frontier.append(resource)

        time.sleep(1)  # Politeness delay

if __name__ == '__main__':
    crawl()
