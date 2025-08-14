# Oracle LiveLabs Workshop Scraper

This project contains three different web scrapers to extract workshop titles from the Oracle LiveLabs website and save them as a JSON file.

## Available Scrapers

### 1. `livelabs_scraper.py` (Recommended - Full Features)
- **Requirements**: Python + Chrome + Selenium dependencies
- **Features**: 
  - Handles dynamic content and JavaScript
  - Automatic pagination using next button clicks
  - Most reliable for complex websites
  - Headless browser automation

### 2. `advanced_livelabs_scraper.py` (No Dependencies)
- **Requirements**: Python only (built-in libraries)
- **Features**:
  - Advanced pagination pattern detection
  - Multiple URL parameter strategies
  - Better error handling
  - No external dependencies

### 3. `simple_livelabs_scraper.py` (Basic - No Dependencies)
- **Requirements**: Python only (built-in libraries)
- **Features**:
  - Simple HTML parsing
  - Basic pagination support
  - Minimal dependencies
  - Good for static content

## Quick Start

### Option 1: Simple Version (No Installation Required)
```bash
python3 simple_livelabs_scraper.py
```

### Option 2: Advanced Version (No Installation Required)
```bash
python3 advanced_livelabs_scraper.py
```

### Option 3: Full Version (Requires Installation)
```bash
# Install dependencies
pip3 install -r requirements.txt

# Run the scraper
python3 livelabs_scraper.py
```

## Features

- Scrapes workshop titles from all pages of the LiveLabs workshop cards
- Handles pagination automatically using the "next" button
- Saves results in JSON format with metadata
- Includes logging for monitoring progress
- Respectful scraping with delays between requests

## Output

All scrapers generate a JSON file with the following structure:
```json
{
  "total_workshops": 1234,
  "scraped_at": "2024-01-15 14:30:25",
  "workshops": [
    {
      "title": "Get Started with Oracle Cloud Infrastructure Core Services",
      "page_number": 1
    },
    ...
  ]
}
```

## Which Scraper to Use?

1. **Start with `simple_livelabs_scraper.py`** - It requires no installation and works with basic websites
2. **Try `advanced_livelabs_scraper.py`** - If the simple version doesn't work well, this handles more complex pagination
3. **Use `livelabs_scraper.py`** - If the website uses heavy JavaScript or dynamic content

## Troubleshooting

### Common Issues:

1. **No workshops found**: The website structure might have changed
2. **Pagination not working**: Try a different scraper version
3. **Installation issues**: Use the simple or advanced versions that don't require external dependencies

### For Dynamic Content:
If the website heavily relies on JavaScript, you'll need the Selenium version:
```bash
# Install Chrome browser first, then:
pip3 install -r requirements.txt
python3 livelabs_scraper.py
```

## Notes

- All scrapers include delays between requests to be respectful to the server
- Progress is logged to the console
- If a scraper encounters errors, it will log them and continue where possible
- The JSON file is saved in the same directory as the script 

https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/view-workshop?wid=703&clear=RR,180&session=112700426194238
https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/run-workshop?p210_wid=703&p210_wec=&session=112700426194238