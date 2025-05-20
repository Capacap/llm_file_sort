import os
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.panel import Panel
from rich.tree import Tree
from rich.columns import Columns
from src.file_utils import list_files_with_metadata, extract_text_content, encode_image_content, list_directories
from src.ai_utils import ai_generate_image_caption, ai_generate_text_summary, ai_map_file_to_directory


def main(kw_args):
    console = Console()
    
    # Load files and metadata from target directory
    files = list_files_with_metadata(kw_args["directory"])
    root_dir = os.path.abspath(kw_args["directory"])

    # Generate content summaries for files
    console.print("\n[bold blue]Generating content summaries...[/]")
    
    with Progress(
        SpinnerColumn(),
        TaskProgressColumn(),
        TextColumn("- {task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Processing files", total=len(files))
        
        for file in files:
            progress.update(task, description=f"{file['relative_path']}")
            file_path = os.path.join(kw_args["directory"], file["relative_path"])
            
            # Handle image files
            if image_content := encode_image_content(file_path):
                file["content_summary"] = ai_generate_image_caption(image_content, file["extension"], kw_args["model"], kw_args["api_key"])
            # Handle text files    
            elif text_content := extract_text_content(file_path, 1024):
                file["content_summary"] = ai_generate_text_summary(text_content, kw_args["model"], kw_args["api_key"])
            # Default case
            else:
                file["content_summary"] = "No summary available."
                
            progress.advance(task)

    # Map files to their target directories
    console.print("\n[bold blue]Generating file mappings...[/]")
    directory_structure = list_directories(kw_args["directory"])
    relative_file_mapping = {}
    
    with Progress(
        SpinnerColumn(),
        TaskProgressColumn(),
        TextColumn("- {task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Mapping files", total=len(files))
        
        for file in files:
            progress.update(task, description=f"{file['relative_path']}")
            mapped_file = ai_map_file_to_directory(file, directory_structure, kw_args["model"], kw_args["api_key"])
            relative_file_mapping.update(mapped_file)
            progress.advance(task)

    # Convert relative paths to absolute paths
    console.print("\n[bold blue]Generating absolute file mappings...[/]")
    absolute_file_mapping = {
        os.path.join(root_dir, rel_src): os.path.join(root_dir, rel_dst.lstrip('/'), os.path.basename(rel_src))
        for rel_src, rel_dst in relative_file_mapping.items()
    }
    
    # Create tree representations of current and proposed file structures
    def build_file_tree(paths, title, style):
        # Create a dict to represent the file tree
        file_dict = {}
        for path in paths:
            # Make path relative to root_dir
            if path.startswith(root_dir):
                rel_path = os.path.relpath(path, root_dir)
            else:
                rel_path = path
                
            parts = rel_path.split(os.sep)
            current = file_dict
            for i, part in enumerate(parts):
                if i == len(parts) - 1:  # Leaf (file)
                    current.setdefault('__files__', []).append(part)
                else:  # Directory
                    if part not in current:
                        current[part] = {}
                    current = current[part]
        
        # Create the tree
        tree = Tree(f"[bold {style}]{title}: {os.path.basename(root_dir)}[/]")
        
        # Recursive function to build the tree
        def add_to_tree(node, tree_node):
            # Add files
            for file in node.get('__files__', []):
                tree_node.add(f"[{style}]{file}[/]")
            
            # Add directories
            for dirname, contents in sorted(((k, v) for k, v in node.items() if k != '__files__')):
                dir_node = tree_node.add(f"[bold {style}]{dirname}/[/]")
                add_to_tree(contents, dir_node)
        
        add_to_tree(file_dict, tree)
        return tree
    
    # Display current and proposed organization as trees
    current_tree = build_file_tree(absolute_file_mapping.keys(), "Current Organization", "yellow")
    proposed_tree = build_file_tree(absolute_file_mapping.values(), "Proposed Organization", "green")
    
    console.print("\n")
    console.print(Columns([current_tree, proposed_tree]))
    
    # Check if any changes are needed
    changes_needed = any(os.path.normpath(src) != os.path.normpath(dst) for src, dst in absolute_file_mapping.items())
    if not changes_needed:
        console.print("\n[bold green]No file organization changes needed.[/]")
        return
        
    # Get user confirmation before proceeding
    if console.input("\n[bold cyan]Apply changes? (y/n): [/]").lower() != "y":
        console.print("[yellow]Operation canceled.[/]")
        return

    # Move files to their target directories
    console.print("\n[bold blue]Moving files...[/]")
    moved = skipped = errors = 0
    
    with Progress(
        SpinnerColumn(),
        TaskProgressColumn(),
        TextColumn("- {task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Moving files", total=len(absolute_file_mapping))
        
        for src_path, dest_path in absolute_file_mapping.items():
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            
            if not os.path.exists(src_path):
                progress.advance(task)
                continue
                
            try:
                if os.path.normpath(src_path) == os.path.normpath(dest_path):
                    progress.update(task, description=f"Skipping: {os.path.basename(src_path)}")
                    skipped += 1
                    progress.advance(task)
                    continue
                
                os.rename(src_path, dest_path)
                progress.update(task, description=f"Moving: {os.path.basename(src_path)}")
                moved += 1
            except Exception as e:
                console.print(f"[bold red]Error moving {src_path}: {e}[/]")
                errors += 1
            
            progress.advance(task)
    
    # Print operation summary
    console.print("\n[bold blue]Operation Summary:[/]")
    console.print(f"[green]Files moved: {moved}[/]")
    console.print(f"[yellow]Files skipped: {skipped}[/]")
    if errors > 0:
        console.print(f"[red]Errors: {errors}[/]")

    # Clean up empty directories if requested
    if kw_args["clean_up"]:
        console.print("\n[bold blue]Cleaning up empty directories...[/]")
        dirs_to_check = [os.path.join(root, d) for root, dirs, _ in os.walk(root_dir, topdown=False) for d in dirs]
        
        if not dirs_to_check:
            console.print("[yellow]No directories to clean up.[/]")
        else:
            removed_count = 0
            for dir_path in dirs_to_check:
                if os.path.exists(dir_path) and not os.listdir(dir_path):
                    os.rmdir(dir_path)
                    console.print(f"[green]Removed empty directory: {dir_path}[/]")
                    removed_count += 1
                    
            console.print(f"[green]Removed {removed_count} empty directories[/]")


if __name__ == "__main__":
    args = {
        "directory": "data/testing",
        "model": "gpt-4.1-nano",  
        "debug": True,
        "api_key": None,
        "api_key_env": "OPENAI_API_KEY",
        "port": None,
        "prompt": "Sort all files with text content into a text directory and all other files into a misc directory",
        "clean_up": True
    }

    main(args)