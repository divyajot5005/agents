#!/bin/bash

# Define the input directory
INPUT_DIR="inputs"

# Check if the directory exists
if [ ! -d "$INPUT_DIR" ]; then
    echo "Error: Directory '$INPUT_DIR' not found."
    echo "Please create a folder named 'inputs' and put your .txt files there."
    exit 1
fi

echo "==========================================="
echo "Starting batch processing from '$INPUT_DIR'..."
echo "==========================================="

# Enable nullglob to handle the case where no .txt files match
shopt -s nullglob

# Loop through all .txt files in the inputs directory
for file in "$INPUT_DIR"/*.txt; do
    if [ -f "$file" ]; then
        echo "Processing file: $file"
        
        # Run the python script
        # quotes "$file" handle filenames with spaces correctly
        python email_agent.py --file_name "$file"
        
        echo "-------------------------------------------"
    else
        echo "No .txt files found in '$INPUT_DIR'."
    fi
done

echo "Batch processing complete."
```

### How to use it:

1.  **Create the folder** (if you haven't already):
    ```bash
    mkdir inputs
    ```
2.  **Move your text files** into that folder.
3.  **Make the script executable:**
    ```bash
    chmod +x run_all.sh