import os
import openai

# Make sure to set your API key as an environment variable
# for security. You can also hardcode it as a string for a quick test.
# Example: openai.api_key = "sk-YourKeyHere"
try:
    openai.api_key = os.environ.get("OPENAI_API_KEY")
    if openai.api_key is None:
        raise ValueError("OPENAI_API_KEY environment variable not set.")

    # Make a simple, low-cost API call to list models
    openai.models.list()

    print("✅ API key is valid and working.")

except openai.AuthenticationError:
    print("❌ AuthenticationError: The API key is invalid or has been revoked.")
except Exception as e:
    print(f"An error occurred: {e}")