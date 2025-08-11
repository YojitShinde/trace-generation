import json
import sqlite3
import ollama
import logging
import time
from datetime import datetime
from typing import List, Dict, Any
from translation import translate_reasoning_trace

def setup_logging():
    """
    Setup logging configuration for the application.
    """
    # Create logs directory if it doesn't exist
    import os
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Setup logging configuration
    log_filename = f"logs/leetcode_traces_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
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
    logger.info("LeetCode Reasoning Trace Collection - Session Started")
    logger.info("=" * 60)
    
    return logger

def read_leetcode_entries(file_path: str, num_entries: int = 2, logger=None) -> List[Dict[str, Any]]:
    """
    Read the first num_entries from the JSONL file.
    
    Args:
        file_path: Path to the JSONL file
        num_entries: Number of entries to read (default: 5)
        logger: Logger instance for logging
    
    Returns:
        List of dictionaries containing the entries
    """
    if logger:
        logger.info(f"Starting to read {num_entries} entries from {file_path}")
    
    entries = []
    start_time = time.time()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for i, line in enumerate(file):
                if i >= num_entries:
                    break
                
                entry = json.loads(line.strip())
                entries.append({
                    'title': entry.get('title', ''),
                    'content': entry.get('content', '')
                })
                
                if logger:
                    logger.info(f"Read entry {i+1}: '{entry.get('title', 'Unknown')}'")
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        success_msg = f"Successfully read {len(entries)} entries from {file_path} in {elapsed_time:.2f} seconds"
        print(success_msg)
        if logger:
            logger.info(success_msg)
        
        return entries
        
    except FileNotFoundError:
        error_msg = f"Error: File {file_path} not found"
        print(error_msg)
        if logger:
            logger.error(error_msg)
        return []
    except json.JSONDecodeError as e:
        error_msg = f"Error parsing JSON: {e}"
        print(error_msg)
        if logger:
            logger.error(error_msg)
        return []
    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        print(error_msg)
        if logger:
            logger.error(error_msg)
        return []


