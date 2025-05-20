import json
import litellm
import base64
import io
from PIL import Image

def ai_generate_image_caption(encoded_image_content, file_extension, model, api_key):
    # Check for compatible image file extensions
    if file_extension not in [".jpg", ".jpeg", ".png", ".webp"]:
        return None
    
    # Validate image data
    try:
        image_data = base64.b64decode(encoded_image_content)
        if len(image_data) > 20 * 1024 * 1024:
            return None
            
        img = Image.open(io.BytesIO(image_data))
        if img.mode not in ['RGB', 'RGBA'] or any(d <= 0 or d > 10000 for d in img.size):
            return None
    except Exception:
        return None

    # Generate AI caption for image
    try:
        litellm.api_key = api_key
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/{file_extension};base64,{encoded_image_content}"}},
                    {"type": "text", "text": "Provide a brief, concise description of this image in 1-2 sentences."}
                ]
            }
        ]
        
        response = litellm.completion(model=model, messages=messages)
        return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"Error generating image caption: {str(e)}")

def ai_generate_text_summary(text_content, model, api_key):
    # Generate AI summary for text content
    try:
        litellm.api_key = api_key
        messages = [
            {"role": "system", "content": "You are a helpful assistant that generates concise summaries."},
            {"role": "user", "content": f"Please summarize the following text:\n\n{text_content}"}
        ]
        
        response = litellm.completion(model=model, messages=messages)
        return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"Error generating text summary: {str(e)}")
    
def ai_map_file_to_directory(file_info, directories, model, api_key):
    # Map file to appropriate directory using AI
    try:
        litellm.api_key = api_key
        
        file_str = json.dumps(file_info, indent=4)
        directories_str = json.dumps(directories, indent=4)
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant that maps files to appropriate directories."},
            {"role": "user", "content": f"Given this file with the following content description:\n\n{file_str}\n\n"
                                        f"Choose the most appropriate directory from this list to place the file:\n"
                                        f"{directories_str}\n\n"
                                        f"Return a JSON object with the original relative path as the key and the path of the directory as the value."}
        ]
        
        response = litellm.completion(
            model=model,
            messages=messages,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        raise Exception(f"Error mapping file to directory: {str(e)}")
