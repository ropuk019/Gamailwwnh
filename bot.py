import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters
from database import Database
from config import TOKEN, ADMIN_ID, ADMIN_USERNAME

# Initialize database
db = Database('gmail_bot.db')

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Main menu keyboard
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("Message", callback_data='message')],
        [InlineKeyboardButton("Register a new Gmail", callback_data='register_gmail')],
        [InlineKeyboardButton("My accounts", callback_data='my_accounts')],
        [InlineKeyboardButton("Balance", callback_data='balance')],
        [InlineKeyboardButton("My referrals", callback_data='referrals')],
        [InlineKeyboardButton("Withdraw", callback_data='withdraw')],
        [InlineKeyboardButton("Settings", callback_data='settings')],
        [InlineKeyboardButton("Help", callback_data='help')]
    ]
    return InlineKeyboardMarkup(keyboard)

# Start command
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Check if user exists in database
    if not db.user_exists(user.id):
        # Check if user was referred
        if context.args:
            referrer_id = int(context.args[0])
            if db.user_exists(referrer_id):
                db.add_user(user.id, user.username, referrer_id)
                # Add referral bonus to referrer
                db.update_balance(referrer_id, 0.05 * 0.05)  # 5% of $0.05
                update.message.reply_text(f"You were referred by @{db.get_username(referrer_id)}! You both earn 5% bonus.")
            else:
                db.add_user(user.id, user.username)
        else:
            db.add_user(user.id, user.username)
    
    update.message.reply_text(
        "Welcome to the Gmail Selling Bot!\n\n"
        "Here you can sell your Gmail accounts and earn money.\n"
        "1 Gmail = $0.05\n"
        "Minimum withdrawal: $1 (110 TK)\n"
        "Referral bonus: 5% of your referrals' earnings\n\n"
        "Select an action from the menu below:",
        reply_markup=main_menu_keyboard()
    )

# Button handler
def button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    
    if query.data == 'message':
        query.edit_message_text(
            text="Send us a message and we'll reply as soon as possible.",
            reply_markup=main_menu_keyboard()
        )
    
    elif query.data == 'register_gmail':
        query.edit_message_text(
            text="Please send the Gmail account details in the following format:\n\n"
                 "Email: example@gmail.com\n"
                 "Password: yourpassword\n"
                 "Recovery Email: recovery@email.com\n\n"
                 "After submission, the Gmail will be pending review.\n"
                 "You'll be notified when it's approved and $0.05 added to your balance.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data='back')]])
        )
        context.user_data['waiting_for_gmail'] = True
    
    elif query.data == 'my_accounts':
        accounts = db.get_user_gmails(user_id)
        if accounts:
            text = "Your registered Gmail accounts:\n\n"
            for account in accounts:
                text += f"Email: {account[1]}\nPassword: {account[2]}\nRecovery: {account[3]}\n\n"
        else:
            text = "You haven't registered any Gmail accounts yet."
        query.edit_message_text(
            text=text,
            reply_markup=main_menu_keyboard()
        )
    
    elif query.data == 'balance':
        balance = db.get_balance(user_id)
        pending_balance = db.get_pending_balance(user_id)
        referrals = db.get_referral_count(user_id)
        query.edit_message_text(
            text=f"Your current balance: ${balance:.2f}\n"
                 f"Pending approval: ${pending_balance:.2f}\n"
                 f"Equivalent to: {int(balance * 110)} TK\n\n"
                 f"Total referrals: {referrals}\n"
                 f"Referral earnings: ${db.get_referral_earnings(user_id):.2f}\n\n"
                 f"Minimum withdrawal: $1 (110 TK)",
            reply_markup=main_menu_keyboard()
        )
    
    elif query.data == 'referrals':
        referrals = db.get_referrals(user_id)
        if referrals:
            text = "Your referrals:\n\n"
            for ref in referrals:
                text += f"@{ref[1]} - ${ref[2]:.2f} earned for you\n"
        else:
            text = "You don't have any referrals yet.\n\n" \
                   "Share your referral link to earn 5% of your referrals' earnings:\n" \
                   f"https://t.me/{context.bot.username}?start={user_id}"
        query.edit_message_text(
            text=text,
            reply_markup=main_menu_keyboard()
        )
    
    elif query.data == 'withdraw':
        balance = db.get_balance(user_id)
        if balance < 1:
            query.edit_message_text(
                text=f"Minimum withdrawal amount is $1 (110 TK).\n"
                     f"Your current balance: ${balance:.2f}\n\n"
                     "Keep selling Gmail accounts to reach the minimum.",
                reply_markup=main_menu_keyboard()
            )
        else:
            query.edit_message_text(
                text=f"Your balance: ${balance:.2f} ({int(balance * 110)} TK)\n\n"
                     "Please send your bKash/Rocket/Nagad number in the following format:\n\n"
                     "Number: 01XXXXXXXXX\n"
                     "Amount: $XX.XX",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data='back')]])
            )
            context.user_data['waiting_for_withdrawal'] = True
    
    elif query.data == 'settings':
        query.edit_message_text(
            text="Settings:\n\n"
                 "1. Change payment method\n"
                 "2. Notification preferences\n"
                 "3. Account information",
            reply_markup=main_menu_keyboard()
        )
    
    elif query.data == 'help':
        query.edit_message_text(
            text="Help Center\n\n"
                 "1. How to sell Gmail accounts?\n"
                 "   - Use the 'Register a new Gmail' option\n"
                 "   - Provide valid account details\n"
                 "   - Earn $0.05 per verified account\n\n"
                 "2. How to withdraw?\n"
                 "   - Minimum $1 (110 TK)\n"
                 "   - Provide your mobile money number\n\n"
                 "3. Referral program\n"
                 "   - Earn 5% of your referrals' earnings\n"
                 "   - Share your referral link\n\n"
                 "For further assistance, contact @Prisoner7_7",
            reply_markup=main_menu_keyboard()
        )
    
    elif query.data == 'back':
        query.edit_message_text(
            text="Select an action from the menu list:",
            reply_markup=main_menu_keyboard()
        )

