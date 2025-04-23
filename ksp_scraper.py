import requests
from bs4 import BeautifulSoup
import pandas as pd

# URL of the laptops category
url = 'https://ksp.co.il/mob/cat/271'  # Replace with the actual laptops page URL if different

# Send a GET request to the URL
response = requests.get(url)
response.raise_for_status()  # Check for request errors

# Parse the HTML content
soup = BeautifulSoup(response.content, 'html.parser')

# Find all product containers
products = soup.find_all('div', class_='product-item')  # Update 'product-item' if necessary to match KSP's structure

# List to store product data
data = []

# Enhanced function to parse specifications into detailed fields
def parse_specs(specs_text):
    # Initialize dictionary with key features
    specs = {
        'Processor': None,
        'RAM': None,
        'Storage': None,
        'Graphics Card': None,
        'Display': None,
        'Battery Life': None,
        'Weight': None,
        'Operating System': None,
        'Connectivity': None,
        'Ports': None,
    }
    
    # Example parsing logic for each key feature
    if 'Processor' in specs_text:
        specs['Processor'] = specs_text.split('Processor: ')[1].split(' ')[0]  # Adjust split logic as needed
    if 'RAM' in specs_text:
        specs['RAM'] = specs_text.split('RAM: ')[1].split(' ')[0]
    if 'Storage' in specs_text:
        specs['Storage'] = specs_text.split('Storage: ')[1].split(' ')[0]
    if 'Graphics Card' in specs_text:
        specs['Graphics Card'] = specs_text.split('Graphics Card: ')[1].split(' ')[0]
    if 'Display' in specs_text:
        specs['Display'] = specs_text.split('Display: ')[1].split(' ')[0]
    if 'Battery Life' in specs_text:
        specs['Battery Life'] = specs_text.split('Battery Life: ')[1].split(' ')[0]
    if 'Weight' in specs_text:
        specs['Weight'] = specs_text.split('Weight: ')[1].split(' ')[0]
    if 'Operating System' in specs_text:
        specs['Operating System'] = specs_text.split('Operating System: ')[1].split(' ')[0]
    if 'Connectivity' in specs_text:
        specs['Connectivity'] = specs_text.split('Connectivity: ')[1].split(' ')[0]
    if 'Ports' in specs_text:
        specs['Ports'] = specs_text.split('Ports: ')[1].split(' ')[0]
        
    return specs

# Extract data for each product
for product in products:
    # Extract basic product information
    name = product.find('div', class_='product-name').get_text(strip=True)
    price = product.find('div', class_='price').get_text(strip=True)
    specs_text = product.find('div', class_='specs').get_text(strip=True)
    
    # Parse specifications into detailed fields
    specs = parse_specs(specs_text)
    
    # Append all product data, including parsed specs, to the data list
    data.append({
        'Name': name,
        'Price': price,
        **specs
    })

# Create a DataFrame from the data list
df = pd.DataFrame(data)

# Save to Excel
df.to_excel('ksp_laptops_detailed.xlsx', index=False)
print('Data has been saved to ksp_laptops_detailed.xlsx')
