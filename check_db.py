#!/usr/bin/env python3
"""
Database Status Checker
This script provides a quick overview of the database status,
including trace counts and translation progress.
"""

import sqlite3
import sys
from datetime import datetime

def check_database_status(db_file: str = "leetcode_traces.db"):
    """
    Check and display the status of the database.
    
    Args:
        db_file: Path to the SQLite database file
    """
    print("=" * 60)
    print("LeetCode Traces Database Status")
    print("=" * 60)
    print(f"Database: {db_file}")
    print(f"Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='leetcode_reasoning'
        """)
        
        if not cursor.fetchone():
            print("❌ Database table 'leetcode_reasoning' not found.")
            print("Run traceWithThink.py first to create the database.")
            return
        
        # Get table schema
        cursor.execute("PRAGMA table_info(leetcode_reasoning)")
        columns = cursor.fetchall()
        
        print("📊 Table Schema:")
        for col in columns:
            print(f"   {col[1]} ({col[2]})")
        print()
        
        # Count total traces
        cursor.execute('SELECT COUNT(*) FROM leetcode_reasoning')
        total_traces = cursor.fetchone()[0]
        
        # Count by translation status
        cursor.execute('''
            SELECT translation_status, COUNT(*) 
            FROM leetcode_reasoning 
            GROUP BY translation_status
        ''')
        status_counts = dict(cursor.fetchall())
        
        # Count traces with Hindi translations
        cursor.execute('''
            SELECT COUNT(*) 
            FROM leetcode_reasoning 
            WHERE trace_hi_with_think IS NOT NULL 
            AND trace_hi_with_think != ''
        ''')
        with_hindi = cursor.fetchone()[0]
        
        # Count traces without Hindi translations
        without_hindi = total_traces - with_hindi
        
        # Get completion percentage
        completion_rate = (with_hindi / total_traces * 100) if total_traces > 0 else 0
        
        print("📈 Summary:")
        print(f"   Total traces: {total_traces}")
        print(f"   With Hindi translation: {with_hindi}")
        print(f"   Without Hindi translation: {without_hindi}")
        print(f"   Completion rate: {completion_rate:.1f}%")
        print()
        
        print("📋 Translation Status:")
        for status, count in status_counts.items():
            percentage = (count / total_traces * 100) if total_traces > 0 else 0
            print(f"   {status}: {count} ({percentage:.1f}%)")
        print()
        
        # Get recent entries
        cursor.execute('''
            SELECT title, translation_status, created_at, translated_at
            FROM leetcode_reasoning 
            ORDER BY created_at DESC 
            LIMIT 5
        ''')
        recent_entries = cursor.fetchall()
        
        if recent_entries:
            print("🕒 Recent Entries:")
            for entry in recent_entries:
                title, status, created, translated = entry
                created_str = created if created else "Unknown"
                translated_str = translated if translated else "Not translated"
                print(f"   {title[:40]:<40} | {status:<10} | {translated_str}")
        
        print()
        
        # Check for errors or issues
        cursor.execute('''
            SELECT COUNT(*) 
            FROM leetcode_reasoning 
            WHERE trace_hi_with_think LIKE 'Translation error:%' 
            OR trace_hi_with_think LIKE 'Translation timeout:%'
            OR trace_hi_with_think LIKE 'Translation request error:%'
            OR trace_hi_with_think LIKE 'Unexpected translation error:%'
        ''')
        error_count = cursor.fetchone()[0]
        
        if error_count > 0:
            print(f"⚠️  Warning: {error_count} traces have translation errors")
            
            # Show error details
            cursor.execute('''
                SELECT title, trace_hi_with_think 
                FROM leetcode_reasoning 
                WHERE trace_hi_with_think LIKE 'Translation error:%' 
                OR trace_hi_with_think LIKE 'Translation timeout:%'
                OR trace_hi_with_think LIKE 'Translation request error:%'
                OR trace_hi_with_think LIKE 'Unexpected translation error:%'
                LIMIT 3
            ''')
            error_entries = cursor.fetchall()
            
            print("   Error examples:")
            for title, error in error_entries:
                error_short = error[:80] + "..." if len(error) > 80 else error
                print(f"   - {title}: {error_short}")
        else:
            print("✅ No translation errors found")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    except FileNotFoundError:
        print(f"❌ Database file '{db_file}' not found.")
        print("Run traceWithThink.py first to create the database.")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def list_problems(db_file: str = "leetcode_traces.db", limit: int = 10):
    """
    List problems in the database.
    
    Args:
        db_file: Path to the SQLite database file
        limit: Number of problems to show
    """
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, translation_status, 
                   CASE 
                       WHEN trace_hi_with_think IS NOT NULL AND trace_hi_with_think != '' 
                       THEN 'Yes' 
                       ELSE 'No' 
                   END as has_hindi,
                   created_at
            FROM leetcode_reasoning 
            ORDER BY id ASC
            LIMIT ?
        ''', (limit,))
        
        problems = cursor.fetchall()
        
        print(f"\n📚 Problems in Database (showing first {limit}):")
        print("-" * 80)
        print(f"{'ID':<4} {'Title':<35} {'Status':<12} {'Hindi':<6} {'Created'}")
        print("-" * 80)
        
        for problem in problems:
            id_val, title, status, has_hindi, created = problem
            title_short = title[:32] + "..." if len(title) > 35 else title
            created_short = created[:10] if created else "Unknown"
            print(f"{id_val:<4} {title_short:<35} {status:<12} {has_hindi:<6} {created_short}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error listing problems: {e}")

def main():
    """
    Main function for the database status checker.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Check LeetCode traces database status")
    parser.add_argument("--db", default="leetcode_traces.db", help="Database file path")
    parser.add_argument("--list", action="store_true", help="List problems in database")
    parser.add_argument("--limit", type=int, default=10, help="Number of problems to list")
    
    args = parser.parse_args()
    
    # Check database status
    check_database_status(args.db)
    
    # List problems if requested
    if args.list:
        list_problems(args.db, args.limit)

if __name__ == "__main__":
    main()
