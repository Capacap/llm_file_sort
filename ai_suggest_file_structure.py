import os
from textwrap import dedent
from litellm import completion
from file_structure_to_json import get_file_structure_string
import json
import sys

# Custom exception for missing files
class MissingFilesError(Exception):
    def __init__(self, missing_files):
        self.missing_files = missing_files
        message = f"{len(missing_files)} files missing from proposed structure"
        super().__init__(message)

api_key = os.getenv("OPENAI_API_KEY")
model = "gpt-4.1-nano"

file_structure = get_file_structure_string("testing_structure")

# Extract all file paths from original structure
def extract_files(structure, current_path="", files=None):
    if files is None:
        files = set()
    
    if isinstance(structure, dict):
        for name, contents in structure.items():
            path = f"{current_path}/{name}" if current_path else name
            if isinstance(contents, dict):
                extract_files(contents, path, files)
            else:
                files.add(path)
    return files

original_files = extract_files(json.loads(file_structure))

instructions = dedent(f"""
<task>
Analyze the provided file structure and suggest a more logical organization.
</task>

<requirements>
1. Group related files together based on functionality, purpose, or domain
2. Place configuration files in appropriate locations
3. Separate code from assets, documentation, and data
4. Create a hierarchy that improves discoverability and maintainability
5. If no clear logical grouping exists, organize by file type or chronology
</requirements>

<input_structure>
{file_structure}
</input_structure>

<output_format>
Return only a valid JSON object representing the proposed file structure.
Use the same schema as the input structure but with your reorganized hierarchy.
</output_format>
""")

user_message = {
  "role": "user",
  "content": instructions
}

print("=== USER MESSAGE ===")
print(user_message["content"])

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
    
    # Validate all files are present in new structure
    proposed_files = extract_files(parsed_structure)
    missing_files = original_files - proposed_files
    
    # If there are missing files, raise an error
    if missing_files:
        raise MissingFilesError(missing_files)
    else:
        print("✓ All original files present in new structure")
    
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