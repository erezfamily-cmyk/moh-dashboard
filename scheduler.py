import schedule
import time
import subprocess
import os

def run_scraper():
    """Run the scraper script."""
    try:
        result = subprocess.run(
            ['python', 'src/scraper.py'],
            cwd=os.path.dirname(os.path.dirname(__file__)),  # Go up to project root
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"Scraping completed successfully at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print(f"Scraping failed: {result.stderr}")
    except Exception as e:
        print(f"Error running scraper: {e}")

# Schedule to run every day at 8:00 AM
schedule.every().day.at("08:00").do(run_scraper)

print("Scheduler started. Scraping will run every day at 08:00.")
print("Press Ctrl+C to stop.")

try:
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute
except KeyboardInterrupt:
    print("Scheduler stopped.")