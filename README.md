# LLM File Sort: AI-Powered File Organizer

LLM File Sort intelligently organizes files into appropriate directories based on the file's content using multimodal AI.

## Features

- **Content Awareness**: Analyzes text and image content to understand file context
- **Smart Mapping**: Maps files to appropriate directories based on content analysis
- **Flexible Configuration**: Works with various AI models (local or API-based)
- **Visual Feedback**: Shows current vs proposed file organization before changes
- **Safe Operation**: Validates changes and requires confirmation before applying

## Installation

```bash
git clone https://github.com/Capacap/llm_file_sort.git
cd llm_file_sort
pip install -r requirements.txt
```

## Usage

```bash
# Basic usage with Ollama model
python main.py -d ~/Downloads -m ollama/gemma3:4b

# Using OpenAI model
python main.py -d ~/Documents/unsorted -m openai/gpt-4o --api-key-env OPENAI_API_KEY

# Custom directories with local model
python main.py -d ~/Pictures -m local/model --port 11434 -c photos,documents,work
```

## Arguments

### Required Arguments
- `-d, --directory` - Target directory to organize files
- `-m, --model` - AI model to use (format: provider/model, e.g., openai/gpt-4o, ollama/gemma3:4b)

### Optional Arguments
- `-c, --custom-directories` - Comma-separated list of destination directories. Uses already present dirctories if this argument is omitted
- `-p, --prompt` - Custom instructions for the AI model

### API Settings
- `--api-key` - API key for cloud models
- `--api-key-env` - Environment variable containing API key
- `--port` - Port for local model server

### Output Settings
- `-v, --verbose` - Enable detailed debugging output and logging
- `--no-color` - Disable colored output

### Behavior Settings
- `--no-cleanup` - Disable removal of empty directories

## Requirements

- Python 3.6+
- Rich (terminal UI)
- Model-specific dependencies (OpenAI, Ollama, etc.)

## Example Run
```bash
py main.py -d ~/Downloads -p "Create dirs for robots, cats, and dogs separatly" --model openai/gpt-4.1-mini --api-key-env OPENAI_API_KEY

Generating content summaries...
  100% - 239424fba61197893d898c5223ea6d3c.jpg

Generating file mappings...
No custom directories provided. Attempting to generate directory structure with AI...
AI generated 3 directories for mapping:
  100% - 239424fba61197893d898c5223ea6d3c.jpg

Validating file mapping...
✓ File mapping validation successful!

Visualizing file organization...
Current Organization: Downloads          Proposed Organization: Downloads                    
├── 97d3256c38a8cb7bfda0b21e67d15d72.jpg └── Images/                                         
├── d5b2d5ad21dbc827fe1255098ef085fa.jpg     ├── Animals/                                    
├── ea18927ba4a8064856762d7b266767b5.jpg     │   ├── Cats/                                   
├── ab40844dca96aa27b7e8ebe7edeee22e.jpg     │   │   ├── d5b2d5ad21dbc827fe1255098ef085fa.jpg
├── f921181b1ee259a1303db879e1a3593f.jpg     │   │   └── affcac4e345f82968eab52dc2b5b3399.jpg
├── affcac4e345f82968eab52dc2b5b3399.jpg     │   └── Dogs/                                   
└── 239424fba61197893d898c5223ea6d3c.jpg     │       ├── ea18927ba4a8064856762d7b266767b5.jpg
                                             │       └── 239424fba61197893d898c5223ea6d3c.jpg
                                             └── Robots/                                     
                                                 ├── 97d3256c38a8cb7bfda0b21e67d15d72.jpg    
                                                 ├── ab40844dca96aa27b7e8ebe7edeee22e.jpg    
                                                 └── f921181b1ee259a1303db879e1a3593f.jpg    

Apply changes? (y/n): y

Moving files...
  100% - Moving: 239424fba61197893d898c5223ea6d3c.jpg

Operation Summary:
Files moved: 7
Files skipped: 0

Cleaning up empty directories...
Removed 0 empty directories
```

## License

MIT License