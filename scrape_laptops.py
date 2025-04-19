import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# Function to scrape laptops data
def scrape_laptops(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to retrieve data from {url}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    laptops = []

    # Example for KSP.co.il - Adjust CSS selectors to match the website
    for item in soup.select('.product-item'):  # Replace '.product-item' with the correct class
        try:
            model_name = item.select_one('.product-title').get_text(strip=True)  # Replace with correct class
            brand = item.select_one('.product-brand').get_text(strip=True)  # Replace with correct class
            processor = item.select_one('.product-processor').get_text(strip=True)  # Replace with correct class
            ram = item.select_one('.product-ram').get_text(strip=True)  # Replace with correct class
            storage = item.select_one('.product-storage').get_text(strip=True)  # Replace with correct class
            graphics_card = item.select_one('.product-graphics').get_text(strip=True)  # Replace with correct class
            display = item.select_one('.product-display').get_text(strip=True)  # Replace with correct class
            battery_life = item.select_one('.product-battery').get_text(strip=True)  # Replace with correct class
            weight = item.select_one('.product-weight').get_text(strip=True)  # Replace with correct class
            operating_system = item.select_one('.product-os').get_text(strip=True)  # Replace with correct class
            connectivity = item.select_one('.product-connectivity').get_text(strip=True)  # Replace with correct class
            ports = item.select_one('.product-ports').get_text(strip=True)  # Replace with correct class
            price = item.select_one('.product-price').get_text(strip=True)  # Replace with correct class

            laptops.append({
                'Model Name': model_name,
                'Brand': brand,
                'Processor': processor,
                'RAM': ram,
                'Storage': storage,
                'Graphics Card': graphics_card,
                'Display Size and Resolution': display,
                'Battery Life': battery_life,
                'Weight': weight,
                'Operating System': operating_system,
                'Connectivity Options': connectivity,
                'Ports': ports,
                'Price': price
            })
        except AttributeError:
            # Skip items with missing information
            continue

    return laptops

# Main function to scrape multiple pages and save to a CSV
def main():
    base_urls = [
        'https://www.ksp.co.il/mob/items/306904',  # Example for KSP laptops page
        'https://www.payngo.co.il/344530.html',   # Example for Payngo laptops page
        'https://www.ivory.co.il/מחשבים_ניידים.html'  # Example for Ivory laptops page
    ]

    all_laptops = []

    for base_url in base_urls:
        print(f"Scraping data from {base_url}")
        laptops = scrape_laptops(base_url)
        all_laptops.extend(laptops)
        time.sleep(2)  # Respectful delay between requests

    # Save the data to a CSV file
    df = pd.DataFrame(all_laptops)
    df.to_csv('laptops_data.csv', index=False, encoding='utf-8')
    print("Data has been saved to laptops_data.csv")

if __name__ == '__main__':
    main()
