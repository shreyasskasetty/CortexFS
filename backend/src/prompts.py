import json
IMAGE_SUMMARY_PROMPT = "Summarize the content of the image in a concise and descriptive manner for use in file system organization. The summary should identify the key elements, objects, or activities in the image and convey their purpose or context in 100 words. Avoid subjective interpretations, and focus on factual details and clarity. For example, include details like the type of image (e.g., photograph, diagram), the primary subjects or objects, notable actions or scenes, and any visible text or labels. Ensure the summary is neutral and helps in categorizing or retrieving the file effectively. Do not give any reasoning after the response. The response should just contain the summary in 100 words. Nothing else!"
DOCUMENT_SUMMARY_PROMPT = "Summarize the content of the document in a clear and concise manner, focusing on its key purpose and contents for efficient file system organization. The summary should include the type of document (e.g., program code, presentation, PDF, text file, log file), its primary topic or functionality, and any notable sections or elements (e.g., code modules, slide themes, main text topics, key log events). Highlight any critical features such as file format, specific functions, or unique content without subjective interpretations. Keep the summary within 100 words to ensure it is both precise and practical for categorization and retrieval. Do not give any reasoning after the response. The response should just contain the summary in 100 words. Nothing else!"
FILE_ORGANIZATION_PROMPT = """
You will be provided with a list of source files and a summary of their contents. For each file, propose a new directory path and filename that adhere to best practices for file organization and naming conventions. Ensure the proposed structure makes it easy to locate, manage, and version files effectively. 
Follow these guidelines:
1. **Context and Relationships**: Consider how the file relates to other files and group related files together in a logical directory hierarchy.
2. **Metadata Identification**: Extract relevant metadata (e.g., date, type, version, project name) from the summary or filename to include in the path or filename.
3. **Abbreviation and Encoding**: Use clear abbreviations or encoded metadata to save space while preserving clarity.
4. **Version Control**: If applicable, include version numbers or identifiers in the filenames.
5. **Search Optimization**: Place the most critical information (e.g., project name, type, or date) at the beginning of the filename to facilitate sorting and searching.
6. **Avoid Special Characters and Spaces**: Use underscores (`_`) or hyphens (`-`) to separate elements, and avoid spaces or special characters.
7. **Preserve Well-Named Files**: If a file already follows these conventions or matches a known standard, keep the destination path the same as the source path.
8. **Consistency**: Maintain consistency across all proposed paths and filenames.
9. **File Name Length**: Maximum of 2 to 3 words can be used to create the file name.

**Output Requirements:**
- Return a JSON object with the following schema:
```json
{
    "files": [
        {
            "src_path": "original file path",
            "dst_path": "new file path under proposed directory structure with proposed file name"
        }
    ]
}
```
- Ensure each `dst_path` reflects the improved organization and naming conventions, unless the file is already well-named, in which case the `dst_path` should match the `src_path`.
""".strip()

FILE_MOVE_SUGGESTION_PROMPT="""
You will be provided with a file and its summary content. Suggest 3 possible destination directory paths, which is most appropriate for the file based on its content and purpose. Consider the following factors when proposing the new directory path:
1. **Content Relevance**: Ensure the directory path reflects the content and purpose of the file for easy retrieval and categorization.
2. **Contextual Relationship**: Place the file in a directory that relates to its content, project, or function.
3. **Metadata Inclusion**: Include relevant metadata (e.g., date, version, project name) in the directory path to provide additional context.
4. **Search Optimization**: Position the file in a directory that facilitates quick search and retrieval based on key information.
5. **Consistency**: Maintain consistency with existing directory structures and naming conventions.
6. **File Type Identification**: Use the file type or category to determine the appropriate directory path.
7. **Version Control**: If applicable, consider version numbers or identifiers in the directory path.
8. **Abbreviation and Encoding**: Use clear abbreviations or encoded metadata to save space while preserving clarity.
9. **Limit the file name length**: Maximum of 2 to 3 words can be used to create the file name.

**Destination Directory paths**:
{destination_directories}
**Output Requirements:**
- Return a JSON object with the following schema:
```json
{{
    "src_path": "original file path",
    "suggestions": [
        "suggested path 1",
        "suggested path 2",
        "suggested path 3"
    ]
}}
```
"""
