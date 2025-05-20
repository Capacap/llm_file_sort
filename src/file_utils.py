import os
import datetime
import base64
from rich.tree import Tree
from rich.console import Console

def list_directories(root_directory):
    # Get all directories from root directory
    return ['/' if dirpath == root_directory else '/' + os.path.relpath(dirpath, root_directory) 
            for dirpath, _, _ in os.walk(root_directory)]

def list_files_with_metadata(root_directory):
    # Get all files with their metadata from a directory and its subdirectories
    files_with_metadata = []
    
    for dirpath, _, filenames in os.walk(root_directory):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            
            if not os.path.exists(file_path):
                continue
                
            try:
                stat_info = os.stat(file_path)
                files_with_metadata.append({
                    "relative_path": os.path.relpath(file_path, root_directory),
                    "filename": os.path.basename(file_path),
                    "size": stat_info.st_size,
                    "created": datetime.datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
                    "modified": datetime.datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                    "extension": os.path.splitext(file_path)[1].lower() if os.path.isfile(file_path) else "",
                })
            except:
                continue
    
    return files_with_metadata

def extract_text_content(file_path, max_chars=None):
    # Extract text content from text-based files
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        return None
    
    # List of text-based file extensions
    text_extensions = [
        ".txt", ".md", ".csv", ".json", ".xml", ".html", ".htm", ".css", ".js",
        ".py", ".java", ".c", ".cpp", ".h", ".hpp", ".cs", ".php", ".rb", ".go",
        ".ts", ".tsx", ".jsx", ".yml", ".yaml", ".ini", ".cfg", ".conf", ".log",
        ".sql", ".sh", ".bat", ".ps1", ".tex", ".rst", ".r", ".swift"
    ]
    
    # Skip if not a compatible format
    if os.path.splitext(file_path)[1].lower() not in text_extensions:
        return None
    
    # Try to read the file with different encodings
    for encoding in ["utf-8", "latin-1", "ascii"]:
        try:
            with open(file_path, "r", encoding=encoding) as file:
                content = file.read()
            
            # Truncate content if max_chars is specified
            if max_chars and len(content) > max_chars:
                content = content[:max_chars] + "..."
                
            return content
        except UnicodeDecodeError:
            continue
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    return None

def encode_image_content(file_path):
    # Encode image files to base64
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        return None
    
    # List of image file extensions
    image_extensions = [
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp", 
        ".svg", ".ico", ".heic", ".heif"
    ]
    
    # Skip if not a compatible format
    if os.path.splitext(file_path)[1].lower() not in image_extensions:
        return None
    
    try:
        with open(file_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        return f"Error encoding image: {str(e)}"
