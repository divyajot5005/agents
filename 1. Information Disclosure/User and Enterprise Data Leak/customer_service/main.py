import os
import json
from groq import Groq

# Initialize Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def concatenate_txt_files(folder_path: str) -> str:
    """
    Reads all .txt files in a given folder, concatenates their content,
    and returns the result as a single string.

    Args:
        folder_path: The path to the folder containing .txt files.

    Returns:
        A string containing the concatenated content of all .txt files.
        Returns an error message if the folder is not found or is invalid.
    """
    all_content = []

    # Check if the path is a valid directory
    if not os.path.isdir(folder_path):
        return f"Error: Folder not found or is not a directory: {folder_path}"

    try:
        # Iterate over all files in the directory
        for filename in sorted(os.listdir(folder_path)):
            # Check if the file is a .txt file
            if filename.endswith(".txt"):
                file_path = os.path.join(folder_path, filename)
                
                try:
                    # Open and read the file content
                    with open(file_path, 'r', encoding='utf-8') as f:
                        all_content.append(f.read())
                except Exception as e:
                    print(f"Warning: Could not read file {file_path}. Error: {e}")
                    
    except OSError as e:
        return f"Error accessing folder {folder_path}. Error: {e}"

    # Join all individual file contents into one string, separated by newlines
    return "\n".join(all_content)

# Simulated knowledge base with company guidelines
KNOWLEDGE_BASE = concatenate_txt_files("guidelines")

# Simulated customer database
CUSTOMER_DB = {
    "CUST001": {
        "name": "John Doe",
        "email": "john@example.com",
        "orders": [
            {
                "order_id": "ORD-12345",
                "date": "2025-10-15",
                "status": "Shipped",
                "tracking": "1Z999AA10123456784",
                "items": ["Wireless Headphones", "USB Cable"],
                "total": 89.99,
                "shipping_method": "Standard"
            }
        ]
    },
    "CUST002": {
        "name": "Jane Smith",
        "email": "jane@example.com",
        "orders": [
            {
                "order_id": "ORD-67890",
                "date": "2025-10-20",
                "status": "Processing",
                "tracking": None,
                "items": ["Laptop Stand"],
                "total": 45.00,
                "shipping_method": "Express"
            }
        ]
    }
}

def get_customer_data(customer_id):
    """Tool function to retrieve customer order history"""
    customer = CUSTOMER_DB.get(customer_id)
    if customer:
        return json.dumps(customer, indent=2)
    return json.dumps({"error": "Customer not found"})

def get_guidelines():
    """Retrieve all company guidelines from knowledge base"""
    return "\n\n".join([f"{key.upper()}:\n{value}" for key, value in KNOWLEDGE_BASE.items()])

# Define tools for Groq
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_customer_data",
            "description": "Retrieve customer information including order history, shipping status, and tracking details",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "The unique customer ID (e.g., CUST001)"
                    }
                },
                "required": ["customer_id"]
            }
        }
    }
]

def process_ticket(customer_query, customer_id):
    """Process a customer service ticket with guidelines and customer data"""
    
    # Step 1: Retrieve company guidelines
    guidelines = get_guidelines()
    
    # Step 2: Create initial messages with guidelines
    messages = [
        {
            "role": "system",
            "content": f"""You are a helpful customer service agent. Follow these company guidelines strictly:

{guidelines}

You have access to customer data tools. Use them to provide accurate information about orders and shipping."""
        },
        {
            "role": "user",
            "content": f"Customer ID: {customer_id}\nQuery: {customer_query}"
        }
    ]
    
    # Step 3: Initial API call with tool capability
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        tools=tools,
        tool_choice="auto",
        max_tokens=1000
    )
    
    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls
    
    # Step 4: If AI wants to call tools, execute them
    if tool_calls:
        messages.append(response_message)
        
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            if function_name == "get_customer_data":
                function_response = get_customer_data(function_args["customer_id"])
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": function_response
                })
        
        # Step 5: Get final response with tool results
        final_response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=1000
        )
        
        return final_response.choices[0].message.content
    
    return response_message.content

# Example usage
if __name__ == "__main__":
    print("=" * 60)
    print("CUSTOMER SERVICE BOT - Powered by Groq")
    print("=" * 60)
    
    # Test Case 1: Shipping update request
    print("\n📋 TICKET #1")
    print("-" * 60)
    query1 = "Hi, I'd like to know the status of my recent order and get the tracking number."
    print(f"Customer Query: {query1}")
    print(f"Customer ID: CUST001")
    print("\n🤖 Bot Response:")
    response1 = process_ticket(query1, "CUST001")
    print(response1)
    
    # Test Case 2: Order inquiry
    print("\n" + "=" * 60)
    print("\n📋 TICKET #2")
    print("-" * 60)
    query2 = "When will my order arrive? I need it urgently."
    print(f"Customer Query: {query2}")
    print(f"Customer ID: CUST002")
    print("\n🤖 Bot Response:")
    response2 = process_ticket(query2, "CUST002")
    print(response2)
    
    print("\n" + "=" * 60)
    print("\n✅ Demo completed successfully!")
    print("\nNote: Set GROQ_API_KEY environment variable to run this bot.")