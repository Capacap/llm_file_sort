"""AI utility functions for image captioning, text summarization, and file organization."""
# --- Imports ---
import json
import base64
import io
import time
import requests
from PIL import Image
import litellm
from litellm.exceptions import (
    APIError, AuthenticationError, BadRequestError, RateLimitError, 
    ServiceUnavailableError, Timeout
)

# --- Exception classes ---
class AIUtilsError(Exception): """Base exception class for all AI utils errors."""
class ImageProcessingError(AIUtilsError): """Exception raised for errors during image processing."""
class TextProcessingError(AIUtilsError): """Exception raised for errors during text processing."""
class MappingError(AIUtilsError): """Exception raised for errors during file mapping."""
class ModelConnectionError(AIUtilsError): """Exception raised for errors connecting to the model API."""
class DirectoryGenerationError(AIUtilsError): """Exception raised for errors during AI directory structure generation."""

def _handle_api_exceptions(e, retries, max_retries, retry_delay, debug=False):
    """Handle common API exceptions with retry logic."""
    if isinstance(e, (RateLimitError, Timeout, ServiceUnavailableError)) and retries < max_retries:
        error_type = "Rate limit hit" if isinstance(e, RateLimitError) else "Request timed out" if isinstance(e, Timeout) else "Service unavailable"
        if debug:
            print(f"{error_type}, retrying in {retry_delay}s ({retries+1}/{max_retries})")
        time.sleep(retry_delay)
        return True
    
    if isinstance(e, AuthenticationError):
        raise ModelConnectionError(f"Authentication error: {str(e)}")
    elif isinstance(e, (RateLimitError, Timeout, ServiceUnavailableError)):
        error_type = "Rate limit exceeded" if isinstance(e, RateLimitError) else "Request timed out" if isinstance(e, Timeout) else "Service unavailable"
        raise ModelConnectionError(f"{error_type} after {max_retries} retries: {str(e)}")
    elif isinstance(e, BadRequestError):
        raise AIUtilsError(f"Bad request: {str(e)}")
    elif isinstance(e, APIError):
        raise ModelConnectionError(f"API error: {str(e)}")
    elif isinstance(e, requests.exceptions.ConnectionError):
        raise ModelConnectionError(f"Connection error: {str(e)}")
    else:
        return False
    
def ai_generate_image_caption(encoded_image_content, file_extension, model, api_key, port=None, debug=False, max_retries=2, retry_delay=1):
    """Generate a caption for an image using an AI model."""
    # Validate image format and content
    if file_extension not in [".jpg", ".jpeg", ".png", ".webp"]:
        raise ImageProcessingError(f"Unsupported image format: {file_extension}")
    
    try:
        image_data = base64.b64decode(encoded_image_content)
        if len(image_data) > 20 * 1024 * 1024:
            raise ImageProcessingError("Image size exceeds the 20MB limit")
            
        img = Image.open(io.BytesIO(image_data))
        if img.mode not in ['RGB', 'RGBA'] or any(d <= 0 or d > 10000 for d in img.size):
            raise ImageProcessingError(f"Invalid image mode or dimensions: mode={img.mode}, size={img.size}")
    except base64.binascii.Error:
        raise ImageProcessingError("Invalid base64 encoding")
    except Image.UnidentifiedImageError:
        raise ImageProcessingError("Cannot identify image format")
    except Exception as e:
        raise ImageProcessingError(f"Error processing image: {str(e)}")

    # Generate caption via API
    retries = 0
    while True:
        try:
            litellm.api_key = api_key
            litellm.api_base = f"http://localhost:{port}" if port is not None else None
                
            messages = [
                {"role": "system", "content": """# Image Caption Generation
You describe images factually with brevity. Focus on key visual elements.

## Guidelines
- Provide 1-2 short sentences only
- Describe what you can see with certainty
- Be specific and objective
- Avoid speculation about image context or purpose"""},
                
                {"role": "user", "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/{file_extension};base64,{encoded_image_content}"}},
                    {"type": "text", "text": """## Task
Describe this image in 1-2 short sentences.

## Examples
- A red sports car parked on a suburban street with trees in the background.
- A bowl of fresh fruit including apples, bananas and grapes on a wooden table."""}
                ]}
            ]
            
            if debug:
                print(f"\n=== Image Caption Request ===\nModel: {model}\n"
                      f"API Base: {litellm.api_base if port is not None else 'default'}\n"
                      f"User prompt: Describe this image in 1-2 short sentences.")
                
            response = litellm.completion(model=model, messages=messages)
            
            if debug:
                print(f"Response: {response.choices[0].message.content}\n============================\n")
                
            return response.choices[0].message.content
            
        except Exception as e:
            if _handle_api_exceptions(e, retries, max_retries, retry_delay, debug):
                retries += 1
                continue
            raise AIUtilsError(f"Unexpected error generating image caption: {str(e)}")

