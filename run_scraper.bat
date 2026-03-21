@echo off
cd /d C:\Users\erezf\moh-project
call venv\Scripts\activate
python src\scraper.py >> logs\scraper.log 2>&1
