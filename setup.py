#!/usr/bin/env python3
"""
Setup Script for LeetCode Reasoning Trace Collection and Translation Pipeline
This script helps users set up the environment and configuration.
"""

import os
import sys
import shutil
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required.")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = ['requests', 'sqlite3']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} is not installed")
    
    if missing_packages:
        print(f"\nTo install missing packages, run:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def check_ollama():
    """Check if Ollama is available and has required models."""
    try:
        import subprocess
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Ollama is installed and running")
            models = result.stdout
            if 'qwen3:8b' in models:
                print("✅ qwen3:8b model is available")
            else:
                print("⚠️  qwen3:8b model not found. Run: ollama pull qwen3:8b")
            
            # Check for Sarvam model
            if 'sarvam' in models:
                print("✅ Sarvam model is available")
            else:
                print("⚠️  Sarvam model not found. Ensure your local Sarvam model is available in Ollama")
                print("   If you have a different model name, update SARVAM_MODEL_NAME in config.py")
            
            return True
        else:
            print("❌ Ollama is not running or not accessible")
            return False
    except FileNotFoundError:
        print("❌ Ollama is not installed")
        print("   Install from: https://ollama.ai/")
        return False
    except Exception as e:
        print(f"❌ Error checking Ollama: {e}")
        return False

def setup_config():
    """Set up configuration file."""
    config_template = "config_template.py"
    config_file = "config.py"
    
    if os.path.exists(config_file):
        print(f"✅ {config_file} already exists")
        
        # Check if model name is configured
        try:
            with open(config_file, 'r') as f:
                content = f.read()
                if 'SARVAM_MODEL_NAME = "sarvam"' in content:
                    print("⚠️  Sarvam model name is still default")
                    print(f"   Edit {config_file} and update SARVAM_MODEL_NAME if needed")
                    return True  # It's OK to use default, just warn user
                else:
                    print("✅ Sarvam model name appears to be configured")
                    return True
        except Exception as e:
            print(f"❌ Error reading {config_file}: {e}")
            return False
    else:
        if os.path.exists(config_template):
            try:
                shutil.copy2(config_template, config_file)
                print(f"✅ Created {config_file} from template")
                print(f"⚠️  You may need to edit {config_file} and update SARVAM_MODEL_NAME")
                return True
            except Exception as e:
                print(f"❌ Error creating {config_file}: {e}")
                return False
        else:
            print(f"❌ {config_template} not found")
            return False

def check_input_file():
    """Check if input file exists."""
    input_file = "leetcode.jsonl"
    if os.path.exists(input_file):
        print(f"✅ {input_file} exists")
        
        # Check file size and format
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                line_count = sum(1 for _ in f)
            print(f"   Contains {line_count} problems")
            return True
        except Exception as e:
            print(f"⚠️  Error reading {input_file}: {e}")
            return False
    else:
        print(f"❌ {input_file} not found")
        print("   This file should contain LeetCode problems in JSONL format")
        return False

def create_directories():
    """Create necessary directories."""
    directories = ['logs']
    
    for directory in directories:
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
                print(f"✅ Created directory: {directory}")
            except Exception as e:
                print(f"❌ Error creating directory {directory}: {e}")
                return False
        else:
            print(f"✅ Directory exists: {directory}")
    
    return True

def display_next_steps(config_ready, input_ready):
    """Display next steps for the user."""
    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    
    if not config_ready:
        print("1. 📝 Configure Local Sarvam Model:")
        print("   - Edit config.py")
        print("   - Update SARVAM_MODEL_NAME to match your local model name")
        print("   - Ensure the model is available in Ollama: ollama list")
        print()
    
    if not input_ready:
        print("2. 📁 Prepare input data:")
        print("   - Ensure leetcode.jsonl contains your LeetCode problems")
        print("   - Each line should be a JSON object with 'title' and 'content' fields")
        print()
    
    if config_ready and input_ready:
        print("🚀 You're ready to run the pipeline!")
        print()
        print("Test the translation service first:")
        print("   python translation.py")
        print()
        print("Run the complete pipeline:")
        print("   python traceWithThink.py")
        print()
        print("Or run only translation for existing traces:")
        print("   python translate_pipeline.py")
        print()
        print("Check database status anytime:")
        print("   python check_db.py")
    else:
        print("⚠️  Complete the above steps, then run this setup script again.")
    
    print("\n📚 For detailed instructions, see README.md")

def main():
    """Main setup function."""
    print("=" * 60)
    print("LeetCode Reasoning Trace Collection & Translation Pipeline")
    print("Setup Script")
    print("=" * 60)
    print()
    
    # Check system requirements
    print("🔍 Checking system requirements...")
    python_ok = check_python_version()
    deps_ok = check_dependencies()
    ollama_ok = check_ollama()
    
    print()
    
    # Setup environment
    print("🛠️  Setting up environment...")
    dirs_ok = create_directories()
    config_ready = setup_config()
    input_ready = check_input_file()
    
    print()
    
    # Summary
    print("📋 Setup Summary:")
    items = [
        ("Python version", python_ok),
        ("Dependencies", deps_ok),
        ("Ollama", ollama_ok),
        ("Directories", dirs_ok),
        ("Configuration", config_ready),
        ("Input file", input_ready),
    ]
    
    for item, status in items:
        icon = "✅" if status else "❌"
        print(f"   {icon} {item}")
    
    all_ready = all(status for _, status in items)
    
    if all_ready:
        print("\n🎉 Setup completed successfully!")
    else:
        print(f"\n⚠️  Setup incomplete. Please address the issues above.")
    
    # Display next steps
    display_next_steps(config_ready, input_ready)

if __name__ == "__main__":
    main()
