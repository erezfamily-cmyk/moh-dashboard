"""
Generates dashboard.html from scraped_data.json.
Visual identity: modern news/data portal inspired by Israeli MOH datadashboard.health.gov.il
"""
import json
import os
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(__file__))
DATA_FILE = os.path.join(ROOT, 'scraped_data.json')
OUTPUT_FILE = os.path.join(ROOT, 'dashboard.html')

# Site-specific gradient fallbacks (when no og:image)
SITE_GRADIENTS = {
    'משרד הבריאות - פורטל ראשי': 'linear-gradient(135deg, #1b2030, #2d4a7a)',
    'פורטל הורים':                'linear-gradient(135deg, #017fa6, #00c2e0)',
    'בריאות הנפש':                'linear-gradient(135deg, #4a6fa5, #6b4fa5)',
    'הגיל השלישי':                'linear-gradient(135deg, #2e7d6e, #1a5c4a)',
    'אפשריבריא':                  'linear-gradient(135deg, #2a7d45, #1a5c2a)',
}

SITE_ACCENTS = {
    'משרד הבריאות - פורטל ראשי': '#2d4a7a',
    'פורטל הורים':                '#017FA6',
    'בריאות הנפש':                '#4a6fa5',
    'הגיל השלישי':                '#2e7d6e',
    'אפשריבריא':                  '#2a7d45',
}

# SVG icons per site (flat, single-color)
SITE_ICONS = {
    'משרד הבריאות - פורטל ראשי': '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
    'פורטל הורים':                '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
    'בריאות הנפש':                '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>',
    'הגיל השלישי':                '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4"/><path d="M6 20v-2a6 6 0 0 1 12 0v2"/><line x1="12" y1="2" x2="12" y2="4"/></svg>',
    'אפשריבריא':                  '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>',
}


def format_date(date_str):
    if not date_str:
        return ''
    try:
        dt = datetime.fromisoformat(date_str[:19])
        return dt.strftime('%d.%m.%Y')
    except Exception:
        if len(date_str) >= 10:
            parts = date_str[:10].split('-')
            if len(parts) == 3:
                return f"{parts[2]}.{parts[1]}.{parts[0]}"
    return date_str[:10]


