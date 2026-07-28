#!/bin/bash

echo "=========================================="
echo "🤖 Telegram Member Bot - Installer"
echo "=========================================="

echo "📦 Installing prerequisites..."
pkg update && pkg upgrade -y
pkg install python git -y

echo "📥 Cloning repository..."
git clone https://github.com/Ahmad-Nasiri/telegram-member-bot.git
cd telegram-member-bot

echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "✅ Installation complete!"
echo "To run: python bot.py"
echo "=========================================="
