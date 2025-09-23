# Combined module to handle OAuth 2.0 flow, API calls, and define the ADK tool.

import json
import logging
import os
from typing import Union

import requests
from google.adk.auth import AuthConfig
from dotenv import load_dotenv
from google.adk.tools import ToolContext

# --- Configuration ---
# Load environment variables from a .env file
load_dotenv()

# The file to store user's access and refresh tokens.
# Created automatically when the authorization flow completes for the first time.
TOKEN_FILE = "token.json"

# Scopes define the level of access you are requesting.
# For the Routes API, 'cloud-platform' is required.
SCOPES = [
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/user.addresses.read",
    "https://www.googleapis.com/auth/userinfo.profile"
]

# The endpoint for the Compute Routes API
ROUTES_API_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"

# The endpoint for the Places API (Text Search)
PLACES_API_URL = "https://places.googleapis.com/v1/places:searchText"

# The endpoint for the People API
PEOPLE_API_URL = "https://people.googleapis.com/v1/people/me?personFields=names,addresses"

from .oauth_helper import get_user_credentials


# --- ADK Tool Definition ---
def get_directions(
    tool_context: ToolContext, origin: str, destination: str, travel_mode: str
) -> str:
  """Gets route information and step-by-step directions between an origin and a destination.

  This tool requires the user to sign in with their Google account to access
  the Google Maps Routes API.

  Args:
      tool_context: The context of the tool run, provided by the ADK.
      origin: The starting address (e.g., "Eiffel Tower, Paris, France").
      destination: The ending address (e.g., "Louvre Museum, Paris, France").
      travel_mode: The mode of travel. Must be one of: DRIVE, WALK, BICYCLE, TRANSIT.
  """
  logging.info(
      "Tool called: Getting directions from '%s' to '%s' via %s.",
      origin,
      destination,
      travel_mode,
  )
  client_id = os.getenv("GOOGLE_CLIENT_ID")
  client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
  redirect_uri = os.getenv("AGENT_REDIRECT_URI")


  if not all([client_id, client_secret, redirect_uri]):
    return "Error: OAuth Client ID, Secret, or Redirect URI is not configured in the .env file."

  creds: Union[AuthConfig, str, None] = get_user_credentials(
      tool_context=tool_context,
      client_id=client_id,
      client_secret=client_secret,
      redirect_uri=redirect_uri,
      scopes=SCOPES,
      credential_cache_key="route_planner_creds",
  )

  if isinstance(creds, AuthConfig) or creds is None:
    return "To get directions, I need you to sign in with your Google account first. Please follow the link to authorize me."

  # At this point, we have valid credentials. Make the API call.
  try:
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
    if not project_id:
      return "Error: GOOGLE_CLOUD_PROJECT_ID is not set in the environment."

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {creds.token}",
        "X-Goog-User-Project": project_id,
        "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.legs.steps.navigationInstruction",
    }
    payload = {
        "origin": {"address": origin},
        "destination": {"address": destination},
        "travelMode": travel_mode.upper(),
        "languageCode": "en-US",
    }

    response = requests.post(ROUTES_API_URL, headers=headers, data=json.dumps(payload))
    response.raise_for_status()
    route_data = response.json()

    if "error" in route_data or not route_data.get("routes"):
      return f"Sorry, I couldn't find a route from {origin} to {destination}. API response: {route_data.get('error', 'No routes found.')}"

    # Format the successful response into a single, user-friendly string.
    route = route_data["routes"][0]
    duration_seconds = int(route["duration"].removesuffix("s"))
    duration_minutes = round(duration_seconds / 60)
    distance_km = route["distanceMeters"] / 1000

    response_lines = [
        f"Directions from '{origin}' to '{destination}' by {travel_mode.lower()}:",
        f"  - Total Distance: {distance_km:.1f} km",
        f"  - Estimated Duration: about {duration_minutes} minutes.",
    ]

    if "legs" in route and route["legs"] and "steps" in route["legs"][0]:
      response_lines.append("  - Steps:")
      for i, step in enumerate(route["legs"][0]["steps"], 1):
        instruction = step.get("navigationInstruction", {}).get("instructions")
        if instruction:
          response_lines.append(f"    {i}. {instruction}")

    return "\n".join(response_lines)

  except requests.exceptions.HTTPError as e:
    logging.error(f"HTTP Error during API call: {e}")
    return f"I encountered an API error while trying to get directions: {e.response.text}"
  except Exception as e:
    logging.error(f"An unexpected error occurred in the tool: {e}", exc_info=True)
    return "Sorry, an unexpected error occurred while trying to get directions."


