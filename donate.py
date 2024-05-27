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
    selected_mosque = int(index) - 1
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


# Function to return a selected mosque details as a string to be printed
async def mosque_extract(path):
    url = f'https://www.tabung.sg{path}'

    # Parse the HTML content
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Initialize variables with default values
    mosque_addy = "Not available"
    mosque_contact = "Not available"
    mosque_email = ": Not available"
    mosque_web = "Not available"
    mosque_uen = "Not available"

    for p_tag in soup.find_all('p'):
        strong_tags = p_tag.find_all('strong')

        for strong_tag in strong_tags:
            label = strong_tag.get_text(strip=True).strip(':')
            next_sibling = strong_tag.find_next_sibling(string = True)

            if next_sibling:
                value = next_sibling.strip()

                if label == 'Address':
                    mosque_addy = value
                elif label == 'Contact':
                    mosque_contact = value
                elif label == 'Email':
                    mosque_email = value
                elif label == 'Web':
                    link_tag = strong_tag.find_next('a')
                    if link_tag:
                        mosque_web = link_tag.get('href')
                        if mosque_web.startswith('http') and not mosque_web.startswith('https'):
                            mosque_web = mosque_web.replace('http', 'https')
                # Assuming UEN is in the same format, add similar extraction if needed
                elif label == 'UEN' or 'UEN' in label:
                    span_tag = strong_tag.find_next('span')
                    if span_tag and ":" in value:
                        mosque_uen = span_tag.get_text(strip=True)
                    else:
                        mosque_uen = value
            elif label == 'UEN':
                span_tag = strong_tag.find_next('span')
                if span_tag:
                    mosque_uen = span_tag.get_text(strip=True)


    # Initialize a formatted string of details
    details = f"{url}\n\n__Information__\n*Address*{mosque_addy}\n"
    details += f"*Contact*{mosque_contact}\n"
    details += f"*Email*{mosque_email}\n"
    details += f"*Web*: {mosque_web}\n\n"
    details += f"*UEN*: {mosque_uen}"

    logger.info(details)

    return details
