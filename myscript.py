# Import libraries (requests and BeautifulSoup)
import requests
from bs4 import BeautifulSoup

# URL to fetch data from (example website for demonstration)
url = "https://example.com"  # Replace this with a real URL later

# Make a request to the URL
response = requests.get(url)

# Check if the request was successful
if response.status_code == 200:
    # Parse the HTML content
    soup = BeautifulSoup(response.content, "html.parser")
    
    # Print the title of the page
    title = soup.title.string
    print("Page Title:", title)
else:
    print("Failed to retrieve the page. Status code:", response.status_code)
