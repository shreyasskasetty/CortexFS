import os
import json
import shutil
import agentops
from pathlib import Path
from typing import Optional
import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from src.organizer import DirectoryOrganizer
from src.summarizer import FileSummarizer
from src.watchdog import FileEventProducer
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,  # Set the desired level: DEBUG, INFO, WARNING, ERROR, CRITICAL
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
load_dotenv()

# Initialize AgentOps
agentops.init(default_tags=["llama-fs"], auto_start_session=False, api_key=os.getenv("AGENTOPS_API_KEY"))


class Request(BaseModel):
    path: Optional[str] = None
    instruction: Optional[str] = None
    private: Optional[bool] = False


class CommitRequest(BaseModel):
    base_path: str
    src_path: str  
    dst_path: str 

class WatchRequest(BaseModel):
    watch_directory: str
    target_directory: str

def create_app():
    app = FastAPI()
    
    origins = ["*"]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize classes
    organizer = DirectoryOrganizer(
        base_dir=None,  # Base directory will be set dynamically
        model_name="llama-3.1-70b-versatile"
    )

    summarizer = FileSummarizer(
        base_path=None,  # Base path will be set dynamically
        azure_api_key=os.getenv("AZURE_API_KEY"),
        tessdata_prefix=os.getenv("TESSDATA_PREFIX"),
    )

    producer = FileEventProducer(
        organizer=organizer,
        summarizer=summarizer,
        rabbitmq_url=os.getenv("RABBITMQ_URL"),
        queue_name="suggestion-notifications",
        logger=logger
    )

    @app.get("/")
    def health_check():
        return {"status": "ok"}

    @app.post("/batch-organize")
    async def batch_organize(request: Request):
        session = agentops.start_session(tags=["LlamaFS"])
        path = request.path

        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="Path not found")

        print("Loading documents...")
        summarizer.base_path = path
        documents, unsupported_files = summarizer.load_documents()

        print(f"Summarizing {len(documents)} documents...")
        summaries = await summarizer.summarize_documents(documents)

        print("Generating reorganization actions...")
        organizer.base_dir = path
        file_moves = organizer.get_reorganization_actions(summaries)

        print("Creating directory structure...")
        tree = organizer.create_directory_structure(file_moves["files"], summaries, path, agentops=session)

        # Add summaries to the file moves
        files = file_moves["files"]
        for file in files:
            file["summary"] = summaries[files.index(file)]["summary"]

        print("Converting tree structure for response...")
        response_data = organizer.convert_to_tree_with_details(files, base_path=path)

        return {"status": "ok", "treeStructure": response_data}

    @app.post("/commit")
    async def commit(request: CommitRequest):
        print('*'*80)
        print(request)
        print(request.base_path)
        print(request.src_path)
        print(request.dst_path)
        print('*'*80)

        src = os.path.join(request.base_path, request.src_path)
        dst = os.path.join(request.base_path, request.dst_path)

        if not os.path.exists(src):
            raise HTTPException(
                status_code=400, detail="Source path does not exist in filesystem"
            )

        # Ensure the destination directory exists
        dst_directory = os.path.dirname(dst)
        os.makedirs(dst_directory, exist_ok=True)

        try:
            # If src is a file and dst is a directory, move the file into dst with the original filename.
            if os.path.isfile(src) and os.path.isdir(dst):
                shutil.move(src, os.path.join(dst, os.path.basename(src)))
            else:
                shutil.move(src, dst)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"An error occurred while moving the resource: {e}"
            )

        return {"message": "Commit successful"}

    @app.post("/start-producer")
    async def start_producer(request: WatchRequest):
        """
        Start the file event producer with the given directory to watch.
        """
        directory_to_watch = request.watch_directory
        target_directory = request.target_directory
        # producer.connect_to_rabbitmq()
        try:
            await asyncio.to_thread(producer.start_monitoring, directory_to_watch, target_directory)
            return {"status": "Producer started", "directory": directory_to_watch}
        except FileNotFoundError as e:
            await producer.connection.close()
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.error(f"Failed to start producer: {e}")
            await producer.connection.close()
            raise HTTPException(status_code=500, detail=f"Failed to start producer: {str(e)}")

    @app.on_event("startup")
    async def startup_event():
        producer.initialize_event_loop_thread()
        await producer.connect_to_rabbitmq()

    @app.on_event("shutdown")
    async def shutdown_event():
        producer.stop_event_loop()
        if producer.connection:
            await producer.connection.close()

    @app.post("/stop-producer")
    async def stop_producer():
        """
        Stop the file event producer.
        """
        try:
            await asyncio.to_thread(producer.stop_monitoring)
            return {"status": "Producer stopped"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to stop producer: {e}")

    return app


if __name__ == "__main__":
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
