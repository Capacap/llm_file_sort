import shutil
import os
import datetime
import mimetypes
import random
from typing import Dict, Any, List, Optional
from pathlib import Path
from rich.console import Console

# List of file extensions that can be treated as text files
TEXT_COMPATIBLE_EXTENSIONS = {
    ".txt", ".md", ".py", ".js", ".html", ".css", ".json", ".xml", ".yml", 
    ".yaml", ".csv", ".log", ".sh", ".bat", ".ps1", ".c", ".cpp", ".h", 
    ".java", ".rb", ".php", ".ts", ".tsx", ".jsx", ".sql", ".ini", ".cfg", 
    ".conf", ".toml", ".rst"
}

def is_likely_text_file(file_path: str) -> bool:
    """Determine if a file is likely to be a text file based on extension and content sampling."""
    extension = os.path.splitext(file_path)[1].lower()
    
    # Check based on extension
    if extension in TEXT_COMPATIBLE_EXTENSIONS:
        return True
    
    # Check based on mimetype
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type and mime_type.startswith('text/'):
        return True
    
    # For unknown types, try a small content sample to check if it's text
    if os.path.getsize(file_path) > 0:
        try:
            with open(file_path, 'rb') as f:
                sample = f.read(512)
                # Check if the content appears to be text (high ratio of ASCII characters)
                text_chars = len([b for b in sample if 32 <= b <= 126 or b in (9, 10, 13)])
                return text_chars / len(sample) > 0.7
        except:
            pass
    
    return False

def extract_random_lines(file_path: str, max_size: int = 256) -> str:
    """Extract random lines from a text file with a size limit."""
    try:
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return ""
            
        # For small files, just read a portion from the beginning
        if file_size <= 1024:
            with open(file_path, 'r', errors='replace') as f:
                content = f.read(max_size)
                if len(content) > max_size:
                    content = content[:max_size - 3] + "..."
                return content
        
        # For larger files, get random positions to sample from
        sample_positions = []
        # Try to get samples from beginning, middle and end parts
        sample_positions.append(0)  # Beginning
        sample_positions.append(file_size // 2)  # Middle
        sample_positions.append(max(0, file_size - 1024))  # End
        
        samples = []
        remaining_chars = max_size
        
        with open(file_path, 'r', errors='replace') as f:
            for pos in sample_positions:
                if remaining_chars <= 0:
                    break
                    
                f.seek(pos)
                # Skip partial line if not at beginning
                if pos > 0:
                    f.readline()
                
                # Get 1-2 lines from this position
                lines = []
                for _ in range(random.randint(1, 2)):
                    line = f.readline().strip()
                    if line:
                        lines.append(line)
                    if not line:
                        break
                
                if lines:
                    # Truncate if too long
                    sample_text = " | ".join(lines)
                    if len(sample_text) > remaining_chars:
                        sample_text = sample_text[:remaining_chars - 3] + "..."
                        remaining_chars = 0
                    else:
                        remaining_chars -= len(sample_text)
                    
                    samples.append(sample_text)
        
        return " ... ".join(samples)
    except Exception:
        return ""

def get_file_info(file_path: str) -> Dict[str, Any]:
    file_stat = os.stat(file_path)
    path_obj = Path(file_path)
    
    file_info = {
        "filename": path_obj.name,
        "path": file_path,
        "size": file_stat.st_size,
        "last_modified": datetime.datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
        "extension": path_obj.suffix,
        "content_sample": "Not available"
    }
    
    # Extract text sample for compatible files
    if file_stat.st_size > 0 and file_stat.st_size < 10_000_000:  # Skip empty or very large files
        try:
            # First check if this is likely to be a text file
            if is_likely_text_file(file_path):
                file_info["content_sample"] = extract_random_lines(file_path, 256)
        except Exception:
            # If we encounter any errors, just skip the content sample
            pass
    
    return file_info

def get_files(root_dir: str, max_depth: Optional[int] = None) -> List[Dict[str, Any]]:
    file_info_list = []
    root_dir = os.path.normpath(root_dir)
    base_depth = root_dir.count(os.sep)
    
    for root, dirs, files in os.walk(root_dir):
        current_depth = root.count(os.sep) - base_depth
        
        if max_depth is not None and current_depth > max_depth:
            dirs.clear()
            continue
            
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, root_dir)
            file_info = get_file_info(file_path)
            file_info["path"] = rel_path
            file_info_list.append(file_info)
    
    return file_info_list

def move_files(file_mapping, console=None):
    """
    Move files according to the provided mapping and clean up empty source directories.
    
    Args:
        file_mapping: Dictionary where keys are source paths and values are destination paths
        console: Optional rich console for output. If None, a new console will be created.
    """
    if console is None:
        console = Console()
    
    source_dirs = set()
    
    for source, destination in file_mapping.items():
        if not os.path.exists(source):
            console.print(f"[yellow]Warning:[/yellow] Source file {source} does not exist. Skipping.")
            continue
            
        source_dir = os.path.dirname(source)
        if source_dir:
            source_dirs.add(source_dir)
            
        dest_dir = os.path.dirname(destination)
        if dest_dir and not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
            
        try:
            shutil.move(source, destination)
            console.print(f"[green]Moved:[/green] {source} → {destination}")
        except Exception as e:
            console.print(f"[red]Error moving[/red] {source} to {destination}: {e}")
    
    if source_dirs:
        dirs_to_check = sorted(source_dirs, key=lambda x: x.count(os.sep), reverse=True)
        
        for dir_path in dirs_to_check:
            try:
                if os.path.exists(dir_path) and not os.listdir(dir_path):
                    os.rmdir(dir_path)
                    console.print(f"[red]Removed empty directory:[/red] {dir_path}")
                    
                    parent = os.path.dirname(dir_path)
                    while parent and os.path.exists(parent) and not os.listdir(parent):
                        os.rmdir(parent)
                        console.print(f"[red]Removed empty parent directory:[/red] {parent}")
                        parent = os.path.dirname(parent)
            except Exception as e:
                console.print(f"[red]Error removing directory[/red] {dir_path}: {e}") 


if __name__ == "__main__":
    file_info_list = get_files("data/testing")
    for file_info in file_info_list:
        print(file_info["path"])
        print(file_info["content_sample"])
        print("-" * 100)