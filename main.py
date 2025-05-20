"""ML-powered file organization tool that maps files to appropriate directories."""
import os
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.panel import Panel
from rich.tree import Tree
from rich.columns import Columns
from src.file_utils import list_files_with_metadata, extract_text_content, encode_image_content, list_directories
from src.ai_utils import ai_generate_image_caption, ai_generate_text_summary, ai_map_file_to_directory


def validate_file_mapping(mapping):
    """Validate file mapping for potential issues."""
    validation_results = {
        "destination_conflicts": {},
        "source_missing": [],
        "destination_exists": []
    }
    
    # Check destination conflicts (multiple files to same destination)
    dest_paths = {}
    for src, dst in mapping.items():
        norm_dst = os.path.normpath(dst)
        if norm_dst in dest_paths:
            if norm_dst not in validation_results["destination_conflicts"]:
                validation_results["destination_conflicts"][norm_dst] = [dest_paths[norm_dst]]
            validation_results["destination_conflicts"][norm_dst].append(src)
        else:
            dest_paths[norm_dst] = src
    
    # Check missing source files and existing destinations
    for src in mapping.keys():
        if not os.path.exists(src):
            validation_results["source_missing"].append(src)
    
    for src, dst in mapping.items():
        if os.path.exists(dst) and os.path.normpath(src) != os.path.normpath(dst):
            validation_results["destination_exists"].append(dst)
    
    return validation_results


def build_file_tree(paths, title, style, root_dir):
    """Create a tree visualization of file structure."""
    # Build dictionary representation of file tree
    file_dict = {}
    for path in paths:
        rel_path = os.path.relpath(path, root_dir) if path.startswith(root_dir) else path
        parts = rel_path.split(os.sep)
        
        current = file_dict
        for i, part in enumerate(parts):
            if i == len(parts) - 1:  # Leaf (file)
                current.setdefault('__files__', []).append(part)
            else:  # Directory
                current.setdefault(part, {})
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


def process_files_content(files, directory, model, api_key, debug=False, console=None):
    """Process files to generate content summaries."""
    console = console or Console()
    
    with Progress(SpinnerColumn(), TaskProgressColumn(), TextColumn("- {task.description}"), console=console) as progress:
        task = progress.add_task("Processing files", total=len(files))
        
        for file in files:
            progress.update(task, description=f"{file['relative_path']}")
            file_path = os.path.join(directory, file["relative_path"])
            
            if image_content := encode_image_content(file_path):
                file["has_image_content"] = True
                file["content_summary"] = ai_generate_image_caption(
                    image_content, file["extension"], model, api_key, debug=debug)
            elif text_content := extract_text_content(file_path, 1024):
                file["has_text_content"] = True
                file["content_summary"] = ai_generate_text_summary(
                    text_content, model, api_key, debug=debug)
            else:
                file["content_summary"] = "No summary available."
                
            progress.advance(task)
    
    return files


def map_files_to_directories(files, directory_structure, model, api_key, prompt=None, debug=False, console=None):
    """Map files to appropriate directories using AI."""
    console = console or Console()
    relative_file_mapping = {}
    
    with Progress(SpinnerColumn(), TaskProgressColumn(), TextColumn("- {task.description}"), console=console) as progress:
        task = progress.add_task("Mapping files", total=len(files))
        
        for file in files:
            progress.update(task, description=f"{file['relative_path']}")
            mapped_file = ai_map_file_to_directory(
                file, directory_structure, model, api_key, prompt, debug=debug)
            relative_file_mapping.update(mapped_file)
            progress.advance(task)
    
    return relative_file_mapping


def display_validation_issues(validation, console=None):
    """Display validation issues found in file mapping."""
    console = console or Console()
    has_issues = False
    
    if validation["destination_conflicts"]:
        has_issues = True
        console.print("\n[bold red]Destination conflicts found:[/]")
        for dst, src_files in validation["destination_conflicts"].items():
            console.print(f"[red]Multiple files map to: {dst}[/]")
            for src in src_files:
                console.print(f"  - {src}")
    
    if validation["source_missing"]:
        has_issues = True
        console.print("\n[bold red]Source files not found:[/]")
        for src in validation["source_missing"]:
            console.print(f"[red]Missing: {src}[/]")
    
    if validation["destination_exists"]:
        has_issues = True
        console.print("\n[bold yellow]Destination files already exist (will be overwritten):[/]")
        for dst in validation["destination_exists"]:
            console.print(f"[yellow]Exists: {dst}[/]")
    
    if has_issues:
        console.print("\n[bold yellow]Warning: Issues found in file mapping.[/]")
    else:
        console.print("\n[bold green]✓ File mapping validation successful![/]")
    
    return has_issues


