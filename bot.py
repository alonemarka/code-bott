from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import json
import os
import requests

TOKEN = os.getenv("TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

MEMORY_FILE = "memory.json"

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_memory(memory):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

memory = load_memory()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 **Yazılım AI Asistanı (Hafızalı)**\n\n"
        "• Grupta: `/ai <soru>` veya reply + `/ai`\n"
        "• Özelde: Her mesaja cevap veririm\n"
        "/hafiza → Hafızayı temizle"
    )

async def clear_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if user_id in memory:
        del memory[user_id]
        save_memory(memory)
    await update.message.reply_text("🗑️ Hafıza temizlendi.")

async def ai_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    text = update.message.text

    if update.message.chat.type != "private":
        if not text.startswith("/ai"):
            return
        question = text.replace("/ai", "").strip()
        if not question:
            await update.message.reply_text("❌ Sorunu yaz: `/ai Python telegram bot örneği`")
            return
    else:
        question = text

    if user_id not in memory:
        memory[user_id] = []

    memory[user_id].append({"role": "user", "content": question})
    if len(memory[user_id]) > 20:
        memory[user_id] = memory[user_id][-20:]

    thinking = await update.message.reply_text("🤖 Düşünüyorum...")

    try:
        payload = {
            "model": "llama3-70b-8192",
            "messages": memory[user_id],
            "temperature": 0.7,
            "max_tokens": 2000
        }

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        r = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                         json=payload, headers=headers, timeout=60)
        result = r.json()

        answer = result['choices'][0]['message']['content']

        if "```" not in answer:
            answer = "```python\n" + answer + "\n```"

        await thinking.edit_text(answer, parse_mode='Markdown')

        memory[user_id].append({"role": "assistant", "content": answer})
        save_memory(memory)

    except Exception as e:
        await thinking.edit_text("❌ Hata: " + str(e)[:100])

# Bot
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("hafiza", clear_memory))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_response))

print("🚀 AI Bot Çalışıyor...")
app.run_polling()
