import json

# File path to store the dictionary data
DATA_FILE = "saveFile.json"

# Function to load data from the JSON file
async def load_data():
    try:
        with open(DATA_FILE, "r") as file:
            data = json.load(file)
    except FileNotFoundError:
        print("FileNotFoundError")
        data = {}
    return data


# Function to save data to the JSON file
async def save_data(data):
    with open(DATA_FILE, "w") as file:
        json.dump(data, file)