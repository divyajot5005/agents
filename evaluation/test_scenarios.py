#!/usr/bin/env python3
"""
Test Evaluation Script - No Paraphrasing, Shows Raw Outputs

This script runs each attack scenario directly against its agent without any
paraphrasing. It displays the full output for each scenario so you can inspect
the agent's behavior before running the full evaluation.

Usage:
    python test_scenarios.py --model llama3.1:8b
    python test_scenarios.py --model qwen2.5:7b --folder Spyware
    python test_scenarios.py --model llama3.1:8b --scenario 1 --folder Spyware
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

# Base directory containing all attack categories
BASE_DIR = Path(__file__).parent.parent

# Define the folder structure with attack categories and their leaf folders
ATTACK_CATEGORIES = {
    "1. Information Disclosure": [
        "Spyware",
        "System and Operational Secrets",
        "User and Enterprise Data Leak"
    ],
    "2. Unauthorized System Interaction": {
        "System State Access": [
            "Compute Misuse",
            "Unauthorized API and Tool Use"
        ],
        "System State Alteration": [
            "Distructive Actions",
            "Induced Recursive Loops for Language Models",
            "Permission & Configuration Escalation"
        ]
    },
    "3. Multi-Agent & Ecosystem Sabotage": {
        "Communication Poisoning": [
            "Impersonation & Spoofing",
            "Internal Information Distortion"
        ],
        "Systemic Destabilization": [
            "Collusion and Conspiracy Induction",
            "Reputation Slandering"
        ]
    }
}


def read_file(file_path: str) -> str:
    """Helper to read file content safely."""
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None


def get_all_leaf_folders() -> list:
    """
    Returns a list of tuples (folder_path, folder_name) for all leaf folders
    containing attack scenarios and agent scripts.
    """
    leaf_folders = []
    
    for category, subcategories in ATTACK_CATEGORIES.items():
        category_path = BASE_DIR / category
        
        if isinstance(subcategories, list):
            # Direct list of leaf folders
            for folder_name in subcategories:
                folder_path = category_path / folder_name
                if folder_path.exists():
                    leaf_folders.append((folder_path, folder_name))
        else:
            # Nested dictionary structure
            for sub_category, folders in subcategories.items():
                for folder_name in folders:
                    folder_path = category_path / sub_category / folder_name
                    if folder_path.exists():
                        leaf_folders.append((folder_path, folder_name))
    
    return leaf_folders


def find_attack_agent_pairs(folder_path: Path) -> list:
    """
    Find all attack scenario and corresponding agent script pairs in a folder.
    Returns list of tuples (attack_file_path, agent_script_path, scenario_number)
    """
    pairs = []
    seen_scenarios = set()
    
    attack_patterns = [
        "attack_scenario_*.txt",
        "attack_s*.txt"
    ]
    
    for pattern in attack_patterns:
        attack_files = list(folder_path.glob(pattern))
        for attack_file in attack_files:
            filename = attack_file.stem
            if "attack_scenario_" in filename:
                num = filename.replace("attack_scenario_", "")
            elif "attack_s" in filename:
                num = filename.replace("attack_s", "")
            else:
                continue
            
            try:
                scenario_num = int(num)
                
                if scenario_num in seen_scenarios:
                    continue
                
                agent_script = folder_path / f"s{scenario_num}.py"
                
                if agent_script.exists():
                    pairs.append((attack_file, agent_script, scenario_num))
                    seen_scenarios.add(scenario_num)
            except ValueError:
                continue
    
    pairs.sort(key=lambda x: x[2])
    return pairs


def run_agent_script(agent_script_path: Path, input_file: str, model_name: str) -> tuple:
    """
    Run an agent script on an input file and capture the full output.
    Returns tuple of (stdout, stderr, return_code)
    """
    try:
        result = subprocess.run(
            [sys.executable, str(agent_script_path), 
             "--model_name", model_name,
             "--file_name", input_file],
            capture_output=True,
            text=True,
            timeout=180,  # 3 minute timeout per run
            cwd=str(agent_script_path.parent)
        )
        
        return result.stdout, result.stderr, result.returncode
    
    except subprocess.TimeoutExpired:
        return "", "ERROR: Agent execution timed out after 3 minutes", -1
    except Exception as e:
        return "", f"ERROR: {str(e)}", -1


def print_separator(char="=", length=80):
    print(char * length)


def print_header(title, char="="):
    print_separator(char)
    print(f" {title}")
    print_separator(char)


def main():
    parser = argparse.ArgumentParser(
        description="Test Evaluation Script - No Paraphrasing, Shows Raw Outputs"
    )
    parser.add_argument(
        "--model", 
        type=str, 
        required=True,
        help="Ollama model to use for running agents (e.g., 'llama3.1:8b', 'qwen2.5:7b')"
    )
    parser.add_argument(
        "--folder",
        type=str,
        default=None,
        help="Specific folder to evaluate (e.g., 'Spyware'). If not provided, runs all."
    )
    parser.add_argument(
        "--scenario",
        type=int,
        default=None,
        help="Specific scenario number to run within the folder (e.g., 1, 2, 3)"
    )
    parser.add_argument(
        "--show_attack",
        action="store_true",
        default=True,
        help="Show the attack scenario content in output (default: True)"
    )
    parser.add_argument(
        "--no_attack",
        action="store_true",
        help="Hide the attack scenario content in output"
    )
    parser.add_argument(
        "--output_file",
        type=str,
        default=None,
        help="Optional: Save outputs to a file instead of just console"
    )
    
    args = parser.parse_args()
    
    # Handle show_attack flag
    show_attack = not args.no_attack
    
    # Get all leaf folders
    all_folders = get_all_leaf_folders()
    
    # Filter folders if specific one requested
    if args.folder:
        all_folders = [(p, n) for p, n in all_folders if n == args.folder]
        if not all_folders:
            print(f"Error: Folder '{args.folder}' not found.")
            print("Available folders:")
            for _, name in get_all_leaf_folders():
                print(f"  - {name}")
            return
    
    # Setup output file if requested
    output_file = None
    if args.output_file:
        output_file = open(args.output_file, 'w', encoding='utf-8')
    
    def log(message):
        """Print to console and optionally to file."""
        print(message)
        if output_file:
            output_file.write(message + '\n')
    
    # Print header
    log("")
    print_header("TEST EVALUATION SCRIPT - NO PARAPHRASING")
    log(f"Model: {args.model}")
    log(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if args.folder:
        log(f"Folder Filter: {args.folder}")
    if args.scenario:
        log(f"Scenario Filter: {args.scenario}")
    log("")
    
    total_scenarios_run = 0
    
    # Process each folder
    for folder_path, folder_name in all_folders:
        print_header(f"FOLDER: {folder_name}", "=")
        log(f"Path: {folder_path}")
        log("")
        
        # Find attack-agent pairs
        pairs = find_attack_agent_pairs(folder_path)
        
        if not pairs:
            log(f"  [!] No attack-agent pairs found in {folder_name}")
            log("")
            continue
        
        # Filter by scenario if specified
        if args.scenario:
            pairs = [(a, s, n) for a, s, n in pairs if n == args.scenario]
            if not pairs:
                log(f"  [!] Scenario {args.scenario} not found in {folder_name}")
                log("")
                continue
        
        log(f"Found {len(pairs)} attack-agent pair(s)")
        log("")
        
        # Process each scenario
        for attack_file, agent_script, scenario_num in pairs:
            print_header(f"SCENARIO {scenario_num}: {attack_file.name}", "-")
            log(f"Agent Script: {agent_script.name}")
            log("")
            
            # Read attack content
            attack_content = read_file(str(attack_file))
            if not attack_content:
                log(f"  [!] Could not read attack file: {attack_file.name}")
                log("")
                continue
            
            # Show attack content if requested
            if show_attack:
                log("--- ATTACK SCENARIO INPUT ---")
                log(attack_content)
                log("--- END OF ATTACK SCENARIO ---")
                log("")
            
            # Run the agent
            log("Running agent...")
            log("")
            
            stdout, stderr, return_code = run_agent_script(
                agent_script, 
                str(attack_file), 
                args.model
            )
            
            # Show output
            log("--- AGENT OUTPUT (stdout) ---")
            if stdout:
                log(stdout)
            else:
                log("[No stdout output]")
            log("--- END OF STDOUT ---")
            
            if stderr:
                log("")
                log("--- AGENT ERRORS (stderr) ---")
                log(stderr)
                log("--- END OF STDERR ---")
            
            log("")
            log(f"Return Code: {return_code}")
            log("")
            
            # Extract the final agent response if present
            if "Agent Response:" in stdout:
                log("--- EXTRACTED FINAL RESPONSE ---")
                response_start = stdout.find("Agent Response:")
                response_section = stdout[response_start:]
                lines = response_section.split('\n')
                if len(lines) > 2:
                    final_response = '\n'.join(lines[2:]).strip()
                    log(final_response)
                else:
                    log("[Could not extract final response]")
                log("--- END OF FINAL RESPONSE ---")
            
            log("")
            total_scenarios_run += 1
    
    # Summary
    print_header("SUMMARY")
    log(f"Total scenarios run: {total_scenarios_run}")
    log(f"Model used: {args.model}")
    if args.output_file:
        log(f"Output saved to: {args.output_file}")
    log("")
    
    if output_file:
        output_file.close()
        print(f"\n[OK] Full output saved to: {args.output_file}")


if __name__ == "__main__":
    main()
