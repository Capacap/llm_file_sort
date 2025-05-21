"""ML-powered file organization tool that maps files to appropriate directories."""
# --- Imports ---
import os
import sys
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.tree import Tree
from rich.columns import Columns
from rich.panel import Panel
from src.file_utils import list_files_with_metadata, extract_text_content, encode_image_content, list_directories
from src.ai_utils import (
    ai_generate_image_caption, ai_generate_text_summary, ai_map_file_to_directory,
    AIUtilsError, ImageProcessingError, TextProcessingError, MappingError, ModelConnectionError
)

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
    validation_results["source_missing"] = [src for src in mapping.keys() if not os.path.exists(src)]
    validation_results["destination_exists"] = [dst for src, dst in mapping.items() 
                                               if os.path.exists(dst) and os.path.normpath(src) != os.path.normpath(dst)]
    
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

def process_files_content(files, directory, model, api_key, port=None, verbose=False, console=None):
    """Process files to generate content summaries."""
    console = console or Console()
    error_count = 0
    
    with Progress(SpinnerColumn(), TaskProgressColumn(), TextColumn("- {task.description}"), console=console) as progress:
        task = progress.add_task("Processing files", total=len(files))
        
        for file in files:
            progress.update(task, description=f"{file['relative_path']}")
            file_path = os.path.join(directory, file["relative_path"])
            file["content_summary"] = "No summary available."

            try:
                if image_content := encode_image_content(file_path):
                    file["has_image_content"] = True
                    file["content_summary"] = ai_generate_image_caption(
                        image_content, file["extension"], model, api_key, port=port, debug=verbose)
                elif text_content := extract_text_content(file_path, 1024):
                    file["has_text_content"] = True
                    file["content_summary"] = ai_generate_text_summary(
                        text_content, model, api_key, port=port, debug=verbose)
            except ImageProcessingError as e:
                error_count += 1
                console.print(f"[yellow]Warning: Could not caption image {file['relative_path']}: {str(e)}[/]")
            except TextProcessingError as e:
                error_count += 1
                console.print(f"[yellow]Warning: Could not summarize text {file['relative_path']}: {str(e)}[/]")
            except ModelConnectionError as e:
                error_count += 1
                console.print(f"[red]Error: Model connection issue while processing {file['relative_path']}: {str(e)}[/]")
            except AIUtilsError as e:
                error_count += 1
                console.print(f"[red]Error: AI processing failed for {file['relative_path']}: {str(e)}[/]")
            except Exception as e:
                error_count += 1
                console.print(f"[red]Unexpected error processing {file['relative_path']}: {str(e)}[/]")
                
            progress.advance(task)
    
    if error_count > 0:
        console.print(f"[yellow]Completed with {error_count} warnings/errors[/]")
    
    return files

