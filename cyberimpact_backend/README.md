# CyberImpact Backend

This is the FastAPI backend for the CyberImpact security scanning application. It handles repository cloning and will eventually run security analysis tools.

## Prerequisites

- Python 3.8+
- pip
- git

## Setup

1.  **Navigate to the backend directory:**
    ```bash
    cd cyberimpact_backend
    ```

2.  **Create a virtual environment:**
    It is recommended to use a virtual environment to manage dependencies.
    ```bash
    python3 -m venv venv
    ```

3.  **Activate the virtual environment:**
    - On Linux/macOS:
        ```bash
        source venv/bin/activate
        ```
    - On Windows:
        ```bash
        .\venv\Scripts\activate
        ```

4.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Running the Server

Start the development server with hot-reloading enabled:

```bash
uvicorn main:app --reload --port 8000
```

The server will be running at `http://localhost:8000`.

## API Endpoints

### `POST /scan/clone`

Clones a GitHub repository to a unique temporary directory on the server.

**Request Body:**

```json
{
  "repo_url": "https://github.com/username/repo.git"
}
```

**Response:**

```json
{
  "message": "Repository cloned successfully",
  "temp_path": "/tmp/cyberimpact_scan_xyz123",
  "repo_url": "https://github.com/username/repo.git"
}
```

## Project Structure

- `main.py`: The entry point for the FastAPI application.
- `requirements.txt`: List of Python dependencies.
