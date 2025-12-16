import requests
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader
import datetime
import sys
import re
import os

# Configuration
# Usage: python weekly_magazine.py [optional_url]
# If no URL provided, it asks for Date interactively.
BASE_URL = sys.argv[1] if len(sys.argv) > 1 and "http" in sys.argv[1] else "https://daktilo1984.com/daktilo2/"
TEMPLATE_FILE = "template.html"
OUTPUT_FILE = "magazine_weekly.html"

# Reference for Issue Number Calculation
# 14 Dec 2025 is Issue 15.
REF_DATE = datetime.date(2025, 12, 14)
REF_ISSUE = 15

def normalize_date_str(date_str):
    """Normalizes date string to match website format (e.g., '07 Aralık' -> '7 Aralık')."""
    try:
        parts = date_str.strip().split()
        if len(parts) >= 3:
            day = int(parts[0]) # Removes leading zero
            month = parts[1]
            year = parts[2]
            return f"{day} {month} {year}"
    except:
        return date_str.strip()
    return date_str.strip()

def parse_turkish_date(date_str):
    """Parses Turkish date string to datetime.date object."""
    try:
        months = {
            "Ocak": 1, "Şubat": 2, "Mart": 3, "Nisan": 4, "Mayıs": 5, "Haziran": 6,
            "Temmuz": 7, "Ağustos": 8, "Eylül": 9, "Ekim": 10, "Kasım": 11, "Aralık": 12
        }
        parts = date_str.strip().split()
        if len(parts) >= 3:
            day = int(parts[0])
            month_name = parts[1]
            year = int(parts[2])
            month = months.get(month_name, 1)
            return datetime.date(year, month, day)
    except:
        pass
    return None

def calculate_issue_number(article_date_str):
    """Calculates issue number based on reference date."""
    current_date = parse_turkish_date(article_date_str)
    if current_date:
        delta = current_date - REF_DATE
        weeks_diff = delta.days // 7
        return REF_ISSUE + weeks_diff
    return REF_ISSUE