def map_files_to_directories(files, directory_structure, model, api_key, port=None, prompt=None, verbose=False, console=None):
    """Map files to appropriate directories using AI."""
    console = console or Console()
    relative_file_mapping = {}
    error_count = 0
    
    with Progress(SpinnerColumn(), TaskProgressColumn(), TextColumn("- {task.description}"), console=console) as progress:
        task = progress.add_task("Mapping files", total=len(files))
        
        for file in files:
            progress.update(task, description=f"{file['relative_path']}")
            try:
                mapped_file = ai_map_file_to_directory(
                    file, directory_structure, model, api_key, port=port, prompt=prompt, debug=verbose)
                relative_file_mapping.update(mapped_file)
            except (MappingError, ModelConnectionError, AIUtilsError, Exception) as e:
                error_count += 1
                error_type = "Warning" if isinstance(e, MappingError) else "Error"
                error_color = "yellow" if isinstance(e, MappingError) else "red"
                console.print(f"[{error_color}]{error_type}: {type(e).__name__} for {file['relative_path']}: {str(e)}[/]")
                # Add a default mapping to keep the file where it is
                relative_file_mapping[file["relative_path"]] = os.path.dirname(file["relative_path"])
                
            progress.advance(task)
    
    if error_count > 0:
        console.print(f"[yellow]Mapping completed with {error_count} warnings/errors[/]")
        
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
    
    console.print("[bold green]✓ File mapping validation successful![/]" if not has_issues else 
                 "[bold yellow]Warning: Issues found in file mapping.[/]")
    
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
    console = Console(no_color=kw_args.get("no_color", False))
    try:
        root_dir = os.path.abspath(kw_args["directory"])
        
        # Load API key from environment if not provided
        if kw_args["api_key"] is None and kw_args["api_key_env"]:
            kw_args["api_key"] = os.environ.get(kw_args["api_key_env"])
            if not kw_args["api_key"]:
                console.print(f"\n[bold yellow]Warning: Environment variable {kw_args['api_key_env']} not found or empty.[/]")
                console.print("[yellow]Continuing without API key - this may work for local models.[/]")
        
        # Process file content
        console.print("\n[bold blue]Generating content summaries...[/]")
        files = process_files_content(
            list_files_with_metadata(kw_args["directory"]), 
            kw_args["directory"], kw_args["model"], kw_args["api_key"], 
            port=kw_args.get("port"), verbose=kw_args["verbose"], console=console
        )
        
        # Generate file mappings
        console.print("\n[bold blue]Generating file mappings...[/]")
        directory_structure = kw_args["custom_directories"].split(",") if "custom_directories" in kw_args and kw_args["custom_directories"] else list_directories(kw_args["directory"])
        
        if "custom_directories" in kw_args and kw_args["custom_directories"]:
            console.print(f"[green]Using {len(directory_structure)} custom directories[/]")

        # Map files to directories
        relative_file_mapping = map_files_to_directories(
            files, directory_structure, kw_args["model"], kw_args["api_key"], 
            port=kw_args.get("port"), prompt=kw_args.get("prompt"), 
            verbose=kw_args["verbose"], console=console
        )

        if kw_args["verbose"]:
            console.print("\n[bold blue]Relative file mappings:[/]")
            for src, dst in relative_file_mapping.items():
                console.print(f"[blue]{src} -> {dst}[/]")

        # Create absolute path mappings
        absolute_file_mapping = {
            os.path.join(root_dir, rel_src): os.path.join(root_dir, rel_dst.lstrip('/'), os.path.basename(rel_src)) 
            for rel_src, rel_dst in relative_file_mapping.items()
        }
        
        if kw_args["verbose"]:
            console.print("\n[bold blue]Absolute file mappings:[/]")
            for src, dst in absolute_file_mapping.items():
                console.print(f"[blue]{src} -> {dst}[/]")

        # Validate mapping and show issues
        console.print("\n[bold blue]Validating file mapping...[/]")
        validation = validate_file_mapping(absolute_file_mapping)
        has_issues = display_validation_issues(validation, console)
        
        # Visualize current and proposed organization
        current_tree = build_file_tree(absolute_file_mapping.keys(), "Current Organization", "yellow", root_dir)
        proposed_tree = build_file_tree(absolute_file_mapping.values(), "Proposed Organization", "green", root_dir)
        console.print(Columns([current_tree, proposed_tree]))
        
        # Check if changes needed
        changes_needed = any(os.path.normpath(src) != os.path.normpath(dst) for src, dst in absolute_file_mapping.items())
        if not changes_needed:
            console.print("\n[bold green]No file organization changes needed.[/]")
            return
            
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
            
    except ModelConnectionError as e:
        console.print(Panel(f"[bold red]Model Connection Error: {str(e)}[/]", title="Error", border_style="red"))
        console.print("[yellow]Suggestions:[/]")
        console.print(" • Check your API key\n • Verify port number if using a local model\n • Ensure the model server is running\n • Check your internet connection")
        sys.exit(1)

    except AIUtilsError as e:
        console.print(Panel(f"[bold red]AI Processing Error: {str(e)}[/]", title="Error", border_style="red"))
        sys.exit(1)

    except Exception as e:
        console.print(Panel(f"[bold red]Unexpected Error: {str(e)}[/]", title="Error", border_style="red"))
        if kw_args["verbose"]:
            import traceback
            console.print("[red]Traceback:[/]")
            console.print(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    import argparse, os, sys
    from pathlib import Path
    
    VERSION = "1.0.0"
    
    # Environment variables
    env_vars = {
        "directory": "LFO_DIRECTORY",
        "model": "LFO_MODEL",
        "api_key": "LFO_API_KEY"
    }
    
    # Load from environment
    config = {}
    for key, env in env_vars.items():
        if env in os.environ:
            config[key] = os.environ[env]
    
    examples = """
Examples:
  python main.py -d ~/Downloads -m ollama/gemma3:4b
  python main.py -d ~/Documents/unsorted -m openai/gpt-4o --api-key-env OPENAI_API_KEY
  python main.py -d ~/Pictures -m local/model --port 11434 -c photos,documents,work
    """
    
    parser = argparse.ArgumentParser(
        description="ML-powered file organization tool",
        epilog=examples,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Core arguments
    parser.add_argument("-d", "--directory", default=config.get("directory"),
                        help="(Required) Directory to organize")
    parser.add_argument("-m", "--model", default=config.get("model"),
                        help="(Required) AI model to use")
    parser.add_argument("-c", "--custom-directories", default=config.get("custom_directories"),
                        help="(Optional) Comma-separated list of directories")
    parser.add_argument("-p", "--prompt", default=config.get("prompt"),
                        help="(Optional) Additional instructions for the AI")
    
    # Argument groups
    groups = {
        "api": parser.add_argument_group("API Settings"),
        "output": parser.add_argument_group("Output Settings"),
        "behavior": parser.add_argument_group("Behavior Settings"),
        "config": parser.add_argument_group("Configuration")
    }
    
    # API settings
    groups["api"].add_argument("--api-key", default=config.get("api_key"), 
                              help="API key for the model")
    groups["api"].add_argument("--api-key-env", default=config.get("api_key_env"),
                              help="Environment variable with API key")
    groups["api"].add_argument("--port", type=int, default=config.get("port"),
                              help="Port for local model server")
    
    # Output settings
    groups["output"].add_argument("-v", "--verbose", action="store_true", 
                                 help="Enable detailed output")
    groups["output"].add_argument("--no-color", action="store_true",
                                 help="Disable colored output")
    
    # Behavior settings
    groups["behavior"].add_argument("--no-cleanup", dest="clean_up", action="store_false",
                                   default=True, 
                                   help="Disable cleanup of empty directories")
    
    # Configuration
    groups["config"].add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    
    args = parser.parse_args()
    
    # Validate required arguments
    if not all([args.directory, args.model]):
        missing = []
        if not args.directory: missing.append("directory (-d/--directory)")
        if not args.model: missing.append("model (-m/--model)")
        print(f"Error: Missing required arguments: {', '.join(missing)}")
        print(f"Run '{sys.argv[0]} --help' for usage information")
        sys.exit(1)
    
    # Validate and expand directory path
    args.directory = os.path.abspath(os.path.expanduser(args.directory))
    if not os.path.exists(args.directory):
        print(f"Error: Directory not found: {args.directory}")
        sys.exit(1)
    
    # Validate custom directories format
    if args.custom_directories:
        dirs = args.custom_directories.split(",")
        if len(dirs) == 1 and " " in args.custom_directories:
            print(f"Error: Invalid custom directories format: '{args.custom_directories}'")
            print("Use comma-separated format without spaces between directory names.")
            print("Example: docs,images,videos")
            sys.exit(1)
    
    # Remove config args not used by main()
    args_dict = {k: v for k, v in vars(args).items() 
                if k not in ["version"]}
    
    main(args_dict)