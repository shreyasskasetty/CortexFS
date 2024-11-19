import asyncio
import json
import os
from collections import defaultdict
import agentops
import base64
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.chat_models import ChatOllama
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyMuPDFLoader,
    AzureAIDocumentIntelligenceLoader,
    UnstructuredImageLoader,
)
from src.prompts import IMAGE_SUMMARY_PROMPT, DOCUMENT_SUMMARY_PROMPT
import ollama
import pandas as pd
from dotenv import load_dotenv
import warnings
import os
os.environ['TESSDATA_PREFIX'] = '/opt/anaconda3/share/tessdata'

warnings.filterwarnings("ignore")
load_dotenv()
# Supported extensions for categorization
SUPPORTED_EXTENSIONS = {
    "images": {"png", "jpeg", "jpg", "heic"},
    "pdfs": {"pdf"},
    "coding_files": {"c", "py", "java", "cpp", "go"},
    "microsoft_files": {"docx", "pptx", "xlsx"},
    "csv": {"csv"},
    "misc": {"txt", "sh", "log"},
}

def categorize_files(file_path):
    files = [
        f
        for f in os.listdir(file_path)
        if os.path.isfile(os.path.join(file_path, f))
    ]
    file_extensions = [(os.path.splitext(f)[1][1:].lower(), f) for f in files]

    categorized_files = {key: [] for key in SUPPORTED_EXTENSIONS.keys()}
    unsupported_files = []

    for ext, fname in file_extensions:
        categorized = False
        for category, extensions in SUPPORTED_EXTENSIONS.items():
            if ext in extensions:
                categorized_files[category].append(fname)
                categorized = True
                break
        if not categorized:
            unsupported_files.append(fname)

    return categorized_files, unsupported_files

def preprocess_csv(file_path):
    """Extract headers from CSV."""
    df = pd.read_csv(file_path)
    headers = df.columns
    return ", ".join(headers)

def encode_image(image_path):
    """Encode image as base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def process_file(file_path, category):
    """Process files based on their category."""
    if category == "images":
        # Process images
        base64_image = encode_image(file_path)
        return base64_image
    
    elif category == "pdfs":
        # Process PDFs
        loader = PyMuPDFLoader(file_path)
        pages = loader.load()
        content = []
        for page in pages[:5]:  # Limit to first 5 pages
            if page.page_content.strip():  # Check for meaningful content
                content.append(page.page_content)
        return "\n\n".join(content) if content else "No meaningful content found in the PDF."
    elif category == "coding_files":
        # Process code files
        with open(file_path, "r") as file:
            return file.read()
    elif category == "microsoft_files":
        # Process MS Office files (Example for PPTX)
        loader = AzureAIDocumentIntelligenceLoader(
            api_endpoint="https://cortexfs.cognitiveservices.azure.com/",  # Replace with actual endpoint
            api_key=os.getenv("AZURE_API_KEY"),       # Replace with actual API key
            file_path=file_path,
            api_model="prebuilt-layout",
        )
        pages = loader.load()
        content = []
        for page in pages[:5]:  # Limit to first 5 pages
            if page.page_content.strip():  # Check for meaningful content
                content.append(page.page_content)
        return "\n\n".join(content) if content else "No meaningful content found in the Microsoft file."
    
    elif category == "csv":
        # Process CSV files
        return preprocess_csv(file_path)
    elif category == "misc":
        # Process miscellaneous files
        with open(file_path, "r") as file:
            return file.read()
    return None

def load_documents_from_directory(base_path):
    categorized_files, unsupported_files = categorize_files(base_path)
    documents = []

    for category, files in categorized_files.items():
        for fname in files:
            full_path = os.path.join(base_path, fname)
            content = process_file(full_path, category)
            if content:
                documents.append(
                    Document(
                        page_content=content,
                        metadata={"file_name": fname, "source": base_path, "category": category},
                    )
                )

    return documents, unsupported_files

async def get_summaries(documents):
    print("Dispatching document summarizers...")
    summaries = await asyncio.gather(
        *[dispatch_document_summarizer(doc) for doc in documents]
    )
    
    return summaries

def dispatch_document_summarizer(doc):
    if doc.metadata["category"] == "images":
        print(f"Summarizing image {doc.metadata['source']}...")
        return summarize_image(doc)
    else:
        print(f"Summarizing document {doc.metadata['source']}...")
        return summarize_document(doc)

async def summarize_image(doc):
    """Make image summary"""
    chat =  ChatOllama(model="llava")

    
    image_url = f"data:image/jpeg;base64,{doc.page_content}"
    msg = await chat.ainvoke(
        [
            HumanMessage(
                content=[
                    {"type": "text", "text": IMAGE_SUMMARY_PROMPT + "file name: " + doc.metadata["file_name"]},
                    {"type": "image_url", "image_url": image_url},
                ]
            )
        ]
    )
    summary = {
        "file_path": doc.metadata["file_name"],
        "summary": msg.content,
    }
    return summary

async def summarize_document(doc):
    chat = ChatOllama(model="llama3.2")
    msg = await chat.ainvoke(
        [
            SystemMessage(
                content=[
                    {"type": "text", "text": DOCUMENT_SUMMARY_PROMPT},
                ]
            ),
            HumanMessage(
                content=[
                    {"type": "text", "text": json.dumps({"text": doc.page_content, "file_path": doc.metadata["source"], "category": doc.metadata["category"]})},
                ]
            )
        ]
    )

    summary = {
        "file_path": doc.metadata["file_name"],
        # "base_path": doc.metadata["source"],
        "summary": msg.content,
    }
    return summary

# Example usage
file_path = "files"
async def main():
    documents, unsupported_files = load_documents_from_directory(file_path)
    summaries = await get_summaries(documents)
    print(summaries)
    print(f"Loaded {len(documents)} documents.")
    if unsupported_files:
        print(f"Unsupported files: {unsupported_files}")

    print(documents[0].metadata)

if __name__ == "__main__":
    asyncio.run(main())