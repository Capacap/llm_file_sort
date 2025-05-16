import json
import os
from src.read_files import get_files
from src.generate_structure_proposal import generate_structure_proposal
from src.visualize_structure import visualize_structure
from src.move_files import move_files

def main(directory_path: str):
    api_key = os.getenv("OPENAI_API_KEY")
    model = "gpt-4.1-nano"

    files = get_files(directory_path)
    file_mapping = generate_structure_proposal(files, api_key, model)

    old_filepaths = list(file_mapping.keys())
    new_filepaths = list(file_mapping.values())

    print("=== Original file structure ===")
    visualize_structure(old_filepaths)

    print("\n=== Proposed file structure ===")
    visualize_structure(new_filepaths)

    absolute_file_mapping = {os.path.join(directory_path, k): os.path.join(directory_path, v) for k, v in file_mapping.items()}
    for k, v in absolute_file_mapping.items():
        print(f"{k} -> {v}")

    user_confirmation = input("\nProceed? (y/n): ")
    if user_confirmation == "y":
        print("\n=== Moving files ===")
        move_files(absolute_file_mapping)
    else:
        print("Operation cancelled.")


if __name__ == "__main__":
    # import argparse
    # parser = argparse.ArgumentParser(description="File organization tool")
    # parser.add_argument("directory", type=str, help="Directory to organize")
    # args = parser.parse_args()
    # main(args.directory)

    main("data/testing")