import random
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

# --- SERVIDOR PARA MANTER O RENDER LIGADO ---
app_flask = Flask('')
@app_flask.route('/')
def home():
    return "Bot RPG Online!"

def run():
    app_flask.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
# ------------------------------------------

TOKEN = "8506567958:AAFn-GXHiZWnXDCn2sVvnZ1aG43aputD2hw"
players = {}

def barra(hp):
    cheio = int(hp / 10)
    return "❤️" + "🟢" * cheio + "⚪" * (10 - cheio)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    players[uid] = {"hp": 100, "gold": 0}
    kb = [[InlineKeyboardButton("⚔️ Caçar", callback_data='c')]]
    img = "https://img.freepik.com/premium-photo/fantasy-rpg-landscape-background-generative-ai_739548-1543.jpg"
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=img, 
                                 caption=f"🏰 **Início da Jornada**\n\n{barra(100)}\n💰 Gold: 0",
                                 reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def clique(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    if uid not in players: return
    dano, ouro = random.randint(0, 15), random.randint(5, 20)
    players[uid]["hp"] -= dano
    players[uid]["gold"] += ouro
    if players[uid]["hp"] <= 0:
        players[uid]["hp"] = 100
        res = "☠️ Você desmaiou e voltou à vila!"
    else:
        res = f"⚔️ Lutou! -{dano} HP | +{ouro} Gold"
    kb = [[InlineKeyboardButton("⚔️ Caçar de novo", callback_data='c')]]
    await q.edit_message_caption(caption=f"🏰 **Combate**\n\n{res}\n\n{barra(players[uid]['hp'])}\n💰 Gold: {players[uid]['gold']}",
                                 reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

if __name__ == '__main__':
    keep_alive()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(clique))
    app.run_polling()
