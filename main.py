import os
import random
import sqlite3
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters, ConversationHandler

# Logs
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# Configurações de Banco e Imagens
DB_FILE = "rpg_game.db"
IMG_BOAS_VINDAS = "https://i.imgur.com/8pS1Xo5.jpeg" 
IMG_MENU_PRINCIPAL = "https://i.imgur.com/uP6M8fL.jpeg"

# Estados do Fluxo Inicial
TELA_CLASSE, TELA_NOME = range(2)

# ============================================
# BANCO DE DADOS
# ============================================
def criar_banco():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS players 
                 (id INTEGER PRIMARY KEY, nome TEXT, classe TEXT, hp INTEGER, hp_max INTEGER, 
                  lv INTEGER, exp INTEGER, gold INTEGER, energia INTEGER, energia_max INTEGER)''')
    conn.commit()
    conn.close()

def get_player(uid):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM players WHERE id = ?", (uid,))
    res = c.fetchone()
    conn.close()
    return res

# ============================================
# FLUXO DE CRIAÇÃO (COM IMAGENS)
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Criar Nova Conta 📝", callback_data='ir_para_classes')]]
    await update.message.reply_photo(
        photo=IMG_BOAS_VINDAS,
        caption="✨ **Bem-vindo ao Aventuras Rabiscadas!**\n\nSua jornada será salva no SQLite.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return TELA_CLASSE

async def menu_classes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🛡️ Guerreiro", callback_data='Guerreiro'), InlineKeyboardButton("🏹 Arqueiro", callback_data='Arqueiro')],
        [InlineKeyboardButton("🔮 Bruxa", callback_data='Bruxa'), InlineKeyboardButton("🔥 Mago", callback_data='Mago')]
    ]
    await query.edit_message_media(
        media=InputMediaPhoto(media=IMG_MENU_PRINCIPAL, caption="🎭 **Escolha sua Classe:**"),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return TELA_NOME

async def pedir_nome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    context.user_data['classe'] = query.data
    await query.answer()
    await query.delete_message()
    msg = await query.message.reply_text(f"⚔️ Classe: **{query.data}**\n\nAgora, digite o **nome** do seu herói:")
    context.user_data['msg_id'] = msg.message_id
    return ConversationHandler.END # Vamos para o menu principal após o texto

# ============================================
# MENU PRINCIPAL E SISTEMA DE CAÇA
# ============================================

async def mostrar_menu_principal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    nome = update.message.text
    classe = context.user_data.get('classe', 'Guerreiro')

    # Salva no Banco
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO players VALUES (?, ?, ?, 100, 100, 1, 0, 250, 20, 20)", (uid, nome, classe))
    conn.commit()
    conn.close()

    try:
        await update.message.delete()
        await context.bot.delete_message(chat_id=uid, message_id=context.user_data['msg_id'])
    except: pass

    return await exibir_status(update, context, uid)

async def exibir_status(update: Update, context, uid):
    p = get_player(uid)
    keyboard = [
        [InlineKeyboardButton("⚔️ Caçar", callback_data='cacar'), InlineKeyboardButton("🗺️ Viajar", callback_data='v')],
        [InlineKeyboardButton("🎒 Inventário", callback_data='i'), InlineKeyboardButton("👤 Perfil", callback_data='p')],
        [InlineKeyboardButton("🏪 Loja", callback_data='l'), InlineKeyboardButton("🏰 Masmorra", callback_data='m')]
    ]
    
    status_msg = (
        f"📍 **Planície (Lv {p['lv']})**\n"
        f"👤 **{p['nome']}** ({p['classe']})\n"
        f"❤️ HP: {p['hp']}/{p['hp_max']}\n"
        f"⚡ Energia: {p['energia']}/{p['energia_max']}\n"
        f"💰 Gold: {p['gold']} | ✨ XP: {p['exp']}"
    )

    if update.callback_query:
        await update.callback_query.edit_message_caption(caption=status_msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    else:
        await update.message.reply_photo(photo=IMG_MENU_PRINCIPAL, caption=status_msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def cacar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = update.effective_user.id
    p = get_player(uid)

    if p['energia'] < 2:
        await query.answer("🪫 Sem energia!", show_alert=True)
        return

    # Lógica de Caça (Tier 1)
    dano = random.randint(3, 8)
    gold = random.randint(10, 25)
    xp = 20
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE players SET hp=hp-?, gold=gold+?, exp=exp+?, energia=energia-2 WHERE id=?", (dano, gold, xp, uid))
    conn.commit()
    conn.close()

    await query.answer(f"⚔️ Você caçou! -{dano} HP | +{gold} Gold | +{xp} XP", show_alert=True)
    await exibir_status(update, context, uid)

# ============================================
# MAIN
# ============================================
if __name__ == '__main__':
    criar_banco()
    token = os.getenv("TELEGRAM_TOKEN")
    app = ApplicationBuilder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            TELA_CLASSE: [CallbackQueryHandler(menu_classes, pattern='^ir_para_classes$')],
            TELA_NOME: [CallbackQueryHandler(pedir_nome)],
        },
        fallbacks=[CommandHandler('start', start)],
    )

    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mostrar_menu_principal))
    app.add_handler(CallbackQueryHandler(cacar, pattern='^cacar$'))

    app.run_polling(drop_pending_updates=True)
