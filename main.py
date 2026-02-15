import os
import random
import sqlite3
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters, ConversationHandler

# Mude para 1.2.2 no GitHub para conferir se o Render atualizou!
VERSAO = "1.2.2 - Correção Caça"

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

DB_FILE = "rpg_game.db"
IMG_MENU = "https://i.imgur.com/uP6M8fL.jpeg" 

TELA_CLASSE, TELA_NOME = range(2)

# --- AUXILIARES ---
def gerar_barra(atual, maximo):
    if maximo <= 0: return "⬜" * 10
    percent = max(0, min(atual / maximo, 1))
    preenchido = int(percent * 10)
    return "🟦" * preenchido + "⬜" * (10 - preenchido)

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# --- LÓGICA DE EXIBIÇÃO ---
async def exibir_status(update, context, uid, texto_combate=""):
    conn = get_connection()
    p = conn.execute("SELECT * FROM players WHERE id = ?", (uid,)).fetchone()
    conn.close()

    if not p:
        await update.effective_message.reply_text("❌ Erro ao carregar perfil. Use /start")
        return

    barra_hp = gerar_barra(p['hp'], p['hp_max'])
    barra_exp = gerar_barra(p['exp'], p['lv'] * 100)

    status_msg = (
        f"🤖 **Versão:** `{VERSAO}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **{p['nome']}** — *{p['classe']} Lv. {p['lv']}*\n\n"
        f"❤️ **Vida:** {p['hp']}/{p['hp_max']}\n"
        f"|{barra_hp}|\n\n"
        f"✨ **XP:** {p['exp']}/{p['lv']*100}\n"
        f"|{barra_exp}|\n\n"
        f"💰 **Gold:** {p['gold']}  |  ⚡ **Energia:** {p['energia']}/{p['energia_max']}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{texto_combate}"
    )

    keyboard = [
        [InlineKeyboardButton("⚔️ Caçar", callback_data='cacar'), InlineKeyboardButton("🗺️ Viajar", callback_data='v')],
        [InlineKeyboardButton("🎒 Mochila", callback_data='i'), InlineKeyboardButton("👤 Status", callback_data='p')],
        [InlineKeyboardButton("🏪 Mercado", callback_data='l'), InlineKeyboardButton("⚙️ Ajustes", callback_data='s')]
    ]

    if update.callback_query:
        await update.callback_query.edit_message_caption(
            caption=status_msg, 
            reply_markup=InlineKeyboardMarkup(keyboard), 
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_photo(
            photo=IMG_MENU, caption=status_msg, 
            reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
        )

# --- SISTEMA DE CAÇA ---
async def cacar_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = update.effective_user.id
    await query.answer()

    conn = get_connection()
    p = conn.execute("SELECT * FROM players WHERE id = ?", (uid,)).fetchone()

    if p['energia'] < 2:
        await query.message.reply_text("🪫 Você está sem energia! Espere um tempo.")
        conn.close()
        return

    # Lógica de Recompensa
    dano = random.randint(4, 10)
    ouro = random.randint(15, 30)
    xp_ganho = 25
    
    # Update no banco
    conn.execute("""UPDATE players SET 
                    hp = MAX(0, hp - ?), 
                    gold = gold + ?, 
                    exp = exp + ?, 
                    energia = energia - 2 
                    WHERE id = ?""", (dano, ouro, xp_ganho, uid))
    conn.commit()
    conn.close()

    resultado = f"⚔️ **Você encontrou um monstro!**\n💥 Perdeu {dano} HP\n💰 Ganhou {ouro} Gold e {xp_ganho} XP!"
    await exibir_status(update, context, uid, texto_combate=resultado)

# --- INICIALIZAÇÃO E COMANDOS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Botão para iniciar o ConversationHandler
    keyboard = [[InlineKeyboardButton("🎮 Começar Jogo", callback_data='ir_para_classes')]]
    await update.message.reply_text(f"✨ RPG Versão `{VERSAO}`", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return TELA_CLASSE

# [As funções menu_classes, pedir_nome e salvar_final continuam aqui...]
# (Mantendo o padrão do código anterior para salvar no SQLite)

def main():
    # Certifique-se de que o Banco existe
    conn = sqlite3.connect(DB_FILE)
    conn.execute('''CREATE TABLE IF NOT EXISTS players 
                 (id INTEGER PRIMARY KEY, nome TEXT, classe TEXT, hp INTEGER, hp_max INTEGER, 
                  lv INTEGER, exp INTEGER, gold INTEGER, energia INTEGER, energia_max INTEGER)''')
    conn.close()

    token = os.getenv("TELEGRAM_TOKEN")
    app = ApplicationBuilder().token(token).build()

    # Conversation para criação
    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            TELA_CLASSE: [CallbackQueryHandler(menu_classes, pattern='^ir_para_classes$')],
            # ... outros estados ...
        },
        fallbacks=[CommandHandler('start', start)],
    )

    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(cacar_handler, pattern='^cacar$')) # BOTÃO CAÇAR
    
    print(f"Bot rodando Versão {VERSAO}")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
