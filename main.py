import os
import sqlite3
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

# --- SERVIDOR PARA O RENDER NÃO DAR ERRO ---
app_flask = Flask('')
@app_flask.route('/')
def home(): return "RPG VIVO"
def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_flask.run(host='0.0.0.0', port=port)

# --- CONFIGURAÇÃO ---
TOKEN = "8506567958:AAEKQHo-TsjW55WeKGwiqVvLYglEWQusxdg"
DB_FILE = "rpg_novo.db"

CLASSES = {
    "Guerreiro": {"hp": 150, "atk": 15},
    "Mago": {"hp": 90, "atk": 25},
    "Arqueiro": {"hp": 110, "atk": 20}
}

# --- BANCO DE DADOS ---
def iniciar_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute('''CREATE TABLE IF NOT EXISTS players 
        (id INTEGER PRIMARY KEY, nome TEXT, classe TEXT, hp INTEGER)''')
    conn.commit()
    conn.close()

# --- COMANDO START ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    conn = sqlite3.connect(DB_FILE)
    p = conn.cursor().execute("SELECT nome FROM players WHERE id=?", (uid,)).fetchone()
    conn.close()

    if p:
        await update.message.reply_text(f"⚔️ Seu personagem {p[0]} já está pronto!")
    else:
        # Só botões, sem campo de texto
        botoes = [[InlineKeyboardButton(f"✨ Escolher {c}", callback_data=f"c_{c}")] for c in CLASSES.keys()]
        await update.message.reply_text("🎮 **NOVO JOGO**\nEscolha sua classe:", 
                                       reply_markup=InlineKeyboardMarkup(botoes), parse_mode='Markdown')

# --- CRIAÇÃO NO CLIQUE (O SEGREDO) ---
async def botao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    data = query.data
    await query.answer()

    if data.startswith("c_"):
        classe = data.replace("c_", "")
        hp = CLASSES[classe]["hp"]
        
        # GRAVA DIRETO NO BANCO COM O NOME DA CLASSE
        conn = sqlite3.connect(DB_FILE)
        conn.execute("INSERT OR REPLACE INTO players VALUES (?, ?, ?, ?)", (uid, classe, classe, hp))
        conn.commit()
        conn.close()

        await query.edit_message_text(f"✅ Personagem **{classe}** criado com sucesso!\nUse /start para ver.")

# --- INICIAR TUDO ---
if __name__ == '__main__':
    iniciar_db()
    Thread(target=run_flask, daemon=True).start()
    
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(botao))
    
    print("🚀 BOT NOVO INICIADO!")
    app.run_polling(drop_pending_updates=True)
