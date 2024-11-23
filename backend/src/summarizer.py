import asyncio
import json
import os
import warnings
import base64
from collections import defaultdict
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.chat_models import ChatOllama
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyMuPDFLoader,
    AzureAIDocumentIntelligenceLoader,
)
from src.prompts import DOCUMENT_SUMMARY_PROMPT, IMAGE_SUMMARY_PROMPT
import pandas as pd

warnings.filterwarnings("ignore")
load_dotenv()

SUPPORTED_EXTENSIONS = {
    "images": {"png", "jpeg", "jpg", "heic"},
    "pdfs": {"pdf"},
    "coding_files": {"c", "py", "java", "cpp", "go", "sql", "html", "js", "css", "ts"},
    "microsoft_files": {"docx", "pptx", "xlsx"},
    "csv": {"csv"},
    "json": {"json", "geojson"},
    "misc": {"txt", "sh", "log", "md", "yaml", "yml", "xml"},
}


class FileSummarizer:
    def __init__(self, base_path, azure_api_key, tessdata_prefix=None):
        self.base_path = base_path
        self.azure_api_key = azure_api_key
        if tessdata_prefix:
            os.environ["TESSDATA_PREFIX"] = tessdata_prefix
    
    def get_file_category(self, file_path):
        ext = os.path.splitext(file_path)[1][1:].lower()
        for category, extensions in SUPPORTED_EXTENSIONS.items():
            if ext in extensions:
                return category
        return None
    
    def categorize_files(self):
        files = [
            f
            for f in os.listdir(self.base_path)
            if os.path.isfile(os.path.join(self.base_path, f))
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

    def preprocess_csv(self, file_path):
        """Extract headers from CSV."""
        df = pd.read_csv(file_path)
        headers = df.columns
        return ", ".join(headers)

    def encode_image(self, image_path):
        """Encode image as base64."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def process_file(self, file_path, category):
        """Process files based on their category."""
        if category == "images":
            return self.encode_image(file_path)
        elif category == "pdfs":
            loader = PyMuPDFLoader(file_path)
            pages = loader.load()
            content = [page.page_content for page in pages[:5] if page.page_content.strip()]
            return "\n\n".join(content) if content else "No meaningful content found in the PDF."
        elif category == "coding_files":
            with open(file_path, "r") as file:
                return file.read()
        elif category == "microsoft_files":
            loader = AzureAIDocumentIntelligenceLoader(
                api_endpoint="https://cortexfs.cognitiveservices.azure.com/",
                api_key=self.azure_api_key,
                file_path=file_path,
                api_model="prebuilt-layout",
            )
            pages = loader.load()
            content = [page.page_content for page in pages[:5] if page.page_content.strip()]
            return "\n\n".join(content) if content else "No meaningful content found in the Microsoft file."
        elif category == "csv":
            return self.preprocess_csv(file_path)
        elif category == "json":
            with json.load(file_path) as file:
                return json.dumps(file, indent=4)
        elif category == "misc":
            with open(file_path, "r") as file:
                return file.read()
        return None

    def load_documents(self):
        categorized_files, unsupported_files = self.categorize_files()
        documents = []

        for category, files in categorized_files.items():
            for fname in files:
                full_path = os.path.join(self.base_path, fname)
                content = self.process_file(full_path, category)
                if content:
                    documents.append(
                        Document(
                            page_content=content,
                            metadata={"file_name": fname, "source": self.base_path, "category": category},
                        )
                    )

        return documents, unsupported_files

    async def summarize_documents(self, documents):
        tasks = [self.summarize_document(doc) for doc in documents]
        return await asyncio.gather(*tasks)

    async def summarize_document(self, doc):
        if doc.metadata["category"] == "images":
            return await self.summarize_image(doc)
        else:
            return await self.summarize_text_document(doc)

    async def summarize_image(self, doc):
        chat = ChatOllama(model="llava")
        image_url = f"data:image/jpeg;base64,{doc.page_content}"
        msg = await chat.ainvoke(
            [
                HumanMessage(
                    content=[
                        {"type": "text", "text": f"{doc.metadata['file_name']}" + "\n" + IMAGE_SUMMARY_PROMPT},
                        {"type": "image_url", "image_url": image_url},
                    ]
                )
            ]
        )
        return {"file_path": doc.metadata["file_name"], "summary": msg.content}

    async def summarize_text_document(self, doc):
        chat = ChatOllama(model="llama3.2")
        msg = await chat.ainvoke(
            [
                SystemMessage(content=[{"type": "text", "text": DOCUMENT_SUMMARY_PROMPT}]),
                HumanMessage(
                    content=[
                        {"type": "text", "text": json.dumps({"text": doc.page_content, "category": doc.metadata["category"]})},
                    ]
                ),
            ]
        )
        return {"file_path": doc.metadata["file_name"], "summary": msg.content}


# Example Usage
async def main():
    file_summarizer = FileSummarizer(base_path="files", azure_api_key=os.getenv("AZURE_API_KEY"))
    documents, unsupported_files = file_summarizer.load_documents()
    summaries = await file_summarizer.summarize_documents(documents)
    
    print("Summaries:")
    for summary in summaries:
        print(summary)
    if unsupported_files:
        print(f"Unsupported files: {unsupported_files}")


if __name__ == "__main__":
    asyncio.run(main())
