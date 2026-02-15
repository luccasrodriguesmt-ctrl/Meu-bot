import os
import logging
import sqlite3
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Configuração de Logs
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# Estados da Conversa
TELA_CLASSE, TELA_NOME, TELA_MENU = range(3)

# --- DADOS DO CÓDIGO ANTIGO ---
ITENS = {
    "Espada de Madeira": {"tipo": "arma", "atk": 5, "preco": 50},
    "Escudo de Couro": {"tipo": "armadura", "def": 3, "preco": 40}
}

MONSTROS = {
    "Slime": {"hp": 20, "atk": 3, "gold_min": 5, "gold_max": 15, "exp": 10},
    "Goblin": {"hp": 45, "atk": 7, "gold_min": 15, "gold_max": 30, "exp": 25}
}

POCOES = {
    "Poção de Vida": {"cura": 30, "preco": 20},
    "Poção de Energia": {"energia": 10, "preco": 30}
}

# --- SISTEMA DE BANCO DE DADOS (SQLite) ---
DB_FILE = "rpg_game.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Tabela de Jogadores
    c.execute('''CREATE TABLE IF NOT EXISTS players 
                 (id INTEGER PRIMARY KEY, nome TEXT, classe TEXT, hp INTEGER, hp_max INTEGER, 
                  lv INTEGER, exp INTEGER, gold INTEGER, energia INTEGER, energia_max INTEGER)''')
    # Tabela de Inventário
    c.execute('''CREATE TABLE IF NOT EXISTS inventario 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, player_id INTEGER, item_nome TEXT, qtd INTEGER)''')
    # Tabela de Equipamentos
    c.execute('''CREATE TABLE IF NOT EXISTS equipamentos 
                 (player_id INTEGER PRIMARY KEY, arma TEXT, armadura TEXT)''')
    conn.commit()
    conn.close()

def salvar_novo_player(uid, nome, classe):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO players VALUES (?, ?, ?, 100, 100, 1, 0, 250, 20, 20)", 
              (uid, nome, classe))
    c.execute("INSERT OR REPLACE INTO equipamentos VALUES (?, 'Mãos Nuas', 'Roupas Comuns')", (uid,))
    conn.commit()
    conn.close()

def get_player(uid):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM players WHERE id = ?", (uid,))
    res = c.fetchone()
    conn.close()
    return res

# --- LÓGICA DO BOT ---
IMG_BOAS_VINDAS = "https://i.imgur.com/8pS1Xo5.jpeg" 
IMG_CLASSES = "https://i.imgur.com/uP6M8fL.jpeg"
IMG_MENU_PRINCIPAL = "https://i.imgur.com/uP6M8fL.jpeg"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Criar Nova Conta 📝", callback_data='ir_para_classes')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_photo(
        photo=IMG_BOAS_VINDAS,
        caption="✨ **Bem-vindo ao Aventuras Rabiscadas!**\n\nSua jornada será salva no nosso banco de dados.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
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
        media=InputMediaPhoto(media=IMG_CLASSES, caption="🎭 **Escolha sua Classe:**"),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return TELA_NOME

async def pedir_nome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    context.user_data['classe'] = query.data
    await query.answer()
    await query.delete_message()
    msg = await query.message.reply_text(f"⚔️ Escolheu **{query.data}**!\n\nAgora, digite o **nome** do seu herói:")
    context.user_data['msg_id'] = msg.message_id
    return TELA_MENU

async def menu_principal_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    nome = update.message.text
    classe = context.user_data.get('classe')

    # Salva no SQLite
    salvar_novo_player(uid, nome, classe)
    p = get_player(uid) # Puxa os dados recém-criados

    try:
        await update.message.delete()
        await context.bot.delete_message(chat_id=uid, message_id=context.user_data['msg_id'])
    except: pass

    keyboard = [
        [InlineKeyboardButton("⚔️ Caçar", callback_data='c'), InlineKeyboardButton("🗺️ Viajar", callback_data='v')],
        [InlineKeyboardButton("🎒 Inventário", callback_data='i'), InlineKeyboardButton("👤 Perfil", callback_data='p')],
        [InlineKeyboardButton("🏪 Loja", callback_data='l'), InlineKeyboardButton("🏰 Masmorra", callback_data='m')]
    ]
    
    # Barra de vida visual usando os dados do banco p[3]=hp, p[4]=hp_max
    status = (
        f"📍 **Planície (Lv {p[5]})**\n"
        f"👤 **{p[1]}** ({p[2]})\n"
        f"❤️ **HP:** {p[3]}/{p[4]} 🟥🟥🟥\n"
        f"⚡ **Energia:** {p[8]}/{p[9]} 🟩🟩🟩\n"
        f"💰 **Gold:** {p[7]}"
    )

    await update.message.reply_photo(
        photo=IMG_MENU_PRINCIPAL,
        caption=status,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    return ConversationHandler.END

def main():
    init_db() # Cria o arquivo .db na primeira vez
    token = os.getenv("TELEGRAM_TOKEN")
    application = Application.builder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            TELA_CLASSE: [CallbackQueryHandler(menu_classes, pattern='^ir_para_classes$')],
            TELA_NOME: [CallbackQueryHandler(pedir_nome)],
            TELA_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, menu_principal_view)],
        },
        fallbacks=[CommandHandler('start', start)],
    )

    application.add_handler(conv_handler)
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
