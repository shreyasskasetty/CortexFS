import os
import json
import shutil
import agentops
from pathlib import Path
from typing import Optional
import uvicorn
from asciitree import LeftAligned
from asciitree.drawing import BOX_LIGHT, BoxStyle
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from src.organizer import get_reorganization_actions, create_directory_structure
from src.summarizer import get_summaries
from src.summarizer import load_documents_from_directory
load_dotenv()

agentops.init(default_tags=["llama-fs"], auto_start_session=False, api_key=os.getenv("AGENTOPS_API_KEY"))
class Request(BaseModel):
    path: Optional[str] = None
    instruction: Optional[str] = None
    private: Optional[bool] = False


def create_app():
    app = FastAPI()
    origins = [
        "*"
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
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
        print(os.getenv("GROQ_API_KEY"))
        print("Loading documents...")
        documents, unsupported_files = load_documents_from_directory(path)
        print(f"Summarizing {len(documents)} documents...")
        # Get summaries of all the files in the directory
        summaries = await get_summaries(documents)
        print("Generating reorganization actions...")
        file_moves = get_reorganization_actions(summaries)
        print(file_moves["files"])
        print("Creating directory structure...")
        tree = create_directory_structure(file_moves["files"], summaries, path, agentops=session)
        
        files = file_moves["files"]
        for file in files:
            file["summary"] = summaries[files.index(file)]["summary"]
        # Generate a tree structure of the summaries
        return {"status": "ok", "summaries": files}
    return app

if __name__ == "__main__":
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)