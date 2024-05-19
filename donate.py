import requests
from bs4 import BeautifulSoup
from main import logger

# Function to scrape the mosque data
async def get_mosques(region):
    url = f'https://www.tabung.sg/collections/all/{region}?sort_by=manual'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    mosques = []
    
    # Find all anchor tags and check if the text starts with "Masjid"
    for a_tag in soup.find_all('a'):
        text = a_tag.get_text(strip=True)
        if text.startswith("Masjid"):
            mosque = {text: a_tag.get('href')}
            mosques.append(mosque)

    return mosques

# Function to get the QR code for a mosque
async def get_qr(path):
    url = f'https://www.tabung.sg{path}'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    qr_code_url = None
    image_border = soup.select_one('.ImageBorder')
    if image_border:
        qr_code_url = image_border['src']

    return qr_code_url

# Function to return a selected mosque and its path
async def select_mosque(region, index):
    region = region.lower()
    selected_mosque = index - 1
    if region in ['north', 'south', 'east', 'west']:
        mosques = await get_mosques(region)
        if mosques:
            if 0 <= selected_mosque < len(mosques):
                return [list(mosques[selected_mosque].keys())[0], list(mosques[selected_mosque].values())[0]]
            else:
                logger.info("Invalid selection.")
        else:
            logger.info("No mosques found in this region.")
    else:
        logger.info("Invalid region. Please select a region: North, South, East, or West")

