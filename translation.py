import ollama
import logging
import time
import os
from datetime import datetime
from typing import Optional

# Try to import configuration, fall back to defaults if not found
try:
    from config import (
        TRANSLATION_MODEL_NAME, MAX_RETRIES, RETRY_DELAY
    )
except ImportError:
    # Default configuration if config.py doesn't exist
    TRANSLATION_MODEL_NAME = "qwen3:8b"  # Use qwen3:8b for translation via Ollama
    MAX_RETRIES = 3
    RETRY_DELAY = 2

def setup_logging():
    """
    Setup logging configuration for the translation module.
    """
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Setup logging configuration
    log_filename = f"logs/translation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler()  # Also log to console
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("Translation Service (Ollama qwen3:8b) - Session Started")
    logger.info("=" * 60)
    
    return logger

def translate_text_to_hindi(text: str, logger=None) -> str:
    """
    Translate English text to Hindi using qwen3:8b model through Ollama.
    
    Args:
        text: The English text to translate
        logger: Logger instance for logging
    
    Returns:
        The translated Hindi text as a string
    """
    if logger:
        logger.info(f"Starting translation of text (length: {len(text)} chars)")
    
    start_time = time.time()
    start_datetime = datetime.now()
    
    # Create translation prompt for qwen3:8b
    translation_prompt = f"""Translate the following English text to Hindi. Maintain the technical terminology and logical flow. Provide only the Hindi translation without any additional text or explanations.

English text:
{text}

Hindi translation:"""
    
    # Retry logic
    for attempt in range(MAX_RETRIES):
        try:
            if logger:
                logger.info(f"Translation attempt {attempt + 1}/{MAX_RETRIES} using model: {TRANSLATION_MODEL_NAME}")
                if attempt > 0:
                    logger.info(f"Retrying after previous attempt failed")
            
            # Use Ollama to call qwen3:8b model for translation
            response = ollama.generate(
                model=TRANSLATION_MODEL_NAME,
                prompt=translation_prompt
            )
            
            end_time = time.time()
            end_datetime = datetime.now()
            elapsed_time = end_time - start_time
            
            if response and 'response' in response:
                translated_text = response['response'].strip()
                
                # Basic validation - check if we got a reasonable translation
                if len(translated_text) > 0 and translated_text != text:
                    success_msg = f"Translation completed successfully in {elapsed_time:.2f} seconds (output length: {len(translated_text)} chars)"
                    print(success_msg)
                    
                    if logger:
                        logger.info(f"Request completed at {end_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
                        logger.info(f"Translation time: {elapsed_time:.2f} seconds")
                        logger.info(f"Input length: {len(text)} characters")
                        logger.info(f"Output length: {len(translated_text)} characters")
                        logger.info(success_msg)
                    
                    return translated_text
                else:
                    error_msg = f"Invalid translation response: empty or unchanged text"
                    print(f"Attempt {attempt + 1} failed: {error_msg}")
                    if logger:
                        logger.warning(f"Attempt {attempt + 1} failed: {error_msg}")
            else:
                error_msg = f"Invalid response format from Ollama"
                print(f"Attempt {attempt + 1} failed: {error_msg}")
                if logger:
                    logger.warning(f"Attempt {attempt + 1} failed: {error_msg}")
            
            if attempt < MAX_RETRIES - 1:
                print(f"Retrying in {RETRY_DELAY} seconds...")
                if logger:
                    logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
                start_time = time.time()  # Reset timer for retry
            else:
                return f"Translation error after {MAX_RETRIES} attempts: Failed to get valid translation"
                    
        except Exception as e:
            end_time = time.time()
            elapsed_time = end_time - start_time
            error_msg = f"Translation request failed after {elapsed_time:.2f} seconds: {e}"
            print(f"Attempt {attempt + 1} failed: {error_msg}")
            if logger:
                logger.warning(f"Attempt {attempt + 1} failed: {error_msg}")
            
            if attempt < MAX_RETRIES - 1:
                print(f"Retrying in {RETRY_DELAY} seconds...")
                if logger:
                    logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
                start_time = time.time()  # Reset timer for retry
            else:
                return f"Translation error after {MAX_RETRIES} attempts: {str(e)}"
    
    # This should never be reached, but just in case
    return "Translation failed: Maximum retries exceeded"

def translate_reasoning_trace(trace_text: str, problem_title: str = "", logger=None) -> str:
    """
    Translate a reasoning trace from English to Hindi.
    
    Args:
        trace_text: The reasoning trace text to translate
        problem_title: The title of the problem (for logging purposes)
        logger: Logger instance for logging
    
    Returns:
        The translated reasoning trace in Hindi
    """
    if logger:
        logger.info(f"Translating reasoning trace for problem: '{problem_title}'")
    
    # Add context to help with better translation
    contextual_prompt = f"""The following is a reasoning trace for a coding problem. Please translate it accurately to Hindi while maintaining the technical terminology and logical flow. Make sure not to use tough hindi words. Instead use simple hindi and use english words wherever technical terms are used.

{trace_text}"""
    
    translated_trace = translate_text_to_hindi(contextual_prompt, logger)
    
    if logger:
        logger.info(f"Completed translation for problem: '{problem_title}'")
    
    return translated_trace

def check_ollama_server(logger=None):
    """
    Check if Ollama server is running and accessible.
    
    Args:
        logger: Logger instance for logging
    
    Returns:
        bool: True if server is accessible, False otherwise
    """
    try:
        # Try to get the list of models to check if Ollama is running
        import subprocess
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        
        if result.returncode == 0:
            if logger:
                logger.info("✅ Ollama server is running and accessible")
            return True
        else:
            if logger:
                logger.warning(f"❌ Ollama server responded with error: {result.stderr}")
            return False
            
    except FileNotFoundError:
        if logger:
            logger.warning("❌ Ollama command not found - please install Ollama")
        return False
    except Exception as e:
        if logger:
            logger.warning(f"❌ Error checking Ollama server: {e}")
        return False

def get_available_models(logger=None):
    """
    Get list of available models from Ollama.
    
    Args:
        logger: Logger instance for logging
    
    Returns:
        list: List of available model names
    """
    try:
        import subprocess
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        
        if result.returncode == 0:
            # Parse the output to extract model names
            lines = result.stdout.strip().split('\n')
            model_names = []
            
            for line in lines[1:]:  # Skip header line
                if line.strip():
                    model_name = line.split()[0]  # First column is model name
                    model_names.append(model_name)
            
            if logger:
                logger.info(f"Available models: {model_names}")
            return model_names
        else:
            if logger:
                logger.warning(f"Failed to get models: {result.stderr}")
            return []
            
    except Exception as e:
        if logger:
            logger.warning(f"Error getting models: {e}")
        return []

def test_translation_service(logger=None):
    """
    Test the translation service with a sample text.
    
    Args:
        logger: Logger instance for logging
    """
    if logger:
        logger.info("Testing translation service...")
    
    test_text = "This is a test of the translation service. The algorithm uses a hash map to solve the two sum problem efficiently."
    
    print("Testing Ollama-based qwen3:8b translation service...")
    print(f"Model: {TRANSLATION_MODEL_NAME}")
    print(f"Original text: {test_text}")
    
    translated = translate_text_to_hindi(test_text, logger)
    
    print(f"Translated text: {translated}")
    
    if logger:
        logger.info("Translation service test completed")

if __name__ == "__main__":
    # Setup logging
    logger = setup_logging()
    
    # Test the translation service
    print("=" * 60)
    print("Ollama qwen3:8b Translation Service Test")
    print("=" * 60)
    
    # Check if Ollama server is running
    print("Checking Ollama server status...")
    if check_ollama_server(logger):
        print("✅ Ollama server is running")
        
        # Check available models
        print("Getting available models...")
        models = get_available_models(logger)
        print(f"Available models: {models}")
        
        if TRANSLATION_MODEL_NAME in models:
            print(f"✅ {TRANSLATION_MODEL_NAME} model is available")
            test_translation_service(logger)
        else:
            print(f"❌ {TRANSLATION_MODEL_NAME} model not found")
            print(f"Available models: {models}")
            print(f"\nTo install the model, run:")
            print(f"ollama pull {TRANSLATION_MODEL_NAME}")
    else:
        print("❌ Ollama server is not accessible")
        print("Please ensure Ollama is running:")
        print("1. Start Ollama: ollama serve")
        print(f"2. Install model: ollama pull {TRANSLATION_MODEL_NAME}")
