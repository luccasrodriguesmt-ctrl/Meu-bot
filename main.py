import os
import sqlite3
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

# --- SERVIDOR PARA O RENDER ---
app_flask = Flask('')
@app_flask.route('/')
def home(): return "RPG ONLINE"
def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_flask.run(host='0.0.0.0', port=port)

# --- CONFIGURAÇÕES ---
TOKEN = "8506567958:AAEcFC9dkj8iwZSm_RMOJ-hfRDXlLvH2kZM"
DB_FILE = "rpg_game.db"

CLASSES = {
    "Guerreiro": {"hp": 120, "atk": 15, "def": 10},
    "Bruxa": {"hp": 80, "atk": 25, "def": 5},
    "Ladino": {"hp": 100, "atk": 18, "def": 7}
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

# --- COMANDO START ---
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    
    conn = sqlite3.connect(DB_FILE)
    p = conn.cursor().execute("SELECT nome FROM players WHERE user_id=?", (uid,)).fetchone()
    conn.close()

    if p:
        await update.message.reply_text(f"⚔️ Bem-vindo, {p[0]}! Seu herói já está pronto.")
    else:
        # Menu de Classes - Aqui o usuário só clica
        btns = [[InlineKeyboardButton(f"✨ Ser {c}", callback_data=f"set_{c}")] for c in CLASSES.keys()]
        await update.message.reply_text("🎮 **BEM-VINDO AO RPG**\nEscolha sua classe:", 
                                       reply_markup=InlineKeyboardMarkup(btns), parse_mode='Markdown')

# --- CRIAÇÃO AUTOMÁTICA (SEM PEDIR NOME) ---
async def processar_botoes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    data = query.data
    await query.answer()

    if data.startswith("set_"):
        classe_nome = data.replace("set_", "")
        info = CLASSES[classe_nome]
        
        # SALVA COM O NOME DA CLASSE DIRETO
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO players VALUES (?, ?, ?, ?, ?, ?)",
                       (uid, classe_nome, classe_nome, info['hp'], info['hp'], 50))
        conn.commit()
        conn.close()

        await query.edit_message_text(f"✅ **{classe_nome}** criado com sucesso!\n\nUse /start para ver seu status.")

# --- INICIALIZAÇÃO ---
if __name__ == '__main__':
    criar_banco()
    
    # Inicia o Flask em paralelo (Obrigatório para o Render)
    Thread(target=run_flask, daemon=True).start()
    
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CallbackQueryHandler(processar_botoes))
    
    # REPARE: Não existe MessageHandler de texto aqui. O bot não "ouve" o teclado.
    
    print("🚀 Bot RPG 100% Automático iniciado!")
    app.run_polling(drop_pending_updates=True)
