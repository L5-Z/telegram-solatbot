import json
import os

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
            data = json.load(file)
    except FileNotFoundError:
        print("FileNotFoundError")
        data = {}
        save_data(data)  # Create a new file

    # Convert string values of "True" and "False" to booleans
    data = convert_values(data)

    return data

# Function to save data to the JSON file
async def save_data(data):
    with open(DATA_FILE, "w") as file:
        json.dump(data, file)