# Agentic Gemini

Agentic Gemini is an exploratory repository demonstrating multi-agent workflows using the `AG2` (autogen) framework and Google's Gemini models (via AI Studio).

The primary objective is to provide a hands-on, runnable example of various agent patterns, from simple code execution and group chats to complex, human-in-the-loop validation, all running securely within a Docker environment.

## Table of Contents

- [Agentic Gemini](#agentic-gemini)
- [Table of Contents](#table-of-contents)
- [Getting Started](#getting-started)

  - [Prerequisites](#prerequisites)
  - [Configuration](#configuration)
  - [Running the Application (Docker)](#running-the-application-docker)
  - [Local Development Setup (Optional)](#local-development-setup-optional)

- [Acknowledgement](#acknowledgement)

## Getting Started

Follow these instructions to get a copy of the project up and running on your local machine.

### Prerequisites

You will need the following tools installed on your system:
- Git
- Python 3.11+
- Docker Engine

### Configuration

The application requires a Google Gemini API key. This project uses a `.gitignore` to protect your keys, so you must create two files:

1.  **`config.json`**:
    Create this file in the root directory, using `sample_config.json` as a template. This file will contain your actual API key.

    ```json
    [
      {
        "model": "gemini-2.5-flash-lite",
        "api_key": "your-AI-Studio-API-key-goes-here",
        "api_type": "google"
      }
    ]
    ```

2.  **`config_path.json`**:
    Create this file in the root directory, using `sample_config_path.json` as a template. This file tells the application where to find your `config.json`. For this project, you can just set it to `config.json`.

    ```json
    {
      "config_path": "config.json"
    }
    ```

### Running the Application (Docker)

This is the recommended way to run the application. It ensures a consistent, secure, and isolated environment.

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/Agentic-Gemini.git](https://github.com/your-username/Agentic-Gemini.git)
    cd Agentic-Gemini
    ```

2.  **Build the Docker image:**
    This command reads the `Dockerfile` and builds a local image named `agentic-gemini`.
    ```bash
    docker build -t agentic-gemini .
    ```

3.  **Run the application:**
    This command runs the app interactively.

    -   The `-v /var/run/docker.sock:/var/run/docker.sock` flag is **required**; it allows the agent inside the container to spawn new Docker containers for code execution.

    -   The `-v "/your/target/directory":"/my_files"` flag is **required for Mode 5**. This mounts your local directory (e.g., `~/Documents`) into the container at `/my_files`, allowing the agent to find, read, edit, and run files.

        -   **Note:** This flag must be **read-write** (without the `:ro` suffix). The agent needs write-access to this directory to create the temporary scripts it uses for code execution, even if you do not plan to edit your original files.

    ```bash
    docker run -it --rm -v /var/run/docker.sock:/var/run/docker.sock -v "/your/local/directory":"/my_files" agentic-gemini
    ```

### Local Development Setup (Optional)

If you want to edit the code locally with IDE support (like linting and code completion in VS Code), you should set up a local virtual environment.

1.  **Navigate to the project directory:**
    ```bash
    cd Agentic-Gemini
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    ```

3.  **Activate the environment:**
    -   **Linux/macOS:**
        ```bash
        source venv/bin/activate
        ```
    -   **Windows (PowerShell):**
        ```bash
        .\venv\Scripts\Activate.ps1
        ```

4.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    You can now open the folder in your IDE. Remember to run the application using the **Docker commands** above.

## Acknowledgement

This project is built upon the `AG2` (autogen) framework.

-   [ag2ai/ag2 Repository](https://github.com/ag2ai/ag2)