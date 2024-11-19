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
from src.organizer import convert_to_tree_with_details
from src.organizer import get_reorganization_actions, create_directory_structure
from src.summarizer import get_summaries
from src.summarizer import load_documents_from_directory
load_dotenv()

agentops.init(default_tags=["llama-fs"], auto_start_session=False, api_key=os.getenv("AGENTOPS_API_KEY"))
class Request(BaseModel):
    path: Optional[str] = None
    instruction: Optional[str] = None
    private: Optional[bool] = False


class CommitRequest(BaseModel):
    base_path: str
    src_path: str  # Relative to base_path
    dst_path: str  # Relative to base_path

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

        response_data = convert_to_tree_with_details(files, base_path=path)
        # Generate a tree structure of the summaries
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

    return app

if __name__ == "__main__":
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)