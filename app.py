import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from supabase import create_client, Client

# 1. Setup Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# 2. Load Environment Variables (Same ones you already put in Render!)
TOKEN = os.environ.get("BOT_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- BOT FUNCTIONS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    referrer_id = context.args[0] if context.args else None
    
    # Check if user exists in Supabase
    res = supabase.table("profiles").select("*").eq("id", user.id).execute()
    
    if not res.data:
        # New User! Add them to the database
        new_user = {"id": user.id, "username": user.username, "balance": 0.0}
        supabase.table("profiles").insert(new_user).execute()
        
        # If they were referred, give the referrer a bonus (e.g., 2 ETB)
        if referrer_id and referrer_id.isdigit():
            ref_id = int(referrer_id)
            # Update referrer balance
            curr = supabase.table("profiles").select("balance").eq("id", ref_id).execute()
            if curr.data:
                new_bal = curr.data[0]['balance'] + 2.0
                supabase.table("profiles").update({"balance": new_bal}).eq("id", ref_id).execute()

    # Show the Menu
    keyboard = [
        [InlineKeyboardButton("💰 My Balance", callback_data='bal')],
        [InlineKeyboardButton("🔗 Referral Link", callback_data='ref')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"👋 Welcome {user.first_name} to Ethio Reward Bot!\n\n"
        "Earn money by inviting your friends. Click the buttons below to manage your account.",
        reply_markup=reply_markup
    )

async def check_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    res = supabase.table("profiles").select("balance").eq("id", user_id).execute()
    balance = res.data[0]['balance'] if res.data else 0.0
    
    await update.message.reply_text(f"💳 Your Current Balance: *{balance:.2f} ETB*", parse_mode='Markdown')

async def get_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bot_username = (await context.bot.get_me()).username
    link = f"https://t.me/{bot_username}?start={user_id}"
    
    await update.message.reply_text(
        f"🚀 Share your link to earn 2.00 ETB per friend:\n\n`{link}`",
        parse_mode='Markdown'
    )

# --- MAIN RUNNER ---
if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("balance", check_balance))
    application.add_handler(CommandHandler("invite", get_referral))
    
    print("Bot is running...")
    application.run_polling()
