import os
from src.file_utils import get_files, move_files
from src.generate_structure_proposal import generate_structure_proposal
from src.visualize_structure import visualize_structure
from rich.console import Console

def main(directory_path: str, debug: bool = False, model: str = "gpt-4.1-nano", api_key: str = None, port: int = 11434):
    # Use environment variable for API key if not provided
    if api_key is None:
        api_key = os.getenv("OPENAI_API_KEY")
    
    # Create a shared console instance
    console = Console()

    console.print("\n=== [bold blue]Starting file organization[/bold blue] ===")

    # Get files
    files = get_files(directory_path)
    file_mapping = generate_structure_proposal(files, api_key, model, debug=debug, console=console, port=port)

    # Visualize original file structure
    console.print("\n=== [bold blue]Original file structure[/bold blue] ===")
    visualize_structure(list(file_mapping.keys()), console=console)

    # Visualize proposed file structure
    console.print("\n=== [bold blue]Proposed file structure[/bold blue] ===")
    visualize_structure(list(file_mapping.values()), console=console)

    # Ask user for confirmation
    user_confirmation = input("\nProceed? (y/n): ")
    if user_confirmation == "y":
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
    # parser.add_argument("--debug", action="store_true", help="Show debug information")
    # parser.add_argument("--model", type=str, default="gpt-4.1-nano", help="LLM model to use")
    # parser.add_argument("--api-key", type=str, help="API key for LLM service (defaults to OPENAI_API_KEY env var)")
    # parser.add_argument("--port", type=int, default=11434, help="Port for Ollama local inference (default: 11434)")
    # args = parser.parse_args()
    # main(args.directory, args.debug, args.model, args.api_key, args.port)

    args = {
        "directory": "data/testing",
        "debug": True,
        "model": "gpt-4.1-nano",
        "api_key": None,  # Will use environment variable
        "port": None # Default Ollama port
    }

    main(
        args["directory"], 
        args["debug"], 
        args["model"], 
        args["api_key"],
        args["port"]
    )