import anyio
from fastmcp.client import Client
import pprint
import sys
import subprocess
import argparse

LOCAL_SERVER_URL = "http://127.0.0.1:8080/mcp/"

def get_project_number(project_id: str) -> str:
    """
    Derives the project number from the project ID using the gcloud CLI.

    Args:
        project_id: The Google Cloud project ID.

    Returns:
        The corresponding project number.

    Raises:
        SystemExit: If gcloud is not found or fails to retrieve the project number.
    """
    try:
        # Get project number
        result = subprocess.run(
            ["gcloud", "projects", "describe", project_id, "--format=value(projectNumber)"],
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        project_number = result.stdout.strip()
        if not project_number:
            raise ValueError(f"Could not derive project number for project ID: {project_id}")
        return project_number
    except FileNotFoundError:
        print("ERROR: 'gcloud' command not found. Please ensure the Google Cloud SDK is installed and in your PATH.", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to get project number using gcloud for project ID '{project_id}'.", file=sys.stderr)
        print(f"gcloud error: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred while getting project number: {e}", file=sys.stderr)
        sys.exit(1)

async def main():
    """
    Connects to the Unsplash MCP server and tests its tools.
    """
    parser = argparse.ArgumentParser(description="Test the Unsplash MCP server. Provide either --local or --project-id.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--local', action='store_true', help='Test against a local server.')
    group.add_argument('--project-id', type=str, help='The Google Cloud project ID to test the remote server.')

    args = parser.parse_args()

    if args.local:
        print("Testing against local server.")
        server_url = LOCAL_SERVER_URL
    else:
        print(f"Deriving project number for project ID: {args.project_id}...")
        project_number = get_project_number(args.project_id)
        print(f"Derived project number: {project_number}")
        server_url = f"https://unsplash-mcp-server-{project_number}.us-central1.run.app/mcp"
        print("Testing against remote server.")

    print(f"Connecting to server at {server_url}...")

    # Create a client to connect to the server.
    # The transport will be automatically inferred from the HTTPS URL.
    client = Client(server_url)

    try:
        async with client:
            await client.ping()
            print("Successfully connected to the server.")
            print("-" * 20)

            #list all tools offered by the mcp server
            print("Listing all tools:")
            tools = await client.list_tools()
            pprint.pprint(tools)
            print("-" * 20)

            # Test search_photos tool
            print("Testing 'search_photos' tool for 'cats'...")
            search_results_obj = await client.call_tool("search_photos", arguments={"query": "cats", "per_page": 3})
            search_results = search_results_obj.data
            pprint.pprint(search_results)
            print("-" * 20)

            # Test get_random_photo tool
            print("Testing 'get_random_photo' tool...")
            random_photo_obj = await client.call_tool("get_random_photo", arguments={"query": "nature"})
            random_photo = random_photo_obj.data
            pprint.pprint(random_photo)
            print("-" * 20)

            # Test get_photo_by_id tool (using an example ID or one from search results)
            if search_results and "results" in search_results and search_results["results"]:
                first_photo_id = search_results["results"][0]["id"]
                print(f"Testing 'get_photo_by_id' tool for ID: {first_photo_id}...")
                photo_details_obj = await client.call_tool("get_photo_by_id", arguments={"photo_id": first_photo_id})
                photo_details = photo_details_obj.data
                pprint.pprint(photo_details)
                print("-" * 20)
            else:
                print("Skipping 'get_photo_by_id' test as no search results were found.")
                print("-" * 20)

        
    except RuntimeError as e:
        if "Session terminated" in str(e):
            print("\n" + "="*60)
            print("ERROR: The client connected, but the server terminated the session immediately.")
        else:
            print(f"\nAn unexpected runtime error occurred: {e}")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

if __name__ == "__main__":
    anyio.run(main)