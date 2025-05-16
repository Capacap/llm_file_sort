import os
import sys
import json
from typing import Dict
from textwrap import dedent
from litellm import completion
from src.read_files import get_files

class MissingFilesError(Exception):
    def __init__(self, missing_files):
        self.missing_files = missing_files
        message = f"{len(missing_files)} files missing from proposed structure"
        super().__init__(message)

def format_files_for_ai(files):
    result = []
    
    for file in sorted(files, key=lambda x: x["path"]):
        file_info = {
            "path": file["path"],
            "size": file["size"],
            "type": file["extension"].lstrip("."),
            "last_modified": file["last_modified"]
        }
        result.append(file_info)
    
    return json.dumps(result, indent=2)

def analyze_files_structure(api_key: str, model: str, formatted_files: str) -> str:
    """First step: Get AI analysis of the file structure"""
    
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
    """Second step: Create the actual file mapping based on analysis"""
    
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

def generate_structure_proposal(files, api_key: str, model: str):
    # Format the files for AI processing
    formatted_files_listing = format_files_for_ai(files)

    print("=== ORIGINAL FILES ===")
    print(formatted_files_listing)

    # Step 1: Analyze file structure
    print("\n=== ANALYZING FILE STRUCTURE ===")
    analysis = analyze_files_structure(api_key, model, formatted_files_listing)
    print(analysis)
    
    # Step 2: Create file mapping based on analysis
    print("\n=== CREATING FILE MAPPING ===")
    file_mapping = create_file_mapping(api_key, model, formatted_files_listing, analysis)
    print(json.dumps(file_mapping, indent=2))
    
    try:
        print("\n=== VALIDATION ===")

        # Check for missing files
        original_files = [file["path"] for file in files]
        proposed_files = file_mapping.keys()
        missing_files = set(original_files) - set(proposed_files)
        if missing_files:
            raise MissingFilesError(missing_files)
        
        print(f"✓ All {len(original_files)} files accounted for in proposed structure")
        
        # Print the mapping for review
        print("\n=== FILE MAPPING ===")
        for original_file, new_file in file_mapping.items():
            print(f"{original_file} -> {new_file}")
        
        # Save the validated JSON response to a file
        output_file = f"data/proposed_file_structure.json"
        with open(output_file, "w") as f:
            json.dump(file_mapping, f, indent=2)
        print(f"\n✓ Saved proposed structure to {output_file}")

        return file_mapping
        
    except MissingFilesError as e:
        print("\n=== MISSING FILES ERROR ===")
        print(f"✗ {str(e)}:")
        for file in sorted(e.missing_files):
            print(f"  - {file}")
        sys.exit(2)  # Different error code for missing files