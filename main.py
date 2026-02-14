import random
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

# --- SERVIDOR FANTASMA ---
app_flask = Flask('')
@app_flask.route('/')
def home(): return "RPG Online!"
def run(): app_flask.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# --- CONFIGURAÇÕES ---
TOKEN = "8506567958:AAFn-GXHiZWnXDCn2sVvnZ1aG43aputD2hw"
players = {}

# Dicionário de Classes com suas respectivas imagens e status iniciais
CLASSES = {
    "Guerreiro": {"img": "https://rpg-static.com/img/warrior.png", "hp": 120, "en": 20},
    "Bruxa": {"img": "https://rpg-static.com/img/witch.png", "hp": 80, "en": 25},
    "Ladino": {"img": "https://rpg-static.com/img/rogue.png", "hp": 90, "en": 22},
    "Monge": {"img": "https://rpg-static.com/img/monk.png", "hp": 110, "en": 18},
    "Bêbado": {"img": "https://rpg-static.com/img/drunk.png", "hp": 150, "en": 10},
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
        [InlineKeyboardButton("🏪 Loja", callback_data='n'), InlineKeyboardButton("🔄 Resetar", callback_data='reset')]
    ]
    return txt, InlineKeyboardMarkup(kb)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    
    # Se o jogador já tem classe, vai pro menu. Se não, escolhe classe.
    if uid in players and "classe" in players[uid]:
        txt, markup = gerar_menu_principal(uid)
        await update.message.reply_text("Bem-vindo de volta!")
    else:
        # Tela de Criação de Personagem
        img_inicio = "https://rpg-static.com/img/select_class.png" 
        kb = [
            [InlineKeyboardButton("🛡️ Guerreiro", callback_data='sel_Guerreiro'), InlineKeyboardButton("🧙 Bruxa", callback_data='sel_Bruxa')],
            [InlineKeyboardButton("🗡️ Ladino", callback_data='sel_Ladino'), InlineKeyboardButton("🧘 Monge", callback_data='sel_Monge')],
            [InlineKeyboardButton("🍺 Bêbado", callback_data='sel_Bêbado')]
        ]
        await context.bot.send_photo(
            chat_id=update.effective_chat.id, 
            photo=img_inicio,
            caption="✨ **Bem-vindo ao Teletofus!**\n\nEscolha sua classe inicial para começar a jornada:",
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode='Markdown'
        )

async def clique(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id
    await q.answer()

    # Seleção de Classe
    if q.data.startswith('sel_'):
        classe_nome = q.data.split('_')[1]
        stats = CLASSES[classe_nome]
        players[uid] = {
            "classe": classe_nome, "hp": stats['hp'], "en": stats['en'], 
            "gold": 0, "lv": 1, "img": stats['img']
        }
        txt, markup = gerar_menu_principal(uid)
        # Muda a imagem para a imagem da classe escolhida
        await q.edit_message_media(media=InputMediaPhoto(stats['img']))
        await q.edit_message_caption(caption="✅ Classe escolhida!\n\n" + txt, reply_markup=markup, parse_mode='Markdown')

    elif q.data == 'reset':
        if uid in players: del players[uid]
        await q.edit_message_caption(caption="Personagem deletado. Use /start para criar outro.")

# No final do arquivo, adicione as imports necessárias que faltaram
from telegram import InputMediaPhoto

if __name__ == '__main__':
    keep_alive()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(clique))
    app.run_polling()
