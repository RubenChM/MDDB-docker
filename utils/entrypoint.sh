#!/bin/bash

set -e

# Function to list available scripts
list_scripts() {
    echo "📋 Available Python scripts:"
    echo "================================"
    for script in /app/scripts/*.py; do
        if [ -f "$script" ]; then
            basename "$script"
        fi
    done
    echo "================================"
}

# Function to run a specific script
run_script() {
    local script_name="$1"
    shift
    local script_path="/app/scripts/${script_name}"
    
    if [ ! -f "$script_path" ]; then
        echo "❌ Script ${script_name} not found!"
        list_scripts
        exit 1
    fi
    
    echo "🚀 Running ${script_name}..."
    python3 "$script_path" "$@"
}

# Main logic for one-off execution
case "$1" in
    "list")
        list_scripts
        ;;
    "run")
        if [ $# -lt 2 ]; then
            echo "❌ Usage: docker run mddb-scripts run <script.py> [arguments]"
            list_scripts
            exit 1
        fi
        run_script "$2" "${@:3}"
        ;;
    "shell")
        exec /bin/bash
        ;;
    "help"|"")
        echo "🔧 MDDB Python Scripts Container (One-off execution)"
        echo ""
        echo "Usage:"
        echo "  docker run --rm mddb-scripts list"
        echo "  docker run --rm mddb-scripts run <script.py> [args]"
        echo "  docker run --rm -it mddb-scripts shell"
        echo ""
        echo "Examples:"
        echo "  docker run --rm mddb-scripts run update.py"
        echo "  docker run --rm mddb-scripts run rebuild.py -s client -t mystack"
        echo ""
        list_scripts
        ;;
    *)
        # Direct script execution - if first argument ends with .py
        if [[ "$1" == *.py ]]; then
            run_script "$@"
        else
            echo "❌ Unknown command: $1"
            echo "Use 'help' to see available commands"
            exit 1
        fi
        ;;
esac