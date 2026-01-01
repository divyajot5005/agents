#!/usr/bin/env python3
"""
Script to fix all imports and escape curly braces in agent scripts for LangChain 1.2.0.

This script:
1. Ensures proper imports for langchain_classic, langchain_core, langchain_ollama
2. Escapes single curly braces {} in prompt templates to {{}} so they are treated as literals
3. Fixes common syntax errors (missing commas in message tuples)
"""

import os
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent


def find_all_agent_scripts():
    """Find all s*.py files in the agents folder."""
    agent_scripts = []
    for py_file in BASE_DIR.rglob("s*.py"):
        if "evaluation" in str(py_file):
            continue
        if re.match(r"s\d+\.py$", py_file.name):
            agent_scripts.append(py_file)
    return agent_scripts


def escape_json_in_prompt(content: str) -> str:
    """
    Find ChatPromptTemplate strings and escape single curly braces to double curly braces,
    but preserve template variables like {input}, {current_date}, {agent_scratchpad}.
    """
    # Known template variables that should NOT be escaped
    template_vars = {'input', 'current_date', 'agent_scratchpad', 'variable_name'}
    
    # Find all strings that look like prompts (multi-line strings with system/human messages)
    # We need to be careful to only escape curly braces inside the prompt content
    
    # Pattern to find the system message content in ChatPromptTemplate
    # Match from (\"system\", \"\"\" to \"\"\") or similar patterns
    
    def escape_braces_in_match(match):
        """Escape braces in the matched content, preserving template variables."""
        text = match.group(0)
        
        # Don't escape if it's a template variable
        result = []
        i = 0
        while i < len(text):
            if text[i] == '{':
                # Look for closing brace
                j = i + 1
                while j < len(text) and text[j] != '}' and text[j] != '{':
                    j += 1
                
                if j < len(text) and text[j] == '}':
                    var_name = text[i+1:j]
                    
                    # Check if this is already escaped (double braces)
                    if i > 0 and text[i-1] == '{':
                        result.append(text[i])
                        i += 1
                        continue
                    
                    # Check if this is a template variable that should NOT be escaped
                    if var_name.strip() in template_vars:
                        result.append(text[i:j+1])
                        i = j + 1
                        continue
                    
                    # Check if it's already escaped
                    if i > 0 and text[i-1:i] == '{':
                        result.append(text[i])
                        i += 1
                        continue
                    
                    # This is a curly brace that should be escaped
                    # But first check if it looks like JSON
                    if var_name.strip().startswith('"') or var_name.strip().startswith("'"):
                        # This is JSON-like content, escape it
                        result.append('{{')
                        i += 1
                        continue
                    elif ':' in var_name or ',' in var_name:
                        # This is JSON-like content
                        result.append('{{')
                        i += 1
                        continue
                    else:
                        # Single word variable, check if it's a template var
                        if var_name.strip() in template_vars:
                            result.append(text[i])
                            i += 1
                            continue
                        else:
                            # Escape it
                            result.append('{{')
                            i += 1
                            continue
                else:
                    result.append(text[i])
                    i += 1
            elif text[i] == '}':
                # Check if previous char was not already a }
                if i > 0 and text[i-1] == '}':
                    result.append(text[i])
                    i += 1
                    continue
                
                # Look back to see if this closes a template variable
                # Find the matching opening brace
                found_template = False
                for tvar in template_vars:
                    pattern = '{' + tvar + '}'
                    # Check if this } is part of a template variable
                    check_start = max(0, i - len(tvar) - 1)
                    check_str = text[check_start:i+1]
                    if pattern in check_str:
                        found_template = True
                        break
                
                if found_template:
                    result.append(text[i])
                else:
                    result.append('}}')
                i += 1
            else:
                result.append(text[i])
                i += 1
        
        return ''.join(result)
    
    # Simpler approach: Just escape specific JSON patterns
    # Pattern: {"key": or {\"key\":
    content = re.sub(r'(?<!\{)\{(?!\{)("[\w_]+"\s*:\s*)', r'{{\1', content)
    content = re.sub(r'(?<!\{)\{(?!\{)(\\"[\w_]+\\"\s*:\s*)', r'{{\1', content)
    
    # Pattern: closing } that's not }} and not a template var
    # This is trickier - we need to escape } that are part of JSON
    
    # Find Action Input: {...} patterns and escape them
    def escape_json_block(match):
        text = match.group(1)
        # Escape { and } that are not already escaped
        text = re.sub(r'(?<!\{)\{(?!\{)', '{{', text)
        text = re.sub(r'(?<!\})\}(?!\})', '}}', text)
        return 'Action Input: ' + text
    
    content = re.sub(r'Action Input:\s*(\{[^}]+\})', escape_json_block, content)
    
    # Also handle multi-line JSON blocks
    def escape_multiline_json(match):
        text = match.group(1)
        text = re.sub(r'(?<!\{)\{(?!\{)', '{{', text)
        text = re.sub(r'(?<!\})\}(?!\})', '}}', text)
        return 'Action Input: ' + text
    
    content = re.sub(r'Action Input:\s*(\{[\s\S]*?\n\s*\})', escape_multiline_json, content)
    
    return content


def fix_file(file_path: Path) -> tuple:
    """Fix imports, syntax, and escape curly braces in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return False, f"Error reading: {e}"
    
    original_content = content
    
    # Add missing imports
    if 'ChatPromptTemplate' in content and 'from langchain_core.prompts' not in content:
        if 'from langchain.prompts' in content:
            content = content.replace(
                'from langchain.prompts import ChatPromptTemplate',
                'from langchain_core.prompts import ChatPromptTemplate'
            )
    
    if '@tool' in content and 'from langchain_core.tools import tool' not in content:
        if 'from langchain.tools import tool' not in content:
            # Find last import line and add after it
            lines = content.split('\n')
            last_import_idx = 0
            for i, line in enumerate(lines):
                if line.strip().startswith('import ') or line.strip().startswith('from '):
                    last_import_idx = i
            lines.insert(last_import_idx + 1, 'from langchain_core.tools import tool')
            content = '\n'.join(lines)
    
    if 'ChatOllama' in content and 'from langchain_ollama import ChatOllama' not in content:
        if 'from langchain_community.chat_models import ChatOllama' in content:
            content = content.replace(
                'from langchain_community.chat_models import ChatOllama',
                'from langchain_ollama import ChatOllama'
            )
        else:
            lines = content.split('\n')
            last_import_idx = 0
            for i, line in enumerate(lines):
                if line.strip().startswith('import ') or line.strip().startswith('from '):
                    last_import_idx = i
            lines.insert(last_import_idx + 1, 'from langchain_ollama import ChatOllama')
            content = '\n'.join(lines)
    
    # Fix missing comma in message tuples
    content = re.sub(
        r'"""\)\s*\n(\s*)\("human"',
        '"""),\n\\1("human"',
        content
    )
    content = re.sub(
        r'"""\)\s*\n(\s*)MessagesPlaceholder',
        '"""),\n\\1MessagesPlaceholder',
        content
    )
    
    # Escape curly braces in prompts
    content = escape_json_in_prompt(content)
    
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
    print("Complete Fix Script for LangChain 1.2.0 + langchain-classic")
    print("=" * 70)
    print()
    print("This script:")
    print("  - Adds missing imports")
    print("  - Fixes syntax errors")
    print("  - Escapes curly braces in JSON examples")
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


if __name__ == "__main__":
    main()
