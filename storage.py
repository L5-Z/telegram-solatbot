import json
import logging

logger = logging.getLogger(__name__)

# File path to store the dictionary data
DATA_FILE = "saveFile.json"

def convert_to_bool(value):
    """
    Converts a string value to a boolean.
    If the value is "True" (case-insensitive), it returns True.
    If the value is "False" (case-insensitive), it returns False.
    For all other values, it returns the original value.
    """
    if isinstance(value, str):
        if value.lower() == "true":
            return True
        elif value.lower() == "false":
            return False
    return value

def convert_values(obj):
    """
    Recursively converts string values of "True" and "False" to booleans in a dictionary or list.
    """
    if isinstance(obj, dict):
        return {key: convert_values(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_values(item) for item in obj]
    else:
        return convert_to_bool(obj)

# Function to load data from the JSON file
def load_data():
    try:
        with open(DATA_FILE, "r") as file:
            data = file.read()
            if data.strip() == "":
                logger.warning("JSON file is empty. Creating a new file")
                data = {}
                new_json(data)
            elif data.strip() == "{}":
                logger.warning("JSON file contains an empty dictionary. Initializing with an empty dictionary")
                data = {}
            else:
                data = json.load(file)

            logger.info("Data loaded successfully from JSON file")
    except FileNotFoundError:
        logger.warning("JSON file not found. Creating a new file")
        data = {}
        new_json(data)  # Create a new file

    # Convert string values of "True" and "False" to booleans
    data = convert_values(data)

    return data

# Function to create new JSON file to save data
def new_json(data):
    try:
        with open(DATA_FILE, "w") as file:
            json.dump(data, file)
            logger.info("Successfully created JSON file")
    except Exception as e:
        logger.error(f"Error creating JSON file: {e}")

# Function to save data to the JSON file
async def save_data(data):
    try:
        with open(DATA_FILE, "w") as file:
            json.dump(data, file)
            logger.info("Data saved successfully to JSON file")
    except Exception as e:
        logger.error(f"Error saving data to JSON file: {e}")