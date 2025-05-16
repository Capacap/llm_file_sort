import os
import random
import string
import shutil
import datetime
import json
from textwrap import dedent

# Realistic folder names
FOLDER_NAMES = [
    "documents", "images", "videos", "music", "downloads", "projects", 
    "backups", "reports", "data", "archives", "presentations", "meetings",
    "research", "templates", "logs", "configs", "scripts", "resources",
    "notes", "personal", "work", "drafts", "books", "tutorials", "samples"
]

# Common file types with extensions
FILE_TYPES = {
    "text": [".txt", ".md", ".csv", ".log", ".json", ".xml"],
    "document": [".doc", ".docx", ".pdf", ".odt", ".rtf"],
    "spreadsheet": [".xls", ".xlsx", ".ods"],
    "presentation": [".ppt", ".pptx", ".odp"],
    "image": [".jpg", ".png", ".gif", ".svg", ".bmp"],
    "code": [".py", ".js", ".html", ".css", ".java", ".cpp", ".sh"],
    "data": [".json", ".xml", ".yaml", ".csv", ".db", ".sql"]
}

# File name prefixes by type
FILE_PREFIXES = {
    "text": ["notes", "readme", "changelog", "todo", "summary", "report"],
    "document": ["report", "contract", "proposal", "manual", "guide", "letter"],
    "spreadsheet": ["budget", "inventory", "expenses", "data", "metrics", "report"],
    "presentation": ["presentation", "slides", "overview", "proposal", "meeting"],
    "image": ["photo", "image", "screenshot", "diagram", "logo", "banner"],
    "code": ["main", "app", "utils", "helpers", "module", "script", "test"],
    "data": ["data", "config", "settings", "output", "results", "backup"]
}

# Lorem ipsum paragraphs for realistic text content
LOREM_PARAGRAPHS = [
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
    "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.",
    "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.",
    "Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.",
    "Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam.",
    "Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores.",
    "Neque porro quisquam est, qui dolorem ipsum quia dolor sit amet, consectetur, adipisci velit.",
    "Quis autem vel eum iure reprehenderit qui in ea voluptate velit esse quam nihil molestiae consequatur."
]

def generate_random_name(length=8):
    """Generate a random alphanumeric name."""
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))

def generate_realistic_folder_name():
    """Generate a realistic folder name."""
    # Choose randomly with 80% chance of realistic name, 20% chance of random name
    if random.random() < 0.8:
        base_name = random.choice(FOLDER_NAMES)
        # Sometimes add a modifier like a date or version
        if random.random() < 0.3:  
            current_year = datetime.datetime.now().year
            year = random.randint(current_year - 5, current_year)
            month = random.randint(1, 12)
            day = random.randint(1, 28)
            date_str = f"{year}-{month:02d}-{day:02d}"
            return f"{base_name}_{date_str}"
        # Sometimes add a numeric suffix
        elif random.random() < 0.3:
            return f"{base_name}_{random.randint(1, 100)}"
        return base_name
    else:
        return generate_random_name()

def generate_realistic_file_name():
    """Generate a realistic file name with appropriate extension."""
    # Choose a random file type category
    file_category = random.choice(list(FILE_TYPES.keys()))
    extension = random.choice(FILE_TYPES[file_category])
    
    # Get appropriate prefix for this type
    prefix = random.choice(FILE_PREFIXES[file_category])
    
    # Add variety with dates, versions, or random numbers
    modifier = ""
    rand_choice = random.random()
    if rand_choice < 0.3:
        # Date-based suffix
        current_year = datetime.datetime.now().year
        year = random.randint(current_year - 3, current_year)
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        modifier = f"_{year}-{month:02d}-{day:02d}"
    elif rand_choice < 0.6:
        # Version-based suffix
        major = random.randint(1, 5)
        minor = random.randint(0, 9)
        modifier = f"_v{major}.{minor}"
    elif rand_choice < 0.8:
        # Numeric suffix
        modifier = f"_{random.randint(1, 100)}"
    
    return f"{prefix}{modifier}{extension}"

def generate_text_content(min_lines, max_lines):
    """Generate lorem ipsum text content."""
    num_paragraphs = random.randint(min_lines, max_lines)
    return "\n\n".join(random.choice(LOREM_PARAGRAPHS) for _ in range(num_paragraphs))

