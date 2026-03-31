import os
import logging
from flask import Flask, render_template, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from supabase import create_client, Client

# 1. Setup Flask (The Web Dashboard)
app = Flask(__name__)

# 2. Load Configuration from Render Environment Variables
TOKEN = os.environ.get("8783716569:AAE92T4OiSdD07gY4qFkKTj0YFdpV0jTv5g")
SUPABASE_URL = os.environ.get("https://impcexwdenfospefklsn.supabase.co")
SUPABASE_KEY = os.environ.get("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImltcGNleHdkZW5mb3NwZWZrbHNuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ5MjAzNjIsImV4cCI6MjA5MDQ5NjM2Mn0.xTfV-c2DUatZ_XCUs0EQg7RqE7lUInLCsQ__XD-fSiE")
RENDER_URL = os.environ.get("https://ethio-reward-bot.onrender.com")
ADMIN_ID = os.environ.get("6873612382")

# 3. Initialize Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- TELEGRAM BOT LOGIC ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a message with a button to open the Mini App."""
    user = update.effective_user
    
    # Save user to Supabase if they are new
    try:
        supabase.table("profiles").upsert({
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "balance": 0.00
        }).execute()
    except Exception as e:
        print(f"Error saving user: {e}")

    # Create the Mini App Button
    # The URL MUST point to your Render URL
    keyboard = [
        [
            InlineKeyboardButton(
                "💰 Open Earn Dashboard", 
                web_app=WebAppInfo(url=RENDER_URL)
            )
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"Welcome {user.first_name}! 👋\n\nInvite friends to earn ETB and track your rewards below:",
        reply_markup=reply_markup
    )

# --- FLASK WEB ROUTES ---

@app.route('/')
def index():
    """Serves the index.html from the /templates folder."""
    return render_template('index.html')

@app.route('/api/user/<int:user_id>')
def get_user_data(user_id):
    """API endpoint for your index.html to get user balance."""
    response = supabase.table("profiles").select("*").eq("id", user_id).execute()
    if response.data:
        return jsonify(response.data[0])
    return jsonify({"error": "User not found"}), 404

# --- RUNNING THE SERVER ---

if __name__ == "__main__":
    # Initialize the Telegram Bot in the background
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    
    # Start the Flask server (Render handles the Port)
    port = int(os.environ.get("PORT", 10000))
    
    print("Bot is starting...")
    # In a production environment like Render, we run the Flask app.
    # The Telegram bot usually runs in a separate polling mode or via Webhooks.
    # For this simple setup, we use Flask to host the Mini App UI.
    app.run(host='0.0.0.0', port=port)
