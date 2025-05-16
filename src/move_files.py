import json
import os
import shutil

# Hardcoded paths
json_path = "proposed_file_structure.json"
new_root_dir = "testing_result"

# Load the file structure mapping
with open(json_path, "r") as f:
    file_mapping = json.load(f)

# Process each file
for source_rel, dest_rel in file_mapping.items():
    # Source path is the original path
    source_path = source_rel
    
    # Replace the root directory in the destination path
    # Assuming the first directory in the path is the root
    if "/" in dest_rel:
        # Get the original root dir
        original_root = dest_rel.split("/")[0]
        # Replace the original root with new_root_dir
        dest_path = dest_rel.replace(original_root, new_root_dir, 1)
    else:
        # If there's no directory structure, just put it in the new root
        dest_path = os.path.join(new_root_dir, dest_rel)
    
    # Create destination directory if it doesn't exist
    dest_dir = os.path.dirname(dest_path)
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    
    # Copy the file
    if os.path.exists(source_path):
        print(f"Copying: {source_path} -> {dest_path}")
        shutil.copy2(source_path, dest_path)
    else:
        print(f"Warning: Source file not found: {source_path}")
