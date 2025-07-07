
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
import asyncio
from telegram.constants import ChatAction
from datetime import datetime

questions = [
    {"text": "Date", "type": "date"},
    {"text": "Auditor Name", "options": ["Ajay Bhaduria", "Niral Patel", "Hardas Bhuva", "Nirav Patel"]},
    {"text": "Is the EV charging working?", "options": ["Yes", "No"]},
    {"text": "Is the CARE entry Andon Board Working?", "options": ["Yes", "No"]},
    {"text": "Flags Performance Overview Screen working?", "options": ["Yes", "No"]},
    {"text": "Cluster Andon Screen Working?", "options": ["Yes", "No"]},
]

def get_date_buttons():
    today = datetime.now().date()
    try:
        display_text = today.strftime("%-d %B %Y")
    except:
        display_text = today.strftime("%#d %B %Y")

    return InlineKeyboardMarkup([
        [InlineKeyboardButton(display_text, callback_data=f"date:{display_text}")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["answers"] = []
    context.user_data["current_q"] = 0
    context.user_data["awaiting_remark"] = False
    await send_question(update, context)

async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    index = context.user_data["current_q"]
    if index < len(questions):
        q = questions[index]
        text = f"Q{index + 1}: {q['text']}"
        message_target = update.message or update.callback_query.message

        if q.get("type") == "date":
            markup = get_date_buttons()
            await message_target.reply_text(text, reply_markup=markup)
            return

        buttons = [[InlineKeyboardButton(opt, callback_data=opt)] for opt in q["options"]]
        markup = InlineKeyboardMarkup(buttons)
        await message_target.reply_text(text, reply_markup=markup)
    else:
        await send_summary(update, context)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    selection = query.data
    if selection.startswith("date:"):
        date_selected = selection.split("date:")[1]
        context.user_data["answers"].append({
            "answer": date_selected,
            "remark": None
        })
        context.user_data["current_q"] += 1
        await send_question(update, context)
        return

    context.user_data["last_answer"] = selection

    if selection == "No" or selection == "Yes":
        context.user_data["awaiting_remark"] = True
        await query.message.reply_text(f"❗️ You selected '{selection}'. Please give a remark.")
    else:
        context.user_data["answers"].append({
            "answer": selection,
            "remark": None
        })
        context.user_data["current_q"] += 1
        await send_question(update, context)

async def handle_remark(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_remark"):
        remark = update.message.text
        last_answer = context.user_data.get("last_answer", "No")
        context.user_data["answers"].append({
            "answer": last_answer,
            "remark": remark
        })
        context.user_data["awaiting_remark"] = False
        context.user_data["current_q"] += 1
        await send_question(update, context)

async def send_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answers = context.user_data["answers"]
    lines = []
    for i, entry in enumerate(answers):
        line = f"Q{i+1}: {questions[i]['text']}\n Answer: {entry['answer']}"
        if entry["remark"]:
            line += f"\n📝 Remark: {entry['remark']}"
        lines.append(line)
    summary = "\n\n".join(lines)

    message = update.message or update.callback_query.message
    await context.bot.send_chat_action(chat_id=message.chat_id, action=ChatAction.TYPING)
    await asyncio.sleep(2)
    await message.reply_text(
        f"📊 *Today's Summary Report:*\n\n{summary}",
        parse_mode='Markdown'
    )

def main():
    app = ApplicationBuilder().token("8097716560:AAE7H3AwYZAU41y5zLpL3SjRQo7ZlyDfWHU").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_remark))

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
