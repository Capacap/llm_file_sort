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

## License

MIT License