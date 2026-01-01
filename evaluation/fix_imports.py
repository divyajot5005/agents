#!/usr/bin/env python3
"""
Script to fix LangChain imports for LangChain 1.2.0

In LangChain 1.x, the correct import is simply:
    from langchain.agents import AgentExecutor, create_tool_calling_agent

This script removes any try-except blocks and uses the direct import.
"""

import os
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

# The simple import for LangChain 1.2.0
CORRECT_IMPORT = 'from langchain.agents import AgentExecutor, create_tool_calling_agent'


def find_all_agent_scripts():
    """Find all s*.py files in the agents folder."""
    agent_scripts = []
    for py_file in BASE_DIR.rglob("s*.py"):
        if "evaluation" in str(py_file):
            continue
        if re.match(r"s\d+\.py$", py_file.name):
            agent_scripts.append(py_file)
    return agent_scripts


def fix_imports_in_file(file_path: Path) -> tuple:
    """Fix the import statements in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return False, f"Error reading: {e}"
    
    original_content = content
    
    # Pattern to match the try-except compatibility block we added
    # This matches the entire block from "# --- LangChain Version Compatibility ---" to "# ---"
    compat_block_pattern = r'# --- LangChain Version Compatibility ---\ntry:\n.*?# ---+\n'
    
    # Check if file has the compatibility block
    if '# --- LangChain Version Compatibility ---' in content:
        # Replace the entire block with simple import
        content = re.sub(
            compat_block_pattern,
            CORRECT_IMPORT + '\n',
            content,
            flags=re.DOTALL
        )
    
    # Also check for older compatibility blocks
    old_compat_pattern = r'# --- Import Fix for LangChain Version Compatibility ---\ntry:.*?# -+\n'
    if '# --- Import Fix for LangChain Version Compatibility ---' in content:
        content = re.sub(
            old_compat_pattern,
            CORRECT_IMPORT + '\n',
            content,
            flags=re.DOTALL
        )
    
    if content != original_content:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, None
        except Exception as e:
            return False, f"Error writing: {e}"
    
    return False, None


def main():
    print("=" * 70)
    print("LangChain 1.2.0 Import Fixer")
    print("=" * 70)
    print()
    print(f"Setting import to: {CORRECT_IMPORT}")
    print()
    
    scripts = find_all_agent_scripts()
    print(f"Found {len(scripts)} agent scripts to check")
    print()
    
    fixed_count = 0
    error_count = 0
    
    for script in sorted(scripts):
        relative_path = script.relative_to(BASE_DIR)
        was_fixed, error = fix_imports_in_file(script)
        
        if error:
            print(f"  [ERROR] {relative_path}: {error}")
            error_count += 1
        elif was_fixed:
            print(f"  [FIXED] {relative_path}")
            fixed_count += 1
    
    print()
    print("=" * 70)
    print(f"Summary: Fixed {fixed_count} files, {error_count} errors")
    print("=" * 70)


if __name__ == "__main__":
    main()
