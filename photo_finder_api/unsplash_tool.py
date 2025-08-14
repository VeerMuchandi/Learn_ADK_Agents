import os
import requests

# load environment variables from .env with force   
from dotenv import load_dotenv
load_dotenv(override=True)

# Get your Unsplash Access Key from an environment variable for security.
UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY")

if not UNSPLASH_ACCESS_KEY:
    raise ValueError("UNSPLASH_ACCESS_KEY environment variable not set.")

def search_unsplash_photos(query: str) -> str:
    """
    Searches for photos on Unsplash based on a keyword query.

    Args:
        query: The keyword to search for (e.g., "mountain", "beach", "cityscape").

    Returns:
        The URL of a high-quality image from Unsplash, or an error message.
    """
    url = "https://api.unsplash.com/search/photos"
    headers = {
        "Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"
    }
    params = {
        "query": query,
        "per_page": 1,  # Get only one result
        "order_by": "relevant"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        
        data = response.json()
        
        if data['results']:
            # Return the regular size URL of the first image
            return data['results'][0]['urls']['regular']
        else:
            return f"Sorry, I couldn't find any images for '{query}'."
            
    except requests.exceptions.RequestException as e:
        return f"An error occurred while calling the Unsplash API: {e}"

def get_random_photo() -> str:
    """
    Fetches a random photo from Unsplash.

    Returns:
        The URL of a random high-quality image from Unsplash, or an error message.
    """
    url = "https://api.unsplash.com/photos/random"
    headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data['urls']['regular']
    except requests.exceptions.RequestException as e:
        return f"An error occurred while calling the Unsplash API: {e}"

def get_photo_by_id(photo_id: str) -> str:
    """
    Fetches a specific photo from Unsplash by its ID.

    Args:
        photo_id: The ID of the photo to fetch.

    Returns:
        The URL of the specified high-quality image from Unsplash, or an error message.
    """
    url = f"https://api.unsplash.com/photos/{photo_id}"
    headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data['urls']['regular']
    except requests.exceptions.RequestException as e:
        return f"An error occurred while calling the Unsplash API: {e}"
