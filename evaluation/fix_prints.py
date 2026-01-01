#!/usr/bin/env python3
"""
Fix script to repair broken f-string print statements.

The issue: Some print statements got malformed with:
- Newlines inside f-strings: print(f"\n{'='*60}") became print(f"
{'='*60}")
- Double braces in f-strings: {{str(e)}} instead of {str(e)}
- Extra closing braces: {args.file_name}} instead of {args.file_name}
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
    """Fix broken print statements."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return False, f"Error reading: {e}"
    
    original_content = content
    
    # Fix print statements with newline before {'='*60}
    # Pattern: print(f"\n{'='*60}") that became print(f"
    # {'='*60}")
    content = re.sub(
        r'print\(f"\s*\n\s*\{\'=\'\*60\}"\)',
        'print(f"\\n{\'=\'*60}")',
        content
    )
    
    # Fix double braces in error messages
    # {{str(e)}} -> {str(e)}
    content = re.sub(r'\{\{str\(e\)\}\}', '{str(e)}', content)
    
    # Fix extra closing brace: {args.file_name}} -> {args.file_name}
    content = re.sub(r'\{args\.file_name\}\}', '{args.file_name}', content)
    content = re.sub(r'\{args\.model_name\}\}', '{args.model_name}', content)
    
    # Fix: {{result['output']}} -> {result['output']}
    content = re.sub(r"\{\{result\['output'\]\}\}", "{result['output']}", content)
    
    # Fix broken multi-line f-strings - join them back
    lines = content.split('\n')
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check if this line ends with unclosed f-string
        if 'print(f"' in line and not line.rstrip().endswith('")'):
            # Check if next line could be the continuation
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                # If next line is just {'='*60}") or similar
                if next_line.strip().startswith("{") and next_line.strip().endswith('")'):
                    # Merge the lines
                    merged = line.rstrip() + '\\n' + next_line.strip()
                    new_lines.append(merged)
                    i += 2
                    continue
        
        new_lines.append(line)
        i += 1
    
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
    print("Print Statement Fix Script")
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
