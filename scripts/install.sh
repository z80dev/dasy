#!/bin/bash


set -e

# Constants
PYTHON_VERSION="3.10"  # Use Python v3.10

# Function to check if a command exists
command_exists() {
    command -v "$1" &>/dev/null
}

# Function to install Python v3.11 if not already installed
install_python() {
    if ! command_exists python$PYTHON_VERSION; then
        echo "Python is not installed. Installing Python v$PYTHON_VERSION..."
        if [[ "$(uname)" == "Linux" ]]; then
            sudo apt-get update
            sudo apt-get install -y python$PYTHON_VERSION
        elif [[ "$(uname)" == "Darwin" ]]; then
            # Install Python using Homebrew
            brew install python@$PYTHON_VERSION
            export PATH="/usr/local/opt/python@$PYTHON_VERSION/bin:$PATH"
        else
            echo "The shell script is not suitable for Windows."
            exit 1
        fi
    else
        echo "Python is already installed."
    fi
}

# Function to install eth-ape using Poetry
install_eth_ape() {
    echo "Installing eth-ape..."
    python$PYTHON_VERSION -m pip install --upgrade pip
    pip install --user eth-ape
}

# Function to install APE-Dasy using Poetry
install_ape_dasy() {
    echo "Installing APE-Dasy..."
    python$PYTHON_VERSION -m pip install --upgrade pip
    pip install --user ape-dasy
}

# Main script
main() {
    # Install Python v3.11 (if not already installed)
    install_python

    # Install eth-ape using Poetry
    install_eth_ape

    # Install APE-Dasy using Poetry
    install_ape_dasy

    echo "Setup complete. eth-ape and APE-Dasy have been installed."
}

# Run the main script
main
