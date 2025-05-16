import json
import os
from rich.tree import Tree
from rich.console import Console
from collections import deque

def visualize_structure(file_paths):
    """Create a minimal visualization of the directory structure using rich."""
    console = Console()
    directories = {}
    
    # Process all files to build directory structure
    for file_path in file_paths:
        path_parts = file_path.split("/")
        
        # Build directory structure
        current_path = ""
        for i, part in enumerate(path_parts[:-1]):
            current_path = part if i == 0 else f"{current_path}/{part}"
            parent_path = "/".join(current_path.split("/")[:-1]) if "/" in current_path else ""
            
            if current_path not in directories:
                directories[current_path] = {
                    "name": part,
                    "parent": parent_path,
                    "files": []
                }
        
        # Add file to deepest directory
        directory = "/".join(path_parts[:-1])
        if directory in directories:
            directories[directory]["files"].append(path_parts[-1])
    
    # Find root directories (those with no parent)
    root_dirs = sorted([p for p in directories if directories[p]["parent"] == ""])
    
    if not root_dirs:
        console.print("No directories found.")
        return
    
    # If there's only one root directory, use it as the tree root
    if len(root_dirs) == 1:
        root_path = root_dirs[0]
        root_info = directories[root_path]
        tree = Tree(f"[cyan]{root_info['name']}/[/cyan]")
        
        # Process children of the root directory
        queue = deque([(tree, root_path)])
        processed = set([root_path])
        
        # Add files in root directory directly to the tree
        for filename in sorted(root_info["files"]):
            tree.add(f"[green]{filename}[/green]")
    else:
        # If multiple root directories, create a common root
        common_root = os.path.commonprefix(root_dirs)
        if common_root:
            tree = Tree(f"[cyan]{common_root}/[/cyan]")
        else:
            tree = Tree("[cyan]/[/cyan]")
            
        # Process each root directory as a branch
        for root_path in root_dirs:
            root_info = directories[root_path]
            display_name = root_info['name'] if common_root else root_path
            branch = tree.add(f"[cyan]{display_name}/[/cyan]")
            
            # Add files in root directory
            for filename in sorted(root_info["files"]):
                branch.add(f"[green]{filename}[/green]")
            
            # Start queue with this branch
            queue = deque([(branch, root_path)])
            processed = set([root_path])
    
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