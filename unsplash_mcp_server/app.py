import os
import requests
from dotenv import load_dotenv
from fastmcp import FastMCP, tools


# Load environment variables from .env file (for local development)
load_dotenv()

# Initialize the FastMCP application
mcp = FastMCP("Unsplash MCP Server")

# Retrieve Unsplash Access Key from environment variables
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
if not UNSPLASH_ACCESS_KEY:
    # Use tool_error for critical setup errors that prevent the tool from functioning
    # FastMCP will handle logging this error.
    raise ValueError("UNSPLASH_ACCESS_KEY environment variable not set. Please set it securely.")

UNSPLASH_API_BASE_URL = "https://api.unsplash.com"

@mcp.tool("search_photos")
def search_photos(query: str, per_page: int = 10, page: int = 1, orientation: str = None) -> dict:
    """
    Searches for photos on Unsplash based on a query. 📸

    This tool allows you to find high-quality images from Unsplash's vast library.
    It supports various filters to refine your search results.

    :param query: The search term for photos (e.g., "mountains", "cityscape", "ocean").
    :param per_page: The number of results to return per page (default: 10, max: 30).
    :param page: The page number of the results to retrieve (default: 1).
    :param orientation: Filter by image orientation ('landscape', 'portrait', or 'squarish').
    :return: A dictionary containing the search results from the Unsplash API.
             Includes photo URLs, descriptions, and photographer details.
    """
    params = {
        "query": query,
        "per_page": per_page,
        "page": page,
        "client_id": UNSPLASH_ACCESS_KEY # Use client_id for public endpoints
    }
    if orientation:
        params["orientation"] = orientation

    try:
        response = requests.get(f"{UNSPLASH_API_BASE_URL}/search/photos", params=params)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        return data
    except requests.exceptions.HTTPError as e:
        error_message = f"Failed to fetch photos from Unsplash. Status: {e.response.status_code}, Details: {e.response.text}"
        tools.tool_error(error_message)
        return {"error": error_message}
    except requests.exceptions.RequestException as e:
        error_message = f"Network error or invalid request to Unsplash API: {e}"
        tools.tool_error(error_message)
        return {"error": error_message}

@mcp.tool("get_random_photo")
def get_random_photo(collection_id: str = None, query: str = None, orientation: str = None) -> dict:
    """
    Fetches a random photo from Unsplash. 🎲

    Useful when you need a spontaneous image without a specific search criteria,
    or a random image from a particular collection or related to a query.

    :param collection_id: The ID of a collection to retrieve a random photo from.
    :param query: A comma-separated list of keywords to filter random photos.
    :param orientation: Filter by image orientation ('landscape', 'portrait', or 'squarish').
    :return: A dictionary containing the random photo details.
             Includes photo URLs, descriptions, and photographer details.
    """
    params = {
        "client_id": UNSPLASH_ACCESS_KEY
    }
    if collection_id:
        params["collection"] = collection_id
    if query:
        params["query"] = query
    if orientation:
        params["orientation"] = orientation

    try:
        response = requests.get(f"{UNSPLASH_API_BASE_URL}/photos/random", params=params)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.HTTPError as e:
        error_message = f"Failed to fetch random photo from Unsplash. Status: {e.response.status_code}, Details: {e.response.text}"
        tools.tool_error(error_message)
        return {"error": error_message}
    except requests.exceptions.RequestException as e:
        error_message = f"Network error or invalid request to Unsplash API: {e}"
        tools.tool_error(error_message)
        return {"error": error_message}

@mcp.tool("get_photo_by_id")
def get_photo_by_id(photo_id: str) -> dict:
    """
    Retrieves a specific photo by its Unsplash ID. 🆔

    Use this tool when you already have the unique identifier for an Unsplash photo
    and need to fetch its detailed information.

    :param photo_id: The unique ID of the Unsplash photo (e.g., "unsplash_photo_id_example").
    :return: A dictionary containing the detailed information for the specified photo.
             Includes URLs, dimensions, descriptions, and photographer details.
    """
    params = {
        "client_id": UNSPLASH_ACCESS_KEY
    }

    try:
        response = requests.get(f"{UNSPLASH_API_BASE_URL}/photos/{photo_id}", params=params)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.HTTPError as e:
        error_message = f"Failed to retrieve photo by ID '{photo_id}'. Status: {e.response.status_code}, Details: {e.response.text}"
        tools.tool_error(error_message)
        return {"error": error_message}
    except requests.exceptions.RequestException as e:
        error_message = f"Network error or invalid request to Unsplash API: {e}"
        tools.tool_error(error_message)
        return {"error": error_message}


if __name__ == "__main__":
    # For Cloud Run, the port is specified by the PORT environment variable.
    # Default to 8080 for local development.
    port = int(os.getenv("PORT", 8080))
    # For Cloud Run, we need to listen on all interfaces (0.0.0.0).
    host = "0.0.0.0" if os.getenv("PORT") else "127.0.0.1"
    mcp.run(transport="http",
            host=host,
            port=port,
            log_level="debug")