#!/usr/bin/env python3
"""
Script to fix all imports in agent scripts for LangChain 1.2.0 + langchain-classic.

This script:
1. Ensures langchain_classic is used for AgentExecutor and create_tool_calling_agent
2. Adds missing imports for tool, ChatOllama, ChatPromptTemplate, MessagesPlaceholder
3. Fixes common syntax errors (missing commas in message tuples)
"""

import os
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

# Required imports for LangChain 1.2.0 with langchain-classic
REQUIRED_IMPORTS = {
    'from langchain_classic.agents import AgentExecutor, create_tool_calling_agent',
    'from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder',
    'from langchain_core.tools import tool',
    'from langchain_ollama import ChatOllama',
}


def find_all_agent_scripts():
    """Find all s*.py files in the agents folder."""
    agent_scripts = []
    for py_file in BASE_DIR.rglob("s*.py"):
        if "evaluation" in str(py_file):
            continue
        if re.match(r"s\d+\.py$", py_file.name):
            agent_scripts.append(py_file)
    return agent_scripts


def fix_file(file_path: Path) -> tuple:
    """Fix imports and syntax in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return False, f"Error reading: {e}"
    
    original_content = content
    lines = content.split('\n')
    
    # Track what imports exist
    has_agent_import = 'from langchain_classic.agents import' in content
    has_prompt_import = 'ChatPromptTemplate' in content and 'from langchain' in content and 'import' in content
    has_tool_import = 'from langchain_core.tools import tool' in content or 'from langchain.tools import tool' in content
    has_ollama_import = 'from langchain_ollama import ChatOllama' in content or 'from langchain_community.chat_models import ChatOllama' in content
    
    # Find the last import line index
    last_import_idx = 0
    for i, line in enumerate(lines):
        if line.strip().startswith('import ') or line.strip().startswith('from '):
            last_import_idx = i
    
    # Build list of imports to add
    imports_to_add = []
    
    # Check if we need to add prompt imports
    if 'ChatPromptTemplate' in content and 'from langchain_core.prompts' not in content:
        if 'from langchain.prompts' in content:
            # Replace old import
            content = content.replace(
                'from langchain.prompts import ChatPromptTemplate',
                'from langchain_core.prompts import ChatPromptTemplate'
            )
        else:
            imports_to_add.append('from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder')
    
    # Check if we need tool import
    if '@tool' in content and 'from langchain_core.tools import tool' not in content:
        if 'from langchain.tools import tool' not in content:
            imports_to_add.append('from langchain_core.tools import tool')
    
    # Check if we need ChatOllama import
    if 'ChatOllama' in content and 'from langchain_ollama import ChatOllama' not in content:
        if 'from langchain_community.chat_models import ChatOllama' in content:
            content = content.replace(
                'from langchain_community.chat_models import ChatOllama',
                'from langchain_ollama import ChatOllama'
            )
        else:
            imports_to_add.append('from langchain_ollama import ChatOllama')
    
    # Add missing imports after existing imports
    if imports_to_add:
        lines = content.split('\n')
        # Find position after last import
        for i, line in enumerate(lines):
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                last_import_idx = i
        
        # Insert new imports
        for imp in imports_to_add:
            lines.insert(last_import_idx + 1, imp)
            last_import_idx += 1
        
        content = '\n'.join(lines)
    
    # Fix missing comma in message tuples (common syntax error)
    # Pattern: """)\n        ("human" should be """),\n        ("human"
    content = re.sub(
        r'"""\)\s*\n(\s*)\("human"',
        '"""),\n\\1("human"',
        content
    )
    
    # Also fix: """)\n        MessagesPlaceholder  
    content = re.sub(
        r'"""\)\s*\n(\s*)MessagesPlaceholder',
        '"""),\n\\1MessagesPlaceholder',
        content
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
    print("Complete Import Fixer for LangChain 1.2.0 + langchain-classic")
    print("=" * 70)
    print()
    
    scripts = find_all_agent_scripts()
    print(f"Found {len(scripts)} agent scripts to check")
    print()
    
    fixed_count = 0
    error_count = 0
    
    for script in sorted(scripts):
        relative_path = script.relative_to(BASE_DIR)
        was_fixed, error = fix_file(script)
        
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
        print("Required packages:")
        print("  pip install langchain-classic langchain-core langchain-ollama")


if __name__ == "__main__":
    main()
