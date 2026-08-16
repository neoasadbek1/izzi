import logging
import json
import os
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# ============================================
# SOZLAMALAR - ENVIRONMENT VARIABLES
# ============================================

# Railway'da environment variables orqali o'rnatiladi
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8764745564:AAHMgfRspc6L6cCzPmitxZfcRTBROXAYvL0")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AQ.Ab8RN6KwiwgF-J7V7-fhWwi7XHPKIqvYPhl0pKKmvsIPrASaJA")
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-3.6-flash")

# Xotira fayli (Railway'da /tmp papkasida saqlanadi)
MEMORY_FILE = "/tmp/memory.json"

# ============================================
# LOGGING
# ============================================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============================================
# GEMINI SOZLASH
# ============================================

try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(MODEL_NAME)
    print(f"✅ Gemini {MODEL_NAME} yuklandi!")
    print(f"🔑 API Key: {GEMINI_API_KEY[:15]}...")
except Exception as e:
    print(f"❌ Gemini xatosi: {e}")
    exit()

# ============================================
# XOTIRA (MEMORY) FUNKSIYALARI
# ============================================

def load_memory():
    """Xotirani fayldan yuklash"""
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except:
        return {}

def save_memory(memory):
    """Xotirani faylga saqlash"""
    try:
        with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(memory, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def add_memory(user_id, key, value):
    """Xotiraga ma'lumot qo'shish"""
    memory = load_memory()
    user_id = str(user_id)
    
    if user_id not in memory:
        memory[user_id] = {}
    
    memory[user_id][key] = {
        "value": value,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    save_memory(memory)
    return True

def get_memory(user_id, key=None):
    """Xotirandan ma'lumot olish"""
    memory = load_memory()
    user_id = str(user_id)
    
    if user_id not in memory:
        return None
    
    if key:
        return memory[user_id].get(key, None)
    return memory[user_id]

def delete_memory(user_id, key):
    """Xotirandan ma'lumot o'chirish"""
    memory = load_memory()
    user_id = str(user_id)
    
    if user_id in memory and key in memory[user_id]:
        del memory[user_id][key]
        save_memory(memory)
        return True
    return False

def clear_memory(user_id):
    """Foydalanuvchining barcha xotirasini tozalash"""
    memory = load_memory()
    user_id = str(user_id)
    
    if user_id in memory:
        del memory[user_id]
        save_memory(memory)
        return True
    return False

# Suhbat tarixi (vaqtinchalik, server qayta ishga tushganda tozalanadi)
chat_history = {}

# ============================================
# BOT FUNKSIYALARI
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start buyrug'i"""
    welcome_text = """
🦾 **IZZI** - Aqlli Virtual Yordamchi

Salom! Men **Gemini 3.6 Flash** bilan ishlayman.

📌 **Qanday ishlatish:**

💬 **Oddiy suhbat:**
Istalgan savolingizni yozing.

🧠 **Xotira (MEMORY):**
• `+ ism: Ali` - ismni eslab qolish
• `+ yosh: 25` - yoshni eslab qolish
• `+ sevimli_ovqat: Palov` - ovqatni eslab qolish
• `? ism` - ismni so'rash
• `? hammasi` - barcha xotirani ko'rish
• `- ism` - ismni o'chirish
• `/clearmemory` - barcha xotirani tozalash

🔧 **Buyruqlar:**
/start - Botni ishga tushirish
/help - Yordam olish
/clear - Suhbat tarixini tozalash
/clearmemory - Xotirani tozalash
/stats - Statistikani ko'rish

⚡ **Tez va aqlli!**
"""
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/help buyrug'i"""
    help_text = """
📖 **IZZI - Yordam**

💬 **Oddiy suhbat:**
Istagan savolingizni yozing, IZZI javob beradi.

🧠 **Xotira (Memory) qanday ishlaydi:**

1️⃣ **Eslab qolish:** `+ narsa: qiymat`
   Masalan: `+ ism: Ali`

2️⃣ **So'rash:** `? narsa`
   Masalan: `? ism`

3️⃣ **Hammasini ko'rish:** `? hammasi`

4️⃣ **O'chirish:** `- narsa`
   Masalan: `- ism`

5️⃣ **Hammasini tozalash:** `/clearmemory`

🔧 **Buyruqlar:**
/start - Botni ishga tushirish
/help - Yordam olish
/clear - Suhbat tarixini tozalash
/clearmemory - Xotirani tozalash
/stats - Statistikani ko'rish

🤖 **Men haqimda:**
- Ism: IZZI
- Model: Gemini 3.6 Flash
- Til: O'zbekcha
- Xotira: Doimiy (serverda saqlanadi)

✨ **Do'stona va samimiy!**
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def clear_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Suhbat tarixini tozalash"""
    user_id = str(update.effective_user.id)
    if user_id in chat_history:
        chat_history[user_id] = []
        await update.message.reply_text("🧹 Suhbat tarixi tozalandi!")
    else:
        await update.message.reply_text("📭 Tarix allaqachon bo'sh.")

async def clear_memory_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xotirani tozalash"""
    user_id = update.effective_user.id
    if clear_memory(user_id):
        await update.message.reply_text("🧹 Barcha xotira tozalandi!")
    else:
        await update.message.reply_text("📭 Xotira allaqachon bo'sh.")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Statistika"""
    user_id = str(update.effective_user.id)
    chat_count = len(chat_history.get(user_id, []))
    
    memory = get_memory(user_id)
    memory_count = len(memory) if memory else 0
    
    await update.message.reply_text(
        f"📊 **Statistika**\n\n"
        f"👤 Foydalanuvchi ID: `{user_id}`\n"
        f"💬 Suhbat xabarlari: {chat_count}\n"
        f"🧠 Xotira ma'lumotlari: {memory_count}\n"
        f"🤖 Model: {MODEL_NAME}\n"
        f"🕐 Vaqt: {datetime.now().strftime('%H:%M:%S')}",
        parse_mode='Markdown'
    )

def process_memory_command(user_id, text):
    """Xotira buyruqlarini qayta ishlash"""
    text = text.strip()
    
    # Eslab qolish: + narsa: qiymat
    if text.startswith('+ '):
        parts = text[2:].split(':', 1)
        if len(parts) == 2:
            key = parts[0].strip()
            value = parts[1].strip()
            if key and value:
                add_memory(user_id, key, value)
                return f"✅ Eslab qoldim! **{key}** → **{value}**"
            else:
                return "❌ Xato format: `+ narsa: qiymat`"
        else:
            return "❌ Xato format: `+ narsa: qiymat`"
    
    # So'rash: ? narsa
    if text.startswith('? '):
        key = text[2:].strip()
        if not key:
            return "❌ Iltimos, nimani so'rashni yozing. Masalan: `? ism`"
        
        if key.lower() == 'hammasi':
            memory = get_memory(user_id)
            if memory and len(memory) > 0:
                result = "🧠 **Xotira:**\n\n"
                for k, v in memory.items():
                    result += f"• **{k}**: {v['value']} (_{v['time']}_)\n"
                return result
            else:
                return "📭 Xotira bo'sh."
        else:
            data = get_memory(user_id, key)
            if data:
                return f"🧠 **{key}** → {data['value']} (_{data['time']}_)"
            else:
                return f"❌ **{key}** haqida hech narsa eslay olmayman."
    
    # O'chirish: - narsa
    if text.startswith('- '):
        key = text[2:].strip()
        if not key:
            return "❌ Iltimos, nimani o'chirishni yozing. Masalan: `- ism`"
        
        if delete_memory(user_id, key):
            return f"🗑️ **{key}** o'chirildi!"
        else:
            return f"❌ **{key}** topilmadi."
    
    return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Foydalanuvchi xabarlarini qayta ishlash"""
    user_id = str(update.effective_user.id)
    user_text = update.message.text
    
    if not user_text:
        return
    
    # Xotira buyrug'ini tekshirish
    memory_result = process_memory_command(user_id, user_text)
    if memory_result:
        await update.message.reply_text(memory_result, parse_mode='Markdown')
        return
    
    # Yozayotganini ko'rsatish
    await update.message.chat.send_action(action="typing")
    
    try:
        # Suhbat tarixini boshqarish
        if user_id not in chat_history:
            chat_history[user_id] = []
        
        chat_history[user_id].append(f"Foydalanuvchi: {user_text}")
        
        # Xotirani olish
        memory = get_memory(user_id)
        memory_text = ""
        if memory and len(memory) > 0:
            memory_text = "\n\n**Foydalanuvchi haqida eslab qolgan ma'lumotlarim:**\n"
            for key, data in memory.items():
                memory_text += f"- {key}: {data['value']}\n"
        
        # Prompt tayyorlash
        history_text = "\n".join(chat_history[user_id][-5:])
        
        prompt = f"""
Senning isming IZZI. Sen aqlli, samimiy va zamonaviy virtual yordamchisan.
O'zbek tilida, qisqa, aniq va do'stona javob ber.
Agar savolni tushunmasang, "Kechirasiz, tushunmadim. Qayta ayta olasizmi?" deb so'ra.

Suhbat tarixi:
{history_text}
{memory_text}

IZZI:
"""
        
        response = model.generate_content(prompt)
        javob = response.text.strip()
        
        chat_history[user_id].append(f"IZZI: {javob}")
        
        if len(chat_history[user_id]) > 10:
            chat_history[user_id] = chat_history[user_id][-10:]
        
        await update.message.reply_text(f"🤖 {javob}")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Xatolik: {str(e)}")
        logger.error(f"Xatolik: {e}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")

# ============================================
# ASOSIY FUNKSIYA
# ============================================

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("clear", clear_history))
    app.add_handler(CommandHandler("clearmemory", clear_memory_command))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)
    
    print("🚀 IZZI bot ishga tushdi!")
    print(f"🤖 Bot token: {TELEGRAM_TOKEN[:10]}...")
    print(f"📡 Model: {MODEL_NAME}")
    print("="*50)
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()