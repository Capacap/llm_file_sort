# LLM File Sort: AI-Powered File Organizer

LLM File Sort intelligently organizes files into appropriate directories using AI models.

## Features

- **Content Awareness**: Analyzes text and image content to understand file context
- **Smart Mapping**: Maps files to appropriate directories based on content analysis
- **Flexible Configuration**: Works with various AI models (local or API-based)
- **Visual Feedback**: Shows current vs proposed file organization before changes
- **Safe Operation**: Validates changes and allows dry runs before applying

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

# Save config for future use
python main.py --save-config -d ~/Downloads -m ollama/gemma3:4b
```

## Configuration

Configuration can be stored in:
- `~/.llm_file_organizer.json`
- `.llm_file_organizer.json` (local)
- Environment variables

Required settings:
- `directory`: Target directory to organize
- `model`: AI model to use

Optional settings:
- `api_key`: API key for cloud models
- `custom_directories`: Comma-separated list of destination directories
- `port`: Port for local model server
- `prompt`: Custom instructions for the AI

## Requirements

- Python 3.6+
- Rich (terminal UI)
- Model-specific dependencies (OpenAI, Ollama, etc.)

## License

MIT License