import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

# URL to test
url = "https://www.KSP.co.il"  # Replace with the website URL

# Fetch the static content using requests and BeautifulSoup
response = requests.get(url)
static_soup = BeautifulSoup(response.content, "html.parser")
static_text = static_soup.get_text()

# Set up Selenium with headless Chrome for dynamic content
chrome_options = Options()
chrome_options.add_argument("--headless")
driver = webdriver.Chrome(options=chrome_options)
driver.get(url)
time.sleep(5)  # Wait for the page to fully load

# Get dynamic content rendered by JavaScript
dynamic_soup = BeautifulSoup(driver.page_source, "html.parser")
dynamic_text = dynamic_soup.get_text()

driver.quit()

# Compare static and dynamic content
if static_text == dynamic_text:
    print("The content appears to be static.")
else:
    print("The content appears to be dynamic (JavaScript-rendered).")

# Optional: Print differences to understand what’s missing in static content
static_lines = set(static_text.splitlines())
dynamic_lines = set(dynamic_text.splitlines())
diff = dynamic_lines - static_lines
print("Differences found in dynamic content (if any):")
for line in diff:
    print(line)
