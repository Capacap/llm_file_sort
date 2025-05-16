import shutil
import os

def move_files(file_mapping):
    """
    Move files according to the provided mapping and clean up empty source directories.
    
    Args:
        file_mapping: Dictionary where keys are source paths and values are destination paths
    """
    # Track source directories to check for cleanup later
    source_dirs = set()
    
    for source, destination in file_mapping.items():
        if not os.path.exists(source):
            print(f"Warning: Source file {source} does not exist. Skipping.")
            continue
            
        # Store source directory for later cleanup
        source_dir = os.path.dirname(source)
        if source_dir:
            source_dirs.add(source_dir)
            
        # Create destination directory if it doesn't exist
        dest_dir = os.path.dirname(destination)
        if dest_dir and not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
            
        # Move the file
        try:
            shutil.move(source, destination)
            print(f"Moved: {source} → {destination}")
        except Exception as e:
            print(f"Error moving {source} to {destination}: {e}")
    
    # Clean up empty source directories (deepest first)
    if source_dirs:
        # Sort directories by depth (descending) to handle nested dirs properly
        dirs_to_check = sorted(source_dirs, key=lambda x: x.count(os.sep), reverse=True)
        
        for dir_path in dirs_to_check:
            try:
                # Check if directory exists and is empty
                if os.path.exists(dir_path) and not os.listdir(dir_path):
                    os.rmdir(dir_path)
                    print(f"Removed empty directory: {dir_path}")
                    
                    # Check if parent directories are now empty
                    parent = os.path.dirname(dir_path)
                    while parent and os.path.exists(parent) and not os.listdir(parent):
                        os.rmdir(parent)
                        print(f"Removed empty parent directory: {parent}")
                        parent = os.path.dirname(parent)
            except Exception as e:
                print(f"Error removing directory {dir_path}: {e}")

