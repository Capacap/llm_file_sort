import os
import sys
from src.file_utils import get_files, move_files
from src.generate_structure_proposal import generate_structure_proposal
from src.visualize_structure import visualize_structure
from rich.console import Console

def validate_args(directory_path: str, debug: bool, model: str, api_key: str, port: int, console: Console) -> bool:
    """Validate command line arguments and parameters.
    
    Args:
        directory_path: Path to the directory to organize
        debug: Whether to show debug information
        model: LLM model to use
        api_key: API key for LLM service
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
    if "gpt" in model.lower() and not api_key:
        console.print("[bold red]Error:[/bold red] API key is required for OpenAI models")
        console.print("Set the OPENAI_API_KEY environment variable or provide it as an argument")
        return False
    
    # Validate port if provided
    if port is not None:
        if not isinstance(port, int) or port <= 0 or port > 65535:
            console.print(f"[bold red]Error:[/bold red] Invalid port number: {port}")
            console.print("Port must be an integer between 1 and 65535")
            return False
    
    return True

def main(directory_path: str, model: str, debug: bool = False, api_key: str = None, port: int = None):
    # Create a shared console instance
    console = Console()

    # Validate arguments
    if not validate_args(directory_path, debug, model, api_key, port, console):
        sys.exit(1)
    
    # Use environment variable for API key if not provided
    if api_key is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key is None and "gpt" in model.lower():
            console.print("[bold red]Error:[/bold red] No API key provided and OPENAI_API_KEY environment variable not set")
            sys.exit(1)

    console.print("\n=== [bold blue]Starting file organization[/bold blue] ===")

    # Get files
    files = get_files(directory_path)
    
    if not files:
        console.print(f"[bold yellow]Warning:[/bold yellow] No files found in '{directory_path}'")
        sys.exit(0)
        
    file_mapping = generate_structure_proposal(files, api_key, model, debug=debug, console=console, port=port)

    # Visualize original file structure
    console.print("\n=== [bold blue]Original file structure[/bold blue] ===")
    visualize_structure(list(file_mapping.keys()), console=console)

    # Visualize proposed file structure
    console.print("\n=== [bold blue]Proposed file structure[/bold blue] ===")
    visualize_structure(list(file_mapping.values()), console=console)

    # Ask user for confirmation
    user_confirmation = input("\nProceed? (y/n): ")
    if user_confirmation.lower() == "y":
        # Move files
        console.print("\n=== [bold green]Moving files[/bold green] ===")
        absolute_file_mapping = {os.path.join(directory_path, k): os.path.join(directory_path, v) for k, v in file_mapping.items()}
        move_files(absolute_file_mapping, console=console)
    else:
        console.print("Operation cancelled.")


if __name__ == "__main__":
    # Uncomment to use command-line arguments
    # import argparse
    # parser = argparse.ArgumentParser(description="File organization tool")
    # parser.add_argument("directory", type=str, help="Directory to organize")
    # parser.add_argument("--model", type=str, required=True, help="LLM model to use")
    # parser.add_argument("--debug", action="store_true", help="Show debug information")
    # parser.add_argument("--api-key", type=str, help="API key for LLM service (defaults to OPENAI_API_KEY env var)")
    # parser.add_argument("--port", type=int, help="Port for Ollama local inference (default: 11434)")
    # args = parser.parse_args()
    # main(args.directory, args.model, args.debug, args.api_key, args.port)

    # Use environment variable for API key
    api_key = os.getenv("OPENAI_API_KEY")

    args = {
        "directory": "data/testing",
        "model": "gpt-4.1-nano",  
        "debug": True,
        "api_key": api_key,
        "port": None
    }

    main(
        args["directory"],
        args["model"],
        args["debug"],
        args["api_key"],
        args["port"]
    )