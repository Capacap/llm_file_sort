import os
import random
import string

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

def populate_with_files(root_path, min_files=1, max_files=5):
    """Populate each directory with random text files."""
    if not os.path.exists(root_path):
        raise ValueError(f"Directory '{root_path}' does not exist")
        
    for dirpath, _, _ in os.walk(root_path):
        num_files = random.randint(min_files, max_files)
        for _ in range(num_files):
            file_name = f"{generate_random_name()}.txt"
            file_path = os.path.join(dirpath, file_name)
            
            with open(file_path, "w") as f:
                f.write(generate_random_content())

if __name__ == "__main__":
    output_dir = "testing_structure"
    min_files = 1
    max_files = 5
    
    try:
        populate_with_files(output_dir, min_files, max_files)
        print(f"Successfully populated '{output_dir}' with random text files")
    except ValueError as e:
        print(f"Error: {e}")