# Handle messages
def handle_message(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    text = update.message.text
    
    if context.user_data.get('waiting_for_gmail'):
        # Process Gmail registration
        try:
            lines = text.split('\n')
            email = lines[0].replace("Email:", "").strip()
            password = lines[1].replace("Password:", "").strip()
            recovery = lines[2].replace("Recovery Email:", "").strip()
            
            # Add Gmail to pending
            db.add_pending_gmail(user_id, email, password, recovery)
            
            # Notify admin
            context.bot.send_message(
                ADMIN_ID,
                f"New Gmail submission from @{update.effective_user.username}:\n\n"
                f"Email: {email}\n"
                f"Password: {password}\n"
                f"Recovery: {recovery}\n\n"
                f"User ID: {user_id}\n"
                "Use /approve_gmail {id} to approve or /reject_gmail {id} [reason] to reject."
            )
            
            update.message.reply_text(
                "Thank you! Your Gmail account has been submitted for review.\n"
                "$0.05 will be added to your balance after approval.",
                reply_markup=main_menu_keyboard()
            )
        except:
            update.message.reply_text(
                "Invalid format. Please use:\n\n"
                "Email: example@gmail.com\n"
                "Password: yourpassword\n"
                "Recovery Email: recovery@email.com",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data='back')]])
            )
        finally:
            context.user_data.pop('waiting_for_gmail', None)
    
    elif context.user_data.get('waiting_for_withdrawal'):
        # Process withdrawal request
        try:
            lines = text.split('\n')
            number = lines[0].replace("Number:", "").strip()
            amount = float(lines[1].replace("Amount: $", "").strip())
            
            balance = db.get_balance(user_id)
            
            if amount < 1:
                update.message.reply_text(
                    "Minimum withdrawal amount is $1 (110 TK).",
                    reply_markup=main_menu_keyboard()
                )
            elif amount > balance:
                update.message.reply_text(
                    f"Insufficient balance. Your current balance: ${balance:.2f}",
                    reply_markup=main_menu_keyboard()
                )
            else:
                # Deduct from balance
                db.update_balance(user_id, -amount)
                # Record withdrawal
                db.add_withdrawal(user_id, number, amount)
                
                # Notify admin
                context.bot.send_message(
                    ADMIN_ID,
                    f"New withdrawal request from @{update.effective_user.username}:\n\n"
                    f"User ID: {user_id}\n"
                    f"Number: {number}\n"
                    f"Amount: ${amount:.2f} ({int(amount * 110)} TK)\n\n"
                    f"Please process this payment."
                )
                
                update.message.reply_text(
                    f"Withdrawal request for ${amount:.2f} ({int(amount * 110)} TK) has been sent.\n"
                    "You will receive payment within 24 hours.\n"
                    "Thank you for using our service!",
                    reply_markup=main_menu_keyboard()
                )
        except:
            update.message.reply_text(
                "Invalid format. Please use:\n\n"
                "Number: 01XXXXXXXXX\n"
                "Amount: $XX.XX",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data='back')]])
            )
        finally:
            context.user_data.pop('waiting_for_withdrawal', None)
    
    else:
        update.message.reply_text(
            "Select an action from the menu list:",
            reply_markup=main_menu_keyboard()
        )