def get_reasoning_trace_with_think(content: str, model_name: str = "qwen3:8b", logger=None) -> str:
    """
    Get reasoning trace from Ollama model with '/think' prefix.
    
    Args:
        content: The problem content/description
        model_name: Name of the Ollama model to use
        logger: Logger instance for logging
    
    Returns:
        The reasoning trace as a string
    """
    if logger:
        logger.info(f"Starting WITH THINK trace generation with model: {model_name}")
    
    start_time = time.time()
    start_datetime = datetime.now()
    
    prompt = f"""/think Given the following coding problem, provide only the reasoning trace - your step-by-step thought process to understand and approach the problem. Do NOT provide the actual solution or code.

Problem:
{content}

Please provide your reasoning trace - the logical steps you would take to understand and approach this problem:"""

    try:
        if logger:
            logger.info(f"WITH THINK - Sending request to model at {start_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
        
        response = ollama.generate(
            model=model_name,
            prompt=prompt
        )
        
        end_time = time.time()
        end_datetime = datetime.now()
        elapsed_time = end_time - start_time
        
        reasoning_trace = response['response'].strip()
        
        success_msg = f"WITH THINK trace generated successfully in {elapsed_time:.2f} seconds (length: {len(reasoning_trace)})"
        print(success_msg)
        
        if logger:
            logger.info(f"WITH THINK - Request completed at {end_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"WITH THINK - Generation time: {elapsed_time:.2f} seconds")
            logger.info(f"WITH THINK - Response length: {len(reasoning_trace)} characters")
            logger.info(success_msg)
        
        return reasoning_trace
        
    except Exception as e:
        end_time = time.time()
        elapsed_time = end_time - start_time
        error_msg = f"Error generating WITH THINK reasoning trace after {elapsed_time:.2f} seconds: {e}"
        print(error_msg)
        
        if logger:
            logger.error(error_msg)
            logger.error("Please ensure:")
            logger.error("1. Ollama is installed and running")
            logger.error(f"2. The model '{model_name}' is available")
            logger.error("3. You can run: ollama list")
        
        return f"Error generating WITH THINK reasoning trace: {str(e)}"

def setup_database(db_path: str = "leetcode_traces.db", logger=None) -> sqlite3.Connection:
    """
    Setup SQLite database and create the table if it doesn't exist.
    
    Args:
        db_path: Path to the SQLite database file
        logger: Logger instance for logging
    
    Returns:
        SQLite connection object
    """
    if logger:
        logger.info(f"Setting up database at: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leetcode_reasoning (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                trace_en_with_think TEXT NOT NULL,
                trace_hi_with_think TEXT,
                translation_status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                translated_at TIMESTAMP
            )
        ''')
        
        conn.commit()
        success_msg = f"Database setup complete: {db_path}"
        print(success_msg)
        if logger:
            logger.info(success_msg)
        
        return conn
        
    except Exception as e:
        error_msg = f"Error setting up database: {e}"
        print(error_msg)
        if logger:
            logger.error(error_msg)
        raise

def save_to_database(conn: sqlite3.Connection, entries_with_traces: List[Dict[str, str]], logger=None) -> None:
    """
    Save the entries with reasoning traces to the database.
    
    Args:
        conn: SQLite connection object
        entries_with_traces: List of dictionaries with title, content, trace_en_with_think, and optionally trace_hi_with_think
        logger: Logger instance for logging
    """
    if logger:
        logger.info(f"Starting to save {len(entries_with_traces)} entries to database")
    
    start_time = time.time()
    
    try:
        cursor = conn.cursor()
        
        for i, entry in enumerate(entries_with_traces, 1):
            if 'trace_hi_with_think' in entry and entry['trace_hi_with_think']:
                # Entry with translation
                cursor.execute('''
                    INSERT INTO leetcode_reasoning (title, content, trace_en_with_think, trace_hi_with_think, translation_status, translated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (entry['title'], entry['content'], entry['trace_en_with_think'], 
                      entry['trace_hi_with_think'], 'completed', datetime.now()))
            else:
                # Entry without translation
                cursor.execute('''
                    INSERT INTO leetcode_reasoning (title, content, trace_en_with_think, translation_status)
                    VALUES (?, ?, ?, ?)
                ''', (entry['title'], entry['content'], entry['trace_en_with_think'], 'pending'))
            
            if logger:
                logger.info(f"Saved entry {i}/{len(entries_with_traces)}: {entry['title']}")
        
        conn.commit()
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        success_msg = f"Successfully saved {len(entries_with_traces)} entries to database in {elapsed_time:.2f} seconds"
        print(success_msg)
        if logger:
            logger.info(success_msg)
        
    except Exception as e:
        error_msg = f"Error saving to database: {e}"
        print(error_msg)
        if logger:
            logger.error(error_msg)
        raise

def get_untranslated_traces(conn: sqlite3.Connection, logger=None) -> List[Dict[str, Any]]:
    """
    Get traces that haven't been translated yet.
    
    Args:
        conn: SQLite connection object
        logger: Logger instance for logging
    
    Returns:
        List of dictionaries containing untranslated traces
    """
    if logger:
        logger.info("Fetching untranslated traces from database")
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, title, trace_en_with_think 
            FROM leetcode_reasoning 
            WHERE translation_status = 'pending' OR trace_hi_with_think IS NULL
            ORDER BY id ASC
        ''')
        
        rows = cursor.fetchall()
        traces = []
        
        for row in rows:
            traces.append({
                'id': row[0],
                'title': row[1],
                'trace_en_with_think': row[2]
            })
        
        if logger:
            logger.info(f"Found {len(traces)} untranslated traces")
        
        return traces
        
    except Exception as e:
        error_msg = f"Error fetching untranslated traces: {e}"
        print(error_msg)
        if logger:
            logger.error(error_msg)
        return []

def update_translation_in_database(conn: sqlite3.Connection, trace_id: int, hindi_trace: str, logger=None) -> None:
    """
    Update the database with the Hindi translation for a specific trace.
    
    Args:
        conn: SQLite connection object
        trace_id: The ID of the trace to update
        hindi_trace: The Hindi translation of the trace
        logger: Logger instance for logging
    """
    if logger:
        logger.info(f"Updating translation for trace ID: {trace_id}")
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE leetcode_reasoning 
            SET trace_hi_with_think = ?, translation_status = 'completed', translated_at = ?
            WHERE id = ?
        ''', (hindi_trace, datetime.now(), trace_id))
        
        conn.commit()
        
        if logger:
            logger.info(f"Successfully updated translation for trace ID: {trace_id}")
        
    except Exception as e:
        error_msg = f"Error updating translation for trace ID {trace_id}: {e}"
        print(error_msg)
        if logger:
            logger.error(error_msg)
        raise

def process_translations(conn: sqlite3.Connection, logger=None) -> None:
    """
    Process all pending translations.
    
    Args:
        conn: SQLite connection object
        logger: Logger instance for logging
    """
    if logger:
        logger.info("=" * 40)
        logger.info("STEP: Processing translations")
        logger.info("=" * 40)
    
    print("\nProcessing translations...")
    
    # Get untranslated traces
    untranslated_traces = get_untranslated_traces(conn, logger)
    
    if not untranslated_traces:
        print("No pending translations found.")
        if logger:
            logger.info("No pending translations found")
        return
    
    print(f"Found {len(untranslated_traces)} traces to translate...")
    
    for i, trace in enumerate(untranslated_traces, 1):
        trace_start_time = time.time()
        print(f"\nTranslating trace {i}/{len(untranslated_traces)}: '{trace['title']}'")
        if logger:
            logger.info(f"Translating trace {i}/{len(untranslated_traces)}: '{trace['title']}'")
        
        # Translate the trace
        hindi_trace = translate_reasoning_trace(
            trace['trace_en_with_think'], 
            trace['title'], 
            logger
        )
        
        # Update the database
        update_translation_in_database(conn, trace['id'], hindi_trace, logger)
        
        trace_end_time = time.time()
        trace_elapsed_time = trace_end_time - trace_start_time
        
        completion_msg = f"Completed translation: {trace['title']} in {trace_elapsed_time:.2f} seconds"
        print(completion_msg)
        if logger:
            logger.info(completion_msg)
            logger.info("-" * 40)

def main():
    """
    Main function to orchestrate the entire process.
    """
    # Setup logging first
    logger = setup_logging()
    
    # Configuration
    JSONL_FILE = "leetcode.jsonl"
    DB_FILE = "leetcode_traces.db"
    MODEL_NAME = "qwen3:8b"
    NUM_ENTRIES = 2
    
    logger.info(f"Configuration:")
    logger.info(f"  - JSONL File: {JSONL_FILE}")
    logger.info(f"  - Database File: {DB_FILE}")
    logger.info(f"  - Model Name: {MODEL_NAME}")
    logger.info(f"  - Number of Entries: {NUM_ENTRIES}")
    
    print("Starting LeetCode Reasoning Trace Collection and Translation Pipeline...")
    print("=" * 70)
    
    overall_start_time = time.time()
    
    # Step 1: Setup database first
    print("Step 1: Setting up database...")
    logger.info("=" * 40)
    logger.info("STEP 1: Setting up database")
    logger.info("=" * 40)
    
    conn = setup_database(DB_FILE, logger)
    
    # Step 2: Read entries from JSONL file
    print("\nStep 2: Reading entries from JSONL file...")
    logger.info("=" * 40)
    logger.info("STEP 2: Reading entries from JSONL file")
    logger.info("=" * 40)
    
    entries = read_leetcode_entries(JSONL_FILE, NUM_ENTRIES, logger)
    
    if not entries:
        error_msg = "No entries found. Exiting."
        print(error_msg)
        logger.error(error_msg)
        conn.close()
        return
    
    # Step 3: Generate reasoning traces and save to database
    print("\nStep 3: Generating reasoning traces...")
    logger.info("=" * 40)
    logger.info("STEP 3: Generating reasoning traces")
    logger.info("=" * 40)
    
    for i, entry in enumerate(entries, 1):
        entry_start_time = time.time()
        print(f"\nProcessing entry {i}/{len(entries)}: '{entry['title']}'")
        logger.info(f"Processing entry {i}/{len(entries)}: '{entry['title']}'")
        logger.info(f"Entry content length: {len(entry['content'])} characters")
        
        # Generate WITH THINK reasoning trace
        print("  Generating WITH THINK reasoning trace...")
        trace_en_with_think = get_reasoning_trace_with_think(entry['content'], MODEL_NAME, logger)
        
        # Save trace to database immediately
        entry_with_trace = {
            'title': entry['title'],
            'content': entry['content'],
            'trace_en_with_think': trace_en_with_think
        }
        save_to_database(conn, [entry_with_trace], logger)
        
        entry_end_time = time.time()
        entry_elapsed_time = entry_end_time - entry_start_time
        completion_msg = f"Completed processing and saved: {entry['title']} in {entry_elapsed_time:.2f} seconds"
        print(completion_msg)
        logger.info(completion_msg)
        logger.info("-" * 40)
        
        # Step 4: Translate the trace immediately after saving
        print("  Translating reasoning trace to Hindi...")
        logger.info("Starting translation for current entry")
        
        translation_start_time = time.time()
        hindi_trace = translate_reasoning_trace(trace_en_with_think, entry['title'], logger)
        
        # Update database with translation
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE leetcode_reasoning 
            SET trace_hi_with_think = ?, translation_status = 'completed', translated_at = ?
            WHERE title = ? AND trace_en_with_think = ?
        ''', (hindi_trace, datetime.now(), entry['title'], trace_en_with_think))
        conn.commit()
        
        translation_end_time = time.time()
        translation_elapsed_time = translation_end_time - translation_start_time
        
        translation_completion_msg = f"Completed translation: {entry['title']} in {translation_elapsed_time:.2f} seconds"
        print(translation_completion_msg)
        logger.info(translation_completion_msg)
        
        total_entry_time = entry_end_time - entry_start_time + translation_elapsed_time
        print(f"Total time for entry '{entry['title']}': {total_entry_time:.2f} seconds")
        logger.info(f"Total time for entry '{entry['title']}': {total_entry_time:.2f} seconds")
        logger.info("=" * 50)
    
    # Step 5: Process any remaining translations (fallback)
    print(f"\nStep 4: Checking for any remaining translations...")
    process_translations(conn, logger)
    
    # Close database connection
    conn.close()
    logger.info("Database connection closed")
    
    overall_end_time = time.time()
    total_elapsed_time = overall_end_time - overall_start_time
    
    print("\n" + "=" * 70)
    print("Process completed successfully!")
    print(f"Generated reasoning traces for {len(entries)} problems")
    print(f"Translated traces to Hindi for {len(entries)} problems")
    print(f"Data saved to: {DB_FILE}")
    print(f"Total execution time: {total_elapsed_time:.2f} seconds")
    logger.info("=" * 60)
    logger.info("PROCESS COMPLETED SUCCESSFULLY!")
    logger.info(f"Generated reasoning traces for {len(entries)} problems")
    logger.info(f"Translated traces to Hindi for {len(entries)} problems")
    logger.info(f"Data saved to: {DB_FILE}")
    logger.info(f"Total execution time: {total_elapsed_time:.2f} seconds")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
