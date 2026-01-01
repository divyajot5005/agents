#!/usr/bin/env python3
"""
Script to fix LangChain import statements across all agent scripts.

For LangChain 0.3.x, the correct import is:
    from langchain.agents import create_tool_calling_agent, AgentExecutor

This script finds and fixes all agent scripts that have broken imports.
"""

import os
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent


def find_all_agent_scripts():
    """Find all s*.py files in the agents folder."""
    agent_scripts = []
    for py_file in BASE_DIR.rglob("s*.py"):
        # Skip files in evaluation folder
        if "evaluation" in str(py_file):
            continue
        # Must match pattern s[number].py
        if re.match(r"s\d+\.py$", py_file.name):
            agent_scripts.append(py_file)
    return agent_scripts


def fix_imports_in_file(file_path: Path) -> tuple:
    """
    Fix the import statements in a single file.
    Returns tuple of (was_fixed, error_message)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
    except Exception as e:
        return False, f"Error reading: {e}"
    
    original_content = content
    modified = False
    
    # New lines to build
    new_lines = []
    i = 0
    skip_until = -1
    
    while i < len(lines):
        line = lines[i]
        
        # Skip if we're in a region to skip
        if i < skip_until:
            i += 1
            continue
        
        # Check for the problematic try-except import block
        # Pattern: starts with "try:" and next line has "from langchain.agents import"
        if line.strip() == "try:" or "# --- Import Fix" in line:
            # Look ahead to see if this is the import try-except block
            block_lines = []
            j = i
            in_import_block = False
            
            while j < len(lines):
                check_line = lines[j]
                block_lines.append(check_line)
                
                if "from langchain.agents import AgentExecutor" in check_line:
                    in_import_block = True
                
                # End detection: line after except block that's not indented
                if in_import_block and j > i:
                    # Check if we hit the end marker or a non-indented line after the import
                    if "# ----" in check_line:
                        j += 1
                        break
                    if check_line.strip() and not check_line.startswith(' ') and not check_line.startswith('\t'):
                        if "from langchain" not in check_line and "except" not in check_line and "try" not in check_line:
                            break
                j += 1
            
            if in_import_block:
                # Replace the entire block with simple import
                new_lines.append("from langchain.agents import create_tool_calling_agent, AgentExecutor")
                skip_until = j
                i = j
                modified = True
                continue
        
        # Check for standalone broken import
        if "from langchain.agents.agent_executor import AgentExecutor" in line:
            # Skip this line entirely (should be handled by the main import)
            i += 1
            modified = True
            continue
        
        new_lines.append(line)
        i += 1
    
    if modified:
        new_content = '\n'.join(new_lines)
        # Clean up any double blank lines created
        new_content = re.sub(r'\n{3,}', '\n\n', new_content)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True, None
        except Exception as e:
            return False, f"Error writing: {e}"
    
    return False, None


def main():
    print("=" * 70)
    print("LangChain Import Fixer for v0.3.x")
    print("=" * 70)
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
        print("Note: Make sure to install the required packages:")
        print("  pip install -r requirements.txt")


if __name__ == "__main__":
    main()
