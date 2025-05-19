import sys
import json
from typing import Dict, List, Any, Optional
from textwrap import dedent
from litellm import completion
from rich.console import Console

class MissingFilesError(Exception):
    def __init__(self, missing_files: set):
        self.missing_files = missing_files
        message = f"{len(missing_files)} files missing from proposed structure"
        super().__init__(message)

def format_files_for_ai_context(file_info_list: List[Dict[str, Any]]) -> str:
    """Convert a list of file information dictionaries to a JSON string.
    
    Args:
        file_info_list: List of dictionaries containing file metadata
        
    Returns:
        A JSON string representation of the files
    """
    formatted_files = []
    
    for file_info in file_info_list:
        # Extract key details, handling optional fields
        formatted_file = {
            "path": file_info.get("path", ""),
            "last_modified": file_info.get("last_modified", ""),
            "content_sample": file_info.get("content_sample", "")
        }
        formatted_files.append(formatted_file)
    
    return json.dumps(formatted_files, indent=2)

def format_directories_for_ai_context(directories: List[str]) -> str:
    """Convert a list of directory paths to a JSON string.
    
    Args:
        directories: List of directory paths
        
    Returns:
        A JSON string representation of the directories
    """
    # Sort directories to group related paths
    sorted_dirs = sorted(directories)
    
    return json.dumps(sorted_dirs, indent=2)

def ai_generate_directory_structure(api_key: str, model: str, formatted_files: str, port: int, prompt: str = None) -> tuple:
    """Generate a directory structure for organizing files.
    
    Args:
        api_key: API key for the LLM service
        model: LLM model identifier
        formatted_files: JSON string containing file metadata
        port: Port number for Ollama API
        prompt: Optional additional instructions for the AI
        
    Returns:
        Tuple containing (directory_structure_object, user_message)
    """
    
    # Define the instructions for the directory structure generation
    directory_instructions = f"""
<task>
Based on the provided files, suggest a logical directory structure to improve organization.
</task>

<input_files>
{formatted_files}
</input_files>

<output_format>
Return ONLY a valid JSON object with a "directories" field containing an array of directory paths.
Each directory should be represented as a string with a path relative to the root.

Example:
{{
    "directories": [
    "code_files",
    "code_files/archives",
    "code_files/downloads",
    "text_files",
    "text_files/reports",
    "text_files/configs",
    "other_files"
    ]
}}
</output_format>

<constraints>
- Keep the directory structure practical (max 3-4 levels deep)
- Focus on creating a logical organization based on file types and purposes
- Consider common organizational patterns for the type of project detected
- Directories should be logical groupings that make navigation intuitive
- Don't create too many directories (aim for quality over quantity)
- Return ONLY the JSON object as specified, nothing else
</constraints>
"""

    # Add user's custom prompt if provided
    if prompt:
        directory_instructions += f"\n\n<additional_instructions>\n{prompt}\n</additional_instructions>"

    # Define the user message
    user_message = {
      "role": "user",
      "content": directory_instructions
    }

    # Get directory structure from AI
    completion_args = {
      "model": model,
      "api_key": api_key,
      "messages": [user_message],
      "temperature": 0.2,
      "response_format": {"type": "json_object"}
    }
    
    # Only use api_base for Ollama if port is specified
    if port is not None:
      completion_args["api_base"] = f"http://localhost:{port}/v1"  # Ollama API endpoint
      
    response = completion(**completion_args)
    
    return response, user_message

def ai_map_files_to_directories(api_key: str, model: str, formatted_files: str, formatted_directories: str, port: int, prompt: str = None) -> tuple:
    """Map files to the provided directory structure.
    
    Args:
        api_key: API key for the LLM service
        model: LLM model identifier
        formatted_files: JSON string containing file metadata
        formatted_directories: JSON string containing directory structure
        port: Port number for Ollama API
        prompt: Optional additional instructions for the AI
        
    Returns:
        Tuple containing (file_mapping_dict, user_message)
    """
    
    # Define the instructions for the file mapping
    mapping_instructions = f"""
<task>
Map each file to the most appropriate directory in the provided structure.
</task>

<input_files>
{formatted_files}
</input_files>

<available_directories>
{formatted_directories}
</available_directories>

<output_format>
Return ONLY a valid JSON object with:
- Keys: original file paths
- Values: new file paths that include an appropriate directory from the provided structure

Example:
{{
    "old_file.txt": "docs/old_file.txt",
    "utils.py": "src/utils/utils.py",
    "core.py": "src/core/core.py"
}}
</output_format>

<constraints>
- Every original file must have a corresponding new path
- Use only the directories provided in the available_directories list
- Maintain original filenames
- Group similar files in the same directory
- Consider file type, content, and purpose when deciding placement
</constraints>
"""

    # Add user's custom prompt if provided
    if prompt:
        mapping_instructions += f"\n\n<additional_instructions>\n{prompt}\n</additional_instructions>"

    # Define the user message
    user_message = {
      "role": "user",
      "content": mapping_instructions
    }

    # Get file mapping from AI
    completion_args = {
      "model": model,
      "api_key": api_key,
      "messages": [user_message],
      "temperature": 0.1,
      "response_format": {"type": "json_object"}
    }
    
    # Only use api_base for Ollama if port is specified
    if port is not None:
      completion_args["api_base"] = f"http://localhost:{port}/v1"  # Ollama API endpoint
      
    response = completion(**completion_args)
    
    return response, user_message

