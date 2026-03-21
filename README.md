# MOH Dashboard Scraper

This project creates a dashboard that scrapes multiple Ministry of Health websites daily for updates, new information, and changes.

## Setup

1. Create a virtual environment:
   python -m venv venv

2. Activate the virtual environment:
   venv\Scripts\activate  (on Windows)

3. Install dependencies:
   pip install -r requirements.txt

## Usage

Run the dashboard:
streamlit run app.py

Run the scraper:
python src/scraper.py

## Configuration

Add the list of websites to scrape in src/scraper.py