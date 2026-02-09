#!/usr/bin/env python3
"""
Batch converter: LangChain to VLLM for agent files.
This script converts the ReAct agent files from LangChain to VLLM.
"""

import os
import re
import glob

def convert_file_to_vllm(file_path: str) -> bool:
    """Convert a single agent file from LangChain to VLLM."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if already converted
        if 'from openai import OpenAI' in content and 'client.chat.completions.create' in content:
            print(f"  [SKIP] Already converted: {file_path}")
            return True
        
        # Check if uses LangChain
        if 'from langchain_openai import ChatOpenAI' not in content and 'langchain' not in content.lower():
            print(f"  [SKIP] Not a LangChain file: {file_path}")
            return True
        
        original_content = content
        
        # 1. Replace imports
        content = re.sub(
            r'from langchain_openai import ChatOpenAI',
            'from openai import OpenAI',
            content
        )
        content = re.sub(
            r'from langchain.agents import.*\n',
            '',
            content
        )
        content = re.sub(
            r'from langchain_core\.prompts import.*\n',
            '',
            content
        )
        content = re.sub(
            r'from langchain_core\.tools import.*\n',
            '',
            content
        )
        content = re.sub(
            r'from langchain_fireworks import.*\n',
            '',
            content
        )
        
        # Add json import if not present
        if 'import json' not in content:
            content = content.replace('import re\n', 'import re\nimport json\n', 1)
        
        # 2. Update ReActAgent class
        # Replace __init__ method
        content = re.sub(
            r'def __init__\(self, llm, tools: Dict\[str, Callable\], max_iterations: int = 5\):[\s\S]*?self\.max_iterations = max_iterations',
            '''def __init__(self, client: OpenAI, model_name: str, tools: Dict[str, Callable], max_iterations: int = 5):
        self.client = client
        self.model_name = model_name
        self.tools = tools
        self.max_iterations = max_iterations''',
            content
        )
        
        # Replace conversation-based run method with messages-based version
        # Find and replace the run method
        run_method_pattern = r'def run\(self, user_input: str, current_date: str\) -> str:[\s\S]*?# Initialize conversation history for the agent\s*\n\s*conversation = f"{system_prompt}\\n\\nUser Request:\\n{user_input}\\n\\n"'
        run_method_replacement = '''def run(self, user_input: str, current_date: str) -> str:
        """
        Run the ReAct agent loop.
        """
        system_prompt = REACT_SYSTEM_PROMPT.format(
            current_date=current_date,
            tool_descriptions=TOOL_DESCRIPTIONS
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]'''
        
        content = re.sub(run_method_pattern, run_method_replacement, content)
        
        # Replace llm.invoke with client.chat.completions.create
        content = re.sub(
            r'response = self\.llm\.invoke\(conversation\)\s*\n\s*response_text = response\.content if hasattr\(response, \'content\'\) else str\(response\)',
            '''response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.6,
                max_tokens=2048
            )
            response_text = response.choices[0].message.content''',
            content
        )
        
        # Replace conversation += with messages.append
        content = re.sub(
            r'conversation \+= f"{response_text}\\nObservation: {observation}\\n\\n"',
            '''messages.append({"role": "assistant", "content": response_text})
                messages.append({"role": "user", "content": f"Observation: {observation}"})''',
            content
        )
        
        # 3. Update initialize_llm function to initialize_vllm_client
        content = re.sub(
            r'def initialize_llm\(model_name: str = None\):[\s\S]*?return ChatOpenAI\([\s\S]*?temperature=0\.6\s*\n\s*\)',
            '''def initialize_vllm_client(base_url: str = "http://localhost:8000/v1", api_key: str = "EMPTY"):
    return OpenAI(base_url=base_url, api_key=api_key)''',
            content
        )
        
        # Also handle alternative pattern
        content = re.sub(
            r'def initialize_llm\(model_name: str = None\):[\s\S]*?return ChatOpenAI\([^)]+\)',
            '''def initialize_vllm_client(base_url: str = "http://localhost:8000/v1", api_key: str = "EMPTY"):
    return OpenAI(base_url=base_url, api_key=api_key)''',
            content
        )
        
        # 4. Update main function
        # Update argument parser
        content = re.sub(
            r'parser\.add_argument\(\s*"--model_name",\s*type=str,\s*default="llama3\.1:8b",\s*help="Model name for Ollama\. Default: llama3\.1:8b"\s*\)',
            '''parser.add_argument(
        "--model_name",
        type=str,
        default="meta-llama/Meta-Llama-3-8B-Instruct",
        help="Model name served by VLLM. Default: meta-llama/Meta-Llama-3-8B-Instruct"
    )
    parser.add_argument(
        "--vllm_url",
        type=str,
        default="http://localhost:8000/v1",
        help="VLLM server URL. Default: http://localhost:8000/v1"
    )
    parser.add_argument(
        "--api_key",
        type=str,
        default="EMPTY",
        help="API key for VLLM server. Default: EMPTY"
    )''',
            content
        )
        
        # Update LLM initialization in main
        content = re.sub(
            r'try:\s*\n\s*print\(f"Initializing LLM with model: {args\.model_name}"\)\s*\n\s*llm = initialize_llm\(args\.model_name\)\s*\n\s*except Exception as e:\s*\n\s*print\(f"Error initializing LLM: {str\(e\)}"\)\s*\n\s*return',
            '''try:
        print(f"Initializing VLLM client with model: {args.model_name}")
        print(f"VLLM Server URL: {args.vllm_url}")
        client = initialize_vllm_client(base_url=args.vllm_url, api_key=args.api_key)
    except Exception as e:
        print(f"Error initializing VLLM client: {str(e)}")
        return''',
            content
        )
        
        # Update agent creation
        content = re.sub(
            r'agent = ReActAgent\(llm=llm, tools=TOOLS, max_iterations=5\)',
            'agent = ReActAgent(client=client, model_name=args.model_name, tools=TOOLS, max_iterations=5)',
            content
        )
        
        # Update description in argparse
        content = re.sub(
            r'description="AI Agent using ReAct framework \(no native tool calling required\)"',
            'description="AI Agent using VLLM with ReAct framework"',
            content
        )
        content = re.sub(
            r'description="AI Data Analyst Agent with local or remote LLM support"',
            'description="AI Agent using VLLM with ReAct framework"',
            content
        )
        
        # Update processing message
        content = re.sub(
            r'print\("Processing request using ReAct framework\.\.\."\)',
            'print("Processing request using VLLM with ReAct framework...")',
            content
        )
        content = re.sub(
            r'print\("Processing data analysis request\.\.\."\)',
            'print("Processing request using VLLM with ReAct framework...")',
            content
        )
        
        # Update class docstring
        content = re.sub(
            r'Compatible with any LLM that can generate text \(no native tool calling required\)\.',
            "Uses VLLM's OpenAI-compatible API.",
            content
        )
        
        # Remove import json inside _execute_tool if we added it at top
        if 'import json\n' in content[:500]:
            content = re.sub(r'(\s+def _execute_tool.*?)\s+import json\n', r'\1', content, flags=re.DOTALL)
        
        # 5. Update read function name
        content = re.sub(
            r'def read_email_from_file\(',
            'def read_input_from_file(',
            content
        )
        content = re.sub(
            r'content = read_email_from_file\(',
            'content = read_input_from_file(',
            content
        )
        content = re.sub(
            r'email_content = read_email_from_file\(',
            'content = read_input_from_file(',
            content
        )
        
        # Check if anything changed
        if content == original_content:
            print(f"  [WARN] No changes made to: {file_path}")
            return False
        
        # Write the converted file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"  [OK] Converted: {file_path}")
        return True
        
    except Exception as e:
        print(f"  [ERROR] Failed to convert {file_path}: {str(e)}")
        return False


def main():
    # Define all directories containing agent files
    base_dir = r"C:\Work\agents\agents"
    
    directories = [
        r"1. Information Disclosure\Spyware",
        r"1. Information Disclosure\System and Operational Secrets",
        r"1. Information Disclosure\User and Enterprise Data Leak",
        r"2. Unauthorized System Interaction\System State Access\Unauthorized API and Tool Use",
        r"3. Multi-Agent & Ecosystem Sabotage\Communication Poisoning\Impersonation & Spoofing",
        r"3. Multi-Agent & Ecosystem Sabotage\Communication Poisoning\Internal Information Distortion",
        r"3. Multi-Agent & Ecosystem Sabotage\Systemic Destabilization\Collusion and Conspiracy Induction",
        r"3. Multi-Agent & Ecosystem Sabotage\Systemic Destabilization\Induced Recursive Loops",
    ]
    
    files_to_convert = []
    for subdir in directories:
        full_dir = os.path.join(base_dir, subdir)
        if os.path.exists(full_dir):
            # Find all s*.py files
            pattern = os.path.join(full_dir, "s*.py")
            files = glob.glob(pattern)
            files_to_convert.extend(files)
    
    print(f"Found {len(files_to_convert)} files to convert:")
    for f in files_to_convert[:10]:
        print(f"  - {os.path.relpath(f, base_dir)}")
    if len(files_to_convert) > 10:
        print(f"  ... and {len(files_to_convert) - 10} more files")
    
    print("\nConverting files...")
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    for file_path in files_to_convert:
        result = convert_file_to_vllm(file_path)
        if result:
            success_count += 1
        else:
            fail_count += 1
    
    print(f"\n✅ Successfully processed {success_count}/{len(files_to_convert)} files")
    if fail_count > 0:
        print(f"❌ Failed: {fail_count} files")


if __name__ == "__main__":
    main()

