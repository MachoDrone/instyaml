# Nosana Dashboard Scraper

A configurable web scraper for the Nosana dashboard with depth control and intelligent element filtering.

## Quick Start

1. **Setup (Automated)**:
   ```bash
   python setup_scraper.py
   ```

2. **Run Basic Scraper**:
   ```bash
   python nosana_scraper.py
   ```

3. **Run Custom Configuration**:
   ```bash
   python example_config.py
   ```

## Answering Your Original Questions

### 1. "What do I provide to you so you know if this is Java or how you determine what is a clickable link?"

**The scraper automatically detects clickable elements using:**

#### **CSS Selectors** (you can customize these):
```python
# Default selectors (already configured)
clickable_selectors = [
    'a[href]',                    # Standard links
    'button[onclick]',            # Buttons with JavaScript
    '[role="button"]',            # ARIA button roles
    '.clickable',                 # Elements with clickable class
    '[data-testid*="link"]',      # Test ID patterns
    '[data-link]',                # Data attributes
]
```

#### **What you need to provide:**
- **Text patterns** of elements you DON'T want clicked (you already provided these)
- **Custom CSS selectors** if the site uses specific patterns
- **Inspection results** from browser dev tools (F12) if needed

#### **For JavaScript/React sites like Nosana:**
- The scraper handles dynamic content automatically
- It waits for pages to load before extracting elements
- It can detect elements with `onClick` handlers

### 2. "What to hover or scrape?"

**The scraper determines this by:**

#### **Element Analysis**:
```python
# It looks for elements with these characteristics:
- href attributes (links)
- onclick handlers (JavaScript buttons)
- role="button" (accessible buttons)
- Specific CSS classes you define
- Data attributes that indicate navigation
```

#### **Safe Defaults**:
- Automatically excludes navigation/menu items
- Avoids elements with dangerous text patterns ('logout', 'delete', etc.)
- Skips JavaScript-only links that don't lead to new pages

### 3. "Some things I don't want clicked-on"

**You control this through exclusion lists:**

#### **By Text Content** (configured based on your requirements):
```python
excluded_elements = [
    'Profile',
    'Deploy Model', 
    # 'Explorer',  # REMOVED - you want to click this to access GPUs
    'Help & Support',
    'Healthy',
    'Nosana dashboard', 
    'Select Wallet',
    '© 2025 Nosana',
    'GPUs Available',  # The counter text, not the GPU section
    '311/1132'         # The specific numbers
]
```

#### **By Patterns** (automatically excludes):
```python
excluded_text_patterns = [
    'logout', 'sign out', 'delete', 'remove', 'cancel'
]
```

#### **By CSS Classes** (automatically avoids):
- Navigation elements (`nav`, `menu`, `header`, `footer`)
- Elements marked with `data-exclude="true"`

### 4. "Adjustable depth"

**Fully configurable:**

```python
config = ScrapingConfig(
    max_depth=1,  # 1 = one click deep
    # max_depth=2,  # 2 = two clicks deep
    # max_depth=3,  # etc.
)
```

#### **Depth Explanation**:
- **Depth 0**: Only the main dashboard page
- **Depth 1**: Main page + any pages reached by one click
- **Depth 2**: Main page + one-click pages + pages reached from those
- **Depth 3+**: Continues the pattern

## Navigation Strategy for Nosana Dashboard

Based on your requirements, the scraper follows this path:

### **Depth 0**: Main Dashboard
- Captures hover data (country info: "United States", "235 online hosts", etc.)
- Identifies "Explorer" as a clickable element

### **Depth 1**: Explorer Section
- Clicks on "Explorer" (NOT excluded)
- Finds "GPUs" and "Host Leaderboard" options
- Will click through to "GPUs" for deeper scraping

### **Depth 2+**: GPU Details
- Navigates through GPU-related pages
- Future path to "Host Leaderboard" data

**Key Point**: Explorer is specifically **allowed** in the configuration to enable this navigation path.

## Configuration Examples

### **Basic Configuration**:
```python
config = ScrapingConfig(
    base_url="https://dashboard.nosana.com/",
    max_depth=1,
    delay_between_requests=2.0,
    output_format="json"
)
```

### **Advanced Configuration**:
```python
config = ScrapingConfig(
    base_url="https://dashboard.nosana.com/",
    max_depth=2,  # Go deeper
    delay_between_requests=3.0,  # Slower for politeness
    timeout=15,
    output_format="json"
)

# Add more exclusions
config.excluded_elements.extend([
    'GPUs Available',
    '311/1132',
    'Settings',
    'Logout'
])

# Add custom clickable elements if needed
config.clickable_selectors.extend([
    '.dashboard-card a',      # Dashboard cards
    '[data-navigate]',        # Custom navigation
    '.btn-primary'            # Primary buttons
])
```

