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

# More realistic content by category
REALISTIC_CONTENT = {
    "meeting_notes": [
        "Meeting started at 10:00 AM with all team members present.",
        "Action items: Update project timeline, contact client about deliverables.",
        "The team discussed the new feature requirements and assigned tasks.",
        "Next sprint planning scheduled for Friday at 2:00 PM.",
        "Budget concerns were raised regarding the server infrastructure costs.",
        "Marketing team will provide updated materials by end of week.",
        "Meeting concluded at 11:30 AM with agreement on next steps."
    ],
    "project_plans": [
        "Project Timeline: Phase 1 to be completed by end of Q2.",
        "Resources required: 2 developers, 1 designer, 1 QA specialist.",
        "Budget allocation: $25,000 for initial development phase.",
        "Key deliverables include user authentication system and admin dashboard.",
        "Risks identified: API integration delays, potential security concerns.",
        "Stakeholder review scheduled after completion of each milestone.",
        "Success metrics: 98% uptime, <2s response time, 90% user satisfaction."
    ],
    "research_notes": [
        "Preliminary findings suggest correlation between variables A and B.",
        "Sample size of 250 participants provides statistically significant results.",
        "Control group showed 15% less variation compared to test group.",
        "Literature review reveals similar patterns in previous studies.",
        "Methodology to be refined based on peer feedback.",
        "Data collection will continue through Q3 with analysis in Q4.",
        "Funding sources include grant #RF-2023-456 and department resources."
    ],
    "todo_lists": [
        "Complete project proposal by Wednesday",
        "Review pull requests for authentication module",
        "Schedule team meeting for sprint planning",
        "Update documentation for API endpoints",
        "Fix bug in user registration form",
        "Prepare presentation for client meeting",
        "Test new feature on staging environment",
        "Submit expense report for last month"
    ],
    "technical_docs": [
        "System requires Python 3.8+ and PostgreSQL 13.2.",
        "API endpoints use JWT authentication with 24-hour token expiration.",
        "Database migrations should be run with '--no-input' flag in production.",
        "Load balancer is configured with round-robin strategy.",
        "Memory usage should not exceed 4GB under normal operation.",
        "Logs are stored in /var/log/app/ with daily rotation.",
        "Backup strategy: full backup weekly, incremental daily."
    ],
    "readme": [
        "# Project Overview\nThis project aims to solve [specific problem].",
        "## Installation\n```\npip install -r requirements.txt\n```",
        "## Usage\n```python\nfrom package import main\nmain.run()\n```",
        "## Configuration\nEdit config.json with your API credentials.",
        "## Contributing\nPlease follow the contribution guidelines in CONTRIBUTING.md.",
        "## License\nThis project is licensed under the MIT License."
    ],
    "logs": [
        "[2023-10-15 08:12:34] INFO: Application started",
        "[2023-10-15 08:12:35] DEBUG: Connecting to database at db.example.com",
        "[2023-10-15 08:12:36] INFO: Successfully connected to database",
        "[2023-10-15 08:13:45] WARN: High memory usage detected (78%)",
        "[2023-10-15 08:14:22] ERROR: Failed to process request: Invalid token",
        "[2023-10-15 08:14:30] INFO: User 'admin' logged in successfully",
        "[2023-10-15 08:15:12] DEBUG: Cache hit ratio: 0.85"
    ]
}

# Add personal notes category
REALISTIC_CONTENT["personal_notes"] = [
    "Remember to call Mom for her birthday next Tuesday.",
    "Grocery list: milk, eggs, bread, apples, pasta, tomato sauce.",
    "Gym schedule: Monday/Wednesday/Friday at 6:30 AM.",
    "Ideas for weekend: hiking at Pine Mountain, movie night, try new restaurant.",
    "Book recommendations from Alex: 'Project Hail Mary', 'Atomic Habits'.",
    "Need to renew driver's license before end of month.",
    "Password hint for work account: favorite vacation spot + year."
]

# Add report sections
REALISTIC_CONTENT["report_sections"] = [
    "Executive Summary:\nThe quarterly results exceeded expectations with a 12% increase in revenue.",
    "Market Analysis:\nCompetitor activity has increased in the Southeast region.",
    "Financial Overview:\nGross margin improved to 34%, up from 31% in previous quarter.",
    "Risk Assessment:\nSupply chain disruptions pose moderate risk to Q4 deliverables.",
    "Recommendations:\nIncrease marketing spend in emerging markets by 15%.",
    "Conclusion:\nOverall performance indicates positive trajectory with cautious outlook.",
    "Appendix A: Detailed sales figures by region and product category."
]