def fetch_latest_articles(target_date_input=None):
    """Fetches articles using pagination search if specific date is requested."""
    print(f"Starting fetch from {BASE_URL}...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    target_date_obj = None
    target_date_str = None
    
    if target_date_input:
        target_date_str = normalize_date_str(target_date_input)
        target_date_obj = parse_turkish_date(target_date_str)
        print(f"Looking for articles dated: {target_date_str}")
    
    found_articles = []
    current_url = BASE_URL
    page_count = 0
    max_pages = 10 # Safety limit
    
    while current_url and page_count < max_pages:
        page_count += 1
        print(f"Scanning page {page_count}: {current_url}")
        
        try:
            response = requests.get(current_url, headers=headers)
            response.raise_for_status()
        except Exception as e:
            print(f"Page fetch error: {e}")
            break
            
        soup = BeautifulSoup(response.text, 'html.parser')
        article_nodes = soup.find_all('article', class_='l-post')
        
        if not article_nodes:
            print("No articles found on this page.")
            break
            
        # Check articles on this page
        page_has_newer = False
        page_has_older = False
        
        for node in article_nodes:
            # Extract basic info
            title_node = node.find('h2', class_='post-title')
            if not title_node: continue
            
            link = title_node.find('a')['href']
            title = title_node.get_text(strip=True)
            
            author_node = node.find('span', class_='post-author')
            author = author_node.get_text(strip=True) if author_node else "Daktilo1984"
            
            date_node = node.find('time', class_='post-date')
            date_text = date_node.get_text(strip=True) if date_node else datetime.date.today().strftime("%d %B %Y")
            
            # Logic
            art_date = parse_turkish_date(date_text)
            
            # Default behavior (No target): Take first article's date as target
            if not target_date_obj:
                target_date_str = date_text
                target_date_obj = art_date
                print(f"No date specified. Defaulting to most recent: {target_date_str}")
            
            # Image extraction
            media_node = node.find('span', class_='img')
            image_url = ""
            if media_node and 'data-bgsrc' in media_node.attrs:
                raw_url = media_node['data-bgsrc']
                image_url = re.sub(r'-\d+x\d+(\.\w+)$', r'\1', raw_url)
            
            excerpt_node = node.find('div', class_='excerpt')
            excerpt = excerpt_node.get_text(strip=True) if excerpt_node else ""
            
            article_data = {
                'title': title,
                'link': link,
                'author': author,
                'date': date_text,
                'image_url': image_url,
                'excerpt': excerpt
            }
            
            if art_date == target_date_obj:
                # Match found!
                # Avoid duplicates
                if not any(a['link'] == link for a in found_articles):
                    found_articles.append(article_data)
            elif art_date > target_date_obj:
                page_has_newer = True
            elif art_date < target_date_obj:
                page_has_older = True
        
        # Decision Logic
        if found_articles and page_has_older:
            # We found our articles and hit older ones, so we are likely done.
            # But valid articles might span across page break?
            # If we found matches on this page, let's just peek ONE more page just in case?
            # No, usually WP sorts strictly.
            print(f"Found {len(found_articles)} articles. Reached older content. Stopping.")
            break
            
        if page_has_older and not found_articles:
            # All articles on this page are OLDER than target.
            # And we haven't found any yet.
            # Means we sadly missed it or it doesn't exist? 
            # Or maybe the target date was "7 Dec" and we are at "6 Dec".
            print("Passed the target date without finding articles. Stopping.")
            break
            
        # Pagination
        next_link = soup.find('a', class_='next page-numbers')
        if next_link:
            current_url = next_link['href']
        else:
            print("No next page.")
            current_url = None

    print(f"Total kept: {len(found_articles)}")
    issue_number = calculate_issue_number(target_date_str) if target_date_str else REF_ISSUE
    return found_articles, target_date_str, issue_number

def fetch_full_content(article):
    """Fetches the full content of an article."""
    print(f"Fetching full content for: {article['title']}")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        response = requests.get(article['link'], headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching article content: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Standard WordPress content area
    content_div = soup.find('div', class_='entry-content')
    if content_div:
        # Remove unwanted elements like scripts, ads, etc.
        for tag in content_div(['script', 'style', 'div.sharedaddy', 'div.related-posts']):
            tag.decompose()
            
        # Fix Lazy Loaded Images
        # WordPress/SmartMag uses data-src for lazy loading. We need to swap it back to src.
        for img in content_div.find_all('img'):
            if img.get('data-src'):
                img['src'] = img['data-src']
            # Remove srcset to avoid browser trying to load other broken/lazy variants
            if img.get('srcset'):
                del img['srcset']
            if img.get('data-srcset'):
                del img['data-srcset']
                
        article['content'] = str(content_div)
    else:
        article['content'] = "<p>Content could not be fetched automatically.</p>"

def generate_magazine_html(articles, issue_date, issue_number):
    if len(articles) < 1:
        print("Not enough articles found for this date.")
        return

    # Organize data
    # Dynamic assignment based on list position, NO specific writer names
    data = {
        "headline": articles[0],
        "sidebar": articles[1] if len(articles) > 1 else None,
        "bottom_articles": articles[2:] if len(articles) > 2 else [],
        "full_articles": articles,
        "issue_date": issue_date,
        "issue_number": issue_number
    }
    
    # Fetch content for all
    for art in articles:
        fetch_full_content(art)
    
    # Post-process Headline
    data["headline"]["intro"] = data["headline"]["excerpt"]

    # Render
    def get_resource_path(relative_path):
        """Get absolute path to resource, works for dev and for PyInstaller"""
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, relative_path)

    # Load template from bundle or local source
    template_path = get_resource_path(TEMPLATE_FILE)
    template_dir = os.path.dirname(template_path)
    
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template(os.path.basename(template_path))
    output = template.render(**data)
    
    # Dynamic Filename
    output_filename = OUTPUT_FILE # Default fallback
    try:
        parts = issue_date.split()
        if len(parts) >= 3:
            day = parts[0]
            month = parts[1]
            year = parts[2]
            short_year = year[-2:] if len(year) == 4 else year
            output_filename = f"{day}{month}{short_year}-daktilo2.html"
    except Exception as e:
        print(f"Error creating filename: {e}")

    # Output should be in the directory where the executable is running (getcwd), 
    # NOT in the temporary _MEIPASS directory.
    output_path = os.path.join(os.getcwd(), output_filename)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output)
    
    print(f"Magazine generated successfully: {output_path}")

