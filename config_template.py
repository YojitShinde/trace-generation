# Configuration file for local Sarvam translation service
# Copy this file to config.py and configure your local model

# Local Sarvam Model Configuration (via Ollama)
SARVAM_MODEL_NAME = "sarvam"  # Change this to your actual Sarvam model name in Ollama

# Retry settings for translation requests
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds between retries

# Optional: You can also configure other models if you have multiple translation models
# BACKUP_TRANSLATION_MODEL = "another-model-name"
