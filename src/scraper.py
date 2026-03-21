import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
from urllib.parse import urljoin

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
}

SITES = {
    'משרד הבריאות - פורטל ראשי': {
        'url': 'https://www.gov.il/he/departments/ministry_of_health/govil-landing-page',
        'type': 'govil',
        'icon': '🏛️',
        'color': '#005baa',
    },
    'פורטל הורים': {
        'url': 'https://me.health.gov.il/parenting/',
        'type': 'me_health',
        'icon': '👶',
        'color': '#2e7d32',
    },
    'בריאות הנפש': {
        'url': 'https://me.health.gov.il/mental-health/',
        'type': 'me_health',
        'icon': '🧠',
        'color': '#6a1b9a',
    },
    'הגיל השלישי': {
        'url': 'https://me.health.gov.il/older-adult/',
        'type': 'me_health',
        'icon': '👴',
        'color': '#e65100',
    },
    'אפשריבריא': {
        'url': 'https://efsharibari.health.gov.il/',
        'type': 'efsharibari',
        'icon': '💪',
        'color': '#00838f',
    },
}

ROOT = os.path.dirname(os.path.dirname(__file__))
DATA_FILE = os.path.join(ROOT, 'scraped_data.json')

# Fallback images for pages blocked by Cloudflare or without accessible images
FALLBACK_IMAGES = {
    'https://www.gov.il/he/pages/minister-of-health':
        'https://www.gov.il/BlobFolder/office/ministry_of_health/he/ministry_of_health.png',
    'https://www.gov.il/he/pages/ministry-director-general':
        'https://www.gov.il/BlobFolder/office/ministry_of_health/he/ministry_of_health.png',
    'https://www.gov.il/he/pages/sheagathaari':
        'https://www.gov.il/BlobFolder/office/ministry_of_health/he/ministry_of_health.png',
    'https://www1.health.gov.il/nursing/':
        'https://www1.health.gov.il/media/farlcak0/nursingai-no-bg-1.png',
    'https://me.health.gov.il/met-calculator/':
        'https://me.health.gov.il/media/zddh0ilj/met-social.jpg',
    'https://efsharibari.health.gov.il/well-being/smoking-prevention/call-center/':
        'http://efsharibari.health.gov.il/media/2434/call-center.jpg',
    'https://efsharibari.health.gov.il/well-being/smoking-prevention/clear-environment/':
        'http://efsharibari.health.gov.il/media/1244/no-smoking-1639349_1920.jpg',
}
PREV_FILE = os.path.join(ROOT, 'scraped_data_prev.json')

# Max article summaries to fetch per site (to keep scraping fast)
MAX_SUMMARIES_PER_SITE = 8

_playwright_instance = None


