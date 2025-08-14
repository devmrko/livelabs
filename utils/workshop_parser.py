#!/usr/bin/env python3
"""
Common workshop parsing utilities
"""

import re
import json
import logging
from bs4 import BeautifulSoup
from datetime import datetime

logger = logging.getLogger(__name__)

class WorkshopParser:
    """Reusable workshop parsing functionality"""
    
    @staticmethod
    def extract_workshops_beautifulsoup(html_content):
        """
        Parse workshops using BeautifulSoup - most readable and maintainable
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        workshops = []
        
        # Find all workshop cards
        cards = soup.find_all('div', class_='a-CardView')
        
        for card in cards:
            try:
                # Extract workshop ID from URL
                link = card.find('a', class_='a-CardView-fullLink')
                href = link.get('href', '') if link else ''
                wid_match = re.search(r'wid=(\d+)', href)
                workshop_id = wid_match.group(1) if wid_match else None
                
                # Extract title
                title_span = card.find('span', style=lambda x: x and 'font-weight:700' in x)
                title = title_span.get_text(strip=True) if title_span else ''
                
                # Extract description
                desc_div = card.find('div', class_='a-CardView-mainContent')
                description = desc_div.get_text(strip=True) if desc_div else ''
                
                # Extract duration
                clock_span = card.find('span', class_='fa fa-clock-o')
                duration = clock_span.get_text(strip=True) if clock_span else ''
                
                # Extract views
                subcontent = card.find('div', class_='a-CardView-subContent')
                views = None
                if subcontent:
                    views_match = re.search(r'(\d+)\s+Views', subcontent.get_text())
                    views = int(views_match.group(1)) if views_match else None
                
                workshops.append({
                    'id': workshop_id,
                    'title': title,
                    'description': description,
                    'duration': duration,
                    'views': views,
                    'url': href.replace('&amp;', '&')
                })
                
            except Exception as e:
                logger.warning(f"Error parsing workshop card: {e}")
                continue
        
        return workshops
    
    @staticmethod
    def save_workshops_to_json(workshops, filename, page_number=1, total_pages=1):
        """Save workshops to JSON file with metadata"""
        try:
            data = {
                "total_workshops": len(workshops),
                "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "page_number": page_number,
                "total_pages": total_pages,
                "workshops": workshops
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Workshops saved to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving to JSON: {e}")
            return False
    
    @staticmethod
    def load_workshops_from_json(filename):
        """Load workshops from JSON file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('workshops', [])
        except Exception as e:
            logger.error(f"Error loading from JSON: {e}")
            return []
    
    @staticmethod
    def print_workshop_summary(workshops, title="WORKSHOP SUMMARY"):
        """Print a formatted summary of workshops"""
        print("\n" + "="*60)
        print(title)
        print("="*60)
        print(f"Total workshops: {len(workshops)}")
        print(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if workshops:
            print("\nSample workshops:")
            print("-" * 40)
            for i, workshop in enumerate(workshops[:5], 1):
                print(f"{i}. {workshop.get('title', 'N/A')}")
                print(f"   ID: {workshop.get('id', 'N/A')}")
                print(f"   Duration: {workshop.get('duration', 'N/A')}")
                print(f"   Views: {workshop.get('views', 'N/A')}")
                print()
        
        print("="*60) 