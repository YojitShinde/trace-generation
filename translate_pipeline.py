#!/usr/bin/env python3
"""
Standalone Translation Pipeline
This script can be used to translate existing English traces to Hindi
independently of the main trace generation process.
"""

import sqlite3
import logging
import time
from datetime import datetime
from translation import translate_reasoning_trace, setup_logging as setup_translation_logging
from traceWithThink import setup_database, get_untranslated_traces, update_translation_in_database

def setup_logging():
    """
    Setup logging configuration for the standalone translation pipeline.
    """
    # Create logs directory if it doesn't exist
    import os
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Setup logging configuration
    log_filename = f"logs/standalone_translation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
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
    logger.info("Standalone Translation Pipeline - Session Started")
    logger.info("=" * 60)
    
    return logger

def check_database_status(conn: sqlite3.Connection, logger=None) -> dict:
    """
    Check the status of traces in the database.
    
    Args:
        conn: SQLite connection object
        logger: Logger instance for logging
    
    Returns:
        Dictionary with counts of different trace statuses
    """
    if logger:
        logger.info("Checking database status...")
    
    try:
        cursor = conn.cursor()
        
        # Count total traces
        cursor.execute('SELECT COUNT(*) FROM leetcode_reasoning')
        total_traces = cursor.fetchone()[0]
        
        # Count completed translations
        cursor.execute('SELECT COUNT(*) FROM leetcode_reasoning WHERE translation_status = "completed" AND trace_hi_with_think IS NOT NULL')
        completed_translations = cursor.fetchone()[0]
        
        # Count pending translations
        cursor.execute('SELECT COUNT(*) FROM leetcode_reasoning WHERE translation_status = "pending" OR trace_hi_with_think IS NULL')
        pending_translations = cursor.fetchone()[0]
        
        status = {
            'total_traces': total_traces,
            'completed_translations': completed_translations,
            'pending_translations': pending_translations
        }
        
        if logger:
            logger.info(f"Database status:")
            logger.info(f"  - Total traces: {total_traces}")
            logger.info(f"  - Completed translations: {completed_translations}")
            logger.info(f"  - Pending translations: {pending_translations}")
        
        return status
        
    except Exception as e:
        error_msg = f"Error checking database status: {e}"
        print(error_msg)
        if logger:
            logger.error(error_msg)
        return {}

