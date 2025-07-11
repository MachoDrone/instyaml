#!/usr/bin/env python3
"""
Debug script to check why Explorer links are not being followed
"""

from nosana_scraper import NosanaScraper, ScrapingConfig
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def debug_explorer_exclusion():
    # Create configuration  
    config = ScrapingConfig(
        base_url="https://dashboard.nosana.com/",
        max_depth=3,
        delay_between_requests=2.0,
        timeout=15,
        output_format="json"
    )
    
    # Add our exclusions
    if config.excluded_elements is None:
        config.excluded_elements = []
    
    config.excluded_elements.extend([
        'deploy', 'Deploy',
        'create a deployment', 'Create a deployment',
        'gpus available', 'GPUs Available',
        'connect wallet', 'Connect Wallet',
        'global priority fee', 'Global Priority Fee'
    ])
    
    if config.excluded_text_patterns is None:
        config.excluded_text_patterns = []
        
    config.excluded_text_patterns.extend([
        'deploy', 'deployment', 'create deployment',
        'new deployment', 'model deployment'
    ])
    
    # Initialize scraper
    scraper = NosanaScraper(config)
    
    print("🔍 Debug: Checking Explorer link exclusion...")
    print(f"Excluded elements: {config.excluded_elements}")
    print(f"Excluded patterns: {config.excluded_text_patterns}")
    
    try:
        # Setup driver and get page
        driver = scraper.setup_driver()
        print(f"\n🌐 Loading page: https://dashboard.nosana.com/")
        driver.get("https://dashboard.nosana.com/")
        
        # Wait for initial load
        print("⏳ Waiting for page to load...")
        time.sleep(5)
        
        # Wait for specific elements that indicate the page has loaded
        try:
            # Wait for either navigation links or main content to appear
            WebDriverWait(driver, 10).until(
                EC.any_of(
                    EC.presence_of_element_located((By.TAG_NAME, "nav")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[href*='explorer']")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a[href]")),
                    EC.element_to_be_clickable((By.TAG_NAME, "a"))
                )
            )
            print("✅ Page loaded with navigation elements")
        except:
            print("⚠️ Navigation elements not found, checking raw content...")
        
        # Check what's actually on the page
        page_title = driver.title
        page_url = driver.current_url
        print(f"📄 Page title: '{page_title}'")
        print(f"📍 Current URL: '{page_url}'")
        
        # Get page text content to see if anything is there
        body_text = driver.find_element(By.TAG_NAME, "body").text[:200]
        print(f"📝 First 200 chars of body text: '{body_text}'")
        
        # Parse page
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Check for different types of elements
        all_links = soup.find_all('a')
        clickable_buttons = soup.find_all('button')
        divs_with_onclick = soup.find_all('div', onclick=True)
        
        print(f"\n📊 Page Analysis:")
        print(f"   🔗 Total <a> tags: {len(all_links)}")
        print(f"   🔗 <a> tags with href: {len([a for a in all_links if a.get('href')])}")
        print(f"   🎯 <button> tags: {len(clickable_buttons)}")
        print(f"   📱 <div> with onclick: {len(divs_with_onclick)}")
        
        # Look for Explorer in page text
        page_text = soup.get_text()
        explorer_count = page_text.lower().count('explorer')
        print(f"   🔍 'Explorer' appears {explorer_count} times in page text")
        
        # Check if page might need JavaScript rendering
        html_content = driver.page_source
        if 'react' in html_content.lower() or 'vue' in html_content.lower() or 'angular' in html_content.lower():
            print("⚡ Page appears to use a JavaScript framework")
        
        # Look for loading indicators by common class names
        loading_indicators = soup.find_all(['div', 'span'], class_=['loading', 'spinner', 'loader'])
        if loading_indicators:
            print(f"⏳ Found {len(loading_indicators)} loading indicators - content may still be loading")
            time.sleep(3)  # Wait a bit more
            soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Find all links again after waiting
        links = soup.find_all('a', href=True)
        print(f"\n📋 Found {len(links)} total links with href on page")
        
        # Check each link for Explorer
        explorer_links = []
        for link in links:
            link_text = link.get_text(strip=True)
            link_href = link.get('href', '')
            link_attrs = link.attrs
            
            if 'explorer' in link_text.lower() or 'explorer' in link_href.lower():
                explorer_links.append({
                    'text': link_text,
                    'href': link_href,
                    'attrs': link_attrs
                })
                
                # Test exclusion
                is_excluded = scraper.is_element_excluded(link_text, link_attrs)
                print(f"\n🔗 Explorer link found:")
                print(f"   Text: '{link_text}'")
                print(f"   Href: '{link_href}'")
                print(f"   Classes: {link_attrs.get('class', [])}")
                print(f"   Excluded: {is_excluded}")
                
                if is_excluded:
                    print("   ❌ This link is being excluded!")
                    
                    # Check why it's excluded
                    element_text_lower = link_text.lower().strip()
                    
                    # Check excluded elements
                    for excluded in config.excluded_elements or []:
                        if excluded.lower() in element_text_lower:
                            print(f"      Reason: Matches excluded element '{excluded}'")
                    
                    # Check excluded patterns
                    for pattern in config.excluded_text_patterns or []:
                        if pattern.lower() in element_text_lower:
                            print(f"      Reason: Matches excluded pattern '{pattern}'")
                    
                    # Check navigation classes
                    class_names = link_attrs.get('class', [])
                    if isinstance(class_names, list):
                        class_names_str = ' '.join(class_names).lower()
                    else:
                        class_names_str = str(class_names).lower()
                    
                    nav_classes = ['nav', 'menu', 'header', 'footer', 'sidebar']
                    for nav_class in nav_classes:
                        if nav_class in class_names_str:
                            print(f"      Reason: Has navigation class '{nav_class}' in '{class_names_str}'")
                else:
                    print("   ✅ This link should be clickable!")
        
        if not explorer_links:
            print("\n❌ No Explorer links found on the page!")
            
            # Show some sample links to understand the page structure
            print("\n📋 Sample links found on page:")
            for i, link in enumerate(links[:5]):  # First 5 links
                text = link.get_text(strip=True)[:30]
                href = link.get('href', '')[:50]
                print(f"   #{i+1}: '{text}' -> '{href}'")
        
        # Get clickable elements using scraper method
        clickable_elements = scraper.get_clickable_elements(soup)
        print(f"\n📊 Clickable elements found by scraper: {len(clickable_elements)}")
        
        explorer_clickable = [elem for elem in clickable_elements if 'explorer' in elem['text'].lower() or 'explorer' in elem['url'].lower()]
        print(f"📊 Explorer elements in clickable list: {len(explorer_clickable)}")
        
        for elem in explorer_clickable:
            print(f"   ✅ Clickable Explorer: '{elem['text']}' -> {elem['url']}")
        
        # Show sample clickable elements
        print(f"\n📋 Sample clickable elements:")
        for i, elem in enumerate(clickable_elements[:5]):  # First 5 clickable
            text = elem['text'][:30]
            url = elem['url'][:50]
            print(f"   #{i+1}: '{text}' -> '{url}'")
        
        return len(explorer_clickable) > 0
        
    finally:
        # Cleanup
        if scraper.driver:
            scraper.driver.quit()

if __name__ == "__main__":
    debug_explorer_exclusion()