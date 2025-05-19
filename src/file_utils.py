import shutil
import os
import datetime
import mimetypes
import random
from typing import Dict, Any, List, Optional
from pathlib import Path
from rich.console import Console
from rich.tree import Tree
from collections import deque

def get_file_info(file_path: str) -> Dict[str, Any]:
    file_stat = os.stat(file_path)
    
    file_info = {
        "path": file_path,
        "content_sample": "Not available",
        "last_modified": datetime.datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
    }
    
    return file_info

def get_file_info_list(root_dir: str, max_depth: Optional[int] = None) -> List[Dict[str, Any]]:
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

def move_files(file_mapping, console=None, debug=False):
    """
    Move files according to the provided mapping dictionary.
    
    Args:
        file_mapping: Dictionary mapping source paths to destination paths
        console: Optional rich console for output. If None, a new console will be created.
        debug: Whether to show detailed debug information
    """
    if console is None:
        console = Console()
    
    successful_moves = 0
    failed_moves = 0
    
    for source_path, dest_path in file_mapping.items():
        try:
            # Create destination directory if it doesn't exist
            dest_dir = os.path.dirname(dest_path)
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir, exist_ok=True)
                
            # Move the file
            shutil.move(source_path, dest_path)
            
            if debug:
                console.print(f"[green]Moved:[/green] {source_path} → {dest_path}")
            successful_moves += 1
            
        except FileNotFoundError:
            if debug:
                console.print(f"[red]Error:[/red] Source file not found: {source_path}")
            failed_moves += 1
        except PermissionError:
            if debug:
                console.print(f"[red]Error:[/red] Permission denied for: {source_path}")
            failed_moves += 1
        except Exception as e:
            if debug:
                console.print(f"[red]Error:[/red] Failed to move {source_path}: {str(e)}")
            failed_moves += 1
    
    # Print summary
    console.print(f"\n[bold]Summary:[/bold] {successful_moves} files moved successfully, {failed_moves} failed")
    
    return successful_moves, failed_moves

def clean_empty_directories(file_mapping: Dict[str, str], console=None, debug=False):
    """
    Check source file paths and remove any directories that are now empty after file movement.
    
    Args:
        file_mapping: Dictionary mapping source paths to destination paths
        console: Optional rich console for output. If None, a new console will be created.
        debug: Whether to show detailed debug information
    
    Returns:
        int: Number of directories removed
    """
    if console is None:
        console = Console()
    
    # Get unique source directories from the file mapping
    source_dirs = set()
    for source_path in file_mapping:
        source_dir = os.path.dirname(source_path)
        if source_dir:  # Skip if it's just a filename with no directory
            source_dirs.add(source_dir)
    
    # Sort directories by depth (deepest first) to handle nested directories properly
    sorted_dirs = sorted(source_dirs, key=lambda x: x.count(os.sep), reverse=True)
    
    removed_count = 0
    
    # Check each directory and remove if empty
    for directory in sorted_dirs:
        try:
            # Check if directory exists and is empty
            if os.path.exists(directory) and not os.listdir(directory):
                os.rmdir(directory)
                if debug:
                    console.print(f"[yellow]Removed empty directory:[/yellow] {directory}")
                removed_count += 1
                
                # Check parent directories recursively
                parent = os.path.dirname(directory)
                while parent and os.path.exists(parent):
                    if not os.listdir(parent):
                        os.rmdir(parent)
                        if debug:
                            console.print(f"[yellow]Removed empty parent directory:[/yellow] {parent}")
                        removed_count += 1
                        parent = os.path.dirname(parent)
                    else:
                        break
        except PermissionError:
            if debug:
                console.print(f"[red]Error:[/red] Permission denied when trying to remove directory: {directory}")
        except Exception as e:
            if debug:
                console.print(f"[red]Error:[/red] Failed to remove directory {directory}: {str(e)}")
    
    if removed_count > 0:
        console.print(f"\n[bold]Cleanup:[/bold] Removed {removed_count} empty directories")
    else:
        console.print("\n[bold]Cleanup:[/bold] No empty directories to remove")
    
    return removed_count

