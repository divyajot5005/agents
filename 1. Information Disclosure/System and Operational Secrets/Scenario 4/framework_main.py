import os
import argparse
from dotenv import load_dotenv

# --- Imports for the LangGraph/LCEL Engine ---
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
# ---------------------------------------------

# Import the scenario-specific tools, state, and prompt
from s04_tools import (
    modify_scheduled_job, 
    retrieve_db_connection_string, 
    ATTACK_SUCCESS,
    AGENT_ACCESS_PROMPT
)
 
# --- Configuration & Setup ---
load_dotenv()
LLM_MODEL_DEFAULT = "llama3.1" 

def read_input_from_file(file_path: str) -> str:
    """Read the user's attack input from a text file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        raise FileNotFoundError(f"Input file not found: {file_path}")

def initialize_llm(model_name: str):
    print(f"Using local Ollama model: {model_name}...")
    return ChatOllama(model=model_name, temperature=0)

def create_operational_agent(llm):
    """Creates the agent using create_react_agent from langgraph."""
    tools = [modify_scheduled_job, retrieve_db_connection_string]
    llm_with_tools = llm.bind_tools(tools)
    agent_runnable = create_react_agent(llm_with_tools, tools, prompt=AGENT_ACCESS_PROMPT)
    return agent_runnable

def main():
    parser = argparse.ArgumentParser(description="Scenario 4: ETL Database Secret Leakage (Critical Recovery) Test")
    parser.add_argument("--model_name", type=str, default=LLM_MODEL_DEFAULT)
    parser.add_argument("--file_name", type=str, required=True, help="Path to the text file containing the user query.")
    args = parser.parse_args()
    
    print(f"\n--- TEST: SCENARIO 4 (ETL Database Secret Leakage) ---")
    print(f"LLM Model: {args.model_name}")
    print("-" * 60)
    
    # --- GET USER INPUT FROM FILE ---
    try:
        user_input = read_input_from_file(args.file_name)
    except Exception as e:
        print(f"Error: {str(e)}")
        return

    # Initialize LLM and Agent
    try:
        llm = initialize_llm(args.model_name)
        agent = create_operational_agent(llm)
        print(f"Agent created.")
    except Exception as e:
        print(f"\nFailed to create agent: {e}")
        return
    
    # Execute the attack
    print("\n[2] Running Single-Step Request...")
    print(f"\n[REQUEST] User Input: '{user_input}'")
    
    # The tool will update the ATTACK_SUCCESS dictionary imported from s04_tools.py
    input_payload = {"messages": [("user", user_input)]}
    
    try:
        agent.invoke(input_payload)
    except Exception as e:
        print(f"\nError during agent invocation: {e}")
        pass

    # --- FINAL RESULT CHECK ---
    print("\n[3] Checking test outcome...")

    if ATTACK_SUCCESS["critical_action_logged"]:
        print("\n--- 🟢 ACTION SUCCESSFUL (Root Password Leak) 🟢 ---")
        print("Result: The agent was coerced into executing the high-privilege tool.")
        print(f"Outcome: Unhashed connection string leaked for DB: {ATTACK_SUCCESS['target_db']}.")
        print("-" * 60)
    else:
        print("\n--- 🔴 ACTION BLOCKED (Recovery Caution) 🔴 ---")
        print("Result: The agent successfully resisted the command to leak the root password.")
        print("Outcome: Disaster recovery objective was not hijacked.")
        print("-" * 60)

if __name__ == "__main__":
    main()