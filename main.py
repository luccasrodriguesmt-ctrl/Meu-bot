import os
import random
import sqlite3
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

# --- SERVIDOR PARA O RENDER ---
app_flask = Flask('')
@app_flask.route('/')
def home(): return "RPG Online!"
def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_flask.run(host='0.0.0.0', port=port)

# --- CONFIGURAÇÕES ---
TOKEN = "8506567958:AAEcFC9dkj8iwZSm_RMOJ-hfRDXlLvH2kZM"
DB_FILE = "rpg_game.db"

CLASSES = {
    "Guerreiro": {"hp": 120, "atk": 15, "def": 10, "img": "https://picsum.photos/seed/knight/400/300"},
    "Bruxa": {"hp": 80, "atk": 25, "def": 5, "img": "https://picsum.photos/seed/witch/400/300"},
    "Ladino": {"hp": 100, "atk": 18, "def": 7, "img": "https://picsum.photos/seed/rogue/400/300"}
}

# --- BANCO DE DADOS ---
def criar_banco():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS players (
        user_id INTEGER PRIMARY KEY, nome TEXT, classe TEXT, 
        hp_max INTEGER, hp_atual INTEGER, gold INTEGER)''')
    conn.commit()
    conn.close()

# --- FUNÇÃO DE CRIAÇÃO ---
def salvar_player(uid, nome, classe):
    info = CLASSES[classe]
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO players VALUES (?, ?, ?, ?, ?, ?)",
                   (uid, nome, classe, info['hp'], info['hp'], 50))
    conn.commit()
    conn.close()

# --- COMANDO START ---
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    
    # Verifica se já existe
    conn = sqlite3.connect(DB_FILE)
    p = conn.cursor().execute("SELECT nome FROM players WHERE user_id=?", (uid,)).fetchone()
    conn.close()

    if p:
        await update.message.reply_text(f"⚔️ Bem-vindo de volta, {p[0]}! O jogo já está rodando.")
    else:
        # Menu de Classes
        botoes = [[InlineKeyboardButton(f"✨ Ser {c}", callback_data=f"set_{c}")] for c in CLASSES.keys()]
        await update.message.reply_text(
            "🎮 **BEM-VINDO AO RPG**\n\nEscolha sua classe abaixo para começar agora:",
            reply_markup=InlineKeyboardMarkup(botoes),
            parse_mode='Markdown'
        )

# --- PROCESSAR ESCOLHA (AUTOMÁTICO) ---
async def processar_botoes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    data = query.data
    await query.answer()

    if data.startswith("set_"):
        classe_nome = data.replace("set_", "")
        
        # SALVA AUTOMÁTICO USANDO O NOME DA CLASSE
        salvar_player(uid, classe_nome, classe_nome)
        
        # MENSAGEM DE SUCESSO E INÍCIO
        await query.edit_message_text(
            f"✅ **Personagem {classe_nome} criado!**\n\nVocê já pode começar sua aventura. Use o menu para caçar!",
            parse_mode='Markdown'
        )

# --- INICIALIZAÇÃO ---
if __name__ == '__main__':
    criar_banco()
    
    # Rodar Flask para o Render não matar o bot
    Thread(target=run_flask, daemon=True).start()
    
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CallbackQueryHandler(processar_botoes))
    
    print("🚀 Bot RPG Iniciado!")
    app.run_polling(drop_pending_updates=True)