def ai_generate_text_summary(text_content, model, api_key, port=None, debug=False, max_retries=2, retry_delay=1):
    """Generate a summary for text content using an AI model."""
    if not text_content or not isinstance(text_content, str):
        raise TextProcessingError("Invalid or empty text content")
        
    # Generate text summary via API
    retries = 0
    while True:
        try:
            litellm.api_key = api_key
            litellm.api_base = f"http://localhost:{port}" if port is not None else None
                
            example = "The Treaty of Versailles was signed on June 28, 1919, exactly five years after the assassination of Archduke Franz Ferdinand, which had directly led to the war. Despite Germany's former status as a major world power, even the German delegation was excluded from the peace conference until May, when they were handed the terms and told to sign. The German government signed the treaty under protest, and the U.S. Senate refused to ratify the treaty."
            example_summary = "The Treaty of Versailles was signed on June 28, 1919, five years after the event that triggered WWI. Germany was excluded from negotiations and forced to sign under protest, while the US Senate never ratified it."
            
            messages = [
                {"role": "system", "content": """# Text Summarization Task
You create concise text summaries that capture main points without extraneous details. Keep summaries short and direct.

## Guidelines
- Summarize in 1-2 sentences only
- Focus on key information and main points
- Be factual and objective
- Maintain the core meaning of the original text
- Eliminate unnecessary details"""},
                
                {"role": "user", "content": f"""## Task
Summarize the following text in 1-2 sentences. Focus on key information only.

## Example Input
```
{example}
```

## Example Summary
```
{example_summary}
```

## Text to Summarize
```
{text_content}
```"""}
            ]
            
            if debug:
                print(f"\n=== Text Summary Request ===\nModel: {model}\n"
                      f"API Base: {litellm.api_base if port is not None else 'default'}\n"
                      f"System: {messages[0]['content']}\nUser: {messages[1]['content']}")
                
            response = litellm.completion(model=model, messages=messages)
            
            if debug:
                print(f"Response: {response.choices[0].message.content}\n============================\n")
                
            return response.choices[0].message.content
                
        except Exception as e:
            if _handle_api_exceptions(e, retries, max_retries, retry_delay, debug):
                retries += 1
                continue
            raise AIUtilsError(f"Unexpected error generating text summary: {str(e)}")

