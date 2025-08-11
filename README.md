# LeetCode Reasoning Trace Collection and Translation Pipeline

This project generates reasoning traces for LeetCode problems and translates them to Hindi using using Ollama - qwen3:8b. The pipeline ensures no race conditions by processing one problem at a time and immediately translating each trace after generation.

## Features

- **Trace Generation**: Uses Ollama (qwen3:8b) to generate reasoning traces for LeetCode problems
- **Hindi Translation**: Translates English traces to Hindi using a local Sarvam model via Ollama
- **Race Condition Prevention**: Sequential processing ensures data integrity
- **Robust Error Handling**: Retry logic and comprehensive error reporting
- **SQLite Database**: Stores all traces and translation status
- **Comprehensive Logging**: Detailed logs for debugging and monitoring

## Setup

### 1. Install Dependencies

```bash
pip install ollama sqlite3
```

### 2. Configure Local Sarvam Model

1. Copy the configuration template:
   ```bash
   cp config_template.py config.py
   ```

2. Edit `config.py` and update the model name if needed:
   ```python
   SARVAM_MODEL_NAME = "your_sarvam_model_name"  # Update if different
   ```

### 3. Ensure Ollama is Running with Required Models

Make sure Ollama is installed and running with both models:
```bash
ollama serve

# For reasoning trace generation
ollama pull qwen3:8b

# For translation - ensure your Sarvam model is available
ollama list  # Check if your Sarvam model is listed
```

## Files Structure

```
trace_collection_v3/
├── leetcode.jsonl              # Input file with LeetCode problems
├── traceWithThink.py          # Main pipeline script
├── translation.py             # Translation service module
├── translate_pipeline.py      # Standalone translation script
├── config_template.py         # Configuration template
├── config.py                  # Your API configuration (create this)
├── leetcode_traces.db         # SQLite database (created automatically)
└── logs/                      # Log files directory
```

## Usage

### Option 1: Full Pipeline (Recommended)

Run the complete pipeline that generates traces and translates them:

```bash
python traceWithThink.py
```

This will:
1. Read problems from `leetcode.jsonl`
2. Generate English reasoning traces using Ollama (qwen3:8b)
3. Save traces to SQLite database
4. Immediately translate each trace to Hindi using local Sarvam model
5. Update database with Hindi translations

### Option 2: Standalone Translation

If you already have English traces in the database, run only the translation:

```bash
python translate_pipeline.py
```

This will:
1. Find all untranslated traces in the database
2. Translate them to Hindi using local Sarvam model via Ollama
3. Update the database with translations

### Option 3: Test Translation Service

Test the translation service before running the full pipeline:

```bash
python translation.py
```

## Flow Diagram

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Read Problem  │ ─> │ Generate Trace  │ ─> │  Save to SQLite │
│  from JSONL     │    │   (Ollama)      │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        v
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Update Database │ <─ │ Translate Trace │ <─ │   Process Next  │
│ with Hindi      │    │(Local Sarvam)   │    │    Problem      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Database Schema

The SQLite database contains a table `leetcode_reasoning` with the following structure:

```sql
CREATE TABLE leetcode_reasoning (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    trace_en_with_think TEXT NOT NULL,
    trace_hi_with_think TEXT,
    translation_status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    translated_at TIMESTAMP
);
```

## Configuration Options

Edit `config.py` to customize the translation service:

```python
# Local Model Configuration
SARVAM_MODEL_NAME = "sarvam"  # Your local Sarvam model name in Ollama

# Request Settings
MAX_RETRIES = 3               # retry attempts
RETRY_DELAY = 2               # seconds between retries
```

## Customization

### Change Number of Problems

Edit `traceWithThink.py`:
```python
NUM_ENTRIES = 5  # Process 5 problems instead of 2
```

### Change Sarvam Model

Edit `config.py`:
```python
SARVAM_MODEL_NAME = "your-custom-sarvam-model"  # Use different model
```

### Different Database File

Edit both scripts:
```python
DB_FILE = "my_custom_traces.db"
```

## Race Condition Prevention

The pipeline prevents race conditions by:

1. **Sequential Processing**: One problem at a time
2. **Immediate Translation**: Each trace is translated right after generation
3. **Database Transactions**: Atomic updates for each step
4. **Status Tracking**: `translation_status` field tracks progress

## Error Handling

The system includes comprehensive error handling:

- **Retry Logic**: Model calls retry up to 3 times with delays
- **Graceful Degradation**: Continues processing other problems if one fails
- **Detailed Logging**: All errors logged with timestamps and context
- **Status Tracking**: Database tracks which translations succeeded/failed

## Monitoring and Logs

Logs are created in the `logs/` directory with timestamps:
- `leetcode_traces_YYYYMMDD_HHMMSS.log` - Main pipeline logs
- `translation_YYYYMMDD_HHMMSS.log` - Translation service logs
- `standalone_translation_YYYYMMDD_HHMMSS.log` - Standalone translation logs

## Troubleshooting

### Common Issues

1. **"Import config could not be resolved"**
   - Create `config.py` from `config_template.py`
   - Update SARVAM_MODEL_NAME if needed

2. **"Ollama connection failed"**
   - Ensure Ollama is running: `ollama serve`
   - Check if models are available: `ollama list`

3. **"Sarvam model not found"**
   - Verify your Sarvam model is available in Ollama: `ollama list`
   - Update SARVAM_MODEL_NAME in `config.py` to match your model name
   - Pull the model if needed: `ollama pull your-model-name`

4. **Translation timeouts or errors**
   - Increase `MAX_RETRIES` in `config.py`
   - Check if the Sarvam model is working: `python translation.py`
   - Ensure sufficient system resources for both models

### Database Inspection

To check the database status:

```python
import sqlite3
conn = sqlite3.connect('leetcode_traces.db')
cursor = conn.cursor()

# Check total traces
cursor.execute('SELECT COUNT(*) FROM leetcode_reasoning')
print(f"Total traces: {cursor.fetchone()[0]}")

# Check translation status
cursor.execute('SELECT translation_status, COUNT(*) FROM leetcode_reasoning GROUP BY translation_status')
for status, count in cursor.fetchall():
    print(f"{status}: {count}")

conn.close()
```

## Performance Notes

- **Generation Time**: ~10-30 seconds per trace (depends on Ollama model and hardware)
- **Translation Time**: ~5-15 seconds per trace (depends on text length and local model performance)
- **Total Time**: Approximately 15-45 seconds per problem end-to-end
- **Concurrent Processing**: Not recommended due to resource constraints when running multiple models
- **Memory Usage**: Ensure sufficient RAM for running both qwen3:8b and Sarvam models simultaneously

## License

This project is for research and educational purposes. Ensure you comply with:
- LeetCode's terms of service for the problem data
- Ollama's usage guidelines
- Your local Sarvam model's license terms
