import os
import random
import sqlite3
import time
import asyncio
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

# === SERVIDOR PARA O RENDER ===
app_flask = Flask('')
@app_flask.route('/')
def home(): return "RPG Ativo"
def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_flask.run(host='0.0.0.0', port=port)

# === CONFIGURAÇÕES ===
TOKEN = "8506567958:AAEcFC9dkj8iwZSm_RMOJ-hfRDXlLvH2kZM"
DB_FILE = "rpg_game.db"

# DICIONÁRIO PARA NÃO TRAVAR NO NOME
ESTADOS_USUARIOS = {}

# --- MANTENHA SEUS DICIONÁRIOS (ITENS, MONSTROS, MAPAS, CLASSES) AQUI ---
# (O código que você já escreveu de ITENS = {...} até CLASSES = {...})

# [COLE AQUI TODO O SEU BLOCO DE 'ITENS', 'MONSTROS', 'MAPAS' E 'CLASSES']

# === BANCO DE DADOS (CUIDADO: Mantenha as funções carregar/salvar player que você já tem) ===
def criar_banco():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS players (
        user_id INTEGER PRIMARY KEY, nome TEXT, classe TEXT, level INTEGER, xp INTEGER, 
        hp_atual INTEGER, hp_max INTEGER, energia_atual INTEGER, energia_max INTEGER,
        ataque INTEGER, defesa INTEGER, gold INTEGER, vitorias INTEGER, derrotas INTEGER,
        mapa_atual TEXT, ultima_energia_update INTEGER)''')
    # Adicione as tabelas inventario, equipamentos e combate_atual conforme seu código original
    conn.commit()
    conn.close()

# === LÓGICA DE START E CRIAÇÃO ===

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    player = carregar_player(uid)
    
    if player:
        txt, kb, img = menu_principal(uid)
        await update.message.reply_photo(photo=img, caption=txt, reply_markup=kb, parse_mode='Markdown')
    else:
        # MENU DE ESCOLHA DE CLASSE
        botoes = [[InlineKeyboardButton(f"✨ {c}", callback_data=f"escolher_classe_{c}")] for c in CLASSES.keys()]
        await update.message.reply_text(
            "⚔️ **BEM-VINDO AO RPG!**\nEscolha sua classe para começar:",
            reply_markup=InlineKeyboardMarkup(botoes),
            parse_mode='Markdown'
        )

async def processar_botoes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    data = query.data
    await query.answer()

    if data.startswith("escolher_classe_"):
        classe = data.replace("escolher_classe_", "")
        # SALVA O ESTADO: "Esperando nome"
        ESTADOS_USUARIOS[uid] = {'estado': 'ESPERANDO_NOME', 'classe': classe}
        
        await query.edit_message_text(
            f"Excelente! Você escolheu **{classe}**.\n\nAgora, **digite o NOME** do seu herói aqui no chat:"
        )
    
    # ... (Mantenha o restante dos seus elif de 'cacar', 'descansar', etc.)

async def processar_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    texto = update.message.text

    # SE O BOT ESTIVER ESPERANDO O NOME:
    if uid in ESTADOS_USUARIOS and ESTADOS_USUARIOS[uid].get('estado') == 'ESPERANDO_NOME':
        classe = ESTADOS_USUARIOS[uid]['classe']
        nome = texto[:20]
        
        c_info = CLASSES[classe]
        novo_p = {
            'nome': nome, 'classe': classe, 'level': 1, 'xp': 0,
            'hp_atual': c_info['hp_base'], 'hp_max': c_info['hp_base'],
            'energia_atual': c_info['energia_base'], 'energia_max': c_info['energia_base'],
            'ataque': c_info['ataque_base'], 'defesa': c_info['defesa_base'],
            'gold': 50, 'vitorias': 0, 'derrotas': 0, 'mapa_atual': 'Planície de Aether'
        }
        
        salvar_player(uid, novo_p)
        del ESTADOS_USUARIOS[uid] # Limpa a memória
        
        await update.message.reply_text(f"✅ Herói **{nome}** criado!")
        txt, kb, img = menu_principal(uid)
        await update.message.reply_photo(photo=img, caption=txt, reply_markup=kb, parse_mode='Markdown')

# === INICIALIZAÇÃO ===
if __name__ == '__main__':
    criar_banco()
    Thread(target=run_flask, daemon=True).start() # Liga o servidor pro Render
    
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CallbackQueryHandler(processar_botoes))
    # ESSA LINHA ABAIXO PEGA O NOME QUE VOCÊ DIGITA:
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, processar_mensagem))
    
    print("🚀 Bot Online!")
    app.run_polling(stop_signals=None, drop_pending_updates=True)
