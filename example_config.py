#!/usr/bin/env python3
"""
Example configuration for Nosana Dashboard Scraper
Customize this file for your specific scraping needs
"""

from nosana_scraper import ScrapingConfig, NosanaScraper

def main():
    # Create configuration
    config = ScrapingConfig(
        base_url="https://dashboard.nosana.com/",
        max_depth=1,  # Start with 1, increase as needed
        delay_between_requests=2.0,  # Be respectful to the server
        timeout=10,
        output_format="json"  # or "csv" or "txt"
    )
    
    # Customize excluded elements (add more as needed)
    # NOTE: Explorer is NOT excluded - we want to click it to access GPUs
    if config.excluded_elements:
        config.excluded_elements.extend([
            'GPUs Available',  # The counter text, not the actual GPU section
            '311/1132',       # The specific numbers
            # Add any other elements you want to avoid
        ])
    
    # Add custom clickable selectors if needed
    # config.clickable_selectors.extend([
    #     '.custom-button',
    #     '[data-action="navigate"]',
    # ])
    
    # Create and run scraper
    scraper = NosanaScraper(config)
    
    try:
        print("🚀 Starting scraper...")
        results = scraper.scrape_with_depth()
        print(f"✅ Scraped {len(results)} pages successfully")
        
        # Save results
        output_file = scraper.save_results("nosana_scrape_results")
        print(f"💾 Results saved to: {output_file}")
        
        # Print summary
        print("\n📊 Scraping Summary:")
        for page in results:
            print(f"  Depth {page.depth}: {page.title} - {page.url}")
            
    except Exception as e:
        print(f"❌ Scraping failed: {e}")
        raise

if __name__ == "__main__":
    main()