def generate_json_content():
    """Generate a simple JSON document."""
    data = {
        "id": random.randint(1000, 9999),
        "name": generate_random_name(),
        "date": f"{random.randint(2020, 2023)}-{random.randint(1, 12)}-{random.randint(1, 28)}",
        "value": round(random.random() * 100, 2),
        "active": random.choice([True, False])
    }
    return json.dumps(data, indent=2)

def generate_xml_content():
    """Generate a simple XML document."""
    id_value = random.randint(1000, 9999)
    name = generate_random_name()
    date = f"{random.randint(2020, 2023)}-{random.randint(1, 12)}-{random.randint(1, 28)}"
    value = round(random.random() * 100, 2)
    active = random.choice(["true", "false"])
    
    return dedent(f"""
        <?xml version="1.0" encoding="UTF-8"?>
        <root>
          <item>
            <id>{id_value}</id>
            <name>{name}</name>
            <date>{date}</date>
            <value>{value}</value>
            <active>{active}</active>
          </item>
        </root>
    """).strip()

def generate_html_content():
    """Generate a simple HTML document."""
    return dedent(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Sample Page</title>
        </head>
        <body>
            <h1>Sample Content</h1>
            <p>{random.choice(LOREM_PARAGRAPHS)}</p>
            <p>{random.choice(LOREM_PARAGRAPHS)}</p>
        </body>
        </html>
    """).strip()

def generate_python_content():
    """Generate a simple Python script."""
    return dedent(f"""
        #!/usr/bin/env python3
        # Sample Python script

        def main():
            print("Hello, world!")
            value = {random.randint(1, 100)}
            print(f"Random value: {{value}}")

        if __name__ == "__main__":
            main()
    """).strip()

def generate_javascript_content():
    """Generate a simple JavaScript file."""
    return dedent(f"""
        // Sample JavaScript file

        function main() {{
          console.log("Hello, world!");
          const value = {random.randint(1, 100)};
          console.log(`Random value: ${{value}}`);
        }}

        main();
    """).strip()

def generate_css_content():
    """Generate a simple CSS file."""
    colors = ["#ff0000", "#00ff00", "#0000ff", "#ffff00", "#00ffff", "#ff00ff"]
    return dedent(f"""
        /* Sample CSS file */

        body {{
          font-family: Arial, sans-serif;
          margin: 0;
          padding: 20px;
          background-color: {random.choice(colors)};
        }}

        h1 {{
          color: {random.choice(colors)};
          font-size: {random.randint(18, 36)}px;
        }}

        p {{
          line-height: 1.6;
          margin-bottom: 15px;
        }}
    """).strip()

def generate_yaml_content():
    """Generate a simple YAML configuration file."""
    return dedent(f"""
        # Sample YAML configuration

        version: {random.randint(1, 5)}.{random.randint(0, 9)}
        environment: {random.choice(['development', 'testing', 'production'])}
        debug: {str(random.choice([True, False])).lower()}

        server:
          host: localhost
          port: {random.choice([3000, 5000, 8000, 8080])}
          
        database:
          type: {random.choice(['mysql', 'postgres', 'mongodb'])}
          host: db.example.com
          user: user{random.randint(1, 100)}
          timeout: {random.randint(30, 120)}
    """).strip()

def generate_csv_content(min_lines, max_lines):
    """Generate a simple CSV file."""
    headers = ["id", "name", "date", "value", "active"]
    rows = [",".join(headers)]
    
    num_rows = random.randint(min_lines, max_lines)
    for i in range(num_rows):
        row_data = [
            str(1000 + i),
            generate_random_name(),
            f"{random.randint(2020, 2023)}-{random.randint(1, 12)}-{random.randint(1, 28)}",
            str(round(random.random() * 100, 2)),
            str(random.choice([True, False])).lower()
        ]
        rows.append(",".join(row_data))
    
    return "\n".join(rows)

def generate_bash_script_content():
    """Generate a simple bash script."""
    return dedent(f"""
        #!/bin/bash
        # Sample bash script

        echo "Starting script..."
        VALUE={random.randint(1, 100)}
        echo "Random value: $VALUE"

        if [ $VALUE -gt 50 ]; then
            echo "Value is greater than 50"
        else
            echo "Value is less than or equal to 50"
        fi

        echo "Script completed."
    """).strip()

def generate_sql_content():
    """Generate a simple SQL file."""
    table_name = random.choice(["users", "products", "orders", "customers", "items"])
    return dedent(f"""
        -- Sample SQL file

        CREATE TABLE {table_name} (
            id INTEGER PRIMARY KEY,
            name VARCHAR(50) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            value NUMERIC({random.randint(5, 10)}, 2),
            active BOOLEAN DEFAULT {random.choice(['TRUE', 'FALSE'])}
        );

        INSERT INTO {table_name} (id, name, value, active)
        VALUES 
            (1, '{generate_random_name()}', {round(random.random() * 100, 2)}, {random.choice(['TRUE', 'FALSE'])}),
            (2, '{generate_random_name()}', {round(random.random() * 100, 2)}, {random.choice(['TRUE', 'FALSE'])}),
            (3, '{generate_random_name()}', {round(random.random() * 100, 2)}, {random.choice(['TRUE', 'FALSE'])});
    """).strip()

def generate_realistic_content(file_path, min_lines=3, max_lines=10):
    """Generate realistic content based on file extension."""
    ext = os.path.splitext(file_path)[1].lower()
    
    # Text files
    if ext in [".txt", ".md", ".log", ".doc", ".docx", ".pdf", ".rtf", ".odt"]:
        return generate_text_content(min_lines, max_lines)
    
    # Data formats
    elif ext == ".json":
        return generate_json_content()
    elif ext == ".xml":
        return generate_xml_content()
    elif ext == ".yaml" or ext == ".yml":
        return generate_yaml_content()
    elif ext == ".csv":
        return generate_csv_content(min_lines, max_lines)
    
    # Web and programming languages
    elif ext == ".html":
        return generate_html_content()
    elif ext == ".py":
        return generate_python_content()
    elif ext == ".js":
        return generate_javascript_content()
    elif ext == ".css":
        return generate_css_content()
    elif ext == ".sh":
        return generate_bash_script_content()
    elif ext == ".sql":
        return generate_sql_content()
    
    # Default for any other file type
    else:
        return generate_text_content(min_lines, max_lines)

def create_folder_structure(root_path, min_dirs=2, max_dirs=5, max_depth=3, current_depth=0):
    """Recursively create a folder structure with realistic subdirectories."""
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
        dir_name = generate_realistic_folder_name()
        dir_path = os.path.join(root_path, dir_name)
        os.makedirs(dir_path, exist_ok=True)
        create_folder_structure(dir_path, min_dirs, max_dirs, max_depth, current_depth + 1)

def populate_with_files(root_path, min_files=1, max_files=5, min_lines=1, max_lines=10):
    """Populate each directory with realistic files."""
    if not os.path.exists(root_path):
        raise ValueError(f"Directory '{root_path}' does not exist")
        
    for dirpath, _, _ in os.walk(root_path):
        num_files = random.randint(min_files, max_files)
        for _ in range(num_files):
            file_name = generate_realistic_file_name()
            file_path = os.path.join(dirpath, file_name)
            
            with open(file_path, "w") as f:
                f.write(generate_realistic_content(file_path, min_lines, max_lines))

def generate_testing_structure(output_dir, min_dirs=2, max_dirs=5, max_depth=3, 
                              min_files=1, max_files=5, min_lines=1, max_lines=10,
                              clean_existing=True):
    """Generate a realistic folder structure and populate it with realistic files."""
    # Remove existing structure if requested
    if clean_existing and os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    
    # Create folder structure
    create_folder_structure(output_dir, min_dirs, max_dirs, max_depth)
    
    # Populate with files
    populate_with_files(output_dir, min_files, max_files, min_lines, max_lines)
    
    return output_dir

if __name__ == "__main__":
    output_dir = "testing_structure"
    
    # Folder structure parameters
    min_dirs = 1      # Minimum number of folders at each level
    max_dirs = 2      # Maximum number of folders at each level
    max_depth = 3     # Maximum folder nesting
    
    # File generation parameters
    min_files = 1     # Minimum files per directory
    max_files = 3     # Maximum files per directory
    min_lines = 1     # Minimum paragraphs per file
    max_lines = 5     # Maximum paragraphs per file
    
    # Generate the structure
    generate_testing_structure(
        output_dir, 
        min_dirs, max_dirs, max_depth,
        min_files, max_files, min_lines, max_lines
    )
    
    print(f"Testing structure created at '{output_dir}'") 