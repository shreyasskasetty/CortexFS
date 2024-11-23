import json
import os
from mimetypes import guess_type
from datetime import datetime
from pathlib import Path
from rich.tree import Tree
from rich import print as rprint
from pydantic import BaseModel
from typing import Optional, List
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from src.prompts import FILE_ORGANIZATION_PROMPT, FILE_MOVE_SUGGESTION_PROMPT

# Models
class FileMove(BaseModel):
    src_path: str
    dst_path: str

class DirectoryTree(BaseModel):
    files: List[FileMove]

class PathSuggestions(BaseModel):
    src_path: str
    suggestions: List[str]

# Class Definition
class DirectoryOrganizer:
    def __init__(self, base_dir: str, model_name: str, exclude_dirs=None):
        self.base_dir = base_dir
        self.model_name = model_name
        self.exclude_dirs = exclude_dirs if exclude_dirs else ["node_modules", ".cache", "build"]
        self.chat_groq = ChatGroq(model=model_name, temperature=0)

    def get_path_suggestions(self, dst_directory, summary: str):
        """
        Get path suggestions for a given summary.
        """
        dst_directies = self.get_directories(dst_directory)
        formatted_prompt = FILE_MOVE_SUGGESTION_PROMPT.format(destination_directories=json.dumps(dst_directies, indent=4))
        structured_chat_groq = self.chat_groq.with_structured_output(PathSuggestions)
        messages = [
            SystemMessage(content=formatted_prompt),
            HumanMessage(content=json.dumps(summary))
        ]
        response = structured_chat_groq.invoke(messages)
        return response.dict()
    
    def get_directories(self, dst_directory):
        """
        Recursively get all directory paths in the base directory, excluding specified directories.
        """
        directory_paths = []

        for root, dirs, _ in os.walk(dst_directory):
            # Modify dirs in-place to exclude specified directories
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]

            for directory in dirs:
                directory_paths.append(os.path.join(root, directory))

        return directory_paths
    
    def get_reorganization_actions(self, summaries: list):
        """
        Generate reorganization actions using the ChatGroq model.
        """
        structured_chat_groq = self.chat_groq.with_structured_output(DirectoryTree)
        messages = [
            SystemMessage(content=FILE_ORGANIZATION_PROMPT),
            HumanMessage(content=json.dumps(summaries))
        ]
        response = structured_chat_groq.invoke(messages)
        return response.dict()
    
    def create_directory_structure(self, file_moves, summaries, base_path, agentops):
        """
        Create a directory tree structure and add summaries for visualization.
        """
        tree = {}
        for file, summary in zip(file_moves, summaries):
            parts = Path(file["dst_path"]).parts
            current = tree
            for part in parts:
                current = current.setdefault(part, {})
            current["__summary__"] = summary["summary"]
            file["dst_path"] = file["dst_path"]
            file["summary"] = summary["summary"]

        root = Tree(base_path)
        self.add_to_tree_visual(tree, root)
        rprint(root)

        agentops.end_session("Success", end_state_reason="Reorganized directory structure")
        return tree
    
    def convert_to_tree_with_details(self, data, base_path):
        """
        Convert data into a tree structure with detailed file information.
        """
        def add_to_tree(tree, path_parts, file_data):
            if not path_parts:
                return
            
            current_part = path_parts[0]
            remaining_parts = path_parts[1:]
            
            child = next((child for child in tree["children"] if child["name"] == current_part), None)
            
            if not child:
                if remaining_parts:
                    child = {
                        "name": current_part,
                        "type": "folder",
                        "path": os.path.join(tree["path"], current_part),
                        "children": [],
                    }
                else:
                    src_abs_path = os.path.join(base_path, file_data["src_path"])
                    size = os.path.getsize(src_abs_path) if os.path.exists(src_abs_path) else "Unknown"
                    file_type = guess_type(src_abs_path)[0] or "Unknown"
                    last_modified = (
                        datetime.fromtimestamp(os.path.getmtime(src_abs_path)).strftime("%Y-%m-%d %H:%M:%S")
                        if os.path.exists(src_abs_path) else "Unknown"
                    )
                    child = {
                        "name": current_part,
                        "type": "file",
                        "path": os.path.join(tree["path"], current_part),
                        "summary": file_data["summary"],
                        "source": file_data["src_path"],
                        "destination": file_data["dst_path"],
                        "size": f"{size} bytes" if size != "Unknown" else size,
                        "lastModified": last_modified,  
                        "fileType": file_type,
                        "status": "Ready to move",
                    }
                tree["children"].append(child)
            
            if child["type"] == "folder":
                add_to_tree(child, remaining_parts, file_data)
        
        root_name = os.path.basename(base_path)
        root = {"name": root_name, "type": "folder", "path": root_name, "children": []}
        
        for item in data:
            dst_path = item["dst_path"]
            path_parts = dst_path.split("/")
            add_to_tree(root, path_parts, item)
        
        return root
    
    def add_to_tree_visual(self, tree, root_node):
        """
        Add nodes to a Rich Tree visual representation.
        """
        for key, value in tree.items():
            if key == "__summary__":
                continue
            child = root_node.add(key)
            if isinstance(value, dict):
                self.add_to_tree_visual(value, child)