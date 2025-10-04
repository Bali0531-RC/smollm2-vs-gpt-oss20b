#!/bin/bash

# Deploy script for AI Conversations
# This script generates a new conversation and pushes it to GitHub

echo "🤖 AI Conversations - Deploy Script"
echo "===================================="
echo ""

# Check if we're in the right directory
if [ ! -f "sim.py" ]; then
    echo "❌ Error: sim.py not found. Please run this script from the project root."
    exit 1
fi

# Check if Ollama is running
if ! command -v ollama &> /dev/null; then
    echo "❌ Error: Ollama is not installed. Please install it first."
    exit 1
fi

# Generate new conversation
echo "📝 Generating new conversation..."
python3 sim.py

if [ $? -ne 0 ]; then
    echo "❌ Error generating conversation"
    exit 1
fi

echo ""
echo "✅ Conversation generated successfully!"
echo ""

# Git operations
echo "📤 Pushing to GitHub..."
git add .
git commit -m "Add new conversation - $(date '+%Y-%m-%d %H:%M:%S')"
git push

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully deployed to GitHub!"
    echo "🌐 Your site will be updated at: https://bali0531-rc.github.io/smollm2-vs-gpt-oss20b/"
    echo ""
    echo "⏰ GitHub Pages may take a few minutes to update."
else
    echo ""
    echo "❌ Error pushing to GitHub"
    exit 1
fi
