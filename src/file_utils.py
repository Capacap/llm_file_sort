import shutil
import os
import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from rich.console import Console

def get_file_info(file_path: str) -> Dict[str, Any]:
    file_stat = os.stat(file_path)
    path_obj = Path(file_path)
    
    return {
        "filename": path_obj.name,
        "path": file_path,
        "size": file_stat.st_size,
        "last_modified": datetime.datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
        "extension": path_obj.suffix
    }

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