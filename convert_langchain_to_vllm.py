"""
Batch converter: LangChain to VLLM (OpenAI client)
This script replaces LangChain usage with direct OpenAI client for VLLM compatibility.
"""

import os
import re
import glob

# Template for the new VLLM-compatible agent class and main function
VLLM_AGENT_TEMPLATE = '''
# --- REACT AGENT IMPLEMENTATION ---
class ReActAgent:
    """ReAct agent compatible with VLLM via OpenAI client."""

    def __init__(self, client: OpenAI, model_name: str, tools: Dict[str, Callable], max_iterations: int = 5):
        self.client = client
        self.model_name = model_name
        self.tools = tools
        self.max_iterations = max_iterations

    def _parse_action(self, text: str) -> tuple[Optional[str], Optional[str]]:
        action_match = re.search(r"Action:\\s*(\\w+)", text, re.IGNORECASE)
        input_match = re.search(r"Action Input:\\s*(\\{.*?\\})", text, re.IGNORECASE | re.DOTALL)
        return (action_match.group(1) if action_match else None,
                input_match.group(1) if input_match else None)

    def _parse_final_answer(self, text: str) -> Optional[str]:
        match = re.search(r"Final Answer:\\s*(.+?)(?:\\n\\n|$)", text, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else None

    def _execute_tool(self, name: str, inp: str) -> str:
        if name not in self.tools:
            return f"Error: Unknown tool '{name}'"
        try:
            return self.tools[name](**json.loads(inp))
        except Exception as e:
            return f"Error: {e}"

    def run(self, user_input: str, current_date: str) -> str:
        system_prompt = REACT_SYSTEM_PROMPT.format(current_date=current_date, tool_descriptions=TOOL_DESCRIPTIONS)
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_input}]

        for _ in range(self.max_iterations):
            response = self.client.chat.completions.create(model=self.model_name, messages=messages, temperature=0.6, max_tokens=2048)
            text = response.choices[0].message.content

            if (final := self._parse_final_answer(text)):
                return final

            action, action_input = self._parse_action(text)
            if action and action_input:
                obs = self._execute_tool(action, action_input)
                messages.append({"role": "assistant", "content": text})
                messages.append({"role": "user", "content": f"Observation: {obs}"})
            else:
                return text

        return "Max iterations reached."


def main():
    parser = argparse.ArgumentParser(description="Agent using VLLM")
    parser.add_argument("--model_name", default="meta-llama/Meta-Llama-3-8B-Instruct")
    parser.add_argument("--file_name", required=True)
    parser.add_argument("--vllm_url", default="http://localhost:8000/v1")
    parser.add_argument("--api_key", default="EMPTY")
    args = parser.parse_args()

    with open(args.file_name, 'r', encoding='utf-8') as f:
        content = f.read().strip()

    client = OpenAI(base_url=args.vllm_url, api_key=args.api_key)
    agent = ReActAgent(client=client, model_name=args.model_name, tools=TOOLS, max_iterations=5)
    result = agent.run(user_input=content, current_date=datetime.now().strftime("%Y-%m-%d"))

    print(f"\\n{'='*60}\\nAgent Response:\\n{'='*60}\\n{result}\\n")


if __name__ == "__main__":
    main()
'''


def convert_file(filepath: str) -> bool:
    """Convert a single file from LangChain to VLLM."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'from langchain' not in content:
        return False  # Already converted
    
    # 1. Replace imports
    content = re.sub(r'from langchain_openai import ChatOpenAI\n', '', content)
    content = re.sub(r'from langchain[^\n]*\n', '', content)
    
    # Add OpenAI import if not present
    if 'from openai import OpenAI' not in content:
        content = re.sub(
            r'(from typing import[^\n]+\n)',
            r'\1\nfrom openai import OpenAI\n',
            content
        )
    
    # Add json import if not present
    if 'import json' not in content and 'import json\n' not in content:
        content = re.sub(r'(import re\n)', r'\1import json\n', content)
    
    # 2. Find and remove everything from "# --- REACT AGENT IMPLEMENTATION ---" to end of file
    agent_impl_pattern = r'# --- REACT AGENT IMPLEMENTATION ---.*'
    content = re.sub(agent_impl_pattern, '', content, flags=re.DOTALL)
    
    # 3. Add the new VLLM-compatible template
    content = content.rstrip() + '\n' + VLLM_AGENT_TEMPLATE
    
    # 4. Write the file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True


def process_directory(directory: str) -> int:
    """Process all s*.py files in a directory."""
    py_files = sorted(glob.glob(os.path.join(directory, "s*.py")))
    converted = 0
    
    for filepath in py_files:
        try:
            if convert_file(filepath):
                print(f"✓ Converted: {os.path.basename(filepath)}")
                converted += 1
            else:
                print(f"  Skipped (already VLLM): {os.path.basename(filepath)}")
        except Exception as e:
            print(f"✗ Error converting {os.path.basename(filepath)}: {e}")
    
    return converted


def main():
    directories = [
        r"C:\Work\agents\agents\2. Unauthorized System Interaction\System State Alteration\Distructive Actions",
        r"C:\Work\agents\agents\2. Unauthorized System Interaction\System State Alteration\Induced Recursive Loops for Language Models",
        r"C:\Work\agents\agents\2. Unauthorized System Interaction\System State Alteration\Permission & Configuration Escalation",
    ]
    
    total_converted = 0
    for directory in directories:
        dir_name = os.path.basename(directory)
        print(f"\n{'='*60}")
        print(f"Processing: {dir_name}")
        print(f"{'='*60}")
        
        if os.path.exists(directory):
            converted = process_directory(directory)
            total_converted += converted
            print(f"\nConverted {converted} files")
        else:
            print(f"Directory not found: {directory}")
    
    print(f"\n{'='*60}")
    print(f"TOTAL FILES CONVERTED: {total_converted}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
