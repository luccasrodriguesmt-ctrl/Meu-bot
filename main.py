import random
import os
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

# --- SERVIDOR PARA MANTER LIGADO ---
app_flask = Flask('')
@app_flask.route('/')
def home():
    return "Bot Online!"

def run():
    app_flask.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- DADOS E CONFIGURAÇÕES ---
TOKEN = "8506567958:AAFn-GXHiZWnXDCn2sVvnZ1aG43aputD2hw"
players = {}

def gerar_menu(user_id):
    p = players[user_id]
    # Criando as barras visuais (🟥 para HP, 🟩 para Energia)
    b_hp = "🟥" * (p['hp'] // 20) + "⬜" * (5 - (p['hp'] // 20))
    b_en = "🟩" * (p['en'] // 4) + "⬜" * (5 - (p['en'] // 4))
    
    texto = (
        f"🏰 **Planície** (Lv {p['lv']})\n"
        f"❤️ HP: {p['hp']}/100 {b_hp}\n"
        f"⚡ Energia: {p['en']}/20 {b_en}\n"
        f"💰 Gold: {p['gold']}"
    )
    
    # Menu igual ao seu print
    keyboard = [
        [InlineKeyboardButton("⚔️ Caçar", callback_data='c'), InlineKeyboardButton("🗺️ Viajar", callback_data='n')],
        [InlineKeyboardButton("🎒 Inventário", callback_data='n'), InlineKeyboardButton("👤 Perfil", callback_data='n')],
        [InlineKeyboardButton("🏪 Loja", callback_data='n'), InlineKeyboardButton("🤝 Troca", callback_data='n')],
        [InlineKeyboardButton("🏟️ Arena", callback_data='n'), InlineKeyboardButton("🔑 Masmorra", callback_data='n')],
        [InlineKeyboardButton("🏰 Guilda", callback_data='n'), InlineKeyboardButton("⚡ Energia", callback_data='n')],
        [InlineKeyboardButton("👥 Online", callback_data='n'), InlineKeyboardButton("🔥 Vire VIP", callback_data='n')]
    ]
    return texto, InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    players[uid] = {"hp": 100, "en": 20, "gold": 0, "lv": 1}
    txt, markup = gerar_menu(uid)
    img = "https://img.freepik.com/premium-photo/fantasy-rpg-landscape-background-generative-ai_739548-1543.jpg"
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=img, caption=txt, reply_markup=markup, parse_mode='Markdown')

async def clique(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    if uid not in players: return

    if q.data == 'c': # Botão de Caçar
        if players[uid]['en'] >= 2:
            players[uid]['en'] -= 2
            ganho = random.randint(10, 25)
            players[uid]['gold'] += ganho
            txt, markup = gerar_menu(uid)
            await q.edit_message_caption(caption=f"⚔️ **Você lutou e ganhou {ganho} Gold!**\n\n{txt}", reply_markup=markup, parse_mode='Markdown')
        else:
            await q.answer("⚡ Você está sem energia!", show_alert=True)

if __name__ == '__main__':
    keep_alive()
    print("Iniciando Bot...")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(clique))
    app.run_polling()
