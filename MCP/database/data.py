#!/usr/bin/env python3
"""
data.py

- Creates SQLite database file: data.db
- Table: main (id INTEGER PRIMARY KEY AUTOINCREMENT, question TEXT, answer TEXT)
- Inserts seed Q&A about National Taiwan University of Science and Technology (NTUST).
- Optional web-scraper (run with --scrape) to fetch more public info from ntust.edu.tw
  and append as question/answer rows.

Usage:
    python data.py            # create DB and insert seed rows
    python data.py --scrape   # also run the polite NTUST site scraper (may take time)
"""

import sqlite3
import argparse
import time
from urllib.parse import urljoin, urlparse
import re

# Optional libraries for scraping. If you want scraping, install required libs:
# pip install requests beautifulsoup4
try:
    import requests
    from bs4 import BeautifulSoup
except Exception:
    requests = None
    BeautifulSoup = None

DB_FILENAME = "data.db"
TABLE_NAME = "main"
NTUST_BASE = "https://www.ntust.edu.tw/"


def create_db(db_filename=DB_FILENAME):
    conn = sqlite3.connect(db_filename)
    c = conn.cursor()
    c.execute(f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT NOT NULL,
        answer TEXT NOT NULL
    )
    """)
    conn.commit()
    return conn


def insert_qa(conn, qa_pairs):
    c = conn.cursor()
    c.executemany(f"INSERT INTO {TABLE_NAME} (question, answer) VALUES (?, ?)", qa_pairs)
    conn.commit()


def seed_data():
    """
    Seed with useful NTUST facts (collected from official site and Wikipedia).
    These are starting points; run the scraper for many more details.
    Sources include NTUST official site and Wikipedia.
    """
    qa = [
        ("Official name", "National Taiwan University of Science and Technology (NTUST), also Taiwan Tech or TaiwanTech."),
        ("Chinese name", "國立臺灣科技大學 (commonly 臺科大)"),
        ("Established", "1974 (established originally as National Taiwan Institute of Technology)."),
        ("Main campus location", "Gongguan Campus, Daan District, Taipei City, Taiwan."),
        ("President (as listed publicly)", "See NTUST official site or Wikipedia for current president name; this can change over time."),
        ("Student population (approx.)", "Around 11,600 students total (numbers vary by year; see official stats)."),
        ("Major colleges", "College of Engineering; College of Electrical Engineering and Computer Science; School of Management; College of Design; College of Liberal Arts and Social Sciences; College of Intellectual Property Studies; Honors College."),
        ("Campus type", "Urban campus, multiple campuses including Gongguan (main) and Huaxia campus (Zhonghe)."),
        ("International students", "NTUST hosts international master's and doctoral students; it is noted as one of Taiwan's most popular universities for international students."),
        ("Notable rankings (examples)", "Ranks in QS subject rankings across multiple subjects; QS Asia ranking and other lists—see NTUST ranking pages for details."),
        ("Research highlights", "NTUST faculty have been recognized among top scientists; NTUST reports many faculty selected among top 2% globally and various IEEE Fellows."),
        ("Website", "https://www.ntust.edu.tw/"),
        ("Short FAQ: What is NTUST known for?", "NTUST (Taiwan Tech) is known for engineering, applied sciences, design, industry collaboration, entrepreneurship, and technology licensing."),
        ("School code (Taiwan)", "School code (MOE listing) 0022 (refer to official MOE data)."),
        ("How to find departments", "Visit https://www.ntust.edu.tw/ and browse 'Academics' for department and graduate program lists."),
        ('What is NTUST?', 'NTUST, also known as Taiwan Tech, is a public research university in Taipei, Taiwan. Established in 1974, it was the first higher education institution of its kind in Taiwan\'s technical and vocational education system.'),
        ('Where is NTUST located?', 'NTUST is located at No. 43, Section 4, Keelung Road, Da\'an District, Taipei City, Taiwan.'),
        ('What are the most popular department in NTUST?', 'Based on recent rankings and citations, some of the most popular and highly-ranked departments at NTUST include: Art and Design, Education and Training, Architecture and Built Environment, and Civil and Structural Engineering. Additionally, core STEM fields like Business and Management, Computer Science, Materials Science, and Electrical Engineering have also shown strong performance.')
        # Add more seed Q&A below if you want
    ]
    return qa


# -----------------------
# Lightweight polite scraper
# -----------------------
def polite_ntust_scraper(conn, max_pages=200, pause=0.6):
    """
    Crawl NTUST site (ntust.edu.tw) to find:
      - department pages
      - faculty listing pages
      - news headlines
    For each item found, insert a Q/A row into the DB.

    NOTE: This is a polite, shallow site-limited crawler. It does NOT attempt to bypass paywalls
    or access private content. It respects the domain boundary and rate-limits requests.

    Requirements: requests, beautifulsoup4
    """
    if requests is None or BeautifulSoup is None:
        print("Scraper requires 'requests' and 'beautifulsoup4'. Install via: pip install requests beautifulsoup4")
        return

    visited = set()
    to_visit = [NTUST_BASE]
    pages_visited = 0

    domain = urlparse(NTUST_BASE).netloc

    while to_visit and pages_visited < max_pages:
        url = to_visit.pop(0)
        if url in visited:
            continue
        visited.add(url)
        try:
            resp = requests.get(url, timeout=12, headers={"User-Agent": "NTUST-data-scraper/1.0 (+your-email@example.com)"})
        except Exception as e:
            print(f"Failed to GET {url}: {e}")
            continue

        pages_visited += 1
        print(f"[{pages_visited}] Visited: {url} (status {resp.status_code})")
        if resp.status_code != 200 or 'text/html' not in resp.headers.get('Content-Type', ''):
            time.sleep(pause)
            continue

        soup = BeautifulSoup(resp.text, "html.parser")

        # Extract news headlines and URLs
        # Common pattern: many NTUST news pages have <h3> or <a> with class or link containing 'p/404' or 'p/406'
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            full = urljoin(url, href)
            parsed = urlparse(full)
            if parsed.netloc != domain:
                continue

            # Basic heuristics for 'news' or 'page' content
            text = a.get_text(strip=True)
            if not text:
                continue

            # If link looks like news / announcement (often contains '/p/404' or '/p/406' or '/p/'):
            if re.search(r'/p/\d', parsed.path) or re.search(r'news|announcement|news', href, re.I):
                q = f"NTUST site link: {text}"
                a_text = f"URL: {full}"
                try:
                    insert_qa(conn, [(q, a_text)])
                except Exception:
                    pass

            # Add to queue if looks like an internal page likely to have faculty or department lists
            if parsed.path.count('/') <= 6 and full not in visited and full not in to_visit:
                to_visit.append(full)

        # Heuristic: look for faculty lists in the page
        # Look for lists with names (two capitalized words or names with Chinese characters)
        # This is heuristic; we'll capture obvious candidate texts.
        blobs = []
        for tag in soup.find_all(['li', 'p', 'div', 'span', 'h2', 'h3']):
            txt = tag.get_text(" ", strip=True)
            if not txt:
                continue
            # look for patterns like "Professor" or email or 'Professor' Chinese '教授' or common faculty keywords
            if re.search(r'\bProfessor\b|\b教授\b|\bProfessor,|\bLecturer\b|\bAssistant Professor\b', txt, re.I) or re.search(r'@mail\.ntust', txt):
                blobs.append(txt)

        for b in blobs:
            q = "Faculty / profile snippet"
            a_text = b
            try:
                insert_qa(conn, [(q, a_text)])
            except Exception:
                pass

        # Always pause
        time.sleep(pause)

    print(f"Scraping finished. Visited {pages_visited} pages, stored many rows in DB.")


def main():
    parser = argparse.ArgumentParser(description="Create NTUST Q/A SQLite DB and optionally scrape ntust.edu.tw")
    parser.add_argument("--scrape", action="store_true", help="Run polite NTUST site scraper after seeding DB")
    args = parser.parse_args()

    conn = create_db()
    seed = seed_data()
    print(f"Inserting {len(seed)} seed Q/A rows into {DB_FILENAME}...")
    insert_qa(conn, seed)
    print(f"Inserted seed data into {DB_FILENAME} table '{TABLE_NAME}'.")

    if args.scrape:
        print("Starting polite scraper of NTUST site (this may take a while)...")
        polite_ntust_scraper(conn, max_pages=250, pause=0.6)

    conn.close()
    print("Done. Database file:", DB_FILENAME)


if __name__ == "__main__":
    main()