# Admin command to approve Gmail
def approve_gmail(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("You are not authorized to use this command.")
        return
    
    if not context.args:
        update.message.reply_text("Usage: /approve_gmail <pending_id>")
        return
    
    pending_id = int(context.args[0])
    pending_gmail = db.get_pending_gmail(pending_id)
    
    if not pending_gmail:
        update.message.reply_text("Pending Gmail not found.")
        return
    
    user_id, email, password, recovery = pending_gmail
    
    # Add to approved gmails
    db.add_gmail(user_id, email, password, recovery)
    # Update user's balance
    db.update_balance(user_id, 0.05)
    # Remove from pending
    db.remove_pending_gmail(pending_id)
    
    # Notify user
    context.bot.send_message(
        user_id,
        f"Your Gmail submission ({email}) has been approved!\n"
        "$0.05 has been added to your balance."
    )
    
    update.message.reply_text(f"Gmail approved and $0.05 added to user {user_id}'s balance.")

# Admin command to reject Gmail
def reject_gmail(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("You are not authorized to use this command.")
        return
    
    if not context.args:
        update.message.reply_text("Usage: /reject_gmail <pending_id> [reason]")
        return
    
    pending_id = int(context.args[0])
    reason = " ".join(context.args[1:]) if len(context.args) > 1 else "Invalid or duplicate account"
    
    pending_gmail = db.get_pending_gmail(pending_id)
    
    if not pending_gmail:
        update.message.reply_text("Pending Gmail not found.")
        return
    
    user_id, email, _, _ = pending_gmail
    
    # Remove from pending
    db.remove_pending_gmail(pending_id)
    
    # Notify user
    context.bot.send_message(
        user_id,
        f"Your Gmail submission ({email}) was rejected.\n"
        f"Reason: {reason}\n\n"
        "Please submit valid, unique Gmail accounts."
    )
    
    update.message.reply_text(f"Gmail rejected and user {user_id} notified.")

# Admin command to list pending Gmails
def pending_gmails(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("You are not authorized to use this command.")
        return
    
    pending = db.get_pending_gmails()
    
    if not pending:
        update.message.reply_text("No pending Gmail submissions.")
        return
    
    text = "Pending Gmail Submissions:\n\n"
    for item in pending:
        text += (f"ID: {item[0]}\n"
                f"User: @{item[1]}\n"
                f"Email: {item[2]}\n"
                f"Submitted: {item[3]}\n\n")
    
    update.message.reply_text(text)

# Error handler
def error(update: Update, context: CallbackContext):
    logger.warning(f'Update {update} caused error {context.error}')

def main():
    # Create updater and dispatcher
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Add handlers
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    # Admin commands
    dp.add_handler(CommandHandler('approve_gmail', approve_gmail))
    dp.add_handler(CommandHandler('reject_gmail', reject_gmail))
    dp.add_handler(CommandHandler('pending_gmails', pending_gmails))
    
    dp.add_error_handler(error)

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()