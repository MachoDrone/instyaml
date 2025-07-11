#!/usr/bin/env python3
"""
Enhanced example configuration for Nosana Dashboard scraping
"""

from nosana_scraper import NosanaScraper, ScrapingConfig

def main():
    # Create configuration using the ScrapingConfig class
    config = ScrapingConfig(
        base_url="https://dashboard.nosana.com/",
        max_depth=3,  # Navigate up to 3 levels deep
        delay_between_requests=2.0,  # 2 seconds between requests
        timeout=15,  # Increased timeout for better reliability
        output_format="json"
    )
    
    # Enhanced exclusions list - FIXED to allow Deployments/Explorer navigation
    if config.excluded_elements is None:
        config.excluded_elements = []
    
    config.excluded_elements.extend([
        # SPECIFIC deploy exclusions to avoid blocking "Deployments" navigation
        'create a deployment',  # Specific creation action
        'Create a deployment', 
        'new deployment',
        'New deployment',
        'deploy model',  # Model deployment specific
        'Deploy Model',
        # Connection and UI elements
        'connect wallet', 'Connect Wallet',
        'global priority fee', 'Global Priority Fee',
        'gpus available', 'GPUs Available',  # Counter text, not navigation
        'select wallet', 'Select Wallet',
        # Keep existing safe exclusions
        'profile', 'Profile',
        'help & support', 'Help & Support',
        'healthy', 'Healthy',
        'nosana dashboard', 'Nosana dashboard',
        '© 2025 nosana', '© 2025 Nosana'
    ])
    
    if config.excluded_text_patterns is None:
        config.excluded_text_patterns = []
        
    config.excluded_text_patterns.extend([
        # SPECIFIC deployment patterns to avoid blocking "Deployments" 
        'create deployment',
        'new deployment', 
        'model deployment',
        'deploy new',
        'deploy a ',  # "deploy a model" etc
        # Safety patterns
        'logout', 'sign out', 'sign-out', 'log out',
        'delete', 'remove', 'cancel', 
        'close account', 'terminate', 'destroy'
    ])
    
    print("🚀 Starting scraper with updated exclusions...")
    print("📍 Targeting: Explorer → GPUs → Host Leaderboard")
    print("🚫 Fixed exclusions to allow Deployments/Explorer navigation")
    print("✅ Removed overly broad 'deploy' exclusions")
    
    # Create and run scraper
    scraper = NosanaScraper(config)
    
    try:
        results = scraper.scrape_with_depth()
        print(f"✅ Scraped {len(results)} pages successfully")
        
        # Save results
        output_file = scraper.save_results("nosana_scrape_results")
        print(f"💾 Results saved to: {output_file}")
        
        # Print summary
        print(f"\n📊 Scraping Summary:")
        for page in results:
            print(f"  Depth {page.depth}: {page.title} - {page.url}")
            
    except Exception as e:
        print(f"❌ Scraping failed: {e}")
        raise

if __name__ == "__main__":
    main()