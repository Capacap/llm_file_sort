import json
import os
from rich.tree import Tree
from rich.console import Console
from collections import deque

def visualize_structure(file_paths, console=None):
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