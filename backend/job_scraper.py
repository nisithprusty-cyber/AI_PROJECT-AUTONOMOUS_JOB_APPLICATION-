"""
Job Scraper Module
Uses BeautifulSoup + requests to scrape job postings
Falls back to Playwright for JavaScript-heavy sites
"""
import requests
from bs4 import BeautifulSoup
import re
import json
import os
from typing import Optional
import time


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}


def scrape_job_posting(url: str) -> dict:
    """
    Scrape a job posting URL and return structured data.
    
    Args:
        url: Job posting URL
        
    Returns:
        dict with keys: title, company, location, description, requirements, raw_description, url
    """
    print(f"[Scraper] Scraping: {url}")
    
    try:
        # Try with requests first (faster)
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        html = response.text
    except Exception as e:
        print(f"[Scraper] requests failed: {e}, trying playwright...")
        try:
            html = scrape_with_playwright(url)
        except Exception as pe:
            print(f"[Scraper] Playwright also failed: {pe}")
            # Return manual entry placeholder
            return {
                "title": "Position",
                "company": "Company",
                "location": "Location",
                "raw_description": f"Could not scrape URL: {url}. Please paste job description manually.",
                "requirements": [],
                "url": url,
            }
    
    return parse_job_html(html, url)


def parse_job_html(html: str, url: str) -> dict:
    """Parse HTML and extract job details."""
    soup = BeautifulSoup(html, "html.parser")
    
    # Remove script and style tags
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    
    # Extract title
    title = extract_job_title(soup)
    
    # Extract company
    company = extract_company(soup, url)
    
    # Extract location
    location = extract_location(soup)
    
    # Get main content text
    raw_description = extract_main_content(soup)
    
    return {
        "title": title,
        "company": company,
        "location": location,
        "raw_description": raw_description,
        "requirements": extract_requirements(raw_description),
        "url": url,
    }


def extract_job_title(soup: BeautifulSoup) -> str:
    """Extract job title from page."""
    # Common selectors for job title
    selectors = [
        {"data-testid": "jobsearch-JobInfoHeader-title"},
        {"class": re.compile(r"job[-_]title|jobTitle|position-title", re.I)},
        {"class": re.compile(r"title", re.I), "itemprop": "title"},
    ]
    
    for sel in selectors:
        el = soup.find(attrs=sel)
        if el:
            return el.get_text(strip=True)
    
    # Try h1
    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)[:100]
    
    return "Software Engineer"


def extract_company(soup: BeautifulSoup, url: str) -> str:
    """Extract company name."""
    selectors = [
        {"data-testid": "inlineHeader-companyName"},
        {"class": re.compile(r"company[-_]name|companyName|employer", re.I)},
        {"itemprop": "hiringOrganization"},
    ]
    
    for sel in selectors:
        el = soup.find(attrs=sel)
        if el:
            return el.get_text(strip=True)[:80]
    
    # Try to extract from URL domain
    match = re.search(r"(?:www\.)?([^/]+)\.", url)
    if match:
        return match.group(1).capitalize()
    
    return "Company"


def extract_location(soup: BeautifulSoup) -> str:
    """Extract job location."""
    selectors = [
        {"data-testid": "job-location"},
        {"class": re.compile(r"location|job-location", re.I)},
        {"itemprop": "jobLocation"},
    ]
    
    for sel in selectors:
        el = soup.find(attrs=sel)
        if el:
            return el.get_text(strip=True)[:100]
    
    return "Remote / On-site"


def extract_main_content(soup: BeautifulSoup) -> str:
    """Extract the main job description text."""
    # Common job description containers
    desc_selectors = [
        {"id": re.compile(r"job[-_]desc|jobDesc|description", re.I)},
        {"class": re.compile(r"job[-_]desc|jobDesc|job-details|description", re.I)},
        {"data-testid": "jobsearch-jobDescriptionText"},
    ]
    
    for sel in desc_selectors:
        el = soup.find(attrs=sel)
        if el:
            return el.get_text(separator="\n", strip=True)[:5000]
    
    # Fallback: get all paragraph text
    paragraphs = soup.find_all(["p", "li", "h2", "h3"])
    text = "\n".join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
    return text[:5000]


def extract_requirements(text: str) -> list:
    """Extract bullet-point requirements from job description."""
    lines = text.split("\n")
    requirements = []
    
    for line in lines:
        line = line.strip()
        # Look for lines that seem like requirements
        if len(line) > 20 and len(line) < 200:
            if any(kw in line.lower() for kw in [
                "experience", "skill", "knowledge", "proficiency",
                "degree", "familiarity", "ability", "year", "required"
            ]):
                requirements.append(line)
    
    return requirements[:20]


def scrape_with_playwright(url: str) -> str:
    """
    Fallback scraper using Playwright for JS-heavy sites.
    Requires: pip install playwright && playwright install chromium
    """
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_extra_http_headers(HEADERS)
            page.goto(url, timeout=30000)
            time.sleep(2)  # Wait for JS to load
            html = page.content()
            browser.close()
            return html
    except ImportError:
        raise ImportError("Playwright not installed. Run: pip install playwright && playwright install chromium")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        result = scrape_job_posting(sys.argv[1])
        print(json.dumps(result, indent=2))
