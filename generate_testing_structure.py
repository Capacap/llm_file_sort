import os
import random
import string
import shutil

def generate_random_name(length=8):
    """Generate a random alphanumeric name."""
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))

def generate_random_content(min_lines=1, max_lines=10, min_chars=10, max_chars=100):
    """Generate random text content for files."""
    num_lines = random.randint(min_lines, max_lines)
    content = []
    
    for _ in range(num_lines):
        line_length = random.randint(min_chars, max_chars)
        line = "".join(random.choice(string.ascii_letters + string.digits + " \n") for _ in range(line_length))
        content.append(line)
    
    return "\n".join(content)

def create_folder_structure(root_path, min_dirs=2, max_dirs=5, max_depth=3, current_depth=0):
    """Recursively create a folder structure with random subdirectories."""
    # Create the root directory if it doesn't exist
    if not os.path.exists(root_path):
        os.makedirs(root_path)
    
    # Stop recursion at max depth
    if current_depth >= max_depth:
        return
    
    # Decide how many subdirectories to create at this level
    num_dirs = random.randint(min_dirs, max_dirs)
    
    # Create and populate subdirectories
    for _ in range(num_dirs):
        dir_name = generate_random_name()
        dir_path = os.path.join(root_path, dir_name)
        os.makedirs(dir_path, exist_ok=True)
        create_folder_structure(dir_path, min_dirs, max_dirs, max_depth, current_depth + 1)

def populate_with_files(root_path, min_files=1, max_files=5, min_lines=1, max_lines=10, min_chars=10, max_chars=100):
    """Populate each directory with random text files."""
    if not os.path.exists(root_path):
        raise ValueError(f"Directory '{root_path}' does not exist")
        
    for dirpath, _, _ in os.walk(root_path):
        num_files = random.randint(min_files, max_files)
        for _ in range(num_files):
            file_name = f"{generate_random_name()}.txt"
            file_path = os.path.join(dirpath, file_name)
            
            with open(file_path, "w") as f:
                f.write(generate_random_content(min_lines, max_lines, min_chars, max_chars))

def generate_testing_structure(output_dir, min_dirs=2, max_dirs=5, max_depth=3, 
                              min_files=1, max_files=5, min_lines=1, max_lines=10, 
                              min_chars=10, max_chars=100, clean_existing=True):
    """Generate a random folder structure and populate it with random files."""
    # Remove existing structure if requested
    if clean_existing and os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    
    # Create folder structure
    create_folder_structure(output_dir, min_dirs, max_dirs, max_depth)
    
    # Populate with files
    populate_with_files(output_dir, min_files, max_files, min_lines, max_lines, min_chars, max_chars)
    
    return output_dir

if __name__ == "__main__":
    output_dir = "testing_structure"
    
    # Folder structure parameters
    min_dirs = 2      # Minimum number of folders at each level
    max_dirs = 5      # Maximum number of folders at each level
    max_depth = 3     # Maximum folder nesting
    
    # File generation parameters
    min_files = 1     # Minimum files per directory
    max_files = 5     # Maximum files per directory
    min_lines = 1     # Minimum lines per file
    max_lines = 10    # Maximum lines per file
    min_chars = 10    # Minimum characters per line
    max_chars = 100   # Maximum characters per line
    
    # Generate the structure
    generate_testing_structure(
        output_dir, 
        min_dirs, max_dirs, max_depth,
        min_files, max_files, min_lines, max_lines, min_chars, max_chars
    )
    
    print(f"Testing structure created at '{output_dir}'") 