def ai_map_file_to_directory(file_info, directories, model, api_key, port=None, prompt=None, debug=False, max_retries=2, retry_delay=1):
    """Map a file to the most appropriate directory using an AI model."""
    # Validate inputs
    if not isinstance(file_info, dict) or "relative_path" not in file_info:
        raise MappingError("Invalid file_info: must be a dictionary containing 'relative_path'")
        
    if not isinstance(directories, list) or not directories:
        raise MappingError("Invalid directories: must be a non-empty list")
        
    # Map file to directory via API
    retries = 0
    while True:
        try:
            litellm.api_key = api_key
            litellm.api_base = f"http://localhost:{port}" if port is not None else None
                
            file_str = json.dumps(file_info, indent=4)
            directories_str = json.dumps(directories, indent=4)
            
            # Prepare prompts
            system_prompt = """Map files to the most appropriate directory based on content, type, and metadata.
Output JSON with exactly this format:
```json
{
  "target_directory": "best directory from available directories list"
}
```
IMPORTANT: target_directory MUST be one of the exact directories from the available directories list."""
            
            user_content = f"""## File Information
```json
{file_str}
```

## Available Directories
```json
{directories_str}
```

"""
            if prompt:
                user_content += f"""## Additional Guidelines
{prompt}

"""
            
            # Add examples
            examples = """## Examples

### Example 1
**Input File:**
```json
{"relative_path": "vacation-photo.jpg", "type": "image/jpeg", "content_summary": "Beach sunset with palm trees"}
```

**Available Directories:**
```json
["/Photos/Vacations", "/Photos/Nature", "/Downloads"]
```

**Expected Output:**
```json
{"target_directory": "/Photos/Vacations"}
```

### Example 2
**Input File:**
```json
{"relative_path": "documents/quarterly-report.pdf", "type": "application/pdf", "content_summary": "Q3 financial data for company XYZ"}
```

**Available Directories:**
```json
["/Work/Reports", "/Personal/Finances", "/Downloads"]
```

**Expected Output:**
```json
{"target_directory": "/Work/Reports"}
```

## Instructions
Map the file to the best directory and output JSON with this exact format:
```json
{
  "target_directory": "best directory from the available list"
}
```
Important: target_directory MUST be one of the directories from the available directories list."""
            user_content += examples
            
            # Make API call
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]
            
            if debug:
                print(f"\n=== Mapping Request ===\nModel: {model}\n"
                      f"API Base: {litellm.api_base if port is not None else 'default'}\n"
                      f"System: {messages[0]['content']}\nUser: {user_content}")
                if prompt:
                    print(f"Prompt: {prompt}")
            
            response = litellm.completion(
                model=model,
                messages=messages,
                response_format={"type": "json_object"}
            )
            
            if debug:
                print(f"Response: {response.choices[0].message.content}\n=======================\n")
            
            # Parse the response    
            try:
                response_json = json.loads(response.choices[0].message.content)
                
                # Validate response format
                if "target_directory" not in response_json:
                    raise MappingError("Response missing 'target_directory' field")
                
                # Check if target directory exists in the directories list
                if response_json["target_directory"] not in directories:
                    if debug:
                        print(f"Invalid directory '{response_json['target_directory']}', not in available directories. Retrying.")
                    raise BadRequestError(f"Target directory '{response_json['target_directory']}' not in available directories")
                    
                # Get source file path from file_info
                source_file_path = file_info["relative_path"]
                
                # Return in expected format {original_path: destination_directory}
                return {source_file_path: response_json["target_directory"]}
            except json.JSONDecodeError:
                raise MappingError("Failed to parse model response as JSON")
                
        except Exception as e:
            if isinstance(e, MappingError):
                raise e
            if _handle_api_exceptions(e, retries, max_retries, retry_delay, debug):
                retries += 1
                continue
            raise AIUtilsError(f"Unexpected error mapping file to directory: {str(e)}")

