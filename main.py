
import random
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

# --- SERVIDOR PARA O RENDER ---
app_flask = Flask('')
@app_flask.route('/')
def home(): return "RPG Online!"
def run(): app_flask.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# --- CONFIGURAÇÕES DO RPG ---
TOKEN = "8506567958:AAFn-GXHiZWnXDCn2sVvnZ1aG43aputD2hw"
players = {}

# Defina aqui os links das imagens para cada classe
CLASSES = {
    "Guerreiro": {
        "img": "https://i.ibb.co/S76XpY7/warrior-pixel.png", 
        "hp": 120, "en": 20, "desc": "🛡️ Alta vida e força bruta."
    },
    "Bruxa": {
        "img": "https://i.ibb.co/vYm6m8j/witch-pixel.png", 
        "hp": 80, "en": 25, "desc": "🧙 Grande mana e feitiços poderosos."
    },
    "Ladino": {
        "img": "https://i.ibb.co/pLzXN0x/rogue-pixel.png", 
        "hp": 90, "en": 22, "desc": "🗡️ Ágil e mestre em roubos."
    },
    "Bêbado": {
        "img": "https://i.ibb.co/f4n6p4V/drunk-pixel.png", 
        "hp": 150, "en": 10, "desc": "🍺 Resistente, mas muito lento."
    }
}

def gerar_menu_principal(uid):
    p = players[uid]
    b_hp = "🟥" * (p['hp'] // 30) + "⬜" * (5 - (p['hp'] // 30))
    b_en = "🟩" * (p['en'] // 5) + "⬜" * (5 - (p['en'] // 5))
    
    txt = (f"🏰 **Planície** (Lv {p['lv']})\n"
           f"👤 Classe: {p['classe']}\n"
           f"❤️ HP: {p['hp']} {b_hp}\n"
           f"⚡ Energia: {p['en']} {b_en}\n"
           f"💰 Gold: {p['gold']}")
    
    kb = [
        [InlineKeyboardButton("⚔️ Caçar", callback_data='c'), InlineKeyboardButton("🗺️ Viajar", callback_data='n')],
        [InlineKeyboardButton("🎒 Inventário", callback_data='n'), InlineKeyboardButton("👤 Perfil", callback_data='n')],
        [InlineKeyboardButton("🔄 Resetar Personagem", callback_data='reset')]
    ]
    return txt, InlineKeyboardMarkup(kb)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    
    if uid in players:
        txt, markup = gerar_menu_principal(uid)
        await context.bot.send_photo(chat_id=uid, photo=players[uid]['img'], caption=txt, reply_markup=markup, parse_mode='Markdown')
    else:
        # Tela de Seleção Inicial
        img_selecao = "https://i.ibb.co/mS6v9zB/select-screen.png"
        kb = [
            [InlineKeyboardButton("🛡️ Guerreiro", callback_data='sel_Guerreiro'), InlineKeyboardButton("🧙 Bruxa", callback_data='sel_Bruxa')],
            [InlineKeyboardButton("🗡️ Ladino", callback_data='sel_Ladino'), InlineKeyboardButton("🍺 Bêbado", callback_data='sel_Bêbado')]
        ]
        await context.bot.send_photo(
            chat_id=uid, 
            photo=img_selecao, 
            caption="✨ **BEM-VINDO AO TELETOFUS**\n\nEscolha sua classe inicial para começar:", 
            reply_markup=InlineKeyboardMarkup(kb), 
            parse_mode='Markdown'
        )

async def clique(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id
    await q.answer()

    if q.data.startswith('sel_'):
        nome_classe = q.data.split('_')[1]
        c = CLASSES[nome_classe]
        players[uid] = {
            "classe": nome_classe, "hp": c['hp'], "en": c['en'], 
            "gold": 0, "lv": 1, "img": c['img']
        }
        txt, markup = gerar_menu_principal(uid)
        
        # Troca a imagem da seleção pela skin da classe
        await q.edit_message_media(media=InputMediaPhoto(c['img']))
        await q.edit_message