def main():
    # Ask for date if not provided as a second arg
    user_date = None
    if len(sys.argv) > 1 and not "http" in sys.argv[1]:
        # Assume arg is date if not http
        user_date = sys.argv[1]
    
    
    # Interactive mode with GUI
    if not user_date:
        try:
            import tkinter as tk
            from tkinter import ttk
            import calendar
            
            def pick_date_gui():
                root = tk.Tk()
                root.title("Dergi Tarihi Seçin")
                root.geometry("300x350")
                
                selected_date = tk.StringVar()
                current_date = datetime.date.today()
                
                # Month/Year Logic
                current_month = current_date.month
                current_year = current_date.year
                
                header_frame = tk.Frame(root)
                header_frame.pack(pady=10)
                
                lbl_month_year = tk.Label(header_frame, text=f"{calendar.month_name[current_month]} {current_year}", font=("Arial", 12, "bold"))
                lbl_month_year.pack(side=tk.LEFT, padx=10)

                cal_frame = tk.Frame(root)
                cal_frame.pack(expand=True, fill='both', padx=10)
                
                def update_calendar(y, m):
                    # Clear frame
                    for widget in cal_frame.winfo_children():
                        widget.destroy()
                        
                    # Weekday headers
                    days = ['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz']
                    for i, day in enumerate(days):
                        tk.Label(cal_frame, text=day, font=("Arial", 8, "bold")).grid(row=0, column=i)
                        
                    # Days
                    month_cal = calendar.monthcalendar(y, m)
                    for r, week in enumerate(month_cal):
                        for c, day in enumerate(week):
                            if day != 0:
                                btn = tk.Button(cal_frame, text=str(day), width=4, 
                                                command=lambda d=day: on_day_select(d, m, y))
                                btn.grid(row=r+1, column=c, padx=1, pady=1)

                    # Update Label (Turkish approximation for display)
                    tr_months = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
                    lbl_month_year.config(text=f"{tr_months[m]} {y}")

                def on_day_select(d, m, y):
                    tr_months = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
                    # Format: 07 Aralık 2025
                    day_str = f"{d:02d}"
                    date_val = f"{day_str} {tr_months[m]} {y}"
                    selected_date.set(date_val)
                    root.destroy()
                    
                def prev_month():
                    nonlocal current_month, current_year
                    current_month -= 1
                    if current_month < 1:
                        current_month = 12
                        current_year -= 1
                    update_calendar(current_year, current_month)

                def next_month():
                    nonlocal current_month, current_year
                    current_month += 1
                    if current_month > 12:
                        current_month = 1
                        current_year += 1
                    update_calendar(current_year, current_month)

                # Navigation Buttons
                btn_prev = tk.Button(header_frame, text="<", command=prev_month)
                btn_prev.pack(side=tk.LEFT)
                
                lbl_month_year.pack(side=tk.LEFT, padx=10) # Re-pack to center
                
                btn_next = tk.Button(header_frame, text=">", command=next_month)
                btn_next.pack(side=tk.LEFT)
                
                # Init
                update_calendar(current_year, current_month)
                
                # Label for instruction
                tk.Label(root, text="Bir tarih seçiniz...", fg="gray").pack(pady=5)
                
                root.mainloop()
                return selected_date.get()

            print("Opening Calendar GUI...")
            user_date = pick_date_gui()
            
        except ImportError:
            # Fallback if tkinter issues (e.g. headless)
            pass
        except Exception as e:
            print(f"GUI Error: {e}")
    
    # Text fallback if GUI failed or closed without selection
    if not user_date:
        try:
            # Interactive prompt
            print("Enter the desired issue date (e.g. '07 Aralık 2025') or press Enter for latest:")
            sys.stdout.flush() 
            input_line = sys.stdin.readline().strip()
            if input_line:
                user_date = input_line
        except Exception:
            pass # Fallback to latest

    result = fetch_latest_articles(user_date)
    
    if not result:
        print("No articles found.")
        return
        
    articles, issue_date, issue_number = result
    
    if not articles:
        print(f"No articles found for date: {issue_date}")
        return
    
    generate_magazine_html(articles, issue_date, issue_number)

if __name__ == "__main__":
    main()
