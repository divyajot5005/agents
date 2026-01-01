#!/usr/bin/env python3
"""
Fix script to repair Python dict literals that were incorrectly double-braced.

The issue: {{ in Python code (like lists of dicts) was accidentally escaped
when it should only be escaped inside prompt template strings.
"""

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


def fix_file(file_path: Path) -> tuple:
    """Fix Python dict literals that were incorrectly double-braced."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return False, f"Error reading: {e}"
    
    original_content = content
    
    # Find dict literals inside Python lists that were incorrectly escaped
    # Pattern: [{{ or , {{ inside Python code (not inside triple-quoted strings)
    
    # We need to be careful to only fix braces OUTSIDE of triple-quoted strings
    # Strategy: Split by triple quotes, fix only odd-indexed parts (outside strings)
    
    # Simpler approach: look for specific patterns that are clearly wrong
    
    # Pattern: list with double-braced dicts
    # [{{" should be [{"
    content = re.sub(r'\[\{\{\"', '[{"', content)
    
    # ,{{" should be ,{"
    content = re.sub(r',\s*\{\{\"', ', {"', content)
    
    # Dict ending incorrectly: "}} should be "}
    # But we need to be careful - }} is correct inside prompts
    # Look for pattern: dict value end followed by comma or bracket
    # "}}, or "}}] - these are likely dict literals, not prompts
    
    # Very specific: filesystem = {{\n or similar
    content = re.sub(r'filesystem = \{\{', 'filesystem = {', content)
    content = re.sub(r'events = \[\s*\n\s*\{\{', 'events = [\n        {', content)
    
    # Fix dict entries that were double-braced
    # Pattern: lines that look like dict entries but have {{
    lines = content.split('\n')
    new_lines = []
    in_triple_string = False
    triple_quote_count = 0
    
    for line in lines:
        # Count triple quotes to track if we're inside a string
        triple_count = line.count('"""')
        if triple_count % 2 == 1:
            in_triple_string = not in_triple_string
        
        if not in_triple_string:
            # Safe to fix double braces in Python code
            # Pattern: {{" at start of dict in list
            if '{{\"' in line and ('[' in line or line.strip().startswith('{{')):
                line = line.replace('{{\"', '{"')
            # Pattern: "}} at end of dict
            if '\"}}' in line and (']' in line or line.strip().endswith('}}')):
                line = line.replace('\"}}', '"}')
            # General pattern for dict in list
            if re.match(r'\s*\{\{\"', line):
                line = re.sub(r'^\s*\{\{\"', lambda m: m.group(0).replace('{{', '{'), line)
        
        new_lines.append(line)
    
    content = '\n'.join(new_lines)
    
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
    print("Python Dict Literal Fix Script")
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


if __name__ == "__main__":
    main()
