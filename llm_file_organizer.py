from src.read_files import get_files
from src.generate_structure_proposal import generate_structure_proposal
from src.visualize_structure import visualize_structure
import json
import os

def main(directory_path: str):
    api_key = os.getenv("OPENAI_API_KEY")
    model = "gpt-4.1-nano"

    file_mapping = generate_structure_proposal(directory_path, api_key, model)

    files = get_files(directory_path)
    old_filepaths = [file["path"] for file in files]
    new_filepaths = list(file_mapping.values())

    print("=== Original file structure ===")
    visualize_structure(old_filepaths)
    print("\n")
    print("=== Proposed file structure ===")
    visualize_structure(new_filepaths)


if __name__ == "__main__":
    # import argparse
    # parser = argparse.ArgumentParser(description="File organization tool")
    # parser.add_argument("directory", type=str, help="Directory to organize")
    # args = parser.parse_args()
    # main(args.directory)

    main("data/testing")