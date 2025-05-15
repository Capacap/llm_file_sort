import os
from textwrap import dedent
from litellm import completion
from file_structure_to_json import get_file_structure_string

api_key = os.getenv("OPENAI_API_KEY")
model = "gpt-4.1-nano"

file_structure = get_file_structure_string("testing_structure")
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

# Optional: Parse JSON response if needed for further processing
# import json
# try:
#     parsed_structure = json.loads(response.choices[0].message.content)
#     # Use parsed_structure for further operations
# except json.JSONDecodeError:
#     print("Warning: Response was not valid JSON")