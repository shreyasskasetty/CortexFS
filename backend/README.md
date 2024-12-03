# CortexFS Backend Setup

The backend for CortexFS is implemented using FastAPI and requires several Python packages and tools to function. This document provides instructions to set up and run the backend.

---

## Prerequisites

Ensure the following are installed on your system:

1. **Python 3.9 or higher**  
2. **RabbitMQ** (for message-based communication)

---

## Required Python Packages

Below is a list of the required Python packages based on the code:

- `fastapi`: For creating RESTful API endpoints.
- `uvicorn`: For running the FastAPI server.
- `pydantic`: For data validation and models.
- `langchain_core`: For managing LLM interactions.
- `langchain_community`: For additional LLM features like ChatOllama.
- `langchain_groq`: For Groq-based LLM operations.
- `python-dotenv`: For managing environment variables.
- `aio-pika`: For asynchronous RabbitMQ communication.
- `watchdog`: For monitoring directory changes.
- `pandas`: For handling CSV preprocessing.
- `rich`: For visualizing directory structures in the terminal.
- `PyMuPDF`: For PDF document processing.
- `azure-ai-formrecognizer`: For processing Microsoft Office files.

---

## Setup Instructions

### Step 1: Clone the Backend Repository

```bash
git clone <backend-repo-link>
cd backend
```

### Step 2: Set Up a Virtual Environment (Optional)
It is recommended to use a virtual environment to manage dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Required Packages
Install the dependencies listed in the `requirements.txt` file:
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
```bash
RABBITMQ_URL=amqp://localhost  # RabbitMQ connection URL
AZURE_API_KEY=<your_azure_api_key>  # Azure AI Form Recognizer API key
TESSDATA_PREFIX=<path_to_tessdata>  # Optional, if using Tesseract for OCR
AGENTOPS_API_KEY=<your_agentops_api_key>  # Optional, for AgentOps integration
```

## Running the Backend

Start the backend server using python

```bash
python server.py
```
The backend will be available at `http://127.0.0.1:8000/`.


### Notes:
* Ensure RabbitMQ is running before starting the backend to avoid connection issues.
* For large file processing, ensure you have sufficient memory and processing power.