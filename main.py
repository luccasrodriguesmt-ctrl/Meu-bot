import random
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

# --- SERVIDOR FANTASMA PARA O RENDER ---
app_flask = Flask('')
@app_flask.route('/')
def home(): 
    return "RPG Online!"

def run(): 
    app_flask.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- CONFIGURAÇÕES DO BOT ---
TOKEN = "8506567958:AAFn-GXHiZWnXDCn2sVvnZ1aG43aputD2hw"
players = {}

# Lista expandida de classes com imagens temporárias
CLASSES = {
    "Guerreiro": {"img": "https://picsum.photos/seed/knight/400/300", "hp": 120, "en": 20},
    "Bruxa": {"img": "https://picsum.photos/seed/witch/400/300", "hp": 80, "en": 25},
    "Ladino": {"img": "https://picsum.photos/seed/rogue/400/300", "hp": 90, "en": 22},
    "Bêbado": {"img": "https://picsum.photos/seed/beer/400/300", "hp": 150, "en": 10},
    "Druida": {"img": "https://picsum.photos/seed/druid/400/300", "hp": 100, "en": 20},
    "Feiticeiro": {"img": "https://picsum.photos/seed/mage/400/300", "hp": 70, "en": 30},
    "Monge": {"img": "https://picsum.photos/seed/monk/400/300", "hp": 110, "en": 18}
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
        [InlineKeyboardButton("🔄 Resetar", callback_data='reset')]
    ]
    return txt, InlineKeyboardMarkup(kb)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in players:
        txt, markup = gerar_menu_principal(uid)
        await context.bot.send_photo(chat_id=uid, photo=players[uid]['img'], caption=txt, reply_markup=markup, parse_mode='Markdown')
    else:
        img_inicio = "https://picsum.photos/seed/rpgstart/400/300"
        # Organizando os botões em pares para caberem na tela
        kb = [
            [InlineKeyboardButton("🛡️ Guerreiro", callback_data='sel_Guerreiro'), InlineKeyboardButton("🧙 Bruxa", callback_data='sel_Bruxa')],
            [InlineKeyboardButton("🗡️ Ladino", callback_data='sel_Ladino'), InlineKeyboardButton("🌿 Druida", callback_data='sel_Druida')],
            [InlineKeyboardButton("✨ Feiticeiro", callback_data='sel_Feiticeiro'), InlineKeyboardButton("🧘 Monge", callback_data='sel_Monge')],
            [InlineKeyboardButton("🍺 Bêbado", callback_data='sel_Bêbado')]
        ]
        await context.bot.send_photo(chat_id=uid, photo=img_inicio, caption="✨ **BEM-VINDO AO RPG**\n\nEscolha sua classe inicial:", reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def clique(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id
    await q.answer()

    if q.data.startswith('sel_'):
        nome_c = q.data.split('_')[1]
        c = CLASSES[nome_c]
        players[uid] = {"classe": nome_c, "hp": c['hp'], "en": c['en'], "gold": 0, "lv": 1, "img": c['img']}
        txt, markup = gerar_menu_principal(uid)
        
        try:
            await q.edit_message_media(media=InputMediaPhoto(c['img']))
            await q.edit_message_caption(caption=f"✅ Você agora é um {nome_c}!\n\n{txt}", reply_markup=markup, parse_mode='Markdown')
        except:
            await q.edit_message_caption(caption=f"✅ Criado!\n\n{txt}", reply_markup=markup, parse_mode='Markdown')

    elif q.data == 'reset':
        if uid in players: del players[uid]
        await q.edit_message_caption(caption="🚮 Personagem deletado! Use /start para recriar.")

    elif q.data == 'c':
        if uid in players and players[uid]['en'] >= 2:
            players[uid]['en'] -= 2
            players[uid]['gold'] += 10
            txt, markup = gerar_menu_principal(uid)
            await q.edit_message_caption(caption=txt, reply_markup=markup, parse_mode='Markdown')
        else:
            await q.answer("⚡ Sem energia!", show_alert=True)

if __name__ == '__main__':
    keep_alive()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(clique))
    app.run_polling()
