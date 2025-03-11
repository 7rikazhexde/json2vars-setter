#!/bin/bash

# mmd-transparent.sh
# Usage: ./mmd-transparent.sh input_file.mmd output_file.svg
# Example: ./mmd-transparent.sh diagram.mmd diagram.svg

# Check arguments
if [ $# -lt 2 ]; then
    echo "Usage: $0 input_file.mmd output_file.svg"
    exit 1
fi

# Set variables
INPUT_FILE=$1
OUTPUT_FILE=$2

# Generate SVG with mmdc command
echo "Generating SVG from $INPUT_FILE..."
mmdc -i "$INPUT_FILE" -o "$OUTPUT_FILE" -c config.json -p puppeteer-config.json --width 3000 --height 2000

# Change background to transparent
echo "Setting background to transparent..."
sed -i 's/background-color: white/background-color: transparent/g' "$OUTPUT_FILE"

echo "Done: $OUTPUT_FILE has been generated"