## Files Created

| File | Purpose |
|------|---------|
| `nosana_scraper.py` | Main scraper with full functionality |
| `requirements.txt` | Python dependencies |
| `setup_scraper.py` | Automated setup and Chrome installation |
| `example_config.py` | Example usage and configuration |
| `SCRAPER_CONFIGURATION_GUIDE.md` | Detailed configuration guide |

## Key Features

### **✅ Intelligent Element Detection**
- Automatically finds clickable elements using multiple strategies
- Handles JavaScript/React applications
- Waits for dynamic content to load

### **✅ Safe by Default**
- Excludes dangerous actions (logout, delete, etc.)
- Avoids navigation elements automatically
- Respects your exclusion lists

### **✅ Configurable Depth**
- Start shallow (depth 1) to understand site structure
- Increase depth for comprehensive scraping
- Each level shows what pages it found

### **✅ Multiple Output Formats**
- JSON for structured data analysis
- CSV for spreadsheet compatibility  
- TXT for human-readable output

### **✅ Hover Data Capture**
- Automatically captures tooltip/popup data on hover
- Detects country information like "United States", "235 online hosts", etc.
- Configurable hover selectors for different tooltip systems

### **✅ Respectful Scraping**
- Configurable delays between requests
- Proper error handling and timeouts
- Logging to track what's happening

## How the Scraper Determines Clickable Elements

The scraper uses a multi-step process:

1. **Load Page**: Uses Chrome WebDriver to load the page fully
2. **Wait for Content**: Waits for JavaScript to render dynamic elements
3. **Parse HTML**: Uses BeautifulSoup to analyze the page structure
4. **Find Elements**: Searches for elements matching the clickable selectors
5. **Filter Elements**: Removes elements that match exclusion criteria
6. **Extract URLs**: Gets the destination URLs from href attributes or onclick handlers
7. **Queue for Next Depth**: Adds valid URLs to scrape at the next depth level

## Output Structure

Each scraped page includes:
```json
{
  "url": "https://dashboard.nosana.com/some-page",
  "title": "Page Title", 
  "text_content": "All visible text from the page",
  "links": ["array", "of", "all", "links", "found"],
  "images": ["array", "of", "image", "urls"],
  "metadata": {"description": "meta tags", "keywords": "etc"},
  "hover_data": {
    "hover_United States": "235 online hosts, 162 running, 73 available",
    "hover_Europe": "150 online hosts, 89 running, 61 available"
  },
  "timestamp": "2024-01-01T12:00:00",
  "depth": 1,
  "source_url": "https://dashboard.nosana.com/"
}
```

## Important Notes

### **⚠️ Legal and Ethical Considerations**
- Check Nosana's robots.txt and terms of service
- Be respectful with request frequency (2-3 second delays)
- Don't overload their servers

### **⚠️ Technical Considerations**
- Start with `max_depth=1` to understand the site structure
- The dashboard may require authentication for full access
- Some content might be loaded dynamically via API calls

### **⚠️ Authentication**
- The scraper starts from the public dashboard page
- If you need authenticated areas, you may need to extend the scraper
- Consider handling login flows if needed

## Troubleshooting

### **No Clickable Elements Found**
1. Check browser dev tools (F12) to see actual HTML structure
2. Look at the console output for excluded elements
3. Add custom selectors for site-specific patterns

### **Authentication Required**
1. The public dashboard should be accessible without login
2. For private areas, consider implementing login handling
3. Check if you need to provide credentials

### **Rate Limiting**
1. Increase `delay_between_requests` to 3-5 seconds
2. Monitor server responses for rate limit messages
3. Consider implementing exponential backoff

### **Chrome/WebDriver Issues**
1. Run `python setup_scraper.py` again
2. Make sure Chrome is installed and up to date
3. Check ChromeDriver compatibility

## Next Steps

1. **Start Simple**: Run with `max_depth=1` first
2. **Analyze Results**: Look at what pages and elements are found
3. **Customize**: Add exclusions or custom selectors as needed
4. **Scale Up**: Increase depth gradually
5. **Monitor**: Watch for any issues or rate limiting

The scraper is designed to be safe and respectful while giving you full control over what gets scraped and what gets avoided.