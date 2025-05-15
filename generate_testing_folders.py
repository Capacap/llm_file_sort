import os
import random
import string

def generate_random_name(length=8):
    """Generate a random alphanumeric name."""
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))

def create_folder_structure(root_path, min_dirs=2, max_dirs=5, max_depth=3, current_depth=0):
    """Recursively create a folder structure with random subdirectories."""
    # Create the root directory if it doesn't exist
    if not os.path.exists(root_path):
        os.makedirs(root_path)
    
    # Stop recursion at max depth
    if current_depth >= max_depth:
        return
    
    # Decide how many subdirectories to create at this level
    # Ensure we create at least the minimum number of directories
    num_dirs = random.randint(min_dirs, max_dirs)
    
    # Create and populate subdirectories
    for _ in range(num_dirs):
        dir_name = generate_random_name()
        dir_path = os.path.join(root_path, dir_name)
        os.makedirs(dir_path, exist_ok=True)
        create_folder_structure(dir_path, min_dirs, max_dirs, max_depth, current_depth + 1)

if __name__ == "__main__":
    output_dir = "testing_structure"
    min_dirs = 2    # Minimum number of folders at each level
    max_dirs = 5    # Maximum number of folders at each level
    max_depth = 3   # Maximum folder nesting
    
    # Remove existing structure if it exists
    if os.path.exists(output_dir):
        import shutil
        shutil.rmtree(output_dir)
    
    create_folder_structure(output_dir, min_dirs, max_dirs, max_depth)
    print(f"Random folder structure created at '{output_dir}'")
