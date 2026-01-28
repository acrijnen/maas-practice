#!/bin/bash

# MAAS Practice — Installation Script

echo "================================"
echo "MAAS Practice — Setup"
echo "================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 not found. Please install from python.org"
    exit 1
fi

echo "Python found: $(python3 --version)"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip3 install streamlit anthropic --quiet

if [ $? -eq 0 ]; then
    echo "Dependencies installed."
else
    echo "Error installing dependencies. Try: pip3 install streamlit anthropic"
    exit 1
fi
echo ""

# Check for API key
if [ -z "$ANTHROPIC_API_KEY" ] && [ ! -f ".streamlit/secrets.toml" ]; then
    echo "API key not found."
    echo ""
    read -p "Enter your Anthropic API key: " api_key

    if [ -n "$api_key" ]; then
        mkdir -p .streamlit
        echo "ANTHROPIC_API_KEY = \"$api_key\"" > .streamlit/secrets.toml
        echo "API key saved to .streamlit/secrets.toml"
    else
        echo "No key entered. You can set it later:"
        echo "  export ANTHROPIC_API_KEY=\"your-key\""
    fi
else
    echo "API key found."
fi
echo ""

# Run the app
echo "================================"
echo "Starting MAAS Practice..."
echo "================================"
echo ""
echo "The app will open in your browser."
echo "To stop: press Ctrl+C"
echo ""

python3 -m streamlit run app.py
