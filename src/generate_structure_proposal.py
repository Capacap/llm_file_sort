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

def format_files_for_ai(files: List[Dict[str, Any]]) -> str:
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

def analyze_files_structure(api_key: str, model: str, formatted_files: str) -> str:
    """Get AI analysis of the file structure.
    
    Args:
        api_key: API key for the LLM service
        model: LLM model identifier
        formatted_files: JSON string containing file metadata
        
    Returns:
        Analysis text from the LLM containing structure recommendations
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

    # Define the user message
    user_message = {
      "role": "user",
      "content": analysis_instructions
    }

    # Get analysis from AI
    response = completion(
      model=model,
      api_key=api_key,
      messages=[user_message],
      temperature=0.2,
    )
    
    return response.choices[0].message.content

def create_file_mapping(api_key: str, model: str, formatted_files: str, analysis: str) -> Dict[str, str]:
    """Create a mapping of original file paths to new paths based on analysis.
    
    Args:
        api_key: API key for the LLM service
        model: LLM model identifier
        formatted_files: JSON string containing file metadata
        analysis: Previous analysis text from the LLM
        
    Returns:
        Dictionary mapping original file paths to proposed new paths
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

    # Define the user message
    user_message = {
      "role": "user",
      "content": mapping_instructions
    }

    # Get mapping from AI
    response = completion(
      model=model,
      api_key=api_key,
      messages=[user_message],
      temperature=0.1,
      response_format={"type": "json_object"},
    )
    
    return json.loads(response.choices[0].message.content)

def generate_structure_proposal(files: List[Dict[str, Any]], api_key: str, model: str, verbose: bool = False, console=None) -> Optional[Dict[str, str]]:
    """Generate a proposal for reorganizing file structure.
    
    Args:
        files: List of file dictionaries containing path, size, extension, and last_modified
        api_key: API key for the LLM service
        model: LLM model identifier
        verbose: If True, print AI responses to stdout
        console: Optional rich console for output. If None, a new console will be created.
        
    Returns:
        Dictionary mapping original file paths to proposed new paths, or None if validation fails
        
    Raises:
        MissingFilesError: If any files are missing from the proposed structure
    """
    if console is None:
        console = Console()
        
    # Format the files for AI processing
    formatted_files_listing = format_files_for_ai(files)

    # Step 1: Analyze file structure
    analysis = analyze_files_structure(api_key, model, formatted_files_listing)
    if verbose:
        console.print("\n=== [bold blue]AI Structure Analysis[/bold blue] ===")
        console.print(analysis)
    
    # Step 2: Create file mapping based on analysis
    file_mapping = create_file_mapping(api_key, model, formatted_files_listing, analysis)
    if verbose:
        console.print("\n=== [bold blue]AI Proposed File Mapping[/bold blue] ===")
        console.print_json(json.dumps(file_mapping, indent=2))
    
    try:
        # Check for missing files
        original_files = [file["path"] for file in files]
        proposed_files = file_mapping.keys()
        missing_files = set(original_files) - set(proposed_files)
        if missing_files:
            raise MissingFilesError(missing_files)
        
        # Save the validated JSON response to a file
        output_file = f"data/proposed_file_structure.json"
        with open(output_file, "w") as f:
            json.dump(file_mapping, f, indent=2)

        return file_mapping
        
    except MissingFilesError as e:
        sys.exit(2)  # Different error code for missing files