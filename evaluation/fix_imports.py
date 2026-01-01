#!/usr/bin/env python3
"""
Script to fix LangChain imports for LangChain 1.2.0

In LangChain 1.2.0, AgentExecutor and create_tool_calling_agent have been moved to langchain_classic.

The correct import is:
    from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
"""

import os
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

# The correct import for LangChain 1.2.0
CORRECT_IMPORT = 'from langchain_classic.agents import AgentExecutor, create_tool_calling_agent'

# Patterns to match old imports
OLD_IMPORT_PATTERNS = [
    r'^from langchain\.agents import AgentExecutor, create_tool_calling_agent\s*$',
    r'^from langchain\.agents import create_tool_calling_agent, AgentExecutor\s*$',
]


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
    
    # Skip if already using langchain_classic
    if 'from langchain_classic.agents import' in content:
        return False, None
    
    # Replace old import patterns
    for pattern in OLD_IMPORT_PATTERNS:
        content = re.sub(
            pattern,
            CORRECT_IMPORT,
            content,
            flags=re.MULTILINE
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
    print("LangChain 1.2.0 Import Fixer (using langchain_classic)")
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
    
    if fixed_count > 0:
        print()
        print("Make sure to install the required package:")
        print("  pip install langchain-classic")


if __name__ == "__main__":
    main()
