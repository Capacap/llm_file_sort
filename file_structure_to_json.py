import os
import json
from pathlib import Path
from typing import Dict, Any


def get_file_info(path: Path) -> Dict[str, Any]:
    """Get basic file information."""
    stat = path.stat()
    return {
        "name": path.name,
        "type": "file",
        "size": stat.st_size,
        "modified": stat.st_mtime
    }


def get_dir_info(path: Path) -> Dict[str, Any]:
    """Get directory information and its contents."""
    return {
        "name": path.name,
        "type": "directory",
        "contents": []
    }


def dir_to_json(root_path: str) -> Dict[str, Any]:
    """Convert directory structure to JSON format."""
    root = Path(root_path)
    
    if not root.exists():
        raise FileNotFoundError(f"Directory not found: {root_path}")
    
    if not root.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {root_path}")
    
    def _build_tree(path: Path) -> Dict[str, Any]:
        if path.is_file():
            return get_file_info(path)
        
        dir_info = get_dir_info(path)
        for item in path.iterdir():
            dir_info["contents"].append(_build_tree(item))
        return dir_info
    
    return _build_tree(root)


def get_file_structure(path: str) -> Dict[str, Any]:
    return dir_to_json(path)

def get_file_structure_string(path: str) -> Dict[str, Any]:
    return json.dumps(dir_to_json(path), indent=2)

if __name__ == "__main__":
    try:
        result = get_file_structure("testing_structure")
        json_str = json.dumps(result, indent=2)
        print(json_str)
    except (FileNotFoundError, NotADirectoryError) as e:
        print(f"Error: {e}")
        exit(1)
