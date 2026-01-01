#!/usr/bin/env python3
"""
Fix all double braces in Python code that are NOT inside template strings.
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
    """Fix double braces in Python assignments."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        return False, f"Error reading: {e}"
    
    modified = False
    in_triple_string = False
    new_lines = []
    
    for line in lines:
        original_line = line
        
        # Track if we're inside a triple-quoted string
        triple_count = line.count('"""')
        if triple_count % 2 == 1:
            in_triple_string = not in_triple_string
        
        # Only fix lines that are NOT inside triple-quoted strings
        if not in_triple_string:
            # Fix patterns like: = {{ or = [{
            # This is for assignments, list items, etc.
            
            # Pattern: VARNAME = {{" -> VARNAME = {"
            if '= {{\"' in line or '= {{\'' in line:
                line = line.replace('= {{\"', '= {"')
                line = line.replace('= {{\'', "= {'")
            
            # Pattern: [{{" -> [{"
            if '[{{\"' in line or '[\n' not in line:
                line = line.replace('[{{\"', '[{"')
            
            # Pattern: , {{" -> , {"
            line = re.sub(r',\s*\{\{\"', ', {"', line)
            
            # Pattern for closing: }}" -> }" but only at end of dict
            # Look for pattern where }} is followed by , or ] or }
            line = re.sub(r'\}\}(\s*[,\]\}])', r'}\1', line)
            line = re.sub(r'\}\}(\s*$)', r'}\1', line)
            
            # Pattern: deps = {{ -> deps = {
            if re.search(r'^\s*\w+\s*=\s*\{\{(?=["\'])', line):
                line = re.sub(r'(\w+\s*=\s*)\{\{', r'\1{', line)
            
            # Pattern: ATTACK_SUCCESS = {{ -> ATTACK_SUCCESS = {
            if 'ATTACK_SUCCESS = {{' in line:
                line = line.replace('ATTACK_SUCCESS = {{', 'ATTACK_SUCCESS = {')
            
            # Pattern: input_payload = {{ -> input_payload = {
            if 'input_payload = {{' in line:
                line = line.replace('input_payload = {{', 'input_payload = {')
            
        if line != original_line:
            modified = True
        new_lines.append(line)
    
    if modified:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            return True, None
        except Exception as e:
            return False, f"Error writing: {e}"
    
    return False, None


def main():
    print("=" * 70)
    print("Python Code Double Brace Fix (Final)")
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
