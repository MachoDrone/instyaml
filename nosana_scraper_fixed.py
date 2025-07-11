#!/usr/bin/env python3
"""
Nosana Dashboard Web Scraper
Configurable web scraper with depth control and element filtering
"""

import time
import json
import csv
import logging
from typing import List, Dict, Set, Optional, Union
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass, asdict
from datetime import datetime

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.chrome.service import Service
    from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
    from bs4 import BeautifulSoup
    import requests
except ImportError as e:
    print(f"Missing required packages. Install with: pip install selenium beautifulsoup4 requests")
    print(f"Error: {e}")
    exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ScrapedPage:
    """Data structure for scraped page information"""
    url: str
    title: str
    text_content: str
    links: List[str]
    images: List[str]
    metadata: Dict[str, str]
    hover_data: Dict[str, str]
    timestamp: str
    depth: int
    source_url: Optional[str] = None

@dataclass
class ScrapingConfig:
    """Configuration for the scraper"""
    base_url: str = "https://dashboard.nosana.com/"
    max_depth: int = 1
    delay_between_requests: float = 2.0
    timeout: int = 10
    
    # Element identification strategies
    clickable_selectors: Optional[List[str]] = None
    excluded_elements: Optional[List[str]] = None
    excluded_text_patterns: Optional[List[str]] = None
    
    # Output configuration
    output_format: str = "json"  # json, csv, txt
    output_file: Optional[str] = None
    
    def __post_init__(self):
        if self.clickable_selectors is None:
            self.clickable_selectors = [
                'a[href]',  # Links with href attribute
                'button[onclick]',  # Buttons with onclick
                '[role="button"]',  # Elements with button role
                '.clickable',  # Elements with clickable class
                '[data-testid*="link"]',  # Test ID links
                '[data-link]',  # Data link attributes
            ]
        
        if self.excluded_elements is None:
            self.excluded_elements = [
                'Profile',
                'Deploy Model', 
                # 'Explorer',  # REMOVED - we want to click this to access GPUs
                'Help & Support',
                'Healthy',
                'Nosana dashboard',
                'Select Wallet',
                '© 2025 Nosana'
            ]
            
        if self.excluded_text_patterns is None:
            self.excluded_text_patterns = [
                'logout',
                'sign out', 
                'sign-out',
                'log out',
                'delete',
                'remove',
                'cancel',
                'close account',
                'terminate',
                'destroy'
            ]