def ai_fix_missing_files(api_key: str, model: str, formatted_files: str, 
                        formatted_directories: str, file_mapping: Dict[str, str], 
                        missing_files: set, port: int, prompt: str = None) -> Dict[str, str]:
    """Ask the AI to include missing files in an incomplete file mapping.
    
    Args:
        api_key: API key for the LLM service
        model: LLM model identifier
        formatted_files: JSON string containing file metadata
        formatted_directories: JSON string containing directory structure
        file_mapping: The incomplete file mapping dictionary
        missing_files: Set of file paths missing from the mapping
        port: Port number for Ollama API
        prompt: Optional additional instructions for the AI
        
    Returns:
        Updated file mapping dictionary with missing files included
    """
    # Format the missing files as a string for the AI
    missing_files_str = "\n".join(missing_files)
    
    # Define the instructions for fixing the missing files
    fix_instructions = f"""
<task>
Add missing files to an incomplete file mapping.
</task>

<input_files>
{formatted_files}
</input_files>

<available_directories>
{formatted_directories}
</available_directories>

<current_mapping>
{json.dumps(file_mapping, indent=2)}
</current_mapping>

<missing_files>
{missing_files_str}
</missing_files>

<output_format>
Return ONLY a valid JSON object with:
- Keys: original file paths for ONLY the missing files
- Values: new file paths that include an appropriate directory from the provided structure

Example:
{{
    "missing_file1.txt": "docs/missing_file1.txt",
    "missing_file2.py": "src/utils/missing_file2.py"
}}
</output_format>

<constraints>
- Map ONLY the missing files listed above
- Use only the directories provided in the available_directories list
- Maintain original filenames
- Group similar files in the same directory as already mapped files
- Consider file type, content, and purpose when deciding placement
- Consider the patterns established in the current mapping
</constraints>
"""

    # Add user's custom prompt if provided
    if prompt:
        fix_instructions += f"\n\n<additional_instructions>\n{prompt}\n</additional_instructions>"

    # Define the user message
    user_message = {
      "role": "user",
      "content": fix_instructions
    }

    # Get file mapping from AI
    completion_args = {
      "model": model,
      "api_key": api_key,
      "messages": [user_message],
      "temperature": 0.1,
      "response_format": {"type": "json_object"}
    }
    
    # Only use api_base for Ollama if port is specified
    if port is not None:
      completion_args["api_base"] = f"http://localhost:{port}/v1"  # Ollama API endpoint
      
    response = completion(**completion_args)
    
    # Extract the fixed mapping from the response
    fixed_mapping = json.loads(response.choices[0].message.content)
    
    # Update the original mapping with the fixed entries
    updated_mapping = {**file_mapping, **fixed_mapping}
    
    return updated_mapping

def ai_generate_file_mapping(files: List[Dict[str, Any]], api_key: str, model: str, port: int, prompt: str = None, debug: bool = False, console: Optional[Console] = None) -> Dict[str, str]:
    """Generate a file mapping using a two-step approach: first create directories, then map files.
    
    Args:
        files: List of file dictionaries containing path, size, extension, and last_modified
        api_key: API key for the LLM service
        model: LLM model identifier
        port: Port number for Ollama API
        prompt: Optional additional instructions for the AI
        debug: Whether to print AI responses to stdout
        console: Rich console for output
        
    Returns:
        Dictionary mapping original file paths to proposed new paths
    """
    if console is None:
        console = Console()
        
    # Format the files for AI processing
    formatted_files_listing = format_files_for_ai_context(files)

    # Step 1: Generate directory structure
    directories_resp, dir_user_message = ai_generate_directory_structure(api_key, model, formatted_files_listing, port, prompt)
    directories = json.loads(directories_resp.choices[0].message.content).get("directories", [])
    formatted_directories = "\n".join(directories)
    
    if debug:
        console.print("\n=== [bold blue]AI Directory Structure - User Message[/bold blue] ===")
        console.print(dir_user_message["content"])
        console.print("\n=== [bold blue]AI Directory Structure - Response[/bold blue] ===")
        console.print_json(json.dumps(directories, indent=2))
    
    # Step 2: Map files to directories
    file_mapping_resp, mapping_user_message = ai_map_files_to_directories(api_key, model, formatted_files_listing, formatted_directories, port, prompt)
    file_mapping = json.loads(file_mapping_resp.choices[0].message.content)
    
    if debug:
        console.print("\n=== [bold blue]AI File Mapping - User Message[/bold blue] ===")
        console.print(mapping_user_message["content"])
        console.print("\n=== [bold blue]AI File Mapping - Response[/bold blue] ===")
        console.print_json(json.dumps(file_mapping, indent=2))
    
    return file_mapping

def validate_file_mapping(file_info_list: List[Dict[str, Any]], file_mapping: Dict[str, str], console: Console) -> None:
    """Validate that all files in file_info_list are included in the file mapping.
    
    Args:
        file_info_list: List of dictionaries containing file metadata
        file_mapping: Dictionary mapping original file paths to new paths
        console: Rich console for output
        
    Raises:
        MissingFilesError: If any files are missing from the mapping
        
    Returns:
        None
    """
    # Extract the original file paths from file_info_list
    original_paths = {file_info.get("path") for file_info in file_info_list if file_info.get("path")}
    
    # Get the keys from the file_mapping (original paths)
    mapped_paths = set(file_mapping.keys())
    
    # Find missing files (in original_paths but not in mapped_paths)
    missing_files = original_paths - mapped_paths
    
    # Find included files (in both original_paths and mapped_paths)
    included_files = original_paths.intersection(mapped_paths)

    return included_files, missing_files