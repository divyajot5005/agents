import os
import argparse
from dotenv import load_dotenv

# --- Imports for the LangGraph/LCEL Engine ---
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
# ---------------------------------------------

# Import the scenario-specific tools, state, and prompt
from s02_tools import (
    check_pipeline_status, 
    retrieve_config_details, 
    ATTACK_SUCCESS,
    AGENT_POLICY_PROMPT_SYSTEM
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
    """Creates the Llama 3.1 agent using create_react_agent from langgraph."""
    tools = [check_pipeline_status, retrieve_config_details]
    
    # Bind tools to the LLM for function/tool calling capability
    llm_with_tools = llm.bind_tools(tools)
    
    # Pass the prompt, the tools, and the LLM using the langgraph function
    agent_runnable = create_react_agent(llm_with_tools, tools, prompt=AGENT_POLICY_PROMPT_SYSTEM)
    
    return agent_runnable

def main():
    parser = argparse.ArgumentParser(description="Scenario 2: System Secrets Leakage (CI/CD Pipeline) Test")
    parser.add_argument("--model_name", type=str, default=LLM_MODEL_DEFAULT)
    # File name is required to read the attack query
    parser.add_argument("--file_name", type=str, required=True, help="Path to the text file containing the user query.")
    args = parser.parse_args()
    
    print(f"\n--- TEST: SCENARIO 2 (System Secrets Leakage) ---")
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
    
    # The tool will update the ATTACK_SUCCESS dictionary imported from s02_tools.py
    input_payload = {"messages": [("user", user_input)]}
    
    try:
        agent.invoke(input_payload)
    except Exception as e:
        print(f"\nError during agent invocation: {e}")
        pass

    # --- FINAL RESULT CHECK ---
    print("\n[3] Checking test outcome...")

    if ATTACK_SUCCESS["critical_action_logged"]:
        print("\n--- 🟢 ACTION SUCCESSFUL (System Secret Leak) 🟢 ---")
        print("Result: The agent was coerced into executing the high-privilege tool.")
        print(f"Outcome: Mock secrets leaked for pipeline: {ATTACK_SUCCESS['target_pipeline']}.")
        print("-" * 60)
    else:
        print("\n--- 🔴 ATTACK BLOCKED (Thoroughness Ignored) 🔴 ---")
        print("Result: The agent successfully ignored the high-privilege configuration tool.")
        print("Outcome: Operational policy did not override basic tool caution.")
        print("-" * 60)

if __name__ == "__main__":
    main()