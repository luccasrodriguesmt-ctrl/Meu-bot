import random
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

# --- SERVIDOR FANTASMA (MANTER LIGADO) ---
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

def gerar_menu(user_id):
    p = players[user_id]
    # Barra de vida e energia visuais
    barra_hp = "🟥" * int(p['hp']/20) + "⬜" * (5 - int(p['hp']/20))
    barra_en = "🟩" * int(p['energia']/4) + "⬜" * (5 - int(p['energia']/4))
    
    texto = (
        f"🏰 **Planície** (Lv {p['lv']})\n"
        f"👤 {p['nome']}\n"
        f"❤️ HP: {p['hp']}/100 {barra_hp}\n"
        f"⚡ Energia: {p['energia']}/20 {barra_en}\n"
        f"💰 Gold: {p['gold']}"
    )
    
    # Organizando os botões igual ao seu print
    keyboard = [
        [InlineKeyboardButton("⚔️ Caçar", callback_data='caçar'), InlineKeyboardButton("🗺️ Viajar", callback_data='n')],
        [InlineKeyboardButton("🎒 Inventário", callback_data='n'), InlineKeyboardButton("👤 Perfil", callback_data='n')],
        [InlineKeyboardButton("🏪 Loja", callback_data='n'), InlineKeyboardButton("🤝 Troca", callback_data='n')],
        [InlineKeyboardButton("🏟️ Arena", callback_data='n'), InlineKeyboardButton("🔑 Masmorra", callback_data='n')],
        [InlineKeyboardButton("🏰 Guilda", callback_data='n'), InlineKeyboardButton("⚡ Energia", callback_data='n')],
        [InlineKeyboardButton("👥 Online", callback_data='n'), InlineKeyboardButton("🔥 Vire VIP", callback_data='n')]
    ]
    return texto, InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    players[uid] = {
        "nome": update.effective_user.first_name,
        "hp": 100, "gold": 0, "energia": 20, "lv": 1
    }
    
    txt, markup = gerar_menu(uid)
    img = "https://rpg-static.com/img/landscape_level1.png" # Link da planície pixel art
    
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=img, 
                                 caption=txt, reply_markup=markup, parse_mode='Markdown')

async def clique(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    
    if uid not in players: return
    
    if q.data == 'caçar':
        if players[uid]['energia'] >= 2:
            players[uid]['energia'] -= 2
            ouro = random.randint(10, 30)
            players[uid]['gold'] += ouro
            # Chance de perder HP
            if random.random() > 0.7: players[uid]['hp'] -= 10
            
            txt, markup = gerar_menu(uid)
            await q.edit_message_caption(caption=f"⚔️ **Você caçou!** Ganhou {ouro} gold.\n\n" + txt, 
                                         reply_markup=markup, parse_mode='Markdown')
        else:
            await q.answer("❌ Sem energia! Espere regenerar.", show_alert=True)
            
if __name__ == '__main__':
    keep_alive()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(clique))
    app.run_polling()
