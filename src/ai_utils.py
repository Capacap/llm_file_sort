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