def _escape(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def _hex_grid_svg():
    """Generate a hexagonal cell grid SVG for the hero background."""
    import math
    r = 26  # hex radius
    w = r * math.sqrt(3)
    h = r * 2
    rows, cols = 8, 22
    hexagons = []
    for row in range(rows):
        offset = w / 2 if row % 2 else 0
        cy = row * h * 0.75 - h
        for col in range(cols):
            cx = col * w + offset - w
            pts = ' '.join(
                f"{cx + r * math.cos(math.radians(60*i - 30)):.1f},{cy + r * math.sin(math.radians(60*i - 30)):.1f}"
                for i in range(6)
            )
            hexagons.append(f'<polygon points="{pts}" fill="none" stroke="white" stroke-width="1"/>')
    return '\n    '.join(hexagons)


def generate(data):
    now = datetime.now().strftime('%d.%m.%Y  %H:%M')
    hex_grid = _hex_grid_svg()

    # Flatten all items into a single list with site metadata attached
    all_items = []
    for site_name, info in data.items():
        accent = SITE_ACCENTS.get(site_name, '#017FA6')
        gradient = SITE_GRADIENTS.get(site_name, 'linear-gradient(135deg, #1b2030, #2d4a7a)')
        icon_svg = SITE_ICONS.get(site_name, '')
        for item in info.get('items', []):
            item = dict(item)  # copy
            item['site_name'] = site_name
            item['site_color'] = accent
            item['site_gradient'] = gradient
            item['site_icon'] = icon_svg
            item['site_url'] = info.get('url', '')
            all_items.append(item)

    # Sort: new items first, then by date descending
    def sort_key(item):
        is_new = 1 if item.get('is_new') else 0
        date_str = item.get('date', '') or ''
        return (is_new, date_str)

    all_items.sort(key=sort_key, reverse=True)

    total_new = sum(1 for i in all_items if i.get('is_new'))

    # Build flat data for JS (site-keyed for email function compatibility)
    data_json = json.dumps(data, ensure_ascii=False)

    # Build ticker content (duplicate for seamless loop)
    ticker_items_data = [(item.get('title',''), item.get('link','')) for item in all_items[:25] if item.get('title')]
    sep = '&nbsp;&nbsp;<span class="tick-sep">&#9670;</span>&nbsp;&nbsp;'
    def _tick_item(title, link):
        t = _escape(title)
        if link:
            return f'<a class="tick-item" href="{_escape(link)}" target="_blank">{t}</a>'
        return f'<span class="tick-item">{t}</span>'
    ticker_single = sep.join(_tick_item(t, l) for t, l in ticker_items_data)
    ticker_content = ticker_single + '&nbsp;&nbsp;&nbsp;' + sep + '&nbsp;&nbsp;&nbsp;' + ticker_single

    # Build news cards HTML
    cards_html = ''
    for card_idx, item in enumerate(all_items):
        title = _escape(item.get('title', ''))
        link = item.get('link', '')
        desc = _escape(item.get('description', ''))
        date_str = format_date(item.get('date', ''))
        is_new = item.get('is_new', False)
        image_url = item.get('image_url', '')
        site_name = item.get('site_name', '')
        site_color = item.get('site_color', '#017FA6')
        site_gradient = item.get('site_gradient', 'linear-gradient(135deg, #1b2030, #2d4a7a)')
        icon_svg = item.get('site_icon', '')

        # Tags for filtering
        tags = []
        kw_map = {
            'חיסון': 'חיסונים', 'חצבת': 'חיסונים', 'חיסוני': 'חיסונים',
            'נפש': 'בריאות נפש', 'אשפוז': 'בריאות נפש', 'התמכרות': 'בריאות נפש', 'פסיכ': 'בריאות נפש',
            'ילד': 'ילדים', 'תינוק': 'ילדים', 'הריון': 'ילדים', 'לידה': 'ילדים', 'הורה': 'ילדים',
            'חירום': 'חירום', 'מלחמה': 'חירום', 'מבצע': 'חירום', 'הרתחת': 'חירום',
            'תזונה': 'תזונה', 'קלורי': 'תזונה', 'תזונת': 'תזונה',
        }
        raw_title = item.get('title', '')
        raw_desc = item.get('description', '')
        for kw, tag in kw_map.items():
            if kw in raw_title or kw in raw_desc:
                if tag not in tags:
                    tags.append(tag)
        tags_attr = ' '.join(tags)

        # Thumbnail block
        if image_url:
            thumbnail_html = f'<div class="card-thumb"><img src="{_escape(image_url)}" alt="" loading="lazy" onerror="this.parentElement.style.background=\'{site_gradient}\';this.remove()"></div>'
        else:
            thumbnail_html = f'''<div class="card-thumb card-thumb-gradient" style="background:{site_gradient}">
              <span class="thumb-icon">{icon_svg}</span>
            </div>'''

        new_pill = '<span class="pill-new" data-i18n="new_badge">חדש</span>' if is_new else ''
        site_tag = f'<span class="site-tag" style="background:{site_color}15;color:{site_color};border-color:{site_color}30">{_escape(site_name)}</span>'
        date_el = f'<span class="card-date">{_escape(date_str)}</span>' if date_str else ''

        title_el = (f'<a href="{_escape(link)}" target="_blank" class="card-title-link">{title}</a>'
                    if link else f'<span class="card-title-link">{title}</span>')

        desc_block = f'<p class="card-desc">{desc}</p>' if desc else ''

        read_more = (f'<a href="{_escape(link)}" target="_blank" class="btn-read-more"><span data-i18n="read_more">קרא עוד</span> <span class="read-more-arrow" aria-hidden="true">←</span></a>'
                     if link else '')

        bookmark_btn = f'''<button class="bookmark-btn" onclick="toggleBookmark(this,event)" title="שמור לקריאה מאוחר יותר">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>
    </button>'''

        delay = min(card_idx * 0.04, 0.5)
        cards_html += f'''<article class="news-card" data-title="{title}" data-desc="{desc}" data-tags="{tags_attr}" data-site="{_escape(site_name)}" data-isnew="{"1" if is_new else "0"}" data-link="{_escape(link)}" style="animation-delay:{delay:.2f}s">
  {thumbnail_html}
  <div class="card-body">
    <div class="card-meta-row">
      {site_tag}
      {date_el}
      {bookmark_btn}
    </div>
    <h2 class="card-headline">{new_pill}{title_el}</h2>
    {desc_block}
    {read_more}
  </div>
</article>
'''

    # Build site filter pills
    site_filter_pills = ''
    for site_name in data.keys():
        site_filter_pills += f'<button class="filter-pill" onclick="setSiteFilter(\'{_escape(site_name)}\',this)">{_escape(site_name)}</button>\n    '

    html = f'''<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>עדכוני משרד הבריאות</title>
  <link rel="icon" type="image/svg+xml" href="https://me.health.gov.il/media/224edbtw/logo-desktop-header.svg">
  <link rel="shortcut icon" href="https://www.health.gov.il/favicon.ico">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Rubik:wght@400;500;600;700;800&family=Open+Sans:wght@400;600;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --navy:      #0d1b3e;
      --navy2:     #1a3a6b;
      --blue:      #0068f5;
      --teal:      #00a99d;
      --light-bg:  #b8d8e8;
      --white:     #ffffff;
      --border:    #93bdd4;
      --text:      #1b2030;
      --secondary: #5e6783;
      --radius:    12px;
      --shadow:    0 2px 16px rgba(13,27,62,.09);
      --shadow-hover: 0 8px 32px rgba(13,27,62,.18);
    }}

    /* ── DARK MODE ── */
    [data-theme="dark"] {{
      --light-bg:  #0e1219;
      --white:     #161c2d;
      --border:    #252e48;
      --text:      #e2e8f4;
      --secondary: #7a85a0;
      --shadow:    0 2px 16px rgba(0,0,0,.4);
      --shadow-hover: 0 8px 32px rgba(0,0,0,.6);
    }}
    [data-theme="dark"] .toolbar {{
      background: #111827;
      border-bottom-color: #252e48;
    }}
    [data-theme="dark"] #search {{
      background: #0e1219;
      color: var(--text);
      border-color: #252e48;
    }}
    [data-theme="dark"] #search:focus {{
      background: #161c2d;
    }}
    [data-theme="dark"] .filter-pill {{
      background: #161c2d;
      border-color: #252e48;
      color: var(--secondary);
    }}
    [data-theme="dark"] .filter-pill:hover {{
      background: #1e2840;
      color: #7ec8fa;
    }}
    [data-theme="dark"] .card-title-link {{ color: var(--text); }}
    [data-theme="dark"] .card-title-link:hover {{ color: #7ec8fa; }}
    [data-theme="dark"] .site-tag {{ opacity: 0.9; }}
    [data-theme="dark"] .btn-top {{
      border-color: rgba(255,255,255,.15);
    }}

    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      font-family: 'Rubik', 'Open Sans', 'Segoe UI', Arial, sans-serif;
      background: var(--light-bg);
      color: var(--text);
      direction: rtl;
      font-size: 17px;
      line-height: 1.5;
    }}

    /* ── SCROLL PROGRESS BAR ── */
    #progress-bar {{
      position: fixed;
      top: 0;
      right: 0;
      left: 0;
      height: 3px;
      width: 0%;
      background: linear-gradient(90deg, var(--blue), var(--teal));
      z-index: 9999;
      transition: width .08s linear;
      pointer-events: none;
    }}

    /* ── TOP HEADER BAR ── */
    .top-bar {{
      background: var(--navy);
      padding: 12px 32px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      position: sticky;
      top: 0;
      z-index: 200;
      box-shadow: 0 2px 12px rgba(0,0,0,.25);
    }}
    .moh-logo {{
      height: 40px;
      width: auto;
    }}
    .top-bar-actions {{
      display: flex;
      gap: 8px;
      align-items: center;
    }}
    .btn-top {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 7px 16px;
      border-radius: 8px;
      font-family: inherit;
      font-size: 0.82rem;
      font-weight: 500;
      cursor: pointer;
      border: 1px solid rgba(255,255,255,.2);
      background: rgba(255,255,255,.08);
      color: rgba(255,255,255,.85);
      text-decoration: none;
      transition: background .15s, border-color .15s;
    }}
    .btn-top:hover {{ background: rgba(255,255,255,.15); border-color: rgba(255,255,255,.4); color: white; }}
    .btn-top-primary {{
      background: var(--blue);
      border-color: var(--blue);
      color: white;
    }}
    .btn-top-primary:hover {{ background: #0055d4; border-color: #0055d4; }}

    /* ── SHARE DROPDOWN ── */
    .share-wrap {{
      position: relative;
    }}
    .share-dropdown {{
      display: none;
      position: absolute;
      top: calc(100% + 8px);
      left: 50%;
      transform: translateX(-50%);
      background: #fff;
      border-radius: 12px;
      box-shadow: 0 8px 32px rgba(0,0,0,.22);
      padding: 8px;
      min-width: 200px;
      z-index: 999;
      flex-direction: column;
      gap: 2px;
    }}
    [data-theme="dark"] .share-dropdown {{
      background: #1e2d4a;
      box-shadow: 0 8px 32px rgba(0,0,0,.45);
    }}
    .share-dropdown.open {{ display: flex; }}
    .share-dropdown::before {{
      content: '';
      position: absolute;
      top: -6px;
      left: 50%;
      transform: translateX(-50%);
      border: 6px solid transparent;
      border-top: 0;
      border-bottom-color: #fff;
    }}
    [data-theme="dark"] .share-dropdown::before {{ border-bottom-color: #1e2d4a; }}
    .share-opt {{
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 9px 14px;
      border-radius: 8px;
      cursor: pointer;
      font-size: 0.85rem;
      font-weight: 500;
      color: #1a2a4a;
      background: none;
      border: none;
      width: 100%;
      text-align: right;
      font-family: inherit;
      transition: background .12s;
    }}
    [data-theme="dark"] .share-opt {{ color: #d0dff5; }}
    .share-opt:hover {{ background: #f0f4ff; }}
    [data-theme="dark"] .share-opt:hover {{ background: rgba(255,255,255,.08); }}
    .share-opt .share-icon {{
      width: 28px;
      height: 28px;
      border-radius: 6px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }}
    .share-sep {{
      height: 1px;
      background: #e8edf5;
      margin: 4px 6px;
    }}
    [data-theme="dark"] .share-sep {{ background: rgba(255,255,255,.1); }}
    .copy-feedback {{
      font-size: 0.75rem;
      color: #22c55e;
      padding: 4px 14px 6px;
      display: none;
    }}
    .copy-feedback.show {{ display: block; }}

    /* ── LANGUAGE SWITCHER ── */
    .lang-switcher {{
      display: flex;
      gap: 4px;
      align-items: center;
      margin-left: auto;
      margin-right: 16px;
    }}
    .lang-btn {{
      padding: 4px 9px;
      border-radius: 6px;
      font-size: 0.75rem;
      font-weight: 600;
      cursor: pointer;
      border: 1px solid rgba(255,255,255,.2);
      background: rgba(255,255,255,.06);
      color: rgba(255,255,255,.65);
      font-family: inherit;
      transition: background .12s, color .12s, border-color .12s;
      letter-spacing: .02em;
    }}
    .lang-btn:hover {{ background: rgba(255,255,255,.15); color: white; border-color: rgba(255,255,255,.35); }}
    .lang-btn.active {{
      background: rgba(255,255,255,.22);
      color: white;
      border-color: rgba(255,255,255,.5);
    }}
    .lang-sep {{ width: 1px; height: 14px; background: rgba(255,255,255,.2); }}

    /* ── TRANSLATION PROGRESS ── */
    .trans-indicator {{
      display: none;
      align-items: center;
      gap: 6px;
      font-size: 0.72rem;
      color: rgba(255,255,255,.7);
      margin-right: 8px;
    }}
    .trans-indicator.visible {{ display: flex; }}
    .trans-spinner {{
      width: 12px; height: 12px;
      border: 2px solid rgba(255,255,255,.25);
      border-top-color: rgba(255,255,255,.85);
      border-radius: 50%;
      animation: spin .7s linear infinite;
    }}
    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
    .trans-progress-bar {{
      width: 60px; height: 3px;
      background: rgba(255,255,255,.2);
      border-radius: 2px;
      overflow: hidden;
    }}
    .trans-progress-fill {{
      height: 100%;
      background: #4ade80;
      border-radius: 2px;
      transition: width .2s;
      width: 0%;
    }}
    /* Skeleton shimmer while card content is loading */
    .card-translating .card-title-link,
    .card-translating .card-desc {{
      background: linear-gradient(90deg, rgba(0,0,0,.06) 25%, rgba(0,0,0,.12) 50%, rgba(0,0,0,.06) 75%);
      background-size: 200% 100%;
      animation: shimmer 1.2s infinite;
      color: transparent !important;
      border-radius: 4px;
      user-select: none;
    }}
    [data-theme="dark"] .card-translating .card-title-link,
    [data-theme="dark"] .card-translating .card-desc {{
      background: linear-gradient(90deg, rgba(255,255,255,.06) 25%, rgba(255,255,255,.12) 50%, rgba(255,255,255,.06) 75%);
      background-size: 200% 100%;
    }}
    @keyframes shimmer {{ to {{ background-position: -200% 0; }} }}

    .btn-darkmode {{
      background: rgba(255,255,255,.06);
      border-color: rgba(255,255,255,.15);
      padding: 7px 10px;
    }}

    /* ── NEWS TICKER ── */
    .ticker-wrap {{
      background: #00aec8;
      overflow: hidden;
      position: relative;
      height: 46px;
      display: flex;
      align-items: center;
      border-bottom: 1px solid rgba(255,255,255,.07);
    }}
    .ticker-badge {{
      background: #0082a0 !important;
      position: absolute;
      right: 0;
      top: 0;
      bottom: 0;
      background: var(--blue);
      display: flex;
      align-items: center;
      padding: 0 18px;
      font-size: 0.85rem;
      font-weight: 700;
      color: white;
      z-index: 2;
      white-space: nowrap;
      letter-spacing: 0.02em;
    }}
    .ticker-badge::after {{
      background: linear-gradient(to left, #0082a0, transparent) !important;
      content: '';
      position: absolute;
      left: -10px;
      top: 0;
      bottom: 0;
      width: 10px;
      background: linear-gradient(to left, var(--blue), transparent);
    }}
    .ticker-overflow {{
      overflow: hidden;
      width: 100%;
      padding-right: 110px;
    }}
    .ticker-track {{
      display: inline-block;
      white-space: nowrap;
      color: rgba(255,255,255,.9);
      font-size: 1.02rem;
      font-weight: 700;
      will-change: transform;
    }}
    .tick-item {{
      display: inline;
      color: white;
      text-decoration: none;
    }}
    a.tick-item:hover {{
      text-decoration: underline;
      color: #fef08a;
    }}
    .tick-sep {{ color: rgba(255,255,255,.5); margin: 0 4px; }}

    /* ── HERO BANNER ── */
    .hero {{
      background: linear-gradient(135deg, var(--navy) 0%, var(--navy2) 100%);
      padding: 52px 32px 48px;
      position: relative;
      overflow: hidden;
      text-align: right;
    }}
    /* CSS dot-grid background */
    .hero::before {{
      content: '';
      position: absolute;
      inset: 0;
      background-image:
        radial-gradient(circle, rgba(0,168,157,.18) 1px, transparent 1px),
        radial-gradient(circle, rgba(0,104,245,.12) 1px, transparent 1px);
      background-size: 40px 40px, 80px 80px;
      background-position: 0 0, 20px 20px;
      pointer-events: none;
    }}
    /* ECG wave SVG */
    .hero-ecg {{
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      width: 100%;
      height: 90px;
      opacity: 0.18;
      pointer-events: none;
    }}
    .hero-inner {{
      position: relative;
      max-width: 1280px;
      margin: 0 auto;
    }}
    .hero-logo {{
      display: block;
      height: 64px;
      width: auto;
      margin-bottom: 18px;
      filter: drop-shadow(0 2px 6px rgba(0,0,0,.25));
    }}
    .hero-title {{
      font-size: clamp(2rem, 5vw, 3rem);
      font-weight: 800;
      color: #ffffff;
      letter-spacing: -0.5px;
      line-height: 1.2;
      margin-bottom: 10px;
      text-shadow: 0 2px 8px rgba(0,0,0,.2);
    }}
    .hero-tagline {{
      font-size: 1.15rem;
      color: #00aec8;
      font-weight: 700;
      margin-bottom: 14px;
      letter-spacing: 0.01em;
    }}
    .hero-sub {{
      font-size: 1rem;
      color: rgba(255,255,255,.65);
      font-weight: 400;
      display: flex;
      align-items: center;
      gap: 16px;
      flex-wrap: wrap;
    }}
    .hero-sub strong {{
      color: rgba(255,255,255,.9);
      font-weight: 600;
    }}
    .refresh-countdown {{
      font-size: 0.78rem;
      color: rgba(255,255,255,.5);
      background: rgba(255,255,255,.07);
      border: 1px solid rgba(255,255,255,.12);
      border-radius: 20px;
      padding: 3px 12px;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }}
    .refresh-countdown .cd-val {{
      color: #7dd3fc;
      font-weight: 600;
    }}
    .hero-stats {{
      display: flex;
      gap: 20px;
      margin-top: 24px;
      flex-wrap: wrap;
    }}
    .hero-stat {{
      background: rgba(255,255,255,.09);
      border: 1px solid rgba(255,255,255,.14);
      border-radius: 10px;
      padding: 10px 18px;
      color: white;
      font-size: 0.85rem;
    }}
    .hero-stat strong {{
      display: block;
      font-size: 1.4rem;
      font-weight: 700;
      color: #7dd3fc;
      line-height: 1.1;
    }}

    /* ── TOOLBAR ── */
    .toolbar {{
      background: var(--white);
      border-bottom: 1px solid var(--border);
      padding: 14px 32px;
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
      box-shadow: 0 2px 8px rgba(0,0,0,.05);
    }}
    .search-wrap {{
      position: relative;
      flex-shrink: 0;
    }}
    .search-icon-inner {{
      position: absolute;
      right: 13px;
      top: 50%;
      transform: translateY(-50%);
      color: var(--secondary);
      pointer-events: none;
    }}
    #search {{
      padding: 9px 40px 9px 18px;
      border: 1.5px solid var(--border);
      border-radius: 50px;
      font-size: 0.88rem;
      font-family: inherit;
      direction: rtl;
      width: 260px;
      background: var(--light-bg);
      color: var(--text);
      outline: none;
      transition: border-color .15s, box-shadow .15s;
    }}
    #search:focus {{
      border-color: var(--blue);
      box-shadow: 0 0 0 3px rgba(0,104,245,.12);
      background: white;
    }}
    #search::placeholder {{ color: var(--secondary); }}

    .filter-group {{
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
      align-items: center;
    }}
    .filter-label {{
      font-size: 0.78rem;
      color: var(--secondary);
      font-weight: 500;
      white-space: nowrap;
    }}
    .filter-pill {{
      padding: 9px 20px;
      border-radius: 50px;
      border: 1.5px solid var(--border);
      background: var(--white);
      color: var(--secondary);
      font-family: inherit;
      font-size: 0.95rem;
      font-weight: 500;
      cursor: pointer;
      transition: all .15s;
      white-space: nowrap;
    }}
    .filter-pill:hover {{
      border-color: var(--blue);
      color: var(--blue);
      background: #eef4ff;
    }}
    .filter-pill.active {{
      background: var(--blue);
      border-color: var(--blue);
      color: white;
      font-weight: 600;
    }}
    .filter-pill.active-teal {{
      background: var(--teal);
      border-color: var(--teal);
      color: white;
      font-weight: 600;
    }}
    .filter-pill.active-gold {{
      background: #f59e0b;
      border-color: #f59e0b;
      color: white;
      font-weight: 600;
    }}
    .results-count {{
      font-size: 0.78rem;
      color: var(--secondary);
      white-space: nowrap;
      margin-right: auto;
    }}
    .results-count strong {{ color: var(--blue); font-weight: 700; }}
    .new-badge-total {{
      background: linear-gradient(135deg, var(--blue), var(--teal));
      color: white;
      padding: 5px 14px;
      border-radius: 50px;
      font-size: 0.78rem;
      font-weight: 700;
      white-space: nowrap;
    }}

    /* ── MAIN GRID ── */
    .container {{
      max-width: 1280px;
      margin: 32px auto;
      padding: 0 24px;
    }}
    .grid {{
      columns: 3;
      column-gap: 20px;
    }}
    @media (max-width: 1024px) {{ .grid {{ columns: 2; }} }}
    @media (max-width: 640px)  {{ .grid {{ columns: 1; }} }}

    /* ── NEWS CARD ── */
    @keyframes cardIn {{
      from {{ opacity: 0; transform: translateY(18px); }}
      to   {{ opacity: 1; transform: translateY(0); }}
    }}
    .news-card {{
      background: var(--white);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      border: 1px solid var(--border);
      overflow: hidden;
      break-inside: avoid;
      margin-bottom: 20px;
      display: inline-block;
      width: 100%;
      opacity: 0;
      animation: cardIn .45s ease forwards;
      transition: box-shadow .2s, border-color .2s, transform .2s;
    }}
    .news-card:hover {{
      box-shadow: var(--shadow-hover);
      transform: translateY(-3px);
    }}
    .news-card.hidden {{ display: none !important; }}
    .news-card.bookmarked-card {{ border-color: #f59e0b88; }}

    /* Thumbnail */
    .card-thumb {{
      width: 100%;
      height: 180px;
      overflow: hidden;
      position: relative;
      background: #e8edf3;
    }}
    .card-thumb img {{
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
      transition: transform .3s;
    }}
    .news-card.visible:hover .card-thumb img {{ transform: scale(1.04); }}
    .card-thumb-gradient {{
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    .thumb-icon {{
      opacity: .75;
    }}

    /* Card body */
    .card-body {{
      padding: 16px 18px 18px;
    }}
    .card-meta-row {{
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 8px;
    }}
    .site-tag {{
      display: inline-block;
      font-size: 0.7rem;
      font-weight: 600;
      padding: 3px 9px;
      border-radius: 50px;
      border: 1px solid transparent;
      white-space: nowrap;
      max-width: 140px;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .card-date {{
      font-size: 0.72rem;
      color: var(--secondary);
      white-space: nowrap;
      flex-shrink: 0;
      margin-right: auto;
    }}
    .card-headline {{
      font-size: 0.97rem;
      font-weight: 700;
      line-height: 1.45;
      color: var(--text);
      margin-bottom: 8px;
    }}
    .card-title-link {{
      color: var(--text);
      text-decoration: none;
    }}
    .card-title-link:hover {{ color: var(--blue); text-decoration: underline; }}
    .pill-new {{
      display: inline-block;
      background: var(--blue);
      color: white;
      font-size: 0.62rem;
      font-weight: 700;
      padding: 2px 7px;
      border-radius: 10px;
      margin-left: 6px;
      vertical-align: middle;
    }}
    .card-desc {{
      font-size: 0.83rem;
      color: var(--secondary);
      line-height: 1.6;
      margin-bottom: 12px;
      display: -webkit-box;
      -webkit-line-clamp: 3;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }}
    .btn-read-more {{
      display: inline-flex;
      align-items: center;
      gap: 4px;
      font-size: 0.8rem;
      font-weight: 600;
      color: var(--blue);
      text-decoration: none;
      transition: color .15s;
    }}
    .btn-read-more:hover {{ color: var(--teal); text-decoration: underline; }}

    /* ── BOOKMARK BUTTON ── */
    .bookmark-btn {{
      background: none;
      border: none;
      cursor: pointer;
      padding: 3px 4px;
      color: var(--secondary);
      transition: color .15s, transform .2s;
      flex-shrink: 0;
      line-height: 0;
      border-radius: 4px;
    }}
    .bookmark-btn:hover {{ color: var(--blue); transform: scale(1.15); }}
    .bookmark-btn.bookmarked {{ color: #f59e0b; }}
    .bookmark-btn.bookmarked svg {{ fill: #f59e0b; stroke: #f59e0b; }}

    /* ── SEARCH HIGHLIGHT ── */
    mark.hl {{
      background: #fef08a;
      color: #1b2030;
      border-radius: 2px;
      padding: 0 1px;
    }}
    [data-theme="dark"] mark.hl {{
      background: #854d0e;
      color: #fef9c3;
    }}

    /* ── FOOTER META ── */
    .page-footer {{
      text-align: center;
      color: var(--secondary);
      font-size: 0.75rem;
      margin: 8px 0 48px;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
    }}
    .page-footer::before, .page-footer::after {{
      content: '';
      flex: 1;
      max-width: 140px;
      height: 1px;
      background: var(--border);
    }}

    /* ── NO RESULTS ── */
    .no-results {{
      text-align: center;
      padding: 60px 20px;
      color: var(--secondary);
      font-size: 1rem;
      display: none;
    }}
    .no-results.visible {{ display: block; }}

    /* ── HAMBURGER ── */
    .toolbar-top-row {{
      display: flex;
      align-items: center;
      gap: 10px;
      width: 100%;
    }}
    .hamburger-btn {{
      display: none;
      align-items: center;
      justify-content: center;
      gap: 6px;
      background: var(--light-bg);
      border: 1.5px solid var(--border);
      border-radius: 50px;
      padding: 9px 16px;
      font-size: 0.88rem;
      font-family: inherit;
      color: var(--secondary);
      cursor: pointer;
      white-space: nowrap;
      flex-shrink: 0;
      transition: background .15s, border-color .15s;
    }}
    .hamburger-btn.open {{ border-color: var(--blue); color: var(--blue); }}
    .toolbar-filters {{
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
      flex: 1;
    }}
    [data-theme="dark"] .hamburger-btn {{
      background: #161c2d;
      border-color: #252e48;
      color: var(--secondary);
    }}

    /* ── MOBILE MENU BUTTON ── */
    .mobile-menu-btn {{
      display: none;
      align-items: center;
      justify-content: center;
      background: rgba(255,255,255,.08);
      border: 1px solid rgba(255,255,255,.2);
      border-radius: 8px;
      padding: 8px 10px;
      cursor: pointer;
      color: rgba(255,255,255,.85);
      transition: background .15s, border-color .15s;
      flex-shrink: 0;
    }}
    .mobile-menu-btn:hover {{ background: rgba(255,255,255,.15); border-color: rgba(255,255,255,.4); color: white; }}
    .mobile-menu-btn.open {{ background: rgba(255,255,255,.18); border-color: rgba(255,255,255,.5); color: white; }}

    /* ── MOBILE MENU PANEL ── */
    .mobile-menu {{
      display: none;
      flex-direction: column;
      gap: 16px;
      padding: 16px;
      background: var(--white);
      border-bottom: 1px solid var(--border);
      position: relative;
      z-index: 99;
    }}
    .mobile-menu.open {{ display: flex; }}
    [data-theme="dark"] .mobile-menu {{
      background: #111827;
      border-bottom-color: #252e48;
    }}
    .mobile-menu #search-mobile {{
      width: 100%;
      box-sizing: border-box;
    }}
    .mobile-menu-search {{
      position: relative;
    }}
    .mobile-menu-search .search-icon-inner {{
      position: absolute;
      right: 13px;
      top: 50%;
      transform: translateY(-50%);
      color: var(--secondary);
      pointer-events: none;
    }}
    .mobile-menu-divider {{
      height: 1px;
      background: var(--border);
      margin: 0;
      border: none;
    }}
    .mobile-menu-lang {{
      display: flex;
      gap: 6px;
      align-items: center;
      flex-wrap: wrap;
    }}
    .mobile-menu-actions {{
      display: flex;
      gap: 8px;
      align-items: center;
      flex-wrap: wrap;
    }}
    .mobile-menu-actions .btn-top {{
      background: rgba(13,27,62,.08);
      border-color: var(--border);
      color: var(--text);
    }}
    .mobile-menu-actions .btn-top:hover {{
      background: rgba(13,27,62,.15);
      border-color: var(--blue);
      color: var(--blue);
    }}
    .mobile-menu-actions .btn-top-primary {{
      background: var(--blue);
      border-color: var(--blue);
      color: white;
    }}
    .mobile-menu-actions .btn-top-primary:hover {{
      background: #0055d4;
      border-color: #0055d4;
    }}
    [data-theme="dark"] .mobile-menu-actions .btn-top {{
      background: rgba(255,255,255,.06);
      border-color: rgba(255,255,255,.15);
      color: rgba(255,255,255,.85);
    }}
    .mobile-menu-results {{
      font-size: 0.78rem;
      color: var(--secondary);
    }}
    .mobile-menu-results strong {{ color: var(--blue); font-weight: 700; }}
    .mobile-menu .lang-btn {{
      background: rgba(13,27,62,.07);
      border-color: var(--border);
      color: var(--secondary);
    }}
    .mobile-menu .lang-btn:hover {{ background: rgba(13,27,62,.14); color: var(--text); border-color: var(--blue); }}
    .mobile-menu .lang-btn.active {{
      background: var(--blue);
      color: white;
      border-color: var(--blue);
    }}
    [data-theme="dark"] .mobile-menu .lang-btn {{
      background: rgba(255,255,255,.06);
      border-color: #252e48;
      color: var(--secondary);
    }}
    [data-theme="dark"] .mobile-menu .lang-btn.active {{
      background: var(--blue);
      color: white;
      border-color: var(--blue);
    }}

    @media (max-width: 768px) {{
      .toolbar {{
        flex-direction: column;
        align-items: stretch;
        gap: 0;
        padding: 12px 16px;
      }}
      .toolbar-top-row {{ gap: 8px; }}
      .search-wrap {{ flex: 1; }}
      #search {{ width: 100%; box-sizing: border-box; }}
      .toolbar-filters {{ display: none !important; }}
      .hamburger-btn {{ display: none !important; }}
      .results-count {{ display: none; }}
      .lang-switcher {{ display: none; }}
      .top-bar-actions {{ display: none; }}
      .mobile-menu-btn {{ display: flex; }}
    }}
    @media (max-width: 640px) {{
      .top-bar {{ padding: 10px 16px; }}
      .hero {{ padding: 32px 16px 28px; }}
      .container {{ padding: 0 12px; margin-top: 20px; }}
      .hero-stats {{ gap: 10px; }}
    }}

    @media print {{
      .top-bar, .toolbar, .ticker-wrap, #progress-bar, #a11y-panel {{ display: none; }}
      .news-card {{ box-shadow: none; border: 1px solid #ccc; break-inside: avoid; opacity: 1; transform: none; }}
      body {{ background: white; }}
      .hero {{ background: #1b2030; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
    }}

    /* ── ACCESSIBILITY PANEL ── */
    #a11y-toggle {{
      position: fixed;
      left: 0;
      top: 50%;
      transform: translateY(-50%);
      z-index: 1000;
      background: var(--blue);
      color: white;
      border: none;
      border-radius: 0 8px 8px 0;
      padding: 12px 10px;
      cursor: pointer;
      font-size: 1.3rem;
      line-height: 1;
      box-shadow: 2px 0 12px rgba(0,0,0,.2);
      transition: background .15s, transform .2s;
      writing-mode: vertical-rl;
      letter-spacing: 2px;
    }}
    #a11y-toggle:hover {{ background: #0055d4; }}
    #a11y-toggle:focus-visible {{ outline: 3px solid #fef08a; outline-offset: 2px; }}

    #a11y-panel {{
      position: fixed;
      left: -280px;
      top: 0;
      bottom: 0;
      width: 270px;
      background: var(--white);
      border-right: none;
      border-left: 2px solid var(--blue);
      box-shadow: 4px 0 24px rgba(0,0,0,.18);
      z-index: 999;
      transition: left .28s cubic-bezier(.4,0,.2,1);
      overflow-y: auto;
      display: flex;
      flex-direction: column;
    }}
    #a11y-panel.open {{ left: 0; }}

    .a11y-header {{
      background: var(--blue);
      color: white;
      padding: 16px 18px;
      font-weight: 700;
      font-size: 0.95rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-shrink: 0;
    }}
    .a11y-close {{
      background: none;
      border: none;
      color: white;
      cursor: pointer;
      font-size: 1.3rem;
      line-height: 1;
      padding: 2px 6px;
      border-radius: 4px;
    }}
    .a11y-close:hover {{ background: rgba(255,255,255,.2); }}

    .a11y-section {{
      padding: 14px 18px 6px;
      border-bottom: 1px solid var(--border);
    }}
    .a11y-section:last-child {{ border-bottom: none; }}
    .a11y-section-title {{
      font-size: 0.72rem;
      font-weight: 700;
      color: var(--secondary);
      text-transform: uppercase;
      letter-spacing: .06em;
      margin-bottom: 10px;
    }}

    .a11y-btn {{
      display: flex;
      align-items: center;
      gap: 10px;
      width: 100%;
      padding: 9px 12px;
      margin-bottom: 6px;
      background: var(--light-bg);
      border: 1.5px solid var(--border);
      border-radius: 8px;
      font-family: inherit;
      font-size: 0.83rem;
      font-weight: 500;
      color: var(--text);
      cursor: pointer;
      text-align: right;
      direction: rtl;
      transition: background .12s, border-color .12s;
    }}
    .a11y-btn:hover {{ background: #e8f0fe; border-color: var(--blue); color: var(--blue); }}
    .a11y-btn.on {{ background: var(--blue); border-color: var(--blue); color: white; }}
    .a11y-btn .a11y-icon {{ font-size: 1.1rem; flex-shrink: 0; }}

    .font-size-row {{
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 10px;
    }}
    .font-size-row span {{
      flex: 1;
      text-align: center;
      font-size: 0.83rem;
      color: var(--secondary);
    }}
    .fs-btn {{
      width: 36px;
      height: 36px;
      border-radius: 8px;
      border: 1.5px solid var(--border);
      background: var(--light-bg);
      font-family: inherit;
      font-size: 1rem;
      font-weight: 700;
      cursor: pointer;
      color: var(--text);
      transition: background .12s;
      flex-shrink: 0;
    }}
    .fs-btn:hover {{ background: #e8f0fe; border-color: var(--blue); color: var(--blue); }}

    .a11y-reset {{
      margin: 10px 18px 18px;
      width: calc(100% - 36px);
      padding: 9px;
      background: #fee2e2;
      border: 1.5px solid #fca5a5;
      border-radius: 8px;
      font-family: inherit;
      font-size: 0.83rem;
      font-weight: 600;
      color: #b91c1c;
      cursor: pointer;
      direction: rtl;
      transition: background .12s;
    }}
    .a11y-reset:hover {{ background: #fecaca; }}

    /* Accessibility modes applied to <html> */
    html.a11y-contrast {{ filter: contrast(1.6); }}
    html.a11y-grayscale {{ filter: grayscale(1); }}
    html.a11y-contrast.a11y-grayscale {{ filter: contrast(1.6) grayscale(1); }}
    html.a11y-big-cursor, html.a11y-big-cursor * {{ cursor: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32"><circle cx="8" cy="8" r="6" fill="%23000"/></svg>') 8 8, auto !important; }}
    html.a11y-underline-links a {{ text-decoration: underline !important; }}
    html.a11y-readable * {{ font-family: Arial, sans-serif !important; letter-spacing: .02em !important; }}
    html.a11y-no-anim *, html.a11y-no-anim *::before, html.a11y-no-anim *::after {{
      animation: none !important;
      transition: none !important;
    }}
    html.a11y-highlight-focus *:focus {{
      outline: 3px solid #f59e0b !important;
      outline-offset: 3px !important;
    }}
    html.a11y-text-spacing {{
      --line-height-boost: 1;
    }}
    html.a11y-text-spacing p, html.a11y-text-spacing li, html.a11y-text-spacing span {{
      line-height: 2 !important;
      letter-spacing: .06em !important;
      word-spacing: .2em !important;
    }}
  </style>
</head>
<body>

<!-- SCROLL PROGRESS BAR -->
<div id="progress-bar"></div>

<!-- ACCESSIBILITY TOGGLE -->
<button id="a11y-toggle" onclick="toggleA11yPanel()" data-i18n-aria="a11y_open" aria-label="פתח תפריט הנגשה" data-i18n-title="a11y" title="הנגשה">
  &#x267F;
</button>

<!-- ACCESSIBILITY PANEL -->
<aside id="a11y-panel" role="dialog" data-i18n-aria="a11y_panel_label" aria-label="תפריט הנגשה" aria-modal="true">
  <div class="a11y-header">
    <span>&#x267F; <span data-i18n="a11y">הנגשה</span></span>
    <button class="a11y-close" onclick="toggleA11yPanel()" data-i18n-aria="close" aria-label="סגור">&#x2715;</button>
  </div>

  <div class="a11y-section">
    <div class="a11y-section-title" data-i18n="text_size">גודל טקסט</div>
    <div class="font-size-row">
      <button class="fs-btn" onclick="changeFontSize(-1)" data-i18n-aria="decrease_font" aria-label="הקטן גופן">A-</button>
      <span id="fs-label">רגיל</span>
      <button class="fs-btn" onclick="changeFontSize(1)" data-i18n-aria="increase_font" aria-label="הגדל גופן">A+</button>
    </div>
  </div>

  <div class="a11y-section">
    <div class="a11y-section-title" data-i18n="color_display">צבע ותצוגה</div>
    <button class="a11y-btn" id="btn-contrast" onclick="toggleA11y('a11y-contrast', this)">
      <span class="a11y-icon">&#x25D1;</span> <span data-i18n="high_contrast">ניגודיות גבוהה</span>
    </button>
    <button class="a11y-btn" id="btn-grayscale" onclick="toggleA11y('a11y-grayscale', this)">
      <span class="a11y-icon">&#x25A1;</span> <span data-i18n="grayscale">גווני אפור</span>
    </button>
  </div>

  <div class="a11y-section">
    <div class="a11y-section-title" data-i18n="readability">קריאות</div>
    <button class="a11y-btn" id="btn-readable" onclick="toggleA11y('a11y-readable', this)">
      <span class="a11y-icon">&#x1F4C4;</span> <span data-i18n="readable_font">גופן קריא (Arial)</span>
    </button>
    <button class="a11y-btn" id="btn-spacing" onclick="toggleA11y('a11y-text-spacing', this)">
      <span class="a11y-icon">&#x21C4;</span> <span data-i18n="more_spacing">ריווח מוגבר</span>
    </button>
    <button class="a11y-btn" id="btn-underline" onclick="toggleA11y('a11y-underline-links', this)">
      <span class="a11y-icon">&#x1F517;</span> <span data-i18n="underline_links">הדגש קישורים</span>
    </button>
  </div>

  <div class="a11y-section">
    <div class="a11y-section-title" data-i18n="nav_motion">ניווט ותנועה</div>
    <button class="a11y-btn" id="btn-focus" onclick="toggleA11y('a11y-highlight-focus', this)">
      <span class="a11y-icon">&#x25A3;</span> <span data-i18n="highlight_focus">הדגש פוקוס</span>
    </button>
    <button class="a11y-btn" id="btn-no-anim" onclick="toggleA11y('a11y-no-anim', this)">
      <span class="a11y-icon">&#x23F8;</span> <span data-i18n="stop_anim">עצור אנימציות</span>
    </button>
    <button class="a11y-btn" id="btn-cursor" onclick="toggleA11y('a11y-big-cursor', this)">
      <span class="a11y-icon">&#x1F5B1;</span> <span data-i18n="big_cursor">סמן גדול</span>
    </button>
  </div>

  <button class="a11y-reset" onclick="resetA11y()">&#x21BA; <span data-i18n="reset_a11y">איפוס הגדרות הנגשה</span></button>
</aside>

<!-- TOP HEADER BAR -->
<header class="top-bar">
  <img src="https://efsharibari.health.gov.il/media/1070/footer-health_logo.png?width=500" class="moh-logo" alt="משרד הבריאות" onerror="this.style.display='none'">
  <div class="lang-switcher">
    <div class="trans-indicator" id="trans-indicator">
      <div class="trans-spinner"></div>
      <div class="trans-progress-bar"><div class="trans-progress-fill" id="trans-fill"></div></div>
    </div>
    <button class="lang-btn active" onclick="setLang('he')" id="lang-he">עב</button>
    <div class="lang-sep"></div>
    <button class="lang-btn" onclick="setLang('ar')" id="lang-ar">عر</button>
    <div class="lang-sep"></div>
    <button class="lang-btn" onclick="setLang('en')" id="lang-en">EN</button>
    <div class="lang-sep"></div>
    <button class="lang-btn" onclick="setLang('ru')" id="lang-ru">РУ</button>
  </div>
  <div class="top-bar-actions">
    <button class="btn-top btn-darkmode" onclick="toggleDarkMode()" id="dark-btn" data-i18n-title="dark_mode" title="מצב לילה">
      <svg id="dark-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
    </button>
    <button class="btn-top" onclick="window.print()">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>
      <span data-i18n="print">הדפסה</span>
    </button>
    <button class="btn-top btn-top-primary" onclick="sendEmail()">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
      <span data-i18n="email">מייל</span>
    </button>

    <div class="share-wrap" id="share-wrap">
      <button class="btn-top" onclick="toggleShareMenu(event)" data-i18n-title="share" title="שיתוף">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>
        <span data-i18n="share">שיתוף</span>
      </button>
      <div class="share-dropdown" id="share-dropdown">
        <button class="share-opt" onclick="shareWhatsApp()">
          <span class="share-icon" style="background:#25d366">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="white"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/><path d="M12 0C5.373 0 0 5.373 0 12c0 2.124.554 4.118 1.526 5.845L.057 23.716a.5.5 0 0 0 .61.637l5.943-1.55A11.945 11.945 0 0 0 12 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 22c-1.9 0-3.68-.524-5.198-1.437l-.372-.22-3.853 1.005 1.03-3.742-.242-.386A9.956 9.956 0 0 1 2 12C2 6.477 6.477 2 12 2s10 4.477 10 10-4.477 10-10 10z"/></svg>
          </span>
          WhatsApp
        </button>
        <button class="share-opt" onclick="shareTelegram()">
          <span class="share-icon" style="background:#229ed9">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="white"><path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/></svg>
          </span>
          Telegram
        </button>
        <button class="share-opt" onclick="shareTwitter()">
          <span class="share-icon" style="background:#000">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="white"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.744l7.73-8.835L1.254 2.25H8.08l4.261 5.636 5.903-5.636Zm-1.161 17.52h1.833L7.084 4.126H5.117Z"/></svg>
          </span>
          X / Twitter
        </button>
        <button class="share-opt" onclick="shareLinkedIn()">
          <span class="share-icon" style="background:#0a66c2">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="white"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 0 1-2.063-2.065 2.064 2.064 0 1 1 2.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
          </span>
          LinkedIn
        </button>
        <div class="share-sep"></div>
        <button class="share-opt" onclick="copyShareLink()">
          <span class="share-icon" style="background:#64748b">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
          </span>
          <span data-i18n="copy_link">העתקת קישור</span>
        </button>
        <div class="copy-feedback" id="copy-feedback" data-i18n="copied">הועתק!</div>
        <button class="share-opt" id="native-share-btn" onclick="nativeShare()" style="display:none">
          <span class="share-icon" style="background:#6366f1">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/><polyline points="16 6 12 2 8 6"/><line x1="12" y1="2" x2="12" y2="15"/></svg>
          </span>
          <span data-i18n="more_share">שיתוף נוסף...</span>
        </button>
      </div>
    </div>
  </div>
  <button class="mobile-menu-btn" id="mobile-menu-btn" onclick="toggleMobileMenu()" aria-label="תפריט">
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
  </button>
</header>

<!-- MOBILE MENU -->
<div class="mobile-menu" id="mobile-menu">
  <div class="mobile-menu-search">
    <span class="search-icon-inner">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
    </span>
    <input type="text" id="search-mobile" data-i18n-placeholder="search_placeholder" placeholder="חיפוש בכל הכתבות..." oninput="document.getElementById('search').value=this.value; filterCards()" autocomplete="off" style="padding:9px 40px 9px 18px;border:1.5px solid var(--border);border-radius:50px;font-size:0.88rem;font-family:inherit;direction:rtl;width:100%;box-sizing:border-box;background:var(--light-bg);color:var(--text);outline:none;">
  </div>
  <div class="toolbar-filters" id="toolbar-filters-mobile" style="display:flex;flex-direction:column;gap:10px;align-items:stretch;">
    <div class="filter-group">
      <span class="filter-label" data-i18n="topic_label">נושא:</span>
      <button class="filter-pill active" onclick="setTagFilter('', this)" data-i18n="all">הכל</button>
      <button class="filter-pill" onclick="setTagFilter('חיסונים', this)" data-i18n="f_vaccines">חיסונים</button>
      <button class="filter-pill" onclick="setTagFilter('בריאות נפש', this)" data-i18n="f_mental">בריאות נפש</button>
      <button class="filter-pill" onclick="setTagFilter('ילדים', this)" data-i18n="f_children">ילדים</button>
      <button class="filter-pill" onclick="setTagFilter('חירום', this)" data-i18n="f_emergency">חירום</button>
      <button class="filter-pill" onclick="setTagFilter('תזונה', this)" data-i18n="f_nutrition">תזונה</button>
    </div>
    <div class="filter-group">
      <span class="filter-label" data-i18n="source_label">מקור:</span>
      <button class="filter-pill active-teal" id="site-all-btn-mobile" onclick="setSiteFilter('', this)" data-i18n="all_sources">כל המקורות</button>
      {site_filter_pills}
    </div>
    <div class="filter-group">
      <button class="filter-pill" id="bookmarks-btn-mobile" onclick="toggleBookmarksFilter(this)">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-1px;margin-left:4px"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>
        <span data-i18n="saved">שמורים</span>
      </button>
    </div>
  </div>
  <hr class="mobile-menu-divider">
  <div class="mobile-menu-lang">
    <button class="lang-btn active" onclick="setLang('he')" id="lang-he-mobile">עב</button>
    <div class="lang-sep"></div>
    <button class="lang-btn" onclick="setLang('ar')" id="lang-ar-mobile">عر</button>
    <div class="lang-sep"></div>
    <button class="lang-btn" onclick="setLang('en')" id="lang-en-mobile">EN</button>
    <div class="lang-sep"></div>
    <button class="lang-btn" onclick="setLang('ru')" id="lang-ru-mobile">РУ</button>
  </div>
  <div class="mobile-menu-actions">
    <button class="btn-top btn-darkmode" onclick="toggleDarkMode()" data-i18n-title="dark_mode" title="מצב לילה">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
      <span data-i18n="dark_mode">מצב לילה</span>
    </button>
    <button class="btn-top" onclick="window.print()">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>
      <span data-i18n="print">הדפסה</span>
    </button>
    <button class="btn-top btn-top-primary" onclick="sendEmail()">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
      <span data-i18n="email">מייל</span>
    </button>
    <button class="btn-top" onclick="toggleShareMenu(event)" data-i18n-title="share" title="שיתוף">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>
      <span data-i18n="share">שיתוף</span>
    </button>
  </div>
  <span class="mobile-menu-results" id="results-count-mobile"><span data-i18n="showing">מוצגות</span> <strong>{len(all_items)}</strong> <span data-i18n="articles_short">כתבות</span></span>
</div>

<!-- NEWS TICKER -->
<div class="ticker-wrap">
  <div class="ticker-badge">&#128240; חדשות</div>
  <div class="ticker-overflow">
    <div class="ticker-track" id="ticker-track">{ticker_content}</div>
  </div>
</div>

<!-- HERO BANNER -->
<section class="hero">

  <!-- ECG heartbeat wave -->
  <svg class="hero-ecg" viewBox="0 0 1440 90" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <linearGradient id="ecg-fade" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0%" stop-color="white" stop-opacity="0"/>
        <stop offset="8%" stop-color="white" stop-opacity="1"/>
        <stop offset="92%" stop-color="white" stop-opacity="1"/>
        <stop offset="100%" stop-color="white" stop-opacity="0"/>
      </linearGradient>
    </defs>
    <path d="M0,45 L80,45 L95,45 L105,38 L112,52 L118,45 L130,45
             L142,45 L148,10 L155,80 L162,20 L168,50 L175,45
             L195,45 L210,38 L217,52 L223,45 L235,45
             L360,45 L375,45 L385,38 L392,52 L398,45 L410,45
             L422,45 L428,10 L435,80 L442,20 L448,50 L455,45
             L475,45 L490,38 L497,52 L503,45 L515,45
             L640,45 L655,45 L665,38 L672,52 L678,45 L690,45
             L702,45 L708,10 L715,80 L722,20 L728,50 L735,45
             L755,45 L770,38 L777,52 L783,45 L795,45
             L920,45 L935,45 L945,38 L952,52 L958,45 L970,45
             L982,45 L988,10 L995,80 L1002,20 L1008,50 L1015,45
             L1035,45 L1050,38 L1057,52 L1063,45 L1075,45
             L1200,45 L1215,45 L1225,38 L1232,52 L1238,45 L1250,45
             L1262,45 L1268,10 L1275,80 L1282,20 L1288,50 L1295,45
             L1315,45 L1330,38 L1337,52 L1343,45 L1355,45 L1440,45"
      fill="none" stroke="url(#ecg-fade)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
  </svg>

  <div class="hero-inner">
    <h1 class="hero-title" data-i18n="title">עדכוני משרד הבריאות</h1>
    <p class="hero-tagline" data-i18n="tagline">מה התחדש באתרי משרד הבריאות השונים בימים האחרונים?</p>
    <p class="hero-sub">
      <span data-i18n="last_updated">עודכן לאחרונה</span>: <strong>{now}</strong>
      <span class="refresh-countdown">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
        <span data-i18n="next_update">עדכון בעוד</span> <span class="cd-val" id="cd-val">...</span> <span data-i18n="minutes">דקות</span>
      </span>
    </p>
    <div class="hero-stats">
      <div class="hero-stat">
        <strong id="stat-total" data-target="{len(all_items)}">0</strong>
        <span data-i18n="articles">כתבות וידיעות</span>
      </div>
      <div class="hero-stat">
        <strong id="stat-new" data-target="{total_new}">0</strong>
        <span data-i18n="new_items">פריטים חדשים</span>
      </div>
      <div class="hero-stat">
        <strong id="stat-src" data-target="{len(data)}">0</strong>
        <span data-i18n="sources">מקורות מידע</span>
      </div>
    </div>
  </div>
</section>

<!-- TOOLBAR -->
<div class="toolbar">
  <div class="toolbar-top-row">
    <div class="search-wrap">
      <span class="search-icon-inner">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
      </span>
      <input type="text" id="search" data-i18n-placeholder="search_placeholder" placeholder="חיפוש בכל הכתבות..." oninput="filterCards()" autocomplete="off">
    </div>
    <button class="hamburger-btn" id="hamburger-btn" onclick="toggleFilters(this)" aria-label="פתח פילטרים">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
      סינון
    </button>
    <span class="results-count" id="results-count"><span data-i18n="showing">מוצגות</span> <strong>{len(all_items)}</strong> <span data-i18n="articles_short">כתבות</span></span>
  </div>
  <div class="toolbar-filters" id="toolbar-filters">
    <div class="filter-group">
      <span class="filter-label" data-i18n="topic_label">נושא:</span>
      <button class="filter-pill active" onclick="setTagFilter('', this)" data-i18n="all">הכל</button>
      <button class="filter-pill" onclick="setTagFilter('חיסונים', this)" data-i18n="f_vaccines">חיסונים</button>
      <button class="filter-pill" onclick="setTagFilter('בריאות נפש', this)" data-i18n="f_mental">בריאות נפש</button>
      <button class="filter-pill" onclick="setTagFilter('ילדים', this)" data-i18n="f_children">ילדים</button>
      <button class="filter-pill" onclick="setTagFilter('חירום', this)" data-i18n="f_emergency">חירום</button>
      <button class="filter-pill" onclick="setTagFilter('תזונה', this)" data-i18n="f_nutrition">תזונה</button>
    </div>
    <div class="filter-group">
      <span class="filter-label" data-i18n="source_label">מקור:</span>
      <button class="filter-pill active-teal" id="site-all-btn" onclick="setSiteFilter('', this)" data-i18n="all_sources">כל המקורות</button>
      {site_filter_pills}
    </div>
    <div class="filter-group">
      <button class="filter-pill" id="bookmarks-btn" onclick="toggleBookmarksFilter(this)">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-1px;margin-left:4px"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>
        <span data-i18n="saved">שמורים</span>
      </button>
    </div>
    {"<span class='new-badge-total' data-i18n-new-total='1'>&#10022; " + str(total_new) + " <span data-i18n=\"new_items\">פריטים חדשים</span></span>" if total_new > 0 else ""}
  </div>
</div>

<!-- MAIN GRID -->
<main class="container">
  <div class="grid" id="grid">
    {cards_html}
  </div>
  <div class="no-results" id="no-results" data-i18n="no_results">לא נמצאו תוצאות לחיפוש זה</div>
  <p class="page-footer"><span data-i18n="footer">נגרד אוטומטית מאתרי משרד הבריאות</span> &middot; {now}</p>
</main>

<script>
  const DATA = {data_json};
  let activeTag = '';
  let activeSite = '';
  let showBookmarksOnly = false;
  let bookmarks = JSON.parse(localStorage.getItem('moh_bookmarks') || '[]');

  // ── TRANSLATIONS ──
  const TRANSLATIONS = {{
    he: {{
      title: 'עדכוני משרד הבריאות',
      tagline: 'מה התחדש באתרי משרד הבריאות השונים בימים האחרונים?',
      last_updated: 'עודכן לאחרונה', next_update: 'עדכון בעוד', minutes: 'דקות',
      articles: 'כתבות וידיעות', new_items: 'פריטים חדשים', sources: 'מקורות מידע',
      print: 'הדפסה', email: 'מייל', share: 'שיתוף', dark_mode: 'מצב לילה',
      copy_link: 'העתקת קישור', copied: 'הועתק!', more_share: 'שיתוף נוסף...',
      search_placeholder: 'חיפוש בכל הכתבות...',
      topic_label: 'נושא:', source_label: 'מקור:',
      all: 'הכל', all_sources: 'כל המקורות', saved: 'שמורים',
      f_vaccines: 'חיסונים', f_mental: 'בריאות נפש', f_children: 'ילדים',
      f_emergency: 'חירום', f_nutrition: 'תזונה',
      showing: 'מוצגות', articles_short: 'כתבות',
      no_results: 'לא נמצאו תוצאות לחיפוש זה',
      footer: 'נגרד אוטומטית מאתרי משרד הבריאות',
      new_badge: 'חדש', read_more: 'קרא עוד', read_more_arrow: '←',
      a11y: 'הנגשה', a11y_open: 'פתח תפריט הנגשה', a11y_panel_label: 'תפריט הנגשה',
      close: 'סגור', text_size: 'גודל טקסט', color_display: 'צבע ותצוגה',
      readability: 'קריאות', nav_motion: 'ניווט ותנועה',
      high_contrast: 'ניגודיות גבוהה', grayscale: 'גווני אפור',
      readable_font: 'גופן קריא (Arial)', more_spacing: 'ריווח מוגבר',
      underline_links: 'הדגש קישורים', highlight_focus: 'הדגש פוקוס',
      stop_anim: 'עצור אנימציות', big_cursor: 'סמן גדול',
      reset_a11y: 'איפוס הגדרות הנגשה',
      decrease_font: 'הקטן גופן', increase_font: 'הגדל גופן',
      font_labels: ['קטן מאוד','קטן','רגיל','בינוני','גדול','גדול מאוד','ענק'],
      dir: 'rtl', lang: 'he'
    }},
    ar: {{
      title: 'تحديثات وزارة الصحة',
      tagline: 'ما الجديد في مواقع وزارة الصحة المختلفة؟',
      last_updated: 'آخر تحديث', next_update: 'تحديث خلال', minutes: 'دقائق',
      articles: 'مقالات وأخبار', new_items: 'عناصر جديدة', sources: 'مصادر المعلومات',
      print: 'طباعة', email: 'بريد', share: 'مشاركة', dark_mode: 'الوضع الليلي',
      copy_link: 'نسخ الرابط', copied: 'تم النسخ!', more_share: 'خيارات إضافية...',
      search_placeholder: 'البحث في جميع المقالات...',
      topic_label: 'الموضوع:', source_label: 'المصدر:',
      all: 'الكل', all_sources: 'جميع المصادر', saved: 'المحفوظات',
      f_vaccines: 'تطعيمات', f_mental: 'الصحة النفسية', f_children: 'أطفال',
      f_emergency: 'طوارئ', f_nutrition: 'تغذية',
      showing: 'يُعرض', articles_short: 'مقالات',
      no_results: 'لا توجد نتائج لهذا البحث',
      footer: 'يُجمع تلقائيًا من مواقع وزارة الصحة',
      new_badge: 'جديد', read_more: 'اقرأ أكثر', read_more_arrow: '→',
      a11y: 'إمكانية الوصول', a11y_open: 'فتح قائمة إمكانية الوصول', a11y_panel_label: 'قائمة إمكانية الوصول',
      close: 'إغلاق', text_size: 'حجم النص', color_display: 'اللون والعرض',
      readability: 'قابلية القراءة', nav_motion: 'التنقل والحركة',
      high_contrast: 'تباين عالٍ', grayscale: 'تدرج الرمادي',
      readable_font: 'خط سهل القراءة (Arial)', more_spacing: 'تباعد أكبر',
      underline_links: 'تسطير الروابط', highlight_focus: 'تمييز التركيز',
      stop_anim: 'إيقاف الحركات', big_cursor: 'مؤشر كبير',
      reset_a11y: 'إعادة تعيين إمكانية الوصول',
      decrease_font: 'تصغير الخط', increase_font: 'تكبير الخط',
      font_labels: ['صغير جداً','صغير','عادي','متوسط','كبير','كبير جداً','ضخم'],
      dir: 'rtl', lang: 'ar'
    }},
    en: {{
      title: 'Ministry of Health Updates',
      tagline: "What's new across the Ministry of Health's websites?",
      last_updated: 'Last updated', next_update: 'Next update in', minutes: 'minutes',
      articles: 'Articles & News', new_items: 'new items', sources: 'Sources',
      print: 'Print', email: 'Email', share: 'Share', dark_mode: 'Night Mode',
      copy_link: 'Copy Link', copied: 'Copied!', more_share: 'More options...',
      search_placeholder: 'Search all articles...',
      topic_label: 'Topic:', source_label: 'Source:',
      all: 'All', all_sources: 'All Sources', saved: 'Saved',
      f_vaccines: 'Vaccines', f_mental: 'Mental Health', f_children: 'Children',
      f_emergency: 'Emergency', f_nutrition: 'Nutrition',
      showing: 'Showing', articles_short: 'articles',
      no_results: 'No results found for this search',
      footer: 'Automatically scraped from Ministry of Health websites',
      new_badge: 'New', read_more: 'Read more', read_more_arrow: '→',
      a11y: 'Accessibility', a11y_open: 'Open accessibility menu', a11y_panel_label: 'Accessibility menu',
      close: 'Close', text_size: 'Text Size', color_display: 'Color & Display',
      readability: 'Readability', nav_motion: 'Navigation & Motion',
      high_contrast: 'High Contrast', grayscale: 'Grayscale',
      readable_font: 'Readable Font (Arial)', more_spacing: 'Increased Spacing',
      underline_links: 'Underline Links', highlight_focus: 'Highlight Focus',
      stop_anim: 'Stop Animations', big_cursor: 'Large Cursor',
      reset_a11y: 'Reset Accessibility Settings',
      decrease_font: 'Decrease font', increase_font: 'Increase font',
      font_labels: ['Tiny','Small','Normal','Medium','Large','X-Large','Huge'],
      dir: 'ltr', lang: 'en'
    }},
    ru: {{
      title: 'Обновления Министерства здравоохранения',
      tagline: 'Что нового на сайтах Министерства здравоохранения?',
      last_updated: 'Последнее обновление', next_update: 'Обновление через', minutes: 'мин',
      articles: 'Статьи и новости', new_items: 'новых материалов', sources: 'Источники',
      print: 'Печать', email: 'Email', share: 'Поделиться', dark_mode: 'Ночной режим',
      copy_link: 'Копировать ссылку', copied: 'Скопировано!', more_share: 'Ещё варианты...',
      search_placeholder: 'Поиск по всем материалам...',
      topic_label: 'Тема:', source_label: 'Источник:',
      all: 'Все', all_sources: 'Все источники', saved: 'Сохранённые',
      f_vaccines: 'Вакцины', f_mental: 'Психическое здоровье', f_children: 'Дети',
      f_emergency: 'Скорая помощь', f_nutrition: 'Питание',
      showing: 'Показано', articles_short: 'материалов',
      no_results: 'Результаты не найдены',
      footer: 'Автоматически собирается с сайтов Министерства здравоохранения',
      new_badge: 'Новое', read_more: 'Читать далее', read_more_arrow: '→',
      a11y: 'Доступность', a11y_open: 'Открыть меню доступности', a11y_panel_label: 'Меню доступности',
      close: 'Закрыть', text_size: 'Размер текста', color_display: 'Цвет и отображение',
      readability: 'Читаемость', nav_motion: 'Навигация и движение',
      high_contrast: 'Высокий контраст', grayscale: 'Оттенки серого',
      readable_font: 'Читаемый шрифт (Arial)', more_spacing: 'Увеличенный интервал',
      underline_links: 'Подчеркнуть ссылки', highlight_focus: 'Выделить фокус',
      stop_anim: 'Остановить анимацию', big_cursor: 'Большой курсор',
      reset_a11y: 'Сбросить настройки доступности',
      decrease_font: 'Уменьшить шрифт', increase_font: 'Увеличить шрифт',
      font_labels: ['Крошечный','Маленький','Нормальный','Средний','Большой','Очень большой','Огромный'],
      dir: 'ltr', lang: 'ru'
    }}
  }};

  var currentLang = 'he';

  function setLang(lang) {{
    if (!TRANSLATIONS[lang]) return;
    currentLang = lang;
    localStorage.setItem('moh_lang', lang);
    const T = TRANSLATIONS[lang];

    // document lang/dir — keep RTL for he/ar, switch for en/ru
    document.documentElement.lang = T.lang;
    // Note: page content is in Hebrew so we keep RTL always, only UI text changes
    // For en/ru we add a helper class so specific UI elements can use ltr
    document.documentElement.setAttribute('data-lang', lang);

    // Update page title
    document.title = T.title;

    // Update all data-i18n elements
    document.querySelectorAll('[data-i18n]').forEach(function(el) {{
      var key = el.getAttribute('data-i18n');
      if (T[key] !== undefined) el.textContent = T[key];
    }});

    // Update placeholders
    document.querySelectorAll('[data-i18n-placeholder]').forEach(function(el) {{
      var key = el.getAttribute('data-i18n-placeholder');
      if (T[key] !== undefined) el.placeholder = T[key];
    }});

    // Update title attributes
    document.querySelectorAll('[data-i18n-title]').forEach(function(el) {{
      var key = el.getAttribute('data-i18n-title');
      if (T[key] !== undefined) el.title = T[key];
    }});

    // Update aria-label attributes
    document.querySelectorAll('[data-i18n-aria]').forEach(function(el) {{
      var key = el.getAttribute('data-i18n-aria');
      if (T[key] !== undefined) el.setAttribute('aria-label', T[key]);
    }});

    // Update read-more arrows direction
    document.querySelectorAll('.read-more-arrow').forEach(function(el) {{
      el.textContent = T.read_more_arrow || (T.dir === 'rtl' ? '←' : '→');
    }});

    // Update font size label
    var lbl = document.getElementById('fs-label');
    if (lbl) lbl.textContent = T.font_labels[baseFontIndex + fontSizeLevel] || T.font_labels[2];

    // Update results count text
    _updateResultsCount();

    // Highlight active lang button (desktop + mobile)
    ['he','ar','en','ru'].forEach(function(l) {{
      var btn = document.getElementById('lang-' + l);
      if (btn) btn.classList.toggle('active', l === lang);
      var btnM = document.getElementById('lang-' + l + '-mobile');
      if (btnM) btnM.classList.toggle('active', l === lang);
    }});

    // Translate card content
    translateCards(lang);
  }}

  function _updateResultsCount() {{
    var count = document.querySelectorAll('.news-card.visible').length;
    var T = TRANSLATIONS[currentLang];
    var el = document.getElementById('results-count');
    if (el) el.innerHTML = T.showing + ' <strong>' + count + '</strong> ' + T.articles_short;
    var elM = document.getElementById('results-count-mobile');
    if (elM) elM.innerHTML = T.showing + ' <strong>' + count + '</strong> ' + T.articles_short;
  }}

  // Init language
  (function() {{
    var saved = localStorage.getItem('moh_lang') || 'he';
    if (TRANSLATIONS[saved]) {{
      // Apply without animation
      setLang(saved);
    }}
  }})();

  // ── DARK MODE ──
  (function() {{
    const saved = localStorage.getItem('moh_theme');
    if (saved === 'dark') {{
      document.documentElement.setAttribute('data-theme', 'dark');
      updateDarkIcon(true);
    }}
  }})();

  function updateDarkIcon(isDark) {{
    const icon = document.getElementById('dark-icon');
    if (!icon) return;
    if (isDark) {{
      icon.innerHTML = '<circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>';
    }} else {{
      icon.innerHTML = '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>';
    }}
  }}

  function toggleFilters(btn) {{
    var panel = document.getElementById('toolbar-filters');
    var open = panel.classList.toggle('open');
    btn.classList.toggle('open', open);
  }}

  function toggleMobileMenu() {{
    var menu = document.getElementById('mobile-menu');
    var btn = document.getElementById('mobile-menu-btn');
    var open = menu.classList.toggle('open');
    btn.classList.toggle('open', open);
  }}

  function toggleDarkMode() {{
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    if (isDark) {{
      document.documentElement.removeAttribute('data-theme');
      localStorage.setItem('moh_theme', 'light');
      updateDarkIcon(false);
    }} else {{
      document.documentElement.setAttribute('data-theme', 'dark');
      localStorage.setItem('moh_theme', 'dark');
      updateDarkIcon(true);
    }}
  }}

  // ── SCROLL PROGRESS BAR ──
  window.addEventListener('scroll', function() {{
    const el = document.getElementById('progress-bar');
    if (!el) return;
    const scrollTop = window.scrollY || document.documentElement.scrollTop;
    const docH = document.documentElement.scrollHeight - document.documentElement.clientHeight;
    const pct = docH > 0 ? (scrollTop / docH) * 100 : 0;
    el.style.width = pct + '%';
  }}, {{ passive: true }});

  // ── ANIMATED COUNTERS ──
  function animateCounter(el) {{
    const target = parseInt(el.getAttribute('data-target') || '0', 10);
    if (target === 0) {{ el.textContent = '0'; return; }}
    const duration = 900;
    const start = performance.now();
    function step(now) {{
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      el.textContent = Math.round(eased * target);
      if (progress < 1) requestAnimationFrame(step);
      else el.textContent = target;
    }}
    requestAnimationFrame(step);
  }}
  window.addEventListener('load', function() {{
    document.querySelectorAll('[data-target]').forEach(animateCounter);

    // After initial card animations complete, freeze them so filter works instantly
    var maxDelay = 500 + 450 + 100; // max stagger + duration + buffer
    setTimeout(function() {{
      document.querySelectorAll('.news-card').forEach(function(c) {{
        c.style.animation = 'none';
        c.style.opacity = '1';
        c.style.transform = 'none';
      }});
    }}, maxDelay);
  }});


  // ── NEWS TICKER ──
  (function() {{
    const track = document.getElementById('ticker-track');
    if (!track) return;
    let pos = 0;
    const speed = 0.55;
    function step() {{
      pos -= speed;
      const halfW = track.scrollWidth / 2;
      if (-pos >= halfW) pos = 0;
      track.style.transform = 'translateX(' + pos + 'px)';
      requestAnimationFrame(step);
    }}
    requestAnimationFrame(step);
  }})();

  // ── REFRESH COUNTDOWN (every 30 min) ──
  (function() {{
    var INTERVAL_MIN = 30;
    var el = document.getElementById('cd-val');
    if (!el) return;
    function nextMark() {{
      var now = new Date();
      var m = now.getMinutes();
      var rem = INTERVAL_MIN - (m % INTERVAL_MIN);
      var next = new Date(now.getTime() + rem * 60000);
      next.setSeconds(0, 0);
      return next;
    }}
    function update() {{
      var diff = Math.max(0, nextMark() - new Date());
      var m = Math.floor(diff / 60000);
      var s = Math.floor((diff % 60000) / 1000);
      el.textContent = m + ':\\u200F' + String(s).padStart(2,'0');
      if (diff < 3000) setTimeout(function() {{ window.location.reload(); }}, diff + 500);
    }}
    update();
    setInterval(update, 1000);
  }})();

  // ── BOOKMARKS ──
  function getCardKey(card) {{
    return card.dataset.link || card.dataset.title || '';
  }}
  function isBookmarked(card) {{
    return bookmarks.includes(getCardKey(card));
  }}
  function toggleBookmark(btn, event) {{
    if (event) event.stopPropagation();
    const card = btn.closest('.news-card');
    if (!card) return;
    const key = getCardKey(card);
    if (!key) return;
    const idx = bookmarks.indexOf(key);
    if (idx === -1) {{
      bookmarks.push(key);
      btn.classList.add('bookmarked');
      card.classList.add('bookmarked-card');
    }} else {{
      bookmarks.splice(idx, 1);
      btn.classList.remove('bookmarked');
      card.classList.remove('bookmarked-card');
    }}
    localStorage.setItem('moh_bookmarks', JSON.stringify(bookmarks));
    if (showBookmarksOnly) filterCards();
  }}

  function toggleBookmarksFilter(btn) {{
    showBookmarksOnly = !showBookmarksOnly;
    btn.classList.toggle('active-gold', showBookmarksOnly);
    // Sync the other bookmarks button (desktop <-> mobile)
    var otherId = btn.id === 'bookmarks-btn' ? 'bookmarks-btn-mobile' : 'bookmarks-btn';
    var other = document.getElementById(otherId);
    if (other) other.classList.toggle('active-gold', showBookmarksOnly);
    filterCards();
  }}

  // Restore bookmarks on load
  document.querySelectorAll('.news-card').forEach(function(card) {{
    if (isBookmarked(card)) {{
      card.classList.add('bookmarked-card');
      const btn = card.querySelector('.bookmark-btn');
      if (btn) btn.classList.add('bookmarked');
    }}
  }});

  // ── SEARCH + FILTER ──
  // Store original HTML for highlight restore
  document.querySelectorAll('.news-card').forEach(function(card) {{
    const tEl = card.querySelector('.card-title-link');
    const dEl = card.querySelector('.card-desc');
    if (tEl) tEl.dataset.orig = tEl.innerHTML;
    if (dEl) dEl.dataset.orig = dEl.innerHTML;
  }});

  function highlightEl(el, q) {{
    if (!el || !el.dataset.orig) return;
    if (!q) {{ el.innerHTML = el.dataset.orig; return; }}
    const esc = q.replace(/[.*+?^${{}}()|[\\]\\\\]/g, '\\\\$&');
    el.innerHTML = el.dataset.orig.replace(new RegExp('(' + esc + ')', 'gi'), '<mark class="hl">$1</mark>');
  }}

  function filterCards() {{
    const q = document.getElementById('search').value.trim().toLowerCase();
    let visible = 0;
    const total = document.querySelectorAll('.news-card').length;
    document.querySelectorAll('.news-card').forEach(function(card) {{
      const title = (card.dataset.title || '').toLowerCase();
      const desc  = (card.dataset.desc  || '').toLowerCase();
      const tags  = (card.dataset.tags  || '').toLowerCase();
      const site  = (card.dataset.site  || '').toLowerCase();

      const matchQ    = !q || title.includes(q) || desc.includes(q) || tags.includes(q) || site.includes(q);
      const matchTag  = !activeTag || tags.includes(activeTag.toLowerCase());
      const matchSite = !activeSite || site === activeSite.toLowerCase();
      const matchBM   = !showBookmarksOnly || isBookmarked(card);

      const show = matchQ && matchTag && matchSite && matchBM;
      card.classList.toggle('hidden', !show);
      if (show) {{
        visible++;
        highlightEl(card.querySelector('.card-title-link'), q);
        highlightEl(card.querySelector('.card-desc'), q);
      }}
    }});
    document.getElementById('no-results').classList.toggle('visible', visible === 0);
    var T = TRANSLATIONS[currentLang] || TRANSLATIONS.he;
    var rc = document.getElementById('results-count');
    if (rc) rc.innerHTML = T.showing + ' <strong>' + visible + '</strong> ' + T.articles_short;
    var rcM = document.getElementById('results-count-mobile');
    if (rcM) rcM.innerHTML = T.showing + ' <strong>' + visible + '</strong> ' + T.articles_short;
    // Sync mobile search input with desktop
    var sm = document.getElementById('search-mobile');
    if (sm && sm !== document.activeElement) sm.value = document.getElementById('search').value;
  }}

  function setTagFilter(tag, btn) {{
    activeTag = tag;
    document.querySelectorAll('.filter-group .filter-pill').forEach(function(b) {{
      if (b.id !== 'site-all-btn' && !b.hasAttribute('data-site-btn') && b.id !== 'bookmarks-btn') {{
        b.classList.remove('active');
      }}
    }});
    btn.classList.add('active');
    filterCards();
  }}

  function setSiteFilter(site, btn) {{
    activeSite = site;
    document.querySelectorAll('[data-site-btn], #site-all-btn, #site-all-btn-mobile').forEach(function(b) {{
      b.classList.remove('active-teal');
    }});
    btn.classList.add('active-teal');
    filterCards();
  }}

  // Mark site filter buttons
  document.querySelectorAll('.filter-pill').forEach(function(btn) {{
    if (btn.getAttribute('onclick') && btn.getAttribute('onclick').startsWith('setSiteFilter')) {{
      btn.setAttribute('data-site-btn', '1');
    }}
  }});

  // ── ACCESSIBILITY ──
  var a11yPanelOpen = false;
  var fontSizeLevel = 0; // -2 to +4
  var fontSizes = ['12px','13px','15px','17px','19px','22px','26px'];
  var fontLabels = ['\u05E7\u05D8\u05DF \u05DE\u05D0\u05D5\u05D3','\u05E7\u05D8\u05DF','\u05E8\u05D2\u05D9\u05DC','\u05D1\u05D9\u05E0\u05D5\u05E0\u05D9','\u05D2\u05D3\u05D5\u05DC','\u05D2\u05D3\u05D5\u05DC \u05DE\u05D0\u05D5\u05D3','\u05E2\u05E0\u05E7'];
  // fontLabels: קטן מאוד, קטן, רגיל, בינוני, גדול, גדול מאוד, ענק
  var baseFontIndex = 2; // 'רגיל' = index 2 = 15px

  (function() {{
    // Restore saved a11y settings
    var saved = JSON.parse(localStorage.getItem('moh_a11y') || '{{}}');
    ['a11y-contrast','a11y-grayscale','a11y-readable','a11y-text-spacing',
     'a11y-underline-links','a11y-highlight-focus','a11y-no-anim','a11y-big-cursor'].forEach(function(cls) {{
      if (saved[cls]) {{
        document.documentElement.classList.add(cls);
        var btn = document.getElementById('btn-' + cls.replace('a11y-',''));
        if (btn) btn.classList.add('on');
      }}
    }});
    if (saved.fontSize !== undefined) {{
      fontSizeLevel = saved.fontSize;
      applyFontSize();
    }}
  }})();

  function toggleA11yPanel() {{
    a11yPanelOpen = !a11yPanelOpen;
    document.getElementById('a11y-panel').classList.toggle('open', a11yPanelOpen);
    document.getElementById('a11y-toggle').setAttribute('aria-expanded', a11yPanelOpen);
    if (a11yPanelOpen) document.querySelector('.a11y-close').focus();
  }}

  // Close panel on Escape
  document.addEventListener('keydown', function(e) {{
    if (e.key === 'Escape' && a11yPanelOpen) toggleA11yPanel();
    if ((e.key === '/' || e.key === 'F' && e.ctrlKey) && !a11yPanelOpen) {{
      e.preventDefault();
      document.getElementById('search').focus();
    }}
  }});

  function toggleA11y(cls, btn) {{
    var on = document.documentElement.classList.toggle(cls);
    btn.classList.toggle('on', on);
    saveA11y();
  }}

  function applyFontSize() {{
    var idx = baseFontIndex + fontSizeLevel;
    idx = Math.max(0, Math.min(fontSizes.length - 1, idx));
    document.documentElement.style.fontSize = fontSizes[idx];
    var lbl = document.getElementById('fs-label');
    if (lbl) lbl.textContent = (TRANSLATIONS[currentLang] || TRANSLATIONS.he).font_labels[idx] || fontLabels[idx];
  }}

  function changeFontSize(dir) {{
    fontSizeLevel += dir;
    fontSizeLevel = Math.max(-2, Math.min(4, fontSizeLevel));
    applyFontSize();
    saveA11y();
  }}

  function saveA11y() {{
    var state = {{ fontSize: fontSizeLevel }};
    ['a11y-contrast','a11y-grayscale','a11y-readable','a11y-text-spacing',
     'a11y-underline-links','a11y-highlight-focus','a11y-no-anim','a11y-big-cursor'].forEach(function(cls) {{
      state[cls] = document.documentElement.classList.contains(cls);
    }});
    localStorage.setItem('moh_a11y', JSON.stringify(state));
  }}

  function resetA11y() {{
    ['a11y-contrast','a11y-grayscale','a11y-readable','a11y-text-spacing',
     'a11y-underline-links','a11y-highlight-focus','a11y-no-anim','a11y-big-cursor'].forEach(function(cls) {{
      document.documentElement.classList.remove(cls);
      var btn = document.getElementById('btn-' + cls.replace('a11y-',''));
      if (btn) btn.classList.remove('on');
    }});
    fontSizeLevel = 0;
    applyFontSize();
    localStorage.removeItem('moh_a11y');
  }}

  // ── CARD TRANSLATION ──
  var _transCache = {{}};
  var _currentTransLang = null;

  async function translateCards(lang) {{
    if (lang === 'he') {{
      _restoreHebrew();
      return;
    }}
    _currentTransLang = lang;
    if (!_transCache[lang]) _transCache[lang] = {{}};

    var cards = Array.from(document.querySelectorAll('.news-card'));

    // Collect unique texts not yet cached
    var seen = new Set();
    var todo = [];
    cards.forEach(function(card) {{
      ['title','desc'].forEach(function(attr) {{
        var text = card.dataset[attr] || '';
        if (text && !_transCache[lang][text] && !seen.has(text)) {{
          seen.add(text);
          todo.push(text);
        }}
      }});
    }});

    // Add shimmer to cards while loading
    cards.forEach(function(c) {{ c.classList.add('card-translating'); }});

    if (todo.length === 0) {{
      _applyTranslations(lang, cards);
      cards.forEach(function(c) {{ c.classList.remove('card-translating'); }});
      return;
    }}

    _setTransProgress(true, 0);

    // Translate in parallel batches of 5, titles first
    var BATCH = 5;
    var done = 0;
    for (var i = 0; i < todo.length; i += BATCH) {{
      if (_currentTransLang !== lang) return; // lang changed, abort
      var chunk = todo.slice(i, i + BATCH);
      await Promise.all(chunk.map(async function(text) {{
        try {{
          _transCache[lang][text] = await _gtrans(text, lang);
        }} catch(e) {{
          _transCache[lang][text] = text; // fallback: keep original
        }}
        done++;
      }}));
      _setTransProgress(true, done / todo.length);
      // Apply partial translations so titles appear as they come in
      _applyTranslations(lang, cards);
    }}

    _setTransProgress(false, 1);
    cards.forEach(function(c) {{ c.classList.remove('card-translating'); }});
    _applyTranslations(lang, cards);
  }}

  // Returns a localized URL for known multilingual sites, or original for Hebrew-only sites.
  // Currently gov.il supports /he/ /en/ /ar/ /ru/ path segments.
  function _localizeLink(url, lang) {{
    if (!url || lang === 'he') return url;
    // gov.il: https://www.gov.il/he/... → /en/ /ar/ /ru/
    var govIl = url.match(/^(https?:\\/\\/[^/]*\\.gov\\.il\\/)(he|en|ar|ru)(\\/.*)?$/i);
    if (govIl) {{
      var seg = {{ar:'ar', en:'en', ru:'ru'}}[lang] || 'he';
      return govIl[1] + seg + (govIl[3] || '');
    }}
    // All other health.gov.il sites are Hebrew-only — return original
    return url;
  }}

  function _applyTranslations(lang, cards) {{
    var cache = _transCache[lang] || {{}};
    (cards || document.querySelectorAll('.news-card')).forEach(function(card) {{
      var titleEl   = card.querySelector('.card-title-link');
      var descEl    = card.querySelector('.card-desc');
      var readMore  = card.querySelector('.btn-read-more');
      var t = card.dataset.title || '';
      var d = card.dataset.desc  || '';
      var origLink  = card.dataset.link || '';
      var localLink = _localizeLink(origLink, lang);

      if (titleEl && cache[t]) titleEl.textContent = cache[t];
      if (descEl  && cache[d]) descEl.textContent  = cache[d];

      // Update hrefs to localized page (or keep original if no translation available)
      if (titleEl && titleEl.tagName === 'A') titleEl.href = localLink || origLink;
      if (readMore) readMore.href = localLink || origLink;
    }});
  }}

  function _restoreHebrew() {{
    _currentTransLang = 'he';
    document.querySelectorAll('.news-card').forEach(function(card) {{
      var titleEl  = card.querySelector('.card-title-link');
      var descEl   = card.querySelector('.card-desc');
      var readMore = card.querySelector('.btn-read-more');
      var origLink = card.dataset.link || '';
      card.classList.remove('card-translating');
      if (titleEl && card.dataset.title) titleEl.textContent = card.dataset.title;
      if (descEl  && card.dataset.desc)  descEl.textContent  = card.dataset.desc;
      if (titleEl && titleEl.tagName === 'A') titleEl.href = origLink;
      if (readMore) readMore.href = origLink;
    }});
  }}

  async function _gtrans(text, tl) {{
    var url = 'https://translate.googleapis.com/translate_a/single'
            + '?client=gtx&sl=he&tl=' + encodeURIComponent(tl)
            + '&dt=t&q=' + encodeURIComponent(text);
    var resp = await fetch(url);
    if (!resp.ok) throw new Error('translate error');
    var data = await resp.json();
    // data[0] is array of [translated_chunk, original_chunk, ...]
    return data[0].map(function(x) {{ return x[0]; }}).join('');
  }}

  function _setTransProgress(visible, pct) {{
    var ind  = document.getElementById('trans-indicator');
    var fill = document.getElementById('trans-fill');
    if (ind)  ind.classList.toggle('visible', visible);
    if (fill) fill.style.width = Math.round((pct || 0) * 100) + '%';
  }}

  // ── SHARE ──
  function toggleShareMenu(e) {{
    e.stopPropagation();
    const dd = document.getElementById('share-dropdown');
    dd.classList.toggle('open');
    if (dd.classList.contains('open')) {{
      setTimeout(() => document.addEventListener('click', closeShareMenu, {{once: true}}), 0);
    }}
  }}
  function closeShareMenu() {{
    document.getElementById('share-dropdown').classList.remove('open');
  }}
  function _shareText() {{
    let lines = ['עדכוני משרד הבריאות — ' + new Date().toLocaleDateString('he-IL')];
    for (const [site, info] of Object.entries(DATA)) {{
      const newItems = (info.items || []).filter(i => i.is_new);
      if (newItems.length) {{
        lines.push('\\n' + site + ':');
        newItems.slice(0, 3).forEach(i => lines.push('• ' + i.title));
      }}
    }}
    lines.push('\\n' + window.location.href);
    return lines.join('\\n');
  }}
  function shareWhatsApp() {{
    const text = encodeURIComponent(_shareText());
    window.open('https://wa.me/?text=' + text, '_blank');
    closeShareMenu();
  }}
  function shareTelegram() {{
    const text = encodeURIComponent(_shareText());
    const url = encodeURIComponent(window.location.href);
    window.open('https://t.me/share/url?url=' + url + '&text=' + text, '_blank');
    closeShareMenu();
  }}
  function shareTwitter() {{
    const text = encodeURIComponent('עדכוני משרד הבריאות 🏥 ' + window.location.href);
    window.open('https://twitter.com/intent/tweet?text=' + text, '_blank');
    closeShareMenu();
  }}
  function shareLinkedIn() {{
    const url = encodeURIComponent(window.location.href);
    window.open('https://www.linkedin.com/sharing/share-offsite/?url=' + url, '_blank');
    closeShareMenu();
  }}
  function copyShareLink() {{
    const text = window.location.href !== 'about:blank' ? window.location.href : _shareText();
    navigator.clipboard.writeText(text).then(() => {{
      const fb = document.getElementById('copy-feedback');
      fb.classList.add('show');
      setTimeout(() => fb.classList.remove('show'), 2000);
    }}).catch(() => {{
      const ta = document.createElement('textarea');
      ta.value = text; document.body.appendChild(ta); ta.select();
      document.execCommand('copy'); document.body.removeChild(ta);
      const fb = document.getElementById('copy-feedback');
      fb.classList.add('show');
      setTimeout(() => fb.classList.remove('show'), 2000);
    }});
  }}
  function nativeShare() {{
    navigator.share({{
      title: 'עדכוני משרד הבריאות',
      text: _shareText(),
      url: window.location.href
    }}).catch(() => {{}});
    closeShareMenu();
  }}
  // Show native share button on supported devices
  if (navigator.share) {{
    document.getElementById('native-share-btn').style.display = 'flex';
  }}

  // ── EMAIL ──
  function sendEmail() {{
    let body = 'דשבורד משרד הבריאות — ' + new Date().toLocaleDateString('he-IL') + '\\n\\n';
    for (const [site, info] of Object.entries(DATA)) {{
      body += '── ' + site + ' ──\\n';
      (info.items || []).forEach(function(i) {{
        body += (i.is_new ? '[חדש] ' : '') + i.title + '\\n';
        if (i.description) body += i.description + '\\n';
        if (i.link) body += i.link + '\\n';
        body += '\\n';
      }});
    }}
    const sub = encodeURIComponent('עדכון משרד הבריאות — ' + new Date().toLocaleDateString('he-IL'));
    window.location.href = 'mailto:?subject=' + sub + '&body=' + encodeURIComponent(body);
  }}
</script>
</body>
</html>'''

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Dashboard generated: {OUTPUT_FILE}")


if __name__ == '__main__':
    if not os.path.exists(DATA_FILE):
        print("No scraped_data.json found. Run scraper first.")
        exit(1)
    with open(DATA_FILE, encoding='utf-8') as f:
        data = json.load(f)
    generate(data)
