import os
import sys
import json
from textwrap import dedent
from litellm import completion
from file_structure_to_json import get_file_structure_json, extract_files_from_structure_json

# Custom exception for missing files
class MissingFilesError(Exception):
    def __init__(self, missing_files):
        self.missing_files = missing_files
        message = f"{len(missing_files)} files missing from proposed structure"
        super().__init__(message)

# Get the API key and select model
api_key = os.getenv("OPENAI_API_KEY")
model = "gpt-4.1-nano"

# Get the files andfile structure
file_structure = get_file_structure_json("testing_structure")
files_in_structure = extract_files_from_structure_json(file_structure)

# Define the instructions for the AI
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
{json.dumps(file_structure, indent=2)}
</input_structure>

<output_format>
Return only a valid JSON object representing the proposed file structure.
Use the same schema as the input structure but with your reorganized hierarchy.
</output_format>
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
print(files_in_structure)

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
    files_in_new_structure = extract_files_from_structure_json(parsed_structure)

    # Count the number of missing files
    missing_count = 0
    for file in files_in_structure:
        if file not in files_in_new_structure:
            missing_count += 1
    
    # If there are missing files, raise an error
    if missing_count > 0:
        raise MissingFilesError(missing_count)
    else:
        print(f"✓ All {len(files_in_structure)} original files present in new structure")
    
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