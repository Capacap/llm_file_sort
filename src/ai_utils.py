"""AI utility functions for image captioning, text summarization, and file organization."""
import json
import base64
import io
from PIL import Image
import litellm

def ai_generate_image_caption(encoded_image_content, file_extension, model, api_key, debug=False):
    # Validate image format and content
    if file_extension not in [".jpg", ".jpeg", ".png", ".webp"]:
        return None
    
    try:
        image_data = base64.b64decode(encoded_image_content)
        if len(image_data) > 20 * 1024 * 1024:
            return None
            
        img = Image.open(io.BytesIO(image_data))
        if img.mode not in ['RGB', 'RGBA'] or any(d <= 0 or d > 10000 for d in img.size):
            return None
    except Exception:
        return None

    # Generate caption via API
    try:
        litellm.api_key = api_key
        messages = [
            {"role": "system", "content": "You describe images factually with brevity. Focus on key visual elements."},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/{file_extension};base64,{encoded_image_content}"}},
                {"type": "text", "text": "Describe this image in 1-2 short sentences. Examples:\n- A red sports car parked on a suburban street with trees in the background.\n- A bowl of fresh fruit including apples, bananas and grapes on a wooden table."}
            ]}
        ]
        
        if debug:
            print("\n=== Image Caption Request ===")
            print(f"User prompt: Describe this image in 1-2 short sentences.")
            
        response = litellm.completion(model=model, messages=messages)
        
        if debug:
            print(f"Response: {response.choices[0].message.content}")
            print("============================\n")
            
        return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"Error generating image caption: {str(e)}")

def ai_generate_text_summary(text_content, model, api_key, debug=False):
    # Generate text summary via API
    try:
        litellm.api_key = api_key
        example = "The Treaty of Versailles was signed on June 28, 1919, exactly five years after the assassination of Archduke Franz Ferdinand, which had directly led to the war. Despite Germany's former status as a major world power, even the German delegation was excluded from the peace conference until May, when they were handed the terms and told to sign. The German government signed the treaty under protest, and the U.S. Senate refused to ratify the treaty."
        example_summary = "The Treaty of Versailles was signed on June 28, 1919, five years after the event that triggered WWI. Germany was excluded from negotiations and forced to sign under protest, while the US Senate never ratified it."
        
        messages = [
            {"role": "system", "content": "You create concise text summaries that capture main points without extraneous details. Keep summaries short and direct."},
            {"role": "user", "content": f"Summarize the following text in 1-2 sentences. Focus on key information only.\n\nExample input:\n{example}\n\nExample summary:\n{example_summary}\n\nText to summarize:\n{text_content}"}
        ]
        
        if debug:
            print("\n=== Text Summary Request ===")
            print(f"System: {messages[0]['content']}")
            print(f"User: {messages[1]['content']}")
            
        response = litellm.completion(model=model, messages=messages)
        
        if debug:
            print(f"Response: {response.choices[0].message.content}")
            print("============================\n")
            
        return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"Error generating text summary: {str(e)}")
    
def ai_map_file_to_directory(file_info, directories, model, api_key, prompt=None, debug=False):
    # Map file to directory via API
    try:
        litellm.api_key = api_key
        
        file_str = json.dumps(file_info, indent=4)
        directories_str = json.dumps(directories, indent=4)
        
        # Prepare prompts
        system_prompt = "Map files to the most appropriate directory based on content, type, and metadata. Output JSON only with format: {\"original_path\": \"best_directory_path\"}."
        
        user_content = f"File:\n{file_str}\n\nAvailable directories:\n{directories_str}\n\n"
        if prompt:
            user_content += f"Additional guidelines:\n{prompt}\n\n"
            
        # Add examples
        examples = """Examples:
        
Example 1:
File: {"path": "vacation-photo.jpg", "type": "image/jpeg", "content_summary": "Beach sunset with palm trees"}
Directories: ["/Photos/Vacations", "/Photos/Nature", "/Downloads"]
Response: {"vacation-photo.jpg": "/Photos/Vacations"}

Example 2:
File: {"path": "quarterly-report.pdf", "type": "application/pdf", "content_summary": "Q3 financial data for company XYZ"}
Directories: ["/Work/Reports", "/Personal/Finances", "/Downloads"] 
Response: {"quarterly-report.pdf": "/Work/Reports"}

Map the file to the best directory and output JSON with format: {"original_path": "best_directory_path"}"""
        user_content += examples
        
        # Make API call
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        if debug:
            print("\n=== Mapping Request ===")
            print(f"System: {messages[0]['content']}")
            print(f"User: {user_content}")
            if prompt:
                print(f"Prompt: {prompt}")
        
        response = litellm.completion(
            model=model,
            messages=messages,
            response_format={"type": "json_object"}
        )
        
        if debug:
            print(f"Response: {response.choices[0].message.content}")
            print("=======================\n")
            
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        raise Exception(f"Error mapping file to directory: {str(e)}")
