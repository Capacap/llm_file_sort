import os
import sys
from src.file_utils import get_files, move_files, visualize_file_tree
from src.ai_utils import build_file_mapping, validate_file_mapping, MissingFilesError
from rich.console import Console

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

def main(directory_path: str, model: str, debug: bool = False, api_key: str = None, api_key_env: str = None, port: int = None, prompt: str = None):
    """Main function for organizing files.
    
    Args:
        directory_path: Path to the directory to organize
        model: LLM model to use
        debug: Whether to show debug information
        api_key: Direct API key for LLM service
        api_key_env: Name of environment variable containing API key
        port: Port for Ollama local inference
        prompt: Optional additional instructions for the AI
    """
    # Create a shared console instance
    console = Console()

    # Validate arguments
    if not validate_args(directory_path, debug, model, api_key, api_key_env, port, console):
        sys.exit(1)
    
    # Get API key - prioritize direct key over environment variable
    effective_api_key = api_key
    
    # If direct API key not provided, try environment variable specified by api_key_env
    if effective_api_key is None and api_key_env:
        effective_api_key = os.getenv(api_key_env)
        
    # Final check for OpenAI models needing an API key
    if effective_api_key is None and "gpt" in model.lower():
        console.print("[bold red]Error:[/bold red] No API key available from any source")
        sys.exit(1)

    console.print("\n=== [bold blue]Starting file organization[/bold blue] ===")

    # Get files
    files = get_files(directory_path)
    
    if not files:
        console.print(f"[bold yellow]Warning:[/bold yellow] No files found in '{directory_path}'")
        sys.exit(0)
        
    # Generate the structure proposal
    file_mapping = build_file_mapping(files, effective_api_key, model, debug, console, port, prompt)
    
    # Validate the file mapping
    try:
        file_mapping = validate_file_mapping(files, file_mapping, console)
    except MissingFilesError as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        console.print("The AI-generated file mapping is missing some files. Please try again.")
        sys.exit(2)

    # Visualize original file structure
    console.print("\n=== [bold blue]Original file structure[/bold blue] ===")
    visualize_file_tree(list(file_mapping.keys()), console=console)

    # Visualize proposed file structure
    console.print("\n=== [bold blue]Proposed file structure[/bold blue] ===")
    visualize_file_tree(list(file_mapping.values()), console=console)

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
    # parser.add_argument("--api-key", type=str, help="API key for LLM service")
    # parser.add_argument("--api-key-env", type=str, help="Name of environment variable containing API key")
    # parser.add_argument("--port", type=int, help="Port for Ollama local inference")
    # parser.add_argument("--prompt", type=str, help="Additional instructions for the AI")
    # args = parser.parse_args()
    # main(args.directory, args.model, args.debug, args.api_key, args.api_key_env, args.port, args.prompt)

    args = {
        "directory": "data/testing",
        "model": "gpt-4.1-nano",  
        "debug": True,
        "api_key": None,
        "api_key_env": "OPENAI_API_KEY",
        "port": None,
        "prompt": "Organize the all text based files into a single folder called 'text_files' and the rest into a folder called 'other_files'"
    }

    main(
        args["directory"],
        args["model"],
        args["debug"],
        args["api_key"],
        args["api_key_env"],
        args["port"],
        args["prompt"]
    )