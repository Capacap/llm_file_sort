import os
import sys
import json
import datetime
from typing import Dict, Any, List, Optional
from textwrap import dedent
from litellm import completion
from pathlib import Path

# Custom exception for missing files
class MissingFilesError(Exception):
    def __init__(self, missing_files):
        self.missing_files = missing_files
        message = f"{len(missing_files)} files missing from proposed structure"
        super().__init__(message)

def get_file_info(file_path: str) -> Dict[str, Any]:
    file_stat = os.stat(file_path)
    path_obj = Path(file_path)
    
    return {
        "filename": path_obj.name,
        "path": file_path,
        "size": file_stat.st_size,
        "last_modified": datetime.datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
        "extension": path_obj.suffix
    }

def get_files(root_dir: str, max_depth: Optional[int] = None) -> List[Dict[str, Any]]:
    file_info_list = []
    root_dir = os.path.normpath(root_dir)
    base_depth = root_dir.count(os.sep)
    
    for root, dirs, files in os.walk(root_dir):
        current_depth = root.count(os.sep) - base_depth
        
        if max_depth is not None and current_depth > max_depth:
            # Clear dirs list to prevent further traversal in this branch
            dirs.clear()
            continue
            
        for file in files:
            file_path = os.path.join(root, file)
            file_info = get_file_info(file_path)
            file_info_list.append(file_info)
    
    return file_info_list

# Format input files for use in the AI instructions
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

def main():
    # Get the API key and select model
    api_key = os.getenv("OPENAI_API_KEY")
    model = "gpt-4.1-nano"

    # Get the files and file structure
    files = get_files("testing_structure")
    formatted_files_listing = format_files_for_ai(files)

    # Define the instructions for the AI
    instructions = dedent(f"""
    <task>
    Analyze the provided files and suggest a more logical structure that improves organization and maintainability.
    The files may not have descriptive or consistent naming patterns.
    </task>

    <requirements>
    1. Group related files together based on functionality, purpose, or domain
    2. When file names are non-descriptive, analyze file types, timestamps, and potential relationships
    3. Place configuration files in appropriate locations (e.g., config/, settings/)
    4. Separate code from assets, documentation, and data
    5. Create a hierarchy that improves discoverability and maintainability
    6. Organize by file type for utility scripts, media files, and documentation
    7. Consider chronological organization for version-controlled or time-sensitive content
    </requirements>

    <organization_strategies>
    Priority order (use the first strategy that applies):
    1. Domain/functionality grouping (e.g., authentication, database, UI components)
    2. File purpose grouping (e.g., configs, tests, documentation, media)
    3. File type grouping (e.g., images/, documents/, scripts/)
    4. Chronological grouping (for versioned files or when other strategies don't apply)
    </organization_strategies>

    <input_files>
    {formatted_files_listing}
    </input_files>

    <output_format>
    Return a valid JSON object with:
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
    - Don't suggest unnecessary nesting (max 3-4 levels deep)
    - Group logically related files in the same directory
    - The root directory of the proposed structure should be the same as the original structure
    - Consider ease of navigation and maintainability in your structure
    </constraints>
    """)

    # Define the user message
    user_message = {
      "role": "user",
      "content": instructions
    }

    # Print the user message
    print("=== USER MESSAGE ===")
    print(user_message["content"])

    # Print the original files
    print("=== ORIGINAL FILES ===")
    print(formatted_files_listing)

    response = completion(
      model=model,
      api_key=api_key,
      messages=[user_message],
      temperature=0.2,
      response_format={"type": "json_object"},
    )

    print("=== ASSISTANT MESSAGE ===")
    print(response.choices[0].message.content)

    # Validate JSON response
    try:
        print("\n=== VALIDATION ===")

        # Parse the response to validate JSON
        parsed_structure = json.loads(response.choices[0].message.content)
        print("✓ Valid JSON structure received")

        # Check for missing files
        original_files = [file["path"] for file in files]
        proposed_files = parsed_structure.keys()
        missing_files = set(original_files) - set(proposed_files)
        if missing_files:
            raise MissingFilesError(missing_files)
        
        print(f"✓ All {len(original_files)} files accounted for in proposed structure")
        
        # Print the mapping for review
        print("\n=== FILE MAPPING ===")
        for original_file, new_file in parsed_structure.items():
            print(f"{original_file} -> {new_file}")
        
        # Save the validated JSON response to a file
        output_file = "proposed_file_structure.json"
        with open(output_file, "w") as f:
            json.dump(parsed_structure, f, indent=2)
        print(f"\n✓ Saved proposed structure to {output_file}")
        
    except json.JSONDecodeError as e:
        print("\n=== JSON DECODE ERROR ===")
        print(f"✗ Invalid JSON response: {str(e)}")
        print(f"Error at line {e.lineno}, column {e.colno}")
        sys.exit(1)  # Exit with error code
        
    except MissingFilesError as e:
        print("\n=== MISSING FILES ERROR ===")
        print(f"✗ {str(e)}:")
        for file in sorted(e.missing_files):
            print(f"  - {file}")
        sys.exit(2)  # Different error code for missing files

if __name__ == "__main__":
    main()