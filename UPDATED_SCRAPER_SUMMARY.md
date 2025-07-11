# 🔄 Updated Nosana Scraper - Key Changes

## ✅ What Was Fixed Based on Your Feedback

### **1. "Explorer" is Now ALLOWED to be Clicked**
- **REMOVED** "Explorer" from the excluded elements list
- The scraper will now click on "Explorer" to access GPUs and Host Leaderboard
- Updated all configuration files to reflect this change

### **2. Added Hover Data Capture** 
- **NEW FEATURE**: Automatically captures tooltip/popup data on hover
- Will capture country information like: "United States", "235 online hosts", "162 running", "73 available"
- Hover data is saved as part of each page's output

### **3. Clarified Safety Exclusions**
Made the safety exclusions more explicit and comprehensive:
```python
excluded_text_patterns = [
    'logout', 'sign out', 'sign-out', 'log out',
    'delete', 'remove', 'cancel', 
    'close account', 'terminate', 'destroy'
]
```

### **4. Updated Navigation Strategy**
- **Depth 0**: Main dashboard + hover data capture
- **Depth 1**: Clicks "Explorer" → finds "GPUs" and "Host Leaderboard"  
- **Depth 2+**: Navigates through GPU pages (future: Host Leaderboard)

## 🎯 Current Exclusions (What WON'T Be Clicked)

```python
excluded_elements = [
    'Profile',           # User profile 
    'Deploy Model',      # Model deployment
    'Help & Support',    # Support pages
    'Healthy',           # Status indicator
    'Nosana dashboard',  # Dashboard title/logo
    'Select Wallet',     # Wallet selection
    '© 2025 Nosana',    # Copyright
    'GPUs Available',    # The counter text (not the GPU section)
    '311/1132'          # The specific numbers
]
```

**Key Change**: `'Explorer'` has been **REMOVED** from exclusions!

## 🎯 What WILL Be Clicked Now

1. **"Explorer"** → Opens GPU and Host Leaderboard options
2. **"GPUs"** → Navigate deeper into GPU data
3. **Links within GPU sections** → Detailed GPU information
4. **Any other navigation elements** that lead to data pages

## 🆕 New Hover Data Feature

The scraper now automatically:
1. **Finds hoverable elements** using selectors like:
   - `[data-tooltip]`, `[title]`, `.map-region`, `.country`, etc.
2. **Hovers over them** and captures tooltip content
3. **Saves hover data** in the output with keys like:
   - `"hover_United States": "235 online hosts, 162 running, 73 available"`

## 📊 Updated Output Structure

Each scraped page now includes:
```json
{
  "url": "https://dashboard.nosana.com/explorer",
  "title": "Explorer - Nosana", 
  "text_content": "All visible text...",
  "links": ["https://dashboard.nosana.com/gpus", ...],
  "images": [...],
  "metadata": {...},
  "hover_data": {
    "hover_United States": "235 online hosts, 162 running, 73 available",
    "hover_Europe": "150 online hosts, 89 running, 61 available"
  },
  "timestamp": "2024-01-01T12:00:00",
  "depth": 1,
  "source_url": "https://dashboard.nosana.com/"
}
```

## 🚀 How to Use the Updated Scraper

### **Quick Start** (Same as before):
```bash
python3 setup_scraper.py    # Install everything
python3 example_config.py   # Run with new configuration
```

### **Custom Configuration** for Your Specific Needs:
```python
from nosana_scraper import ScrapingConfig, NosanaScraper

config = ScrapingConfig(
    base_url="https://dashboard.nosana.com/",
    max_depth=2,  # Go deeper to reach GPU data
    delay_between_requests=2.0,
    output_format="json"
)

# Explorer is NOT excluded - it will be clicked!
# Only exclude what you actually don't want
if config.excluded_elements:
    config.excluded_elements.extend([
        'Profile',           # Still don't want this
        'GPUs Available',    # Counter text, not the link
        '311/1132',         # Specific numbers
    ])

scraper = NosanaScraper(config)
results = scraper.scrape_with_depth()
scraper.save_results("nosana_explorer_data")
```

## 🎯 Expected Navigation Flow

1. **Start**: `https://dashboard.nosana.com/`
   - Captures hover data from map regions
   - Finds "Explorer" link

2. **Depth 1**: Clicks "Explorer"
   - Finds "GPUs" and "Host Leaderboard" options
   - Continues to GPU section

3. **Depth 2+**: Navigates GPU pages
   - Captures detailed GPU information
   - Future expansion to Host Leaderboard

## ⚠️ Important Notes

- **Explorer is now clickable** - this is the key change you requested
- **Hover data is captured automatically** - no extra configuration needed
- **Start with depth 1-2** to see the navigation working
- **Monitor the logs** to see what elements are being found and clicked

## 🔍 Debugging the Navigation

If you want to see exactly what's happening:
```python
import logging
logging.basicConfig(level=logging.INFO)  # Shows clickable elements found
# or
logging.basicConfig(level=logging.DEBUG)  # Shows everything including hover attempts
```

The scraper will now properly navigate through Explorer → GPUs and capture all the tooltip data along the way!