def _get_summary(url, use_playwright=False):
    """Fetch meta description + first paragraph from an article page."""
    if not url or not url.startswith('http'):
        return '', ''

    def _parse(html):
        soup = BeautifulSoup(html, 'lxml')
        # Meta description
        meta = (soup.find('meta', property='og:description') or
                soup.find('meta', attrs={'name': 'description'}))
        summary = meta.get('content', '').strip() if meta else ''

        # First meaningful paragraph as full text
        full_text = ''
        for p in soup.find_all('p'):
            t = p.get_text(strip=True)
            if len(t) > 80:
                full_text = t
                break

        # og:image
        img_el = soup.find('meta', property='og:image')
        image_url = img_el.get('content', '').strip() if img_el else ''

        # Fallback: first meaningful content image in the page
        if not image_url:
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            skip_kw = ['logo', 'icon', 'sprite', 'favicon', 'avatar',
                       'pixel', 'track', 'analytic', 'blank', 'spacer',
                       'banner-top', 'header', 'footer', 'bg', 'background']
            for img in soup.find_all('img', src=True):
                src = img.get('src', '').strip()
                if not src or src.startswith('data:'):
                    continue
                if any(kw in src.lower() for kw in skip_kw):
                    continue
                try:
                    w = int(img.get('width', 0) or 0)
                    h = int(img.get('height', 0) or 0)
                    if (w and w < 150) or (h and h < 100):
                        continue
                except (ValueError, TypeError):
                    pass
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = f"{parsed_url.scheme}://{parsed_url.netloc}{src}"
                elif not src.startswith('http'):
                    continue
                image_url = src
                break

        return summary[:300], full_text[:600], image_url

    try:
        if not use_playwright:
            r = requests.get(url, headers=HEADERS, timeout=8)
            if r.status_code == 200:
                return _parse(r.text)
            use_playwright = True  # fallback

        if use_playwright:
            from playwright.sync_api import sync_playwright
            from playwright_stealth import Stealth
            with Stealth().use_sync(sync_playwright()) as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, wait_until='networkidle', timeout=20000)
                page.wait_for_timeout(2000)
                # Try to get a real rendered image via JS (works for SPAs)
                rendered_image = page.evaluate("""() => {
                    const og = document.querySelector('meta[property="og:image"]');
                    if (og && og.content) return og.content;
                    const skip = ['logo','icon','sprite','favicon','avatar','pixel','track','blank','spacer','header','footer'];
                    const imgs = Array.from(document.querySelectorAll('img'));
                    for (const img of imgs) {
                        const src = img.currentSrc || img.src || '';
                        if (!src || src.startsWith('data:')) continue;
                        if (skip.some(k => src.toLowerCase().includes(k))) continue;
                        if (img.naturalWidth >= 200 && img.naturalHeight >= 150) return src;
                    }
                    return '';
                }""")
                html = page.content()
                browser.close()
            result = list(_parse(html))
            if rendered_image and not result[2]:
                result[2] = rendered_image
            return tuple(result)
    except Exception:
        pass
    return '', '', ''


def _enrich_items(items, use_playwright=False):
    """Fetch summaries for items that are missing descriptions."""
    enriched = 0
    for item in items:
        link = item.get('link', '')
        if not link:
            continue
        # Apply fallback image for known-blocked pages
        if not item.get('image_url') and link in FALLBACK_IMAGES:
            item['image_url'] = FALLBACK_IMAGES[link]
        if enriched >= MAX_SUMMARIES_PER_SITE:
            continue
        # Skip only if already has both description AND image
        if len(item.get('description', '')) > 60 and item.get('image_url'):
            continue
        summary, full_text, image_url = _get_summary(link, use_playwright=use_playwright)
        if summary: item['description'] = summary
        if full_text and full_text != summary: item['full_text'] = full_text
        if image_url: item['image_url'] = image_url
        if summary or full_text or image_url:
            enriched += 1
    return items


def _load_previous():
    if os.path.exists(PREV_FILE):
        with open(PREV_FILE, encoding='utf-8') as f:
            return json.load(f)
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, encoding='utf-8') as f:
            return json.load(f)
    return {}


def _mark_new_items(site_name, items, prev_data):
    """Mark items as 'new' if they weren't in the previous scrape."""
    prev_titles = set()
    if site_name in prev_data:
        prev_titles = {i['title'] for i in prev_data[site_name].get('items', [])}
    for item in items:
        item['is_new'] = item['title'] not in prev_titles
    return items