# Add emails
REALISTIC_CONTENT["emails"] = [
    "Subject: Project Update - Week 43\n\nHi team,\n\nWe're on track with the current sprint. Backend integration is complete and frontend updates are at 80%. Please submit your hours by Friday.\n\nThanks,\nProject Manager",
    "Subject: Meeting Rescheduled\n\nDear all,\n\nThe budget review meeting has been moved to Thursday at 2 PM. Please confirm your attendance.\n\nBest regards,\nOffice Admin",
    "Subject: New Feature Request\n\nHello Dev Team,\n\nThe client has requested a new dashboard feature. I've added the details to the task board. Priority is high.\n\nCheers,\nProduct Owner",
    "Subject: System Maintenance Notice\n\nImportant: The system will be down for maintenance on Sunday from 2 AM to 5 AM. Please save all work before this time.\n\nIT Department"
]

# Add contracts/legal text
REALISTIC_CONTENT["legal"] = [
    "CONFIDENTIALITY AGREEMENT\n\nThis Agreement is entered into as of the Effective Date by and between the parties.",
    "TERMS OF SERVICE\n\n1. ACCEPTANCE OF TERMS\nBy accessing or using the Service, you agree to be bound by these Terms.",
    "PRIVACY POLICY\n\nWe collect personal information to provide and improve our services to you.",
    "LICENSE AGREEMENT\n\nSubject to the terms and conditions of this Agreement, Company grants you a non-exclusive, non-transferable license.",
    "WARRANTY DISCLAIMER\n\nTHE SOFTWARE IS PROVIDED \"AS IS\" WITHOUT WARRANTY OF ANY KIND."
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

def generate_text_content(min_lines, max_lines, file_name=""):
    """Generate realistic text content based on file name and type."""
    num_paragraphs = random.randint(min_lines, max_lines)
    
    # Determine content type based on file name
    content_type = "meeting_notes"  # Default
    
    file_name_lower = file_name.lower()
    
    if "readme" in file_name_lower:
        content_type = "readme"
    elif "todo" in file_name_lower or "task" in file_name_lower:
        content_type = "todo_lists"
    elif "meeting" in file_name_lower or "minutes" in file_name_lower:
        content_type = "meeting_notes"
    elif "log" in file_name_lower:
        content_type = "logs"
    elif "report" in file_name_lower or "summary" in file_name_lower:
        content_type = "report_sections"
    elif "plan" in file_name_lower or "project" in file_name_lower:
        content_type = "project_plans"
    elif "research" in file_name_lower or "study" in file_name_lower:
        content_type = "research_notes"
    elif "note" in file_name_lower or "personal" in file_name_lower:
        content_type = "personal_notes"
    elif "doc" in file_name_lower or "api" in file_name_lower or "tech" in file_name_lower:
        content_type = "technical_docs"
    elif "email" in file_name_lower or "message" in file_name_lower:
        content_type = "emails"
    elif "contract" in file_name_lower or "legal" in file_name_lower or "terms" in file_name_lower:
        content_type = "legal"
    else:
        # If no specific match, use a random content type
        content_type = random.choice(list(REALISTIC_CONTENT.keys()))
    
    # Get paragraphs from the selected content type
    content_paragraphs = REALISTIC_CONTENT[content_type]
    
    # Handle case where we need more paragraphs than available
    if num_paragraphs > len(content_paragraphs):
        # Repeat with random selection to get enough paragraphs
        selected_paragraphs = []
        for _ in range(num_paragraphs):
            selected_paragraphs.append(random.choice(content_paragraphs))
    else:
        # Randomly select paragraphs without repetition
        selected_paragraphs = random.sample(content_paragraphs, num_paragraphs)
    
    return "\n\n".join(selected_paragraphs)

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
    file_name = os.path.basename(file_path)
    
    # Text files
    if ext in [".txt", ".md", ".log", ".doc", ".docx", ".pdf", ".rtf", ".odt"]:
        return generate_text_content(min_lines, max_lines, file_name)
    
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
        return generate_text_content(min_lines, max_lines, file_name)

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
    output_dir = "data/testing"
    
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