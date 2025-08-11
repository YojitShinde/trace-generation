# Configuration file for the trace collection and translation pipeline

# Translation Configuration
TRANSLATION_MODEL_NAME = "qwen3:8b"  # Ollama model for translation
MAX_RETRIES = 3  # Maximum number of retry attempts for API calls
RETRY_DELAY = 2  # Delay between retries in seconds

# Reasoning Trace Configuration  
MODEL_NAME = "qwen3:8b"  # Ollama model for reasoning trace generation
TRACE_MODEL = "qwen3:8b"  # Alternative name for trace model
USE_TRANSLATION = True  # Whether to enable automatic translation

# Database Configuration
DATABASE_PATH = "leetcode_traces.db"
ENABLE_LOGGING = True

# Ollama Configuration
OLLAMA_HOST = "http://localhost:11434"  # Default Ollama server URL
