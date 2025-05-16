from src.read_files import get_files
from visualize_structure import visualize_structure
import json

def main(directory_path: str):
    files = get_files(directory_path)
    old_filepaths = [file["path"] for file in files]

    json_path = "data/proposed_file_structure.json"
    with open(json_path, "r") as f:
        file_mapping = json.load(f)
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

    main("testing_structure")