def _extract_date_from_page(url):
    """Try to fetch a page and extract its publish date."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=8)
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.content, 'lxml')
        # Try common date meta tags and elements
        for selector in [
            'meta[property="article:published_time"]',
            'meta[name="date"]',
            'meta[name="DC.date"]',
            'time[datetime]',
        ]:
            el = soup.select_one(selector)
            if el:
                val = el.get('content') or el.get('datetime') or el.get_text(strip=True)
                if val:
                    return val[:10]
        # Try looking for Hebrew date patterns in text
        import re
        text = soup.get_text()
        match = re.search(r'(\d{1,2})[./](\d{1,2})[./](\d{4})', text)
        if match:
            d, m, y = match.groups()
            return f"{y}-{m.zfill(2)}-{d.zfill(2)}"
    except Exception:
        pass
    return None


def scrape_me_health(url, site_name):
    """Scrape me.health.gov.il sites."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'lxml')

        items = []
        seen_titles = set()

        card_selectors = [
            'article', '.card', '.post', '.entry', '.wp-block-post',
            '[class*="card"]', '[class*="post"]', '[class*="article"]', '[class*="item"]',
        ]

        for selector in card_selectors:
            for card in soup.select(selector):
                title_el = card.find(['h1', 'h2', 'h3', 'h4'])
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                if not title or title in seen_titles or len(title) < 5:
                    continue
                seen_titles.add(title)

                link = ''
                if card.name == 'a' and card.get('href'):
                    link = card['href']
                else:
                    parent = card.parent
                    if parent and parent.name == 'a' and parent.get('href'):
                        link = parent['href']
                    else:
                        link_el = card.find('a', href=True)
                        link = link_el['href'] if link_el else ''
                if link and not link.startswith('http'):
                    link = urljoin(url, link)

                desc_el = card.find('p')
                description = desc_el.get_text(strip=True)[:200] if desc_el else ''

                # Try to get date from time element
                date_el = card.find('time')
                date_str = ''
                if date_el:
                    date_str = date_el.get('datetime', date_el.get_text(strip=True))[:10]

                items.append({
                    'title': title,
                    'link': link,
                    'description': description,
                    'date': date_str,
                })

            if len(items) >= 3:
                break

        # Fallback: extract headings with links
        if len(items) < 3:
            for a in soup.find_all('a', href=True):
                heading = a.find(['h2', 'h3', 'h4'])
                if heading:
                    title = heading.get_text(strip=True)
                    if title and title not in seen_titles and len(title) > 5:
                        seen_titles.add(title)
                        link = a['href']
                        if not link.startswith('http'):
                            link = urljoin(url, link)
                        items.append({
                            'title': title,
                            'link': link,
                            'description': '',
                            'date': '',
                        })

        items = _enrich_items(items[:15], use_playwright=False)
        return {
            'status': 'ok',
            'url': url,
            'items': items,
            'last_scraped': datetime.now().isoformat(),
        }

    except Exception as e:
        return {
            'status': 'error',
            'url': url,
            'error': str(e),
            'items': [],
            'last_scraped': datetime.now().isoformat(),
        }


def scrape_efsharibari(url, site_name):
    """Scrape efsharibari.health.gov.il (SPA - needs Playwright)."""
    try:
        from playwright.sync_api import sync_playwright
        from playwright_stealth import Stealth

        with Stealth().use_sync(sync_playwright()) as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until='networkidle', timeout=30000)
            page.wait_for_timeout(3000)
            html = page.content()
            browser.close()

        soup = BeautifulSoup(html, 'lxml')
        items = []
        seen_titles = set()

        # Try cards/articles
        for selector in ['article', '.card', '[class*="card"]', '[class*="item"]', 'li']:
            for el in soup.select(selector):
                title_el = el.find(['h1', 'h2', 'h3', 'h4'])
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                if not title or title in seen_titles or len(title) < 5:
                    continue
                seen_titles.add(title)
                link_el = el.find('a', href=True)
                link = link_el['href'] if link_el else ''
                if link and not link.startswith('http'):
                    link = urljoin(url, link)
                desc_el = el.find('p')
                description = desc_el.get_text(strip=True)[:200] if desc_el else ''
                items.append({'title': title, 'link': link, 'description': description, 'date': ''})
            if items:
                break

        # Fallback: heading links
        if not items:
            for a in soup.find_all('a', href=True):
                heading = a.find(['h2', 'h3', 'h4'])
                if not heading:
                    continue
                title = heading.get_text(strip=True)
                if not title or title in seen_titles or len(title) < 5:
                    continue
                seen_titles.add(title)
                link = a['href']
                if not link.startswith('http'):
                    link = urljoin(url, link)
                items.append({'title': title, 'link': link, 'description': '', 'date': ''})

        items = _enrich_items(items[:12], use_playwright=True)
        return {
            'status': 'ok' if items else 'error',
            'url': url,
            'error': '' if items else 'לא נמצא תוכן',
            'items': items,
            'last_scraped': datetime.now().isoformat(),
        }
    except Exception as e:
        return {
            'status': 'error',
            'url': url,
            'error': str(e),
            'items': [],
            'last_scraped': datetime.now().isoformat(),
        }