def move_files(file_mapping, console=None):
    """Move files according to the provided mapping."""
    console = console or Console()
    moved = skipped = errors = 0
    
    with Progress(SpinnerColumn(), TaskProgressColumn(), TextColumn("- {task.description}"), console=console) as progress:
        task = progress.add_task("Moving files", total=len(file_mapping))
        
        for src_path, dest_path in file_mapping.items():
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            
            if not os.path.exists(src_path):
                progress.advance(task)
                continue
                
            try:
                if os.path.normpath(src_path) == os.path.normpath(dest_path):
                    progress.update(task, description=f"Skipping: {os.path.basename(src_path)}")
                    skipped += 1
                else:
                    os.rename(src_path, dest_path)
                    progress.update(task, description=f"Moving: {os.path.basename(src_path)}")
                    moved += 1
            except Exception as e:
                console.print(f"[bold red]Error moving {src_path}: {e}[/]")
                errors += 1
            
            progress.advance(task)
    
    return moved, skipped, errors


def cleanup_empty_dirs(root_dir, console=None):
    """Remove empty directories under the given root directory."""
    console = console or Console()
    dirs_to_check = [os.path.join(root, d) for root, dirs, _ in os.walk(root_dir, topdown=False) for d in dirs]
    
    if not dirs_to_check:
        console.print("[yellow]No directories to clean up.[/]")
        return 0
    
    removed_count = 0
    for dir_path in dirs_to_check:
        if os.path.exists(dir_path) and not os.listdir(dir_path):
            os.rmdir(dir_path)
            console.print(f"[green]Removed empty directory: {dir_path}[/]")
            removed_count += 1
    
    console.print(f"[green]Removed {removed_count} empty directories[/]")
    return removed_count


def main(kw_args):
    console = Console()
    root_dir = os.path.abspath(kw_args["directory"])
    
    # Load files and generate content summaries
    console.print("\n[bold blue]Generating content summaries...[/]")
    files = list_files_with_metadata(kw_args["directory"])
    files = process_files_content(files, kw_args["directory"], kw_args["model"], 
                                  kw_args["api_key"], kw_args["debug"], console)

    # Map files to directories
    console.print("\n[bold blue]Generating file mappings...[/]")
    directory_structure = list_directories(kw_args["directory"])
    relative_file_mapping = map_files_to_directories(
        files, directory_structure, kw_args["model"], kw_args["api_key"], 
        kw_args.get("prompt"), kw_args["debug"], console)

    # Create absolute path mappings
    console.print("\n[bold blue]Generating absolute file mappings...[/]")
    absolute_file_mapping = {
        os.path.join(root_dir, rel_src): os.path.join(root_dir, rel_dst.lstrip('/'), os.path.basename(rel_src))
        for rel_src, rel_dst in relative_file_mapping.items()
    }
    
    # Visualize current and proposed organization
    current_tree = build_file_tree(absolute_file_mapping.keys(), "Current Organization", "yellow", root_dir)
    proposed_tree = build_file_tree(absolute_file_mapping.values(), "Proposed Organization", "green", root_dir)
    
    console.print("\n")
    console.print(Columns([current_tree, proposed_tree]))
    
    # Check if changes needed
    changes_needed = any(os.path.normpath(src) != os.path.normpath(dst) 
                        for src, dst in absolute_file_mapping.items())
    if not changes_needed:
        console.print("\n[bold green]No file organization changes needed.[/]")
        return
    
    # Validate mapping and show issues
    console.print("\n[bold blue]Validating file mapping...[/]")
    validation = validate_file_mapping(absolute_file_mapping)
    has_issues = display_validation_issues(validation, console)
        
    # Get confirmation and apply changes
    if console.input("\n[bold cyan]Apply changes? (y/n): [/]").lower() != "y":
        console.print("[yellow]Operation canceled.[/]")
        return

    # Move files
    console.print("\n[bold blue]Moving files...[/]")
    moved, skipped, errors = move_files(absolute_file_mapping, console)
    
    # Operation summary
    console.print("\n[bold blue]Operation Summary:[/]")
    console.print(f"[green]Files moved: {moved}[/]")
    console.print(f"[yellow]Files skipped: {skipped}[/]")
    if errors > 0:
        console.print(f"[red]Errors: {errors}[/]")

    # Clean up empty directories
    if kw_args["clean_up"]:
        console.print("\n[bold blue]Cleaning up empty directories...[/]")
        cleanup_empty_dirs(root_dir, console)


if __name__ == "__main__":
    args = {
        "directory": "data/testing",
        "model": "gpt-4.1-nano",  
        "debug": True,
        "api_key": None,
        "api_key_env": "OPENAI_API_KEY",
        "port": None,
        "prompt": "Sort all files with text content into the text directory and all other files into the misc directory",
        "clean_up": True
    }

    main(args)