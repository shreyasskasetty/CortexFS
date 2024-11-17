import json
import os
from src.prompts import FILE_ORGANIZATION_PROMPT
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
# from langchain.output_parsers import JsonOutputParser
from pydantic import BaseModel
from typing import Optional, List
from pathlib import Path
from rich.tree import Tree
from rich import print as rprint

# def create_directory_tree(summaries: list, session):
#     client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
#     chat_completion = client.chat.completions.create(
#         messages=[
#             {"role": "system", "content": FILE_ORGANIZATION_PROMPT},
#             {"role": "user", "content": json.dumps(summaries)},
#         ],
#         model="llama-3.1-70b-versatile",
#         response_format={"type": "json_object"},  # Uncomment if needed
#         temperature=0,
#     )

#     file_tree = json.loads(chat_completion.choices[0].message.content)["files"]
#     return file_tree

class FileMove(BaseModel):
    src_path: str
    dst_path: str

class DirectoryTree(BaseModel):
    files: List[FileMove]


def get_reorganization_actions(summaries: list):
    chat_groq = ChatGroq(
        model="llama-3.1-70b-versatile",
        temperature=0,
    )
    
    # parser = JsonOutputParser(pydantic_object=DirectoryTree)
    
    structured_chat_groq = chat_groq.with_structured_output(DirectoryTree)
    
    messages = [
        SystemMessage(content=FILE_ORGANIZATION_PROMPT),
        HumanMessage(content=json.dumps(summaries))
    ]
    
    response = structured_chat_groq.invoke(messages)
    
    return response.dict()

def create_directory_structure(file_moves, summaries, base_path, agentops):
    """
    Create a directory tree dictionary from file paths and add summaries.

    Args:
        files (list): List of file objects with "dst_path" and optional metadata.
        summaries (list): List of summaries corresponding to the files.
        base_path (str): Base path to prepend to all "dst_path" values.

    Returns:
        list: Updated list of files with summaries and adjusted "dst_path".
    """
    # Initialize the root of the directory tree
    tree = {}

    # Build the tree structure
    for file, summary in zip(file_moves, summaries):
        # Split the destination path into parts
        parts = Path(file["dst_path"]).parts
        current = tree

        # Create nested dictionaries for the path parts
        for part in parts:
            current = current.setdefault(part, {})

        # Attach the summary to the final part of the path
        current["__summary__"] = summary["summary"]

        # Prepend base path to the destination path
        file["dst_path"] = str(Path(base_path) / file["dst_path"])
        file["summary"] = summary["summary"]

    # Convert tree structure into a visual representation
    root = Tree(base_path)
    add_to_tree_visual(tree, root)

    # Display the tree structure
    rprint(root)

    # End session and return updated files
    agentops.end_session(
        "Success", end_state_reason="Reorganized directory structure"
    )
    return tree

def add_to_tree_visual(tree, root_node):
    """
    Recursively add nodes to the rich.Tree visual representation.

    Args:
        tree (dict): The dictionary representing the directory structure.
        root_node (rich.tree.Tree): The root node of the visual tree.
    """
    for key, value in tree.items():
        if key == "__summary__":
            continue  # Skip the summary metadata
        # Add a new branch for the current directory or file
        child = root_node.add(key)
        # Recursively process subdirectories/files
        if isinstance(value, dict):
            add_to_tree_visual(value, child)
