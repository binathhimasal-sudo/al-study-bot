import asyncio
import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai

# Render Environment Variables වලින් Keys ලබා ගැනීම
TELEGRAM_TOKEN = os.environ.get("9299790257:AAHMhOcEiwS8YbLoUByMAgVWRUC9Wu60l0k")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# 1. Start Command එක
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "ආයුබෝවන්! මම ඔයාගේ **A/L Study Assistant Bot** 🎓\n\n"
        "මට පුළුවන් මේ දේවල් කරන්න:\n"
        "1️⃣ **ඕනෑම පාඩමක් ගැන අහන්න:** නිකන්ම මැසේජ් එකක් එවන්න.\n"
        "2️⃣ **Past Papers ගන්න:** `/papers` කියලා Type කරන්න.\n"
        "3️⃣ **Time එකට Quiz කරන්න:** `/quiz <විෂය> <තත්පර_ගණන>` විදිහට එවන්න.\n"
        "   *(උදා: `/quiz Physics 30` හෝ `/quiz Accounting 45`)*"
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

# 2. හැම විෂයකටම Past Papers ලබා දෙන කොටස
async def past_papers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Physics", url="https://pastpapers.wiki/g-c-e-a-l-physics-past-papers/"),
         InlineKeyboardButton("Chemistry", url="https://pastpapers.wiki/g-c-e-a-l-chemistry-past-papers/")],
        [InlineKeyboardButton("Biology", url="https://pastpapers.wiki/g-c-e-a-l-biology-past-papers/"),
         InlineKeyboardButton("Combined Maths", url="https://pastpapers.wiki/g-c-e-a-l-combined-mathematics-past-papers/")],
        [InlineKeyboardButton("Accounting", url="https://pastpapers.wiki/g-c-e-a-l-accounting-past-papers/"),
         InlineKeyboardButton("Economics", url="https://pastpapers.wiki/g-c-e-a-l-economics-past-papers/")],
        [InlineKeyboardButton("Business Studies", url="https://pastpapers.wiki/g-c-e-a-l-business-studies-past-papers/"),
         InlineKeyboardButton("ICT", url="https://pastpapers.wiki/g-c-e-a-l-ict-past-papers/")],
        [InlineKeyboardButton("Media", url="https://pastpapers.wiki/g-c-e-a-l-media-past-papers/"),
         InlineKeyboardButton("SFT", url="https://pastpapers.wiki/g-c-e-a-l-science-for-technology-sft-past-papers/")],
        [InlineKeyboardButton("ET", url="https://pastpapers.wiki/g-c-e-a-l-engineering-technology-et-past-papers/")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("ඔයාගේ A/L විෂය තෝරන්න (Past Papers සඳහා):", reply_markup=reply_markup)

# 3. Time එකට ප්‍රශ්න හදන සහ Countdown යන කොටස
async def timed_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        subject = context.args[0]
        seconds = int(context.args[1])
        if seconds > 300:
            await update.message.reply_text("කරුණාකර තත්පර 300 (විනාඩි 5) ට අඩු කාලයක් දෙන්න.")
            return
    except (IndexError, ValueError):
        await update.message.reply_text("වැරදියි! මේ විදිහට එවන්න:\n`/quiz Physics 30`", parse_mode='Markdown')
        return

    wait_msg = await update.message.reply_text(f"⏳ {subject} වලින් ප්‍රශ්නයක් හදමින් පවතී...")

    prompt = (
        f"Create one Sri Lankan G.C.E. A/L {subject} Multiple Choice Question (MCQ) in Sinhala with 5 options (1 to 5). "
        f"Do NOT show the answer yet. Format it clearly. "
        f"At the very end, put '---ANSWER---' and then write the correct option number and a short explanation in Sinhala."
    )

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
    )

    full_text = response.text
    parts = full_text.split("---ANSWER---")
    question_text = parts[0].strip()
    answer_text = parts[1].strip() if len(parts) > 1 else "පිළිතුර ලබා ගැනීමට නොහැකි විය."

    quiz_msg = await wait_msg.edit_text(
        f"📝 **{subject} ප්‍රශ්නය:**\n\n{question_text}\n\n⏱ **ඉතිරි කාලය:** තත්පර {seconds}",
        parse_mode='Markdown'
    )

    remaining = seconds
    while remaining > 0:
        sleep_time = min(5, remaining)
        await asyncio.sleep(sleep_time)
        remaining -= sleep_time
        if remaining > 0:
            try:
                await quiz_msg.edit_text(
                    f"📝 **{subject} ප්‍රශ්නය:**\n\n{question_text}\n\n⏱ **ඉතිරි කාලය:** තත්පර {remaining}",
                    parse_mode='Markdown'
                )
            except Exception:
                pass

    await quiz_msg.edit_text(
        f"📝 **{subject} ප්‍රශ්නය:**\n\n{question_text}\n\n🛑 **කාලය අවසන්!**\n\n✅ **නිවැරදි පිළිතුර:**\n{answer_text}",
        parse_mode='Markdown'
    )

# 4. සාමාන්‍ය Chat ("Hi" කිව්වම සහ පාඩම් ගැන අහනකොට Reply කරන කොටස)
async def ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')

    system_instruction = (
        "You are a friendly, helpful Sri Lankan G.C.E. A/L study assistant bot covering all streams "
        "(Science, Maths, Commerce, Arts, Technology). "
        "Reply in natural Sinhala (or Singlish/English if the user uses it). "
        "If someone says 'Hi' or greets you, greet them warmly and ask how you can help with their A/L studies today. "
        "Keep explanations clear, accurate, and encouraging."
    )

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=f"{system_instruction}\n\nUser: {user_message}",
    )

    await update.message.reply_text(response.text)

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("papers", past_papers))
    app.add_handler(CommandHandler("quiz", timed_quiz))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_chat))

    print("Bot සාර්ථකව ක්‍රියාත්මක වේ...")
    app.run_polling()

if __name__ == '__main__':
    main()
