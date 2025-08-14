

## Prerequisites

- **Python 3.8+**
- **Unsplash Access Key**: Some examples interact with the Unsplash API. You can get a free key from the [Unsplash Developer portal](https://unsplash.com/developers).

## General Setup
### Python Virtual Environment

Using a virtual environment is a best practice for Python projects to manage dependencies and isolate project-specific packages.

1.  **Create a virtual environment:**

    From your project's root directory, run one of the following commands to create a virtual environment folder named `venv`.

    *   **On macOS and Linux:**
        ```bash
        python3 -m venv venv
        ```

    *   **On Windows:**
        ```bash
        python -m venv venv
        ```

2.  **Activate the virtual environment:**

    *   **On macOS and Linux:**
        ```bash
        source venv/bin/activate
        ```

    *   **On Windows:**
        ```bash
        .\venv\Scripts\activate
        ```

    After activation, you will see `(venv)` at the beginning of your command prompt. All `pip` installations will now be local to this environment.

    
### Install Google Agent Development Kit (ADK)

Once your virtual environment is active, you can install the required Python packages. The Google ADK provides the necessary tools and libraries to build and run agents.

Install the `google-adk` package using pip:

    ```bash
    pip install google-adk
    ```

3.  **Verify the installation (Optional):**

    Run the following command to ensure that the `google-adk` package is installed correctly:

    ```bash
    pip show google-adk
    ```

## Learning Agents and Tools

The examples in this repository are designed to be followed in sequence to demonstrate a progression from a simple, direct API integration to a more robust, scalable, and production-ready architecture using a standalone tool server.

We recommend going through the examples in the following order:

1.  **Start with Direct API Integration (`photo_finder_api`)**

    This example shows the simplest way to give an agent a new capability: by writing a Python function that directly calls an external REST API. It's a great starting point for rapid prototyping.

    *   **Go to the example:** `photo_finder_api/README.md`

2.  **Build a Standalone Tool Server (`unsplash_mcp_server`)**

    This example refactors the direct API calls into a separate, reusable tool server using FastMCP. This decouples your tools from your agent, making them independently deployable and scalable. You will also learn how to deploy this server to Google Cloud Run.

    *   **Go to the example:** `unsplash_mcp_server/README.md`

3.  **Connect an Agent to the Tool Server (`photo_finder_mcp`)**

    Finally, this example shows how to modify the original agent to connect to the MCP tool server instead of calling the API directly. This demonstrates the recommended pattern for building production-grade agents with shared, robust tools.

    *   **Go to the example:** `photo_finder_mcp/README.md`

To begin, navigate to the `photo_finder_api` directory and follow the instructions in its `README.md` file.