class NosanaScraper:
    """Main scraper class for Nosana dashboard"""
    
    def __init__(self, config: ScrapingConfig):
        self.config = config
        self.visited_urls: Set[str] = set()
        self.scraped_data: List[ScrapedPage] = []
        self.driver = None
        
    def setup_driver(self) -> webdriver.Chrome:
        """Setup Chrome WebDriver with appropriate options"""
        chrome_options = ChromeOptions()
        chrome_options.add_argument('--headless')  # Run in background
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(self.config.timeout)
            return self.driver
        except WebDriverException as e:
            logger.error(f"Failed to setup Chrome driver: {e}")
            logger.info("Make sure Chrome and ChromeDriver are installed")
            raise
    
    def is_element_excluded(self, element_text: str, element_attrs: Dict) -> bool:
        """Check if an element should be excluded from clicking"""
        
        # Check excluded text patterns
        element_text_lower = element_text.lower().strip()
        for excluded in self.config.excluded_elements or []:
            if excluded.lower() in element_text_lower:
                return True
                
        for pattern in self.config.excluded_text_patterns or []:
            if pattern.lower() in element_text_lower:
                return True
        
        # Check specific attributes that indicate exclusion
        if element_attrs.get('data-exclude') == 'true':
            return True
            
        # Check for navigation/menu elements (common patterns)
        class_names = element_attrs.get('class', '').lower()
        if any(cls in class_names for cls in ['nav', 'menu', 'header', 'footer', 'sidebar']):
            return True
            
        return False
    
    def get_clickable_elements(self, soup: BeautifulSoup) -> List[Dict]:
        """Find all clickable elements on the page"""
        clickable_elements = []
        
        for selector in self.config.clickable_selectors or []:
            elements = soup.select(selector)
            for element in elements:
                element_text = element.get_text(strip=True)
                element_attrs = element.attrs
                
                # Skip if excluded
                if self.is_element_excluded(element_text, element_attrs):
                    continue
                    
                # Get the URL or action
                url = None
                if element.name == 'a':
                    url = element.get('href')
                elif element.get('onclick'):
                    # Try to extract URL from onclick
                    onclick = element.get('onclick')
                    if onclick and isinstance(onclick, str) and ('location.href' in onclick or 'window.open' in onclick):
                        # Basic extraction - you might need to enhance this
                        continue  # Skip complex onclick for now
                
                if url and isinstance(url, str) and not url.startswith('javascript:'):
                    full_url = urljoin(self.config.base_url, url)
                    clickable_elements.append({
                        'element': element,
                        'text': element_text,
                        'url': full_url,
                        'attrs': element_attrs
                    })
        
        return clickable_elements
    
    def capture_hover_data(self, elements_to_hover: List) -> Dict[str, str]:
        """Capture data that appears on hover (tooltips, popups, etc.)"""
        hover_data = {}
        
        if not self.driver:
            return hover_data
            
        try:
            actions = ActionChains(self.driver)
            
            for element in elements_to_hover:
                try:
                    # Hover over the element
                    actions.move_to_element(element).perform()
                    time.sleep(1)  # Wait for hover content to appear
                    
                    # Look for tooltip/popup content
                    tooltip_selectors = [
                        '[role="tooltip"]',
                        '.tooltip',
                        '.popup',
                        '.hover-content',
                        '[data-tooltip]',
                        '.tippy-content',  # Common tooltip library
                        '.ant-tooltip',    # Ant Design tooltips
                    ]
                    
                    for selector in tooltip_selectors:
                        tooltips = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for tooltip in tooltips:
                            if tooltip.is_displayed():
                                tooltip_text = tooltip.text.strip()
                                if tooltip_text:
                                    element_text = element.text.strip()[:50]  # First 50 chars as key
                                    hover_data[f"hover_{element_text}"] = tooltip_text
                    
                    # Also check for any newly appeared text elements
                    time.sleep(0.5)
                    current_body = self.driver.find_element(By.TAG_NAME, "body")
                    current_text = current_body.text
                    
                    # Move mouse away to clear hover state
                    actions.move_by_offset(100, 100).perform()
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.debug(f"Error capturing hover data for element: {e}")
                    continue
                    
        except Exception as e:
            logger.debug(f"Error in hover data capture: {e}")
            
        return hover_data

    def scrape_page(self, url: str, depth: int = 0, source_url: Optional[str] = None) -> ScrapedPage:
        """Scrape a single page and extract relevant information"""
        logger.info(f"Scraping page at depth {depth}: {url}")
        
        try:
            self.driver.get(url)
            time.sleep(self.config.delay_between_requests)
            
            # Wait for page to load
            WebDriverWait(self.driver, self.config.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Get page source and parse with BeautifulSoup
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Extract page information
            title = soup.title.string if soup.title else "No Title"
            
            # Get text content (remove script and style elements)
            for script in soup(["script", "style"]):
                script.decompose()
            text_content = soup.get_text()
            
            # Clean up text
            lines = (line.strip() for line in text_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text_content = '\n'.join(chunk for chunk in chunks if chunk)
            
            # Extract links
            links = []
            for link in soup.find_all('a', href=True):
                full_url = urljoin(url, link['href'])
                links.append(full_url)
            
            # Extract images
            images = []
            for img in soup.find_all('img', src=True):
                full_url = urljoin(url, img['src'])
                images.append(full_url)
            
            # Extract metadata
            metadata = {}
            for meta in soup.find_all('meta'):
                name = meta.get('name') or meta.get('property') or meta.get('http-equiv')
                content = meta.get('content')
                if name and content:
                    metadata[name] = content
            
            # Capture hover data from hoverable elements
            hover_data = {}
            try:
                # Find elements that might have hover data (common patterns)
                hoverable_selectors = [
                    '[data-tooltip]',
                    '[title]',
                    '.map-region',  # Geographic elements
                    '.country',
                    '.region', 
                    '.host-info',
                    '.gpu-info',
                    '[data-hover]',
                    '.hoverable'
                ]
                
                hoverable_elements = []
                for selector in hoverable_selectors:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    hoverable_elements.extend(elements[:5])  # Limit to first 5 per selector
                
                if hoverable_elements:
                    hover_data = self.capture_hover_data(hoverable_elements)
                    
            except Exception as e:
                logger.debug(f"Error finding hoverable elements: {e}")
            
            scraped_page = ScrapedPage(
                url=url,
                title=title or "No Title",
                text_content=text_content,
                links=links,
                images=images,
                metadata=metadata,
                hover_data=hover_data,
                timestamp=datetime.now().isoformat(),
                depth=depth,
                source_url=source_url
            )
            
            self.scraped_data.append(scraped_page)
            return scraped_page
            
        except TimeoutException:
            logger.warning(f"Timeout loading page: {url}")
            return None
        except Exception as e:
            logger.error(f"Error scraping page {url}: {e}")
            return None
    
    def scrape_with_depth(self) -> List[ScrapedPage]:
        """Main scraping method with configurable depth"""
        if not self.driver:
            self.setup_driver()
            
        try:
            # Start with the base URL
            urls_to_visit = [(self.config.base_url, 0, None)]
            
            while urls_to_visit:
                current_url, current_depth, source_url = urls_to_visit.pop(0)
                
                # Skip if already visited or depth exceeded
                if current_url in self.visited_urls or current_depth > self.config.max_depth:
                    continue
                    
                self.visited_urls.add(current_url)
                
                # Scrape the current page
                scraped_page = self.scrape_page(current_url, current_depth, source_url)
                
                if scraped_page and current_depth < self.config.max_depth:
                    # Get clickable elements for next depth
                    self.driver.get(current_url)
                    time.sleep(1)
                    soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                    clickable_elements = self.get_clickable_elements(soup)
                    
                    # Add new URLs to visit
                    for element_info in clickable_elements:
                        new_url = element_info['url']
                        if new_url not in self.visited_urls:
                            urls_to_visit.append((new_url, current_depth + 1, current_url))
                            logger.info(f"Added to queue: {element_info['text']} -> {new_url}")
            
            return self.scraped_data
            
        finally:
            if self.driver:
                self.driver.quit()
    
    def save_results(self, filename: Optional[str] = None):
        """Save scraped results in the specified format"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"nosana_scrape_{timestamp}"
        
        if self.config.output_format.lower() == 'json':
            output_file = f"{filename}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(page) for page in self.scraped_data], f, indent=2, ensure_ascii=False)
        
        elif self.config.output_format.lower() == 'csv':
            output_file = f"{filename}.csv"
            if self.scraped_data:
                with open(output_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=asdict(self.scraped_data[0]).keys())
                    writer.writeheader()
                    for page in self.scraped_data:
                        writer.writerow(asdict(page))
        
        elif self.config.output_format.lower() == 'txt':
            output_file = f"{filename}.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                for page in self.scraped_data:
                    f.write(f"URL: {page.url}\n")
                    f.write(f"Title: {page.title}\n")
                    f.write(f"Depth: {page.depth}\n")
                    f.write(f"Timestamp: {page.timestamp}\n")
                    f.write("-" * 50 + "\n")
                    f.write(page.text_content)
                    f.write("\n" + "=" * 50 + "\n\n")
        
        logger.info(f"Results saved to: {output_file}")
        return output_file

def main():
    """Example usage and configuration"""
    
    # Create configuration
    config = ScrapingConfig(
        base_url="https://dashboard.nosana.com/",
        max_depth=1,  # Adjust this for deeper scraping
        delay_between_requests=2.0,
        output_format="json"
    )
    
    # You can customize excluded elements here
    # NOTE: Explorer is NOT excluded - we want to click it to access GPUs and Host Leaderboard
    if config.excluded_elements:
        config.excluded_elements.extend([
            'GPUs Available',  # The counter text, not the actual GPU links
            '311/1132',       # The specific numbers  
            # Add any additional elements to exclude
        ])
    
    # Create and run scraper
    scraper = NosanaScraper(config)
    
    try:
        results = scraper.scrape_with_depth()
        print(f"Scraped {len(results)} pages successfully")
        
        # Save results
        output_file = scraper.save_results()
        print(f"Results saved to: {output_file}")
        
        # Print summary
        for page in results:
            print(f"Depth {page.depth}: {page.title} - {page.url}")
            
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        raise

if __name__ == "__main__":
    main()