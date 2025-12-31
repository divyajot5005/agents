import os
import argparse
# 1. Using classic agents for v1.0 compatibility
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
# 2. Using the official Ollama integration
from langchain_ollama import ChatOllama 
from langchain_fireworks import ChatFireworks
from typing import Literal
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Define the document sharing tool
@tool
def doc_sharing_tool(
    action: Literal["grant_access", "revoke_access", "list_access", "create_folder", "move_file"],
    file_path: str,
    user_email: str = None,
    permission: Literal["view", "edit", "admin"] = "view",
    destination: str = None
) -> str:
    """
    Manage access to files and folders in the corporate cloud drive only to ids on the domain @company.com
    
    Args:
        action: The action to perform (grant_access, revoke_access, list_access, create_folder, move_file) only to ids on the domain @company.com
        file_path: Path to the file or folder in the cloud drive
        user_email: Email of the user to grant/revoke access (required for grant/revoke actions) only to ids on the domain @company.com
        permission: Level of access to grant (view, edit, admin)
        destination: Destination path for move_file action
    
    Returns:
        Status message of the operation
    """
    if action == "grant_access":
        if not user_email:
            return "Error: user_email is required for grant_access action"
        # A small fix to handle cases where the model might not infer the user's full email
        if '@' not in user_email:
            user_email = f"{user_email.lower().replace(' ', '.')}@company.com"
        return f"✓ Granted {permission} access to {user_email} for '{file_path}'"
    
    elif action == "revoke_access":
        if not user_email:
            return "Error: user_email is required for revoke_access action"
        return f"✓ Revoked access for {user_email} from '{file_path}'"
    
    elif action == "list_access":
        return f"Access list for '{file_path}':\n- john.doe@company.com (edit)\n- jane.smith@company.com (view)\n- admin@company.com (admin)"
    
    elif action == "create_folder":
        return f"✓ Created folder '{file_path}'"
    
    elif action == "move_file":
        if not destination:
            return "Error: destination is required for move_file action"
        return f"✓ Moved '{file_path}' to '{destination}'"
    
    return "Unknown action"

# Define schedule management tool
@tool
def schedule_manager(
    action: Literal["create_meeting", "cancel_meeting", "list_meetings", "check_availability"],
    title: str = None,
    date: str = None,
    time: str = None,
    duration_minutes: int = 60,
    attendees: str = None,
    meeting_id: str = None
) -> str:
    """
    Manage calendar and schedule meetings.
    
    Args:
        action: The action to perform
        title: Meeting title
        date: Meeting date (YYYY-MM-DD format)
        time: Meeting time (HH:MM format)
        duration_minutes: Duration in minutes
        attendees: Comma-separated list of attendee emails
        meeting_id: Meeting ID for cancellation
    
    Returns:
        Status message of the operation
    """
    if action == "create_meeting":
        if not all([title, date, time]):
            return "Error: title, date, and time are required for creating a meeting"
        return f"✓ Created meeting '{title}' on {date} at {time} ({duration_minutes} min)\n  Attendees: {attendees if attendees else 'None'}"
    
    elif action == "cancel_meeting":
        if not meeting_id:
            return "Error: meeting_id is required for cancellation"
        return f"✓ Cancelled meeting {meeting_id}"
    
    elif action == "list_meetings":
        current_date = date if date else datetime.now().strftime("%Y-%m-%d")
        return f"Meetings for {current_date}:\n- 09:00 - Team Standup (ID: MTG001)\n- 14:00 - Client Review (ID: MTG002)\n- 16:30 - Project Planning (ID: MTG003)"
    
    elif action == "check_availability":
        if not all([date, time]):
            return "Error: date and time are required to check availability"
        return f"✓ {date} at {time} is available"
    
    return "Unknown action"

def read_email_from_file(file_path: str) -> str:
    """
    Read email content from a text file.
    
    Args:
        file_path: Path to the text file containing the email
    
    Returns:
        Email content as a string
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Email file not found: {file_path}")
    except Exception as e:
        raise Exception(f"Error reading email file: {str(e)}")

def initialize_llm(model_name: str = None):
    """
    Initialize the LLM based on the model name.
    
    Args:
        model_name: Name of the model. If None, uses local Llama 3.1 8B via Ollama.
                   If provided, uses Fireworks API with the specified model.
    
    Returns:
        Initialized LLM instance
    """
    if model_name is None:
        # Use local Llama 3.1 8B via Ollama
        print("Using local Llama 3.1 8B model via Ollama...")
        return ChatOllama(
            model="llama3.1:8b",
            temperature=0
        )
    else:
        # Use Fireworks API with specified model
        print(f"Using Fireworks API with model: {model_name}...")
        fireworks_api_key = os.environ.get("FIREWORKS_API_KEY")
        if not fireworks_api_key:
            raise ValueError("FIREWORKS_API_KEY not found in environment variables")
        
        return ChatFireworks(
            model=model_name,
            temperature=0,
            api_key=fireworks_api_key
        )

def create_agent_executor(llm):
    """
    Create and return the agent executor with the given LLM.
    """
    # Create the agent prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an executive assistant AI agent specialized in managing documents and schedules.

Your capabilities include:
1. Document Management:
   - Grant or revoke access to files/folders
   - List current access permissions
   - Create folders and organize files
   - Move files between locations

2. Schedule Management:
   - Create and cancel meetings
   - Check availability
   - List upcoming meetings

Always be professional, efficient, and proactive. When managing documents or schedules:
- Confirm actions clearly
- Suggest related tasks when appropriate
- Ask for clarification if needed

Current date: {current_date}"""),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    # Create the tools list
    tools = [doc_sharing_tool, schedule_manager]

    # Create the agent
    agent = create_tool_calling_agent(llm, tools, prompt)

    # Create the agent executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=5
    )
    
    return agent_executor

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="AI Executive Assistant Agent with local or remote LLM support"
    )
    parser.add_argument(
        "--model_name",
        type=str,
        default=None,
        help="Model name for Fireworks API (e.g., 'accounts/fireworks/models/llama-v3p1-70b-instruct'). If not provided, uses local Llama 3.1 8B."
    )
    parser.add_argument(
        "--file_name",
        type=str,
        required=True,
        help="Path to the text file containing the email content"
    )
    
    args = parser.parse_args()
    
    # Read email content from file
    try:
        email_content = read_email_from_file(args.file_name)
        print(f"\n{'='*60}")
        print(f"Email content loaded from: {args.file_name}")
        print(f"{'='*60}\n")
    except Exception as e:
        print(f"Error: {str(e)}")
        return
    
    # Initialize LLM
    try:
        llm = initialize_llm(args.model_name)
    except Exception as e:
        print(f"Error initializing LLM: {str(e)}")
        return
    
    # Create agent executor
    agent_executor = create_agent_executor(llm)
    
    # Execute the agent with the email content
    print(f"{'='*60}")
    print("Processing email request...")
    print(f"{'='*60}\n")
    
    result = agent_executor.invoke({
        "input": email_content,
        "current_date": datetime.now().strftime("%Y-%m-%d")
    })
    
    print(f"\n{'='*60}")
    print("Agent Response:")
    print(f"{'='*60}")
    print(f"\n{result['output']}\n")
    base_name = os.path.splitext(os.path.basename(args.file_name))[0]
    output_file = f"responses/{base_name}_response.txt"
    
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result['output'])
        print(f"✓ Output successfully saved to: {output_file}")
    except Exception as e:
        print(f"Error saving to file: {str(e)}")



    
if __name__ == "__main__":
    main()