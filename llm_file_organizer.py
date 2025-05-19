import os
import sys
import json
from rich.console import Console
from src.file_utils import get_file_info_list, move_files, visualize_file_tree, clean_empty_directories
from src.ai_utils import (
    format_files_for_ai_context, 
    format_directories_for_ai_context,
    ai_generate_directory_structure,
    ai_map_files_to_directories,
    ai_fix_missing_files,
    validate_file_mapping, 
)

def validate_args(directory_path: str, debug: bool, model: str, api_key: str, api_key_env: str, port: int, console: Console) -> bool:
    """Validate command line arguments and parameters.
    
    Args:
        directory_path: Path to the directory to organize
        debug: Whether to show debug information
        model: LLM model to use
        api_key: API key for LLM service
        api_key_env: Name of environment variable containing API key
        port: Port for Ollama local inference
        console: Console instance for output
        
    Returns:
        True if all arguments are valid, False otherwise
    """
    # Check if directory exists
    if not directory_path:
        console.print("[bold red]Error:[/bold red] Directory path must be provided")
        return False
        
    if not os.path.exists(directory_path):
        console.print(f"[bold red]Error:[/bold red] Directory '{directory_path}' does not exist")
        return False
    
    if not os.path.isdir(directory_path):
        console.print(f"[bold red]Error:[/bold red] '{directory_path}' is not a directory")
        return False
        
    # Check if model is provided
    if not model:
        console.print("[bold red]Error:[/bold red] Model name must be provided")
        return False
    
    # Check if API key is available when using OpenAI models
    if "gpt" in model.lower() and not api_key and not api_key_env:
        console.print("[bold red]Error:[/bold red] API key or API key environment variable must be provided for OpenAI models")
        console.print("Set an environment variable or provide the API key directly")
        return False
    
    # If API key environment variable is provided, check if it exists
    if api_key_env and os.getenv(api_key_env) is None:
        console.print(f"[bold red]Error:[/bold red] Environment variable '{api_key_env}' not found or empty")
        return False
    
    # Validate port if provided
    if port is not None:
        if not isinstance(port, int) or port <= 0 or port > 65535:
            console.print(f"[bold red]Error:[/bold red] Invalid port number: {port}")
            console.print("Port must be an integer between 1 and 65535")
            return False
    
    return True

def main_two_step(kw_args: dict):
    console = Console()

    # Get files and format them for AI processing
    file_info_list = get_file_info_list(kw_args["directory"])
    formatted_files = format_files_for_ai_context(file_info_list)

    # Generate directory structure
    assistant_response, user_message = ai_generate_directory_structure(
        api_key=kw_args["api_key"],
        model=kw_args["model"],
        formatted_files=formatted_files,
        port=kw_args["port"],
        prompt=kw_args["prompt"]
    )

    # Debug print user and assistant messages
    if kw_args["debug"]:
        console.print("=== [bold blue]User Message[/bold blue] ===")
        console.print(user_message["content"])
        console.print("=== [bold blue]Assistant Response[/bold blue] ===")
        console.print(assistant_response.choices[0].message.content)

    # Parse assistant response
    try:
        dir_structure = json.loads(assistant_response.choices[0].message.content)
        directories = dir_structure.get("directories", [])
        formatted_dirs = format_directories_for_ai_context(directories)
    except json.JSONDecodeError:
        console.print("[bold red]Error:[/bold red] Failed to parse assistant response as JSON")
        return

    # Map files to directories
    assistant_response, user_message = ai_map_files_to_directories(
        api_key=kw_args["api_key"],
        model=kw_args["model"],
        formatted_files=formatted_files,
        formatted_directories=formatted_dirs,
        port=kw_args["port"],
        prompt=kw_args["prompt"]
    )

    # Debug print user and assistant messages
    if kw_args["debug"]:
        console.print("=== [bold blue]User Message[/bold blue] ===")
        console.print(user_message["content"])
        console.print("=== [bold blue]Assistant Response[/bold blue] ===")
        console.print(assistant_response.choices[0].message.content)

    # Parse assistant response
    try:
        file_mapping = json.loads(assistant_response.choices[0].message.content)
    except json.JSONDecodeError:
        console.print("[bold red]Error:[/bold red] Failed to parse assistant response as JSON")
        return
    
    # Check for missing files
    included_files, missing_files = validate_file_mapping(file_info_list, file_mapping, console)
    if missing_files:
        file_mapping = ai_fix_missing_files(api_key=kw_args["api_key"], model=kw_args["model"], formatted_files=formatted_files, formatted_directories=formatted_dirs, file_mapping=file_mapping, missing_files=missing_files, port=kw_args["port"], prompt=kw_args["prompt"])
        included_files, missing_files = validate_file_mapping(file_info_list, file_mapping, console)
        if missing_files:
            console.print("[bold red]Error:[/bold red] Failed to fix missing files")
            return

    # Visualize original file structure
    console.print("\n=== [bold blue]Original file structure[/bold blue] ===")
    visualize_file_tree(list(file_mapping.keys()), console=console)

    # Visualize proposed file structure
    console.print("\n=== [bold blue]Proposed file structure[/bold blue] ===")
    visualize_file_tree(list(file_mapping.values()), console=console)

    # Get user confirmation
    user_confirmation = input("Are you sure you want to move the files? (y/n): ")
    if user_confirmation.lower() != "y":
        console.print("[bold yellow]Warning:[/bold yellow] Files not moved")
        return
    
    # Move files
    root_dir = kw_args["directory"]
    absolute_mapping = {os.path.abspath(os.path.join(root_dir, old)): os.path.abspath(os.path.join(root_dir, new)) for old, new in file_mapping.items()}
    move_files(absolute_mapping, console=console, debug=kw_args["debug"])

    # Clean empty directories
    clean_empty_directories(absolute_mapping, console=console, debug=kw_args["debug"])

if __name__ == "__main__":
    args = {
        "directory": "data/testing",
        "model": "gpt-4.1-nano",  
        "debug": True,
        "api_key": None,
        "api_key_env": "OPENAI_API_KEY",
        "port": None,
        "prompt": "Sort all text files into a text directory and all other files into a misc directory",
    }

    main_two_step(args)