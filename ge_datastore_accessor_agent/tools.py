import os
import requests
from google.auth import default
from google.auth import transport
from google.adk.tools import ToolContext, FunctionTool

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")
DATA_STORE_ID = os.getenv("DATA_STORE_ID")
AUTH_NAME = os.getenv("AUTH_NAME")

class DatastoreService:
    def __init__(self, access_token: str):
        self.access_token = None
        if access_token: 
            self.access_token = access_token
        else: 
            creds, project_id = default()
            auth_req = transport.requests.Request()  # Use google.auth here
            creds.refresh(auth_req)
            access_token = creds.token
            self.access_token = access_token


    def search_datastore(self, project_id, location, datastore_id, query):
        # Define API endpoint and headers
        url = f"https://{location}-discoveryengine.googleapis.com/v1alpha/projects/{project_id}/locations/{location}/collections/default_collection/dataStores/{datastore_id}/servingConfigs/default_search:search"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        # Define request data with placeholders for query
        data = {
            "query": f"{query}",
            "pageSize":10,
            "queryExpansionSpec":{"condition":"AUTO"},
            "spellCorrectionSpec":{"mode":"AUTO"},
            "relevanceScoreSpec":{"returnRelevanceScore":True},
            "languageCode":"en-US",
            "contentSearchSpec":{"snippetSpec":{"returnSnippet":True}},
            "naturalLanguageQueryUnderstandingSpec":{"filterExtractionCondition":"ENABLED"},
            "userInfo":{"timeZone":"Europe/Warsaw"}
            }

        # Make POST request
        response = requests.post(url, headers=headers, json=data)
        resp = response.json()
        print(resp)
        return resp


def search_datastore_records(query: str, tool_context: ToolContext):
        """
        Searches the connected secure corporate datastore for information related to the query.
        
        Args:
            query (str): The search query string describing what information to look for in the datastore.

        Returns:
            dict: The search results from the datastore in JSON format. Do not guess information, only use what is returned here.
        """
        datastore_service = None
        
        # Log the keys in the tool context state for debugging in Logs Explorer
        state_dict = tool_context.state.to_dict()
        print(f"DEBUG: tool_context.state keys: {list(state_dict.keys())}")
        
        access_token = tool_context.state.get(AUTH_NAME)
        
        if access_token:
            print(f"DEBUG: Successfully found token at key: {AUTH_NAME}")
        else:
            print(f"DEBUG: Could not find token at key: {AUTH_NAME}")
            access_token = ""

        datastore_service = DatastoreService(access_token)
        # Call the search method of the DatastoreService with the project ID, App Engine ID, and query
        results = datastore_service.search_datastore(PROJECT_ID, LOCATION, DATA_STORE_ID, query) 
        # Return the search results
        return results

datastore_search_tool = FunctionTool(func=search_datastore_records)
