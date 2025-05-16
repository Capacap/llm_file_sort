import os
import sys
import json
from textwrap import dedent
from litellm import completion
from file_structure_to_json import get_files

# Custom exception for missing files
class MissingFilesError(Exception):
    def __init__(self, missing_files):
        self.missing_files = missing_files
        message = f"{len(missing_files)} files missing from proposed structure"
        super().__init__(message)

# Function to format files for AI instructions
def format_files_for_ai(files):
    result = []
    
    for file in sorted(files, key=lambda x: x["path"]):
        file_info = {
            "path": file["path"],
            "size": file["size"],
            "type": file["extension"].lstrip(".")
        }
        result.append(file_info)
    
    return json.dumps(result, indent=2)

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
</task>

<requirements>
1. Group related files together based on functionality, purpose, or domain
2. Place configuration files in appropriate locations
3. Separate code from assets, documentation, and data
4. Create a hierarchy that improves discoverability and maintainability
5. If no clear logical grouping exists, organize by file type or chronology
</requirements>

<input_files>
{formatted_files_listing}
</input_files>

<output_format>
Return a valid JSON object with:
- Keys: original file paths
- Values: suggested new file paths
</output_format>

<constraints>
- Maintain original filenames
- Don't suggest unnecessary nesting
- Group logically related files in the same directory
- The root directory of the proposed structure should be the same as the original structure
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