def ai_generate_directory_structure(files_info, model, api_key, port=None, prompt=None, debug=False, max_retries=2, retry_delay=1):
    """Generate a directory structure for a list of files using an AI model."""
    if not isinstance(files_info, list):
        raise DirectoryGenerationError("Invalid files_info: must be a list of file details")

    retries = 0
    while True:
        try:
            litellm.api_key = api_key
            litellm.api_base = f"http://localhost:{port}" if port is not None else None

            # To keep the prompt size manageable, we'll only send essential info for each file
            simplified_files_info = [
                {
                    "relative_path": f.get("relative_path"),
                    "extension": f.get("extension"),
                    "content_summary": f.get("content_summary", "N/A")
                }
                for f in files_info
            ]
            
            files_str = json.dumps(simplified_files_info, indent=2)
            if len(files_str) > 100000: # Heuristic limit for prompt size
                 # If too large, send a summary instead
                extensions_summary = {}
                for f_info in simplified_files_info:
                    ext = f_info.get("extension", "unknown")
                    extensions_summary[ext] = extensions_summary.get(ext, 0) + 1
                files_representation = {
                    "total_files": len(simplified_files_info),
                    "extensions_summary": extensions_summary,
                    "first_few_files_examples": simplified_files_info[:5] # Show first 5 as examples
                }
                files_str = json.dumps(files_representation, indent=2)
                prompt_info_source = "file summary (due to large number of files)"
            else:
                prompt_info_source = "full file list"


            system_prompt = """You are an AI assistant that specializes in creating optimal directory structures for organizing files.
Based on the provided list of files (including their paths, types, and content summaries), generate a concise and logical list of directory paths.
The directory paths should be suitable for organizing the given files.
Output JSON with exactly this format:
```json
{
  "directory_paths": ["/path/to/dir1", "/another/path/dir2", "/top_level_dir"]
}
```
The paths should start with a '/' and represent a relative structure from a common root.
Aim for a manageable number of top-level directories, and use subdirectories where appropriate for better organization.
Consider common organizational patterns (e.g., by project, by file type, by date, by topic).
Ensure directory paths are valid and do not contain invalid characters.
The list should not be empty if files are present.
"""
            
            user_content = f"""## File Information ({prompt_info_source})
```json
{files_str}
```

## Task
Analyze the files listed (or summarized) above and propose a hierarchical directory structure to organize them effectively.
Provide the directory structure as a JSON list of strings, where each string is a directory path. Each path must start with '/'.

## Example Output Format
```json
{{
  "directory_paths": ["/Images/Animals", "/Documents/Work/Reports", "/Projects/Alpha/SourceCode"]
}}
```

## Instructions
Generate the `directory_paths` list. Ensure the output is valid JSON in the specified format and that the list is not empty if files were provided.
"""
            if prompt:
                user_content += f"""
## Additional Guidelines
{prompt}
"""

            user_content += """
## Instructions
Generate the `directory_paths` list. Ensure the output is valid JSON in the specified format and that the list is not empty if files were provided.
"""
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]
            
            if debug:
                print(f"\n=== Directory Structure Generation Request ===\nModel: {model}\n"
                      f"API Base: {litellm.api_base if port is not None else 'default'}\n"
                      f"System: {messages[0]['content']}\\nUser content based on: {prompt_info_source}")
                if len(files_str) < 2000: # Only print if not excessively long
                    print(f"User files data: {files_str}")

            response = litellm.completion(
                model=model,
                messages=messages,
                response_format={"type": "json_object"}
            )
            
            if debug:
                print(f"Response: {response.choices[0].message.content}\n======================================\n")
            
            try:
                response_json = json.loads(response.choices[0].message.content)
                
                if "directory_paths" not in response_json:
                    raise DirectoryGenerationError("Response missing 'directory_paths' field")
                
                dir_paths = response_json["directory_paths"]
                if not isinstance(dir_paths, list) or not all(isinstance(p, str) and p.startswith('/') for p in dir_paths):
                    raise DirectoryGenerationError("Invalid 'directory_paths' format: must be a list of strings starting with '/'")
                
                if not dir_paths and files_info: # If files were provided, expect some directories
                    raise DirectoryGenerationError("AI returned an empty list of directories.")

                return dir_paths
            except json.JSONDecodeError:
                raise DirectoryGenerationError("Failed to parse model response as JSON")
            except DirectoryGenerationError as e: # Re-raise specific errors
                if debug: print(f"DirectoryGenerationError: {str(e)}")
                raise e

        except Exception as e:
            if isinstance(e, DirectoryGenerationError): # Propagate if already handled
                raise e
            if _handle_api_exceptions(e, retries, max_retries, retry_delay, debug):
                retries += 1
                continue
            raise AIUtilsError(f"Unexpected error generating directory structure: {str(e)}")