def get_address_of_place(tool_context: ToolContext, place_name: str) -> str:
  """
  Finds the full address and coordinates of a named place, like 'home', 'office', or a business name.

  Args:
      tool_context: The context of the tool run, provided by the ADK.
      place_name: The name of the place to find the address for (e.g., "Googleplex", "home", "office").

  Returns:
      A JSON string containing the formatted address and location (latitude/longitude) of the place, or an error message.
  """
  logging.info("Tool called: Getting address for '%s'.", place_name)

  client_id = os.getenv("GOOGLE_CLIENT_ID")
  client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
  redirect_uri = os.getenv("AGENT_REDIRECT_URI")


  if not all([client_id, client_secret, redirect_uri]):
    return "Error: OAuth Client ID, Secret, or Redirect URI is not configured in the .env file."

  creds: Union[AuthConfig, str, None] = get_user_credentials(
      tool_context=tool_context,
      client_id=client_id,
      client_secret=client_secret,
      redirect_uri=redirect_uri,
      scopes=SCOPES,
      credential_cache_key="route_planner_creds",
  )

  if isinstance(creds, AuthConfig) or creds is None:
    return "To find an address, I need you to sign in with your Google account first. Please follow the link to authorize me."

  # Handle special keywords "home" and "office" by calling the People API
  if place_name.lower() in ["home", "office"]:
    # Verify that the necessary scope was granted.
    people_api_scope = "https://www.googleapis.com/auth/user.addresses.read"
    if people_api_scope not in creds.scopes:
      return f"Error: The permission to read your address was not granted. Please sign in again and approve the request to access your address information."

    try:
      project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
      if not project_id:
        return "Error: GOOGLE_CLOUD_PROJECT_ID is not set in the environment."

      people_headers = {
          "Authorization": f"Bearer {creds.token}",
          "X-Goog-User-Project": project_id,
      }
      people_response = requests.get(PEOPLE_API_URL, headers=people_headers)
      people_response.raise_for_status()
      profile_data = people_response.json()

      if "addresses" in profile_data:
        for address in profile_data["addresses"]:
          addr_type = address.get("type", "").lower()
          if addr_type == place_name.lower():
            # People API does not return coordinates, so we can't get them here.
            # We will return the address and let the next step geocode it if needed.
            address_result = {
                "formattedAddress": address.get(
                    "formattedValue",
                    f"I found your {place_name} address, but it's not formatted correctly.",
                )
            }
            return json.dumps(address_result)
      return f"Sorry, I couldn't find a '{place_name}' address in your Google profile. Please provide a full address."
    except requests.exceptions.HTTPError as e:
      logging.error(f"HTTP Error during People API call: {e}")
      return f"I encountered an API error while trying to get your profile address: {e.response.text}"
    except Exception as e:
      logging.error(f"An unexpected error occurred in get_address_of_place for profile: {e}", exc_info=True)
      return "Sorry, an unexpected error occurred while trying to get your profile address."
  try:
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
    if not project_id:
      return "Error: GOOGLE_CLOUD_PROJECT_ID is not set in the environment."

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {creds.token}",
        "X-Goog-User-Project": project_id,
        "X-Goog-FieldMask": "places.formattedAddress,places.displayName,places.location",
    }
    payload = {"textQuery": place_name}

    response = requests.post(
        PLACES_API_URL, headers=headers, data=json.dumps(payload)
    )
    response.raise_for_status()
    places_data = response.json()

    if "error" in places_data or not places_data.get("places"):
      return f"Sorry, I couldn't find an address for '{place_name}'. The API returned: {places_data.get('error', 'No places found.')}"

    # Return the address of the first result
    first_place = places_data["places"][0]
    address_result = {
        "formattedAddress": first_place.get("formattedAddress", "Address not found."),
        "location": first_place.get("location")
    }
    return json.dumps(address_result)

  except requests.exceptions.HTTPError as e:
    logging.error(f"HTTP Error during Places API call: {e}")
    return f"I encountered an API error while trying to find the address: {e.response.text}"
  except Exception as e:
    logging.error(f"An unexpected error occurred in get_address_of_place: {e}", exc_info=True)
    return "Sorry, an unexpected error occurred while trying to find the address."


