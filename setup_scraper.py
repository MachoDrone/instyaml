#!/usr/bin/env python3
"""
Setup script for Nosana Dashboard Scraper
Installs dependencies and sets up Chrome WebDriver
"""

import subprocess
import sys
import platform
import os
from pathlib import Path

def run_command(command, description):
    """Run a system command with error handling"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✅ Python {version.major}.{version.minor} is compatible")

def install_python_packages():
    """Install required Python packages"""
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print("❌ requirements.txt not found")
        return False
    
    return run_command(
        f"{sys.executable} -m pip install -r requirements.txt",
        "Installing Python packages"
    )

def install_chrome_linux():
    """Install Chrome on Linux"""
    commands = [
        "wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -",
        "echo 'deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main' | sudo tee /etc/apt/sources.list.d/google-chrome.list",
        "sudo apt-get update",
        "sudo apt-get install -y google-chrome-stable"
    ]
    
    for cmd in commands:
        if not run_command(cmd, f"Running: {cmd}"):
            return False
    return True

def install_chrome_macos():
    """Install Chrome on macOS"""
    # Check if Homebrew is installed
    if not run_command("which brew", "Checking for Homebrew"):
        print("❌ Homebrew is required on macOS. Install from https://brew.sh/")
        return False
    
    return run_command("brew install --cask google-chrome", "Installing Chrome via Homebrew")

def check_chrome_installation():
    """Check if Chrome is installed"""
    system = platform.system().lower()
    
    if system == "linux":
        return run_command("google-chrome --version", "Checking Chrome installation")
    elif system == "darwin":  # macOS
        return run_command("/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --version", "Checking Chrome installation")
    elif system == "windows":
        chrome_paths = [
            "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
        ]
        for path in chrome_paths:
            if os.path.exists(path):
                print("✅ Chrome found on Windows")
                return True
        print("❌ Chrome not found on Windows")
        return False
    else:
        print(f"❌ Unsupported operating system: {system}")
        return False

def install_chrome():
    """Install Chrome based on the operating system"""
    system = platform.system().lower()
    
    if system == "linux":
        return install_chrome_linux()
    elif system == "darwin":  # macOS
        return install_chrome_macos()
    elif system == "windows":
        print("📝 For Windows, please download Chrome from: https://www.google.com/chrome/")
        print("   Then run this script again")
        return False
    else:
        print(f"❌ Unsupported operating system: {system}")
        return False

def setup_chromedriver():
    """Set up ChromeDriver using webdriver-manager"""
    print("🔄 Setting up ChromeDriver...")
    test_code = """
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

try:
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get('https://www.google.com')
    print('✅ ChromeDriver setup successful')
    driver.quit()
except Exception as e:
    print(f'❌ ChromeDriver setup failed: {e}')
    exit(1)
"""
    
    try:
        exec(test_code)
        return True
    except Exception as e:
        print(f"❌ ChromeDriver setup failed: {e}")
        return False

def create_example_config():
    """Create an example configuration file"""
    example_config = '''#!/usr/bin/env python3
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
    config.excluded_elements.extend([
        'GPUs Available',
        '311/1132',
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
        print("\\n📊 Scraping Summary:")
        for page in results:
            print(f"  Depth {page.depth}: {page.title} - {page.url}")
            
    except Exception as e:
        print(f"❌ Scraping failed: {e}")
        raise

if __name__ == "__main__":
    main()
'''
    
    with open("example_config.py", "w") as f:
        f.write(example_config)
    
    print("✅ Created example_config.py")

def main():
    """Main setup function"""
    print("🚀 Nosana Dashboard Scraper Setup")
    print("=" * 40)
    
    # Check Python version
    check_python_version()
    
    # Install Python packages
    if not install_python_packages():
        print("❌ Failed to install Python packages")
        sys.exit(1)
    
    # Check if Chrome is installed
    if not check_chrome_installation():
        print("📦 Chrome not found, attempting to install...")
        if not install_chrome():
            print("❌ Failed to install Chrome")
            sys.exit(1)
    
    # Set up ChromeDriver
    if not setup_chromedriver():
        print("❌ Failed to set up ChromeDriver")
        sys.exit(1)
    
    # Create example configuration
    create_example_config()
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Review SCRAPER_CONFIGURATION_GUIDE.md for detailed configuration options")
    print("2. Customize example_config.py for your specific needs")
    print("3. Run: python example_config.py")
    print("4. Or run the basic scraper: python nosana_scraper.py")
    
    print("\n⚠️  Important reminders:")
    print("- Be respectful with scraping frequency")
    print("- Check the website's robots.txt and terms of service")
    print("- Start with low depth (1) to understand the site structure")

if __name__ == "__main__":
    main()