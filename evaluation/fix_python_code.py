#!/usr/bin/env python3
"""
Fix script to repair the invoke calls that were accidentally double-braced.

The issue: agent_executor.invoke({{ was changed when it should remain agent_executor.invoke({
Only the content inside prompt template strings should have double braces.
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
    """Fix the invoke calls and other Python code that shouldn't have double braces."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return False, f"Error reading: {e}"
    
    original_content = content
    
    # Fix agent_executor.invoke({{ -> agent_executor.invoke({
    content = re.sub(r'\.invoke\(\{\{', '.invoke({', content)
    
    # Fix closing }} at end of invoke call that should be }
    # Pattern: }}\s*\)\s*$ or }}\s*\) at end of statement
    content = re.sub(r'\}\}\s*\)', '})', content)
    
    # Fix print statements that accidentally got double braces
    content = re.sub(r"print\(f\"\\n\{\{'='\*60\}\}", "print(f\"\\n{'='*60}", content)
    content = re.sub(r"\{\{'='\*60\}\}", "{'='*60}", content)
    content = re.sub(r"\{\{args\.", "{args.", content)
    
    # Fix f-string expressions that shouldn't be escaped
    # Pattern: {{result['output']}} -> {result['output']}
    content = re.sub(r"\{\{result\['(\w+)'\]\}\}", r"{result['\1']}", content)
    
    # Fix {{args.file_name}} -> {args.file_name}
    content = re.sub(r"\{\{args\.(\w+)\}\}", r"{args.\1}", content)
    
    # Fix any remaining f-string variables
    content = re.sub(r"\{\{(\w+)\}\}", r"{\1}", content)
    
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
    print("Python Code Fix Script")
    print("=" * 70)
    print()
    print("Fixing:")
    print("  - agent_executor.invoke({{ -> invoke({")
    print("  - f-string expressions that were accidentally escaped")
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