def search_nearby_places(
    tool_context: ToolContext, location: str, query: str, max_results: int = 5
) -> str:
  """
  Searches for places of a specific type near a given location.

  Args:
      tool_context: The context of the tool run, provided by the ADK.
      location: The address or name of the location to search near.
      query: The type of place to search for (e.g., "restaurant", "coffee shop", "park").
      max_results: The maximum number of results to return (default is 5).

  Returns:
      A formatted string listing the nearby places found, or an error message.
  """
  logging.info(
      "Tool called: Searching for '%s' near '%s'.", query, location
  )

  client_id = os.getenv("GOOGLE_CLIENT_ID")
  client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
  redirect_uri = os.getenv("AGENT_REDIRECT_URI")


  if not all([client_id, client_secret, redirect_uri]):
    return "Error: OAuth Client ID, Secret, or Redirect URI is not configured in the .env file."

  creds: Union[AuthConfig, str, None] = get_user_credentials(
      tool_context=tool_context,
      client_id=client_id,
      client_secret=client_secret,
      redirect_uri=redirect_uri,
      scopes=SCOPES,
      credential_cache_key="route_planner_creds",
  )

  if isinstance(creds, AuthConfig) or creds is None:
    return "To search for nearby places, I need you to sign in with your Google account first. Please follow the link to authorize me."

  try:
    # First, get the coordinates for the given location string.
    location_details_json = get_address_of_place(tool_context, location)
    try:
      location_details = json.loads(location_details_json)
      if "location" not in location_details:
        # This can happen if the address comes from the People API (home/work)
        # which doesn't provide coordinates. We need to re-run it through Places API.
        location_details_json = get_address_of_place(tool_context, location_details["formattedAddress"])
        location_details = json.loads(location_details_json)

      coordinates = location_details.get("location")
      if not coordinates or "latitude" not in coordinates or "longitude" not in coordinates:
        return f"Sorry, I could not find the exact coordinates for '{location}'."
    except (json.JSONDecodeError, TypeError):
      return f"Sorry, I could not find the location '{location}'. The address lookup returned: {location_details_json}"

    project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
    if not project_id:
      return "Error: GOOGLE_CLOUD_PROJECT_ID is not set in the environment."

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {creds.token}",
        "X-Goog-User-Project": project_id,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.rating",
    }

    payload = {
        "textQuery": query,
        "pageSize": min(max_results, 20), # API max is 20
        "locationBias": {
            "circle": {"center": coordinates, "radius": 500.0}
        },
    }

    logging.info(f"Sending payload: {json.dumps(payload)}")

    response = requests.post(PLACES_API_URL, headers=headers, data=json.dumps(payload))
    response.raise_for_status()
    places_data = response.json()

    if "error" in places_data or not places_data.get("places"):
      return f"Sorry, I couldn't find any '{query}' near '{location}'. API response: {places_data.get('error', 'No places found.')}"

    response_lines = [f"Here are some '{query}' options near '{location}':"]
    for place in places_data["places"]:
      rating = f" (Rating: {place.get('rating', 'N/A')})" if place.get('rating') else ""
      response_lines.append(f"  - {place.get('displayName', 'Unknown')}{rating}: {place.get('formattedAddress', 'No address available.')}")

    return "\n".join(response_lines)
  
  except requests.exceptions.HTTPError as e:
    logging.error(f"HTTP Error during Nearby Search API call: {e}")
    return f"I encountered an API error while trying to find nearby places: {e.response.text}"
  except Exception as e:
    logging.error(f"An unexpected error occurred in search_nearby_places: {e}", exc_info=True)
    return "Sorry, an unexpected error occurred while trying to find nearby places."