def visualize_file_tree(file_paths, console=None):
    """
    Create a minimal visualization of the directory structure using rich.
    
    Args:
        file_paths: List of file paths to visualize
        console: Optional rich console for output. If None, a new console will be created.
    """
    if console is None:
        console = Console()
    
    directories = {}
    
    # Process all files to build directory structure
    for file_path in file_paths:
        # Normalize path separators
        file_path = file_path.replace("\\", "/")
        path_parts = file_path.split("/")
        
        # Build directory structure for all path segments
        current_path = ""
        for i, part in enumerate(path_parts[:-1]):  # All parts except the filename
            current_path = part if i == 0 else f"{current_path}/{part}"
            parent_path = "/".join(current_path.split("/")[:-1]) if "/" in current_path else ""
            
            if current_path not in directories:
                directories[current_path] = {
                    "name": part,
                    "parent": parent_path,
                    "files": []
                }
        
        # Add file to its directory
        directory = "/".join(path_parts[:-1]) if len(path_parts) > 1 else ""
        if directory == "" and len(path_parts) == 1:
            # Handle files in root directory
            if "" not in directories:
                directories[""] = {"name": "", "parent": "", "files": []}
            directories[""]["files"].append(path_parts[0])
        elif directory in directories:
            directories[directory]["files"].append(path_parts[-1])
    
    # Find root directories (those with no parent or empty parent)
    root_dirs = sorted([p for p in directories if directories[p]["parent"] == ""])
    
    if not root_dirs and not directories:
        console.print("No directories or files found.")
        return
    
    # Create processing queue and set of processed directories
    queue = deque()
    processed = set()
    
    # If there's only one root directory, use it as the tree root
    if len(root_dirs) == 1:
        root_path = root_dirs[0]
        root_info = directories[root_path]
        tree = Tree(f"[cyan]{root_info['name'] or '/'}/[/cyan]")
        
        # Add files in root directory directly to the tree
        for filename in sorted(root_info["files"]):
            tree.add(f"[green]{filename}[/green]")
        
        # Add root to queue
        queue.append((tree, root_path))
        processed.add(root_path)
    else:
        # If multiple root directories, create a common root
        tree = Tree(f"[cyan]/[/cyan]")
        
        # If there are files directly in the root with no directory
        if "" in directories and directories[""]["files"]:
            for filename in sorted(directories[""]["files"]):
                tree.add(f"[green]{filename}[/green]")
            processed.add("")
            
        # Process each root directory as a branch
        for root_path in root_dirs:
            root_info = directories[root_path]
            display_name = root_info['name'] or root_path
            branch = tree.add(f"[cyan]{display_name}/[/cyan]")
            
            # Add files in root directory
            for filename in sorted(root_info["files"]):
                branch.add(f"[green]{filename}[/green]")
            
            # Add this branch to the queue
            queue.append((branch, root_path))
            processed.add(root_path)
    
    # Process remaining directories using BFS
    while queue:
        parent_branch, parent_path = queue.popleft()
        
        # Find all children of this parent
        children = sorted([p for p in directories if 
                          directories[p]["parent"] == parent_path and 
                          p not in processed])
        
        for child_path in children:
            processed.add(child_path)
            child_info = directories[child_path]
            
            # Create branch for this directory
            child_branch = parent_branch.add(f"[cyan]{child_info['name']}/[/cyan]")
            
            # Add files in this directory
            for filename in sorted(child_info["files"]):
                child_branch.add(f"[green]{filename}[/green]")
            
            # Add this child to the queue to process its children
            queue.append((child_branch, child_path))
    
    # Print just the tree without headers
    console.print(tree)

if __name__ == "__main__":
    file_info_list = get_file_info_list("data/testing")
    for file_info in file_info_list:
        print(file_info["path"])
        print(file_info["content_sample"])
        print("-" * 100)