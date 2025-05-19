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

def _format_files_for_ai_context(files: List[Dict[str, Any]]) -> str:
    """Format file metadata to a JSON string for AI processing.
    
    Args:
        files: List of file dictionaries containing path, size, extension, and last_modified
        
    Returns:
        JSON string with formatted file information
    """
    result = []
    
    for file in sorted(files, key=lambda x: x["path"]):
        file_info = {
            "path": file["path"],
            "size": file["size"],
            "type": file["extension"].lstrip("."),
            "last_modified": file["last_modified"],
            "content_sample": file["content_sample"]
        }
        result.append(file_info)
    
    return json.dumps(result, indent=2)

def _ai_analyze_file_tree(api_key: str, model: str, formatted_files: str, port: int, prompt: str = None) -> tuple:
    """Get AI analysis of the file structure.
    
    Args:
        api_key: API key for the LLM service
        model: LLM model identifier
        formatted_files: JSON string containing file metadata
        port: Port number for Ollama API
        prompt: Optional additional instructions for the AI
        
    Returns:
        Tuple containing (analysis_text, user_message)
    """
    
    # Define the instructions for the AI analysis phase
    analysis_instructions = dedent(f"""
    <task>
    Analyze the provided files and suggest a logical structure that would improve organization and maintainability.
    </task>

    <requirements>
    1. Analyze file types, sizes, timestamps, and naming patterns
    2. Identify potential functional groups or domains
    3. Consider organization strategies (domain/functionality, file purpose, file type)
    4. Provide brief reasoning for your suggested structure
    </requirements>

    <input_files>
    {formatted_files}
    </input_files>

    <output_format>
    Provide a concise analysis with:
    1. Short summary of file collection (key types and patterns)
    2. Core identified groups or categories
    3. Suggested directory structure with minimal justification
    </output_format>

    <constraints>
    - Keep suggested structure practical (max 3-4 levels deep)
    - Maintain original filenames
    - Prioritize maintainability and ease of navigation
    - Be concise and to the point - avoid unnecessary elaboration
    - Focus on the most important observations and recommendations
    </constraints>
    """)

    # Add user's custom prompt if provided
    if prompt:
        analysis_instructions += f"\n\n<additional_instructions>\n{prompt}\n</additional_instructions>"

    # Define the user message
    user_message = {
      "role": "user",
      "content": analysis_instructions
    }

    # Get analysis from AI
    completion_args = {
      "model": model,
      "api_key": api_key,
      "messages": [user_message],
      "temperature": 0.2
    }
    
    # Only use api_base for Ollama if port is specified
    if port is not None:
      completion_args["api_base"] = f"http://localhost:{port}/v1"  # Ollama API endpoint
      
    response = completion(**completion_args)
    
    return response.choices[0].message.content, user_message

def _ai_generate_file_mapping(api_key: str, model: str, formatted_files: str, analysis: str, port: int, prompt: str = None) -> tuple:
    """Create a mapping of original file paths to new paths based on analysis.
    
    Args:
        api_key: API key for the LLM service
        model: LLM model identifier
        formatted_files: JSON string containing file metadata
        analysis: Previous analysis text from the LLM
        port: Port number for Ollama API
        prompt: Optional additional instructions for the AI
        
    Returns:
        Tuple containing (file_mapping_dict, user_message)
    """
    
    mapping_instructions = dedent(f"""
    <task>
    Based on your previous analysis, create a specific file mapping JSON that reorganizes the files.
    </task>

    <previous_analysis>
    {analysis}
    </previous_analysis>

    <input_files>
    {formatted_files}
    </input_files>

    <output_format>
    Return ONLY a valid JSON object with:
    - Keys: original file paths
    - Values: suggested new file paths
    
    Example:
    {{
      "old/path/file.txt": "new/structured/path/file.txt",
      "random_name.py": "core/utilities/random_name.py"
    }}
    </output_format>

    <constraints>
    - Maintain original filenames
    - Ensure the structure matches your previous analysis
    - Don't suggest unnecessary nesting (max 3-4 levels deep)
    - The root directory of the proposed structure should be the same as the original structure
    - Every original file must have a corresponding new path
    </constraints>
    """)

    # Add user's custom prompt if provided
    if prompt:
        mapping_instructions += f"\n\n<additional_instructions>\n{prompt}\n</additional_instructions>"

    # Define the user message
    user_message = {
      "role": "user",
      "content": mapping_instructions
    }

    # Get mapping from AI
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
    
    return json.loads(response.choices[0].message.content), user_message

def validate_file_mapping(files: List[Dict[str, Any]], file_mapping: Dict[str, str], console=None) -> Dict[str, str]:
    """Validates that the proposed file mapping includes all original files.
    
    Args:
        files: List of file dictionaries containing path and other metadata
        file_mapping: Dictionary mapping original file paths to proposed new paths
        console: Optional rich console for output
        
    Returns:
        The validated file mapping
        
    Raises:
        MissingFilesError: If any files are missing from the proposed structure
    """
    if console is None:
        console = Console()
        
    # Check for missing files
    original_files = [file["path"] for file in files]
    proposed_files = file_mapping.keys()
    missing_files = set(original_files) - set(proposed_files)
    
    if missing_files:
        raise MissingFilesError(missing_files)
    
    return file_mapping

def build_file_mapping(files: List[Dict[str, Any]], api_key: str, model: str, debug: bool, console, port: int, prompt: str = None) -> Dict[str, str]:
    """Generate a proposal for reorganizing file structure.
    
    Args:
        files: List of file dictionaries containing path, size, extension, and last_modified
        api_key: API key for the LLM service
        model: LLM model identifier
        debug: Whether to print AI responses to stdout
        console: Rich console for output
        port: Port number for Ollama local inference
        prompt: Optional additional instructions for the AI
        
    Returns:
        Dictionary mapping original file paths to proposed new paths
    """
    if console is None:
        console = Console()
        
    # Format the files for AI processing
    formatted_files_listing = _format_files_for_ai_context(files)

    # Step 1: Analyze file structure
    analysis, analysis_user_message = _ai_analyze_file_tree(api_key, model, formatted_files_listing, port, prompt)
    if debug:
        console.print("\n=== [bold blue]AI Structure Analysis - User Message[/bold blue] ===")
        console.print(analysis_user_message["content"])
        console.print("\n=== [bold blue]AI Structure Analysis - Response[/bold blue] ===")
        console.print(analysis)
    
    # Step 2: Create file mapping based on analysis
    file_mapping, mapping_user_message = _ai_generate_file_mapping(api_key, model, formatted_files_listing, analysis, port, prompt)
    if debug:
        console.print("\n=== [bold blue]AI File Mapping - User Message[/bold blue] ===")
        console.print(mapping_user_message["content"])
        console.print("\n=== [bold blue]AI Proposed File Mapping - Response[/bold blue] ===")
        console.print_json(json.dumps(file_mapping, indent=2))
    
    return file_mapping