def _is_moh_relevant(link):
    if not link:
        return False
    moh_patterns = ['/he/pages/', '/he/departments/ministry_of_health', 'health.gov.il', 'ironswords']
    for p in moh_patterns:
        if p in link:
            return True
    exclude = ['israel_tax', 'car_licence', 'income_ta', 'government-service',
               'pension', 'land', 'social_security', 'courts', 'police']
    for e in exclude:
        if e in link:
            return False
    return False


def scrape_govil(url, site_name):
    """Scrape gov.il using Playwright + Stealth."""
    try:
        from playwright.sync_api import sync_playwright
        from playwright_stealth import Stealth

        html = None
        for _ in range(2):
            try:
                with Stealth().use_sync(sync_playwright()) as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()
                    page.goto(url, wait_until='networkidle', timeout=30000)
                    page.wait_for_timeout(3000)
                    html = page.content()
                    browser.close()
                if 'Cloudflare Ray ID' in html or len(html) < 5000:
                    html = None
                    continue
                break
            except Exception:
                continue

        if not html:
            return {
                'status': 'blocked',
                'url': url,
                'error': 'האתר חוסם גישה אוטומטית (Cloudflare)',
                'items': [],
                'last_scraped': datetime.now().isoformat(),
            }

        soup = BeautifulSoup(html, 'lxml')
        items = []
        seen_titles = set()

        for selector in ['article', '.card', '[class*="card"]', '[class*="news"]', '[class*="item"]', 'li']:
            for el in soup.select(selector):
                title_el = el.find(['h1', 'h2', 'h3', 'h4', 'h5'])
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                if not title or title in seen_titles or len(title) < 5:
                    continue

                link_el = el.find('a', href=True)
                link = link_el['href'] if link_el else ''
                if link and not link.startswith('http'):
                    link = urljoin('https://www.gov.il', link)

                if not _is_moh_relevant(link):
                    continue

                seen_titles.add(title)
                desc_el = el.find('p')
                description = desc_el.get_text(strip=True)[:200] if desc_el else ''
                date_el = el.find('time')
                date_str = ''
                if date_el:
                    date_str = date_el.get('datetime', date_el.get_text(strip=True))[:10]

                items.append({'title': title, 'link': link, 'description': description, 'date': date_str})

        # Try to get real dates for news items (links with /he/pages/DDMMYYYY pattern)
        import re
        for item in items:
            if not item['date'] and item['link']:
                m = re.search(r'/(\d{2})(\d{2})(\d{4})', item['link'])
                if m:
                    d, mo, y = m.groups()
                    item['date'] = f"{y}-{mo}-{d}"

        items = _enrich_items(items[:15], use_playwright=True)
        return {
            'status': 'ok' if items else 'blocked',
            'url': url,
            'error': '' if items else 'לא נמצא תוכן',
            'items': items,
            'last_scraped': datetime.now().isoformat(),
        }

    except Exception as e:
        return {
            'status': 'error',
            'url': url,
            'error': str(e),
            'items': [],
            'last_scraped': datetime.now().isoformat(),
        }


def scrape_all():
    prev_data = _load_previous()

    # Back up current data
    if os.path.exists(DATA_FILE):
        import shutil
        shutil.copy2(DATA_FILE, PREV_FILE)

    data = {}
    scrapers = {
        'govil': scrape_govil,
        'me_health': scrape_me_health,
        'efsharibari': scrape_efsharibari,
    }

    for site_name, config in SITES.items():
        print(f"Scraping: {site_name} ...")
        scraper = scrapers.get(config['type'], scrape_me_health)
        result = scraper(config['url'], site_name)
        result['icon'] = config.get('icon', '🏥')
        result['color'] = config.get('color', '#005baa')

        # Mark new items
        result['items'] = _mark_new_items(site_name, result['items'], prev_data)

        data[site_name] = result
        new_count = sum(1 for i in result['items'] if i.get('is_new'))
        print(f"  -> {result['status']} ({len(result['items'])} items, {new_count} new)")

    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Auto-generate dashboard HTML
    try:
        from src.generate_dashboard import generate
    except ImportError:
        try:
            sys.path.insert(0, os.path.dirname(__file__))
            from generate_dashboard import generate
        except ImportError:
            generate = None

    if generate:
        generate(data)

    print("Done.")
    return data


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    scrape_all()
