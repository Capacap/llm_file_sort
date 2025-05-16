import os
from src.file_utils import get_files, move_files
from src.generate_structure_proposal import generate_structure_proposal
from src.visualize_structure import visualize_structure
from rich.console import Console

def main(directory_path: str, verbose: bool = False):
    api_key = os.getenv("OPENAI_API_KEY")
    model = "gpt-4.1-nano"
    
    # Create a shared console instance
    console = Console()

    console.print("\n=== [bold blue]Starting file organization[/bold blue] ===")

    files = get_files(directory_path)
    file_mapping = generate_structure_proposal(files, api_key, model, verbose=verbose, console=console)

    console.print("\n=== [bold blue]Original file structure[/bold blue] ===")
    visualize_structure(list(file_mapping.keys()), console=console)

    console.print("\n=== [bold blue]Proposed file structure[/bold blue] ===")
    visualize_structure(list(file_mapping.values()), console=console)

    user_confirmation = input("\nProceed? (y/n): ")
    if user_confirmation == "y":
        console.print("\n=== [bold green]Moving files[/bold green] ===")
        absolute_file_mapping = {os.path.join(directory_path, k): os.path.join(directory_path, v) for k, v in file_mapping.items()}
        move_files(absolute_file_mapping, console=console)
    else:
        console.print("Operation cancelled.")


if __name__ == "__main__":
    # import argparse
    # parser = argparse.ArgumentParser(description="File organization tool")
    # parser.add_argument("directory", type=str, help="Directory to organize")
    # args = parser.parse_args()
    # main(args.directory)

    args = {
        "directory": "data/testing",
        "verbose": True
    }

    main(args["directory"], args["verbose"])