def translate_all_pending_traces(db_file: str = "leetcode_traces.db", logger=None):
    """
    Translate all pending traces in the database.
    
    Args:
        db_file: Path to the SQLite database file
        logger: Logger instance for logging
    """
    if logger:
        logger.info(f"Starting standalone translation pipeline for database: {db_file}")
    
    print("=" * 60)
    print("Standalone Translation Pipeline")
    print("=" * 60)
    
    overall_start_time = time.time()
    
    # Connect to database
    try:
        conn = sqlite3.connect(db_file)
        print(f"Connected to database: {db_file}")
        if logger:
            logger.info(f"Connected to database: {db_file}")
    except Exception as e:
        error_msg = f"Failed to connect to database: {e}"
        print(error_msg)
        if logger:
            logger.error(error_msg)
        return
    
    # Check database status
    print("\nChecking database status...")
    status = check_database_status(conn, logger)
    
    if not status:
        print("Failed to check database status. Exiting.")
        conn.close()
        return
    
    print(f"Total traces: {status['total_traces']}")
    print(f"Completed translations: {status['completed_translations']}")
    print(f"Pending translations: {status['pending_translations']}")
    
    if status['pending_translations'] == 0:
        print("\nNo pending translations found. All traces are already translated!")
        if logger:
            logger.info("No pending translations found")
        conn.close()
        return
    
    # Get untranslated traces
    print(f"\nFetching {status['pending_translations']} pending traces...")
    untranslated_traces = get_untranslated_traces(conn, logger)
    
    if not untranslated_traces:
        print("No untranslated traces found despite status check. Exiting.")
        conn.close()
        return
    
    print(f"Found {len(untranslated_traces)} traces to translate.")
    print("\nStarting translation process...")
    print("-" * 60)
    
    # Process translations
    successful_translations = 0
    failed_translations = 0
    
    for i, trace in enumerate(untranslated_traces, 1):
        trace_start_time = time.time()
        print(f"\n[{i}/{len(untranslated_traces)}] Translating: '{trace['title']}'")
        
        if logger:
            logger.info(f"Translating trace {i}/{len(untranslated_traces)}: '{trace['title']}'")
            logger.info(f"Trace ID: {trace['id']}")
            logger.info(f"English trace length: {len(trace['trace_en_with_think'])} characters")
        
        try:
            # Translate the trace
            hindi_trace = translate_reasoning_trace(
                trace['trace_en_with_think'], 
                trace['title'], 
                logger
            )
            
            # Check if translation was successful (not an error message)
            if hindi_trace.startswith(("Translation error:", "Translation timeout:", "Translation request error:", "Unexpected translation error:")):
                print(f"  ❌ Translation failed: {hindi_trace}")
                if logger:
                    logger.error(f"Translation failed for trace ID {trace['id']}: {hindi_trace}")
                failed_translations += 1
                continue
            
            # Update the database
            update_translation_in_database(conn, trace['id'], hindi_trace, logger)
            
            trace_end_time = time.time()
            trace_elapsed_time = trace_end_time - trace_start_time
            
            print(f"  ✅ Completed in {trace_elapsed_time:.2f} seconds")
            if logger:
                logger.info(f"Successfully translated trace ID {trace['id']} in {trace_elapsed_time:.2f} seconds")
                logger.info(f"Hindi trace length: {len(hindi_trace)} characters")
            
            successful_translations += 1
            
        except Exception as e:
            trace_end_time = time.time()
            trace_elapsed_time = trace_end_time - trace_start_time
            error_msg = f"  ❌ Error after {trace_elapsed_time:.2f} seconds: {e}"
            print(error_msg)
            if logger:
                logger.error(f"Error translating trace ID {trace['id']}: {e}")
            failed_translations += 1
    
    # Close database connection
    conn.close()
    if logger:
        logger.info("Database connection closed")
    
    overall_end_time = time.time()
    total_elapsed_time = overall_end_time - overall_start_time
    
    # Final summary
    print("\n" + "=" * 60)
    print("Translation Pipeline Completed!")
    print("-" * 60)
    print(f"Total traces processed: {len(untranslated_traces)}")
    print(f"Successful translations: {successful_translations}")
    print(f"Failed translations: {failed_translations}")
    print(f"Total execution time: {total_elapsed_time:.2f} seconds")
    if successful_translations > 0:
        avg_time = total_elapsed_time / successful_translations
        print(f"Average time per translation: {avg_time:.2f} seconds")
    print("=" * 60)
    
    if logger:
        logger.info("=" * 60)
        logger.info("STANDALONE TRANSLATION PIPELINE COMPLETED!")
        logger.info(f"Total traces processed: {len(untranslated_traces)}")
        logger.info(f"Successful translations: {successful_translations}")
        logger.info(f"Failed translations: {failed_translations}")
        logger.info(f"Total execution time: {total_elapsed_time:.2f} seconds")
        if successful_translations > 0:
            logger.info(f"Average time per translation: {total_elapsed_time / successful_translations:.2f} seconds")
        logger.info("=" * 60)

def main():
    """
    Main function for the standalone translation pipeline.
    """
    # Setup logging
    logger = setup_logging()
    
    # Configuration
    DB_FILE = "leetcode_traces.db"
    
    print("Starting Standalone Translation Pipeline...")
    logger.info("Starting standalone translation pipeline")
    logger.info(f"Target database: {DB_FILE}")
    
    # Run translation process
    translate_all_pending_traces(DB_FILE, logger)

if __name__ == "__main__":
    main()
