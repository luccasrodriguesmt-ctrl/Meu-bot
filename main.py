import os
import random
import sqlite3
import time
import asyncio
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

# ============================================
# SERVIDOR WEB (PARA O RENDER MANTER ONLINE)
# ============================================
app_flask = Flask('')
@app_flask.route('/')
def home(): return "RPG Online Ativo!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_flask.run(host='0.0.0.0', port=port)

# ============================================
# CONFIGURAÇÕES
# ============================================
TOKEN = "8506567958:AAEcFC9dkj8iwZSm_RMOJ-hfRDXlLvH2kZM"
DB_FILE = "rpg_game.db"

# Memória temporária para criação de nome
ESTADOS_USUARIOS = {}

# Copie aqui seus dicionários (ITENS, MONSTROS, CLASSES, MAPAS) 
# que você já tem no seu código original...
# [MANTENHA OS DICIONÁRIOS QUE VOCÊ JÁ TINHA]

CLASSES = {
    "Guerreiro": {"hp_base": 120, "energia_base": 20, "ataque_base": 15, "defesa_base": 10, "img": "https://picsum.photos/seed/knight/400/300"},
    "Bruxa": {"hp_base": 80, "energia_base": 30, "ataque_base": 20, "defesa_base": 5, "img": "https://picsum.photos/seed/witch/400/300"},
    "Ladino": {"hp_base": 90, "energia_base": 25, "ataque_base": 18, "defesa_base": 7, "img": "https://picsum.photos/seed/rogue/400/300"},
    "Druida": {"hp_base": 100, "energia_base": 22, "ataque_base": 12, "defesa_base": 8, "img": "https://picsum.photos/seed/druid/400/300"},
}

# [AQUI VÃO AS FUNÇÕES DE BANCO DE DADOS QUE VOCÊ JÁ TEM: criar_banco, salvar_player, carregar_player, etc.]

# ============================================
# LÓGICA DE INÍCIO E NOME (A PARTE QUE TRAVAVA)
# ============================================

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    player = carregar_player(uid)
    
    if player:
        txt, kb, img = menu_principal(uid)
        await update.message.reply_photo(photo=img, caption=txt, reply_markup=kb, parse_mode='Markdown')
    else:
        # Primeira vez: Escolher Classe
        botoes = []
        for nome_classe in CLASSES.keys():
            botoes.append([InlineKeyboardButton(f"✨ {nome_classe}", callback_data=f"sel_classe_{nome_classe}")])
        
        reply_markup = InlineKeyboardMarkup(botoes)
        await update.message.reply_text(
            "🎮 **BEM-VINDO AO RPG!**\n\nPara começar sua jornada, escolha uma classe abaixo:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def processar_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    texto = update.message.text

    # Se o bot estava esperando o nome do personagem:
    if uid in ESTADOS_USUARIOS and ESTADOS_USUARIOS[uid]['estado'] == 'ESPERANDO_NOME':
        classe = ESTADOS_USUARIOS[uid]['classe']
        nome_escolhido = texto[:20] # Limita o nome
        
        c_info = CLASSES[classe]
        novo_player = {
            'nome': nome_escolhido,
            'classe': classe,
            'level': 1, 'xp': 0,
            'hp_max': c_info['hp_base'], 'hp_atual': c_info['hp_base'],
            'energia_max': c_info['energia_base'], 'energia_atual': c_info['energia_base'],
            'ataque': c_info['ataque_base'], 'defesa': c_info['defesa_base'],
            'gold': 50, 'vitorias': 0, 'derrotas': 0, 'mapa_atual': 'Planície de Aether'
        }
        
        salvar_player(uid, novo_player)
        del ESTADOS_USUARIOS[uid] # Limpa a memória temporária
        
        await update.message.reply_text(f"✅ Personagem **{nome_escolhido}** criado com sucesso!")
        txt, kb, img = menu_principal(uid)
        await update.message.reply_photo(photo=img, caption=txt, reply_markup=kb, parse_mode='Markdown')
        return

async def processar_botoes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    data = query.data
    await query.answer()

    # Quando o usuário clica na classe:
    if data.startswith("sel_classe_"):
        classe_nome = data.replace("sel_classe_", "")
        # Salva a intenção e pede o nome
        ESTADOS_USUARIOS[uid] = {'estado': 'ESPERANDO_NOME', 'classe': classe_nome}
        
        await query.edit_message_text(
            f"Você escolheu: **{classe_nome}**!\n\nAgora, **digite o nome** do seu personagem aqui no chat:",
            parse_mode='Markdown'
        )
    
    # [AQUI CONTINUAM OS SEUS OUTROS 'ELIF' DE COMBATE, CAÇAR, INVENTÁRIO...]

# ============================================
# INICIALIZAÇÃO CORRIGIDA
# ============================================
if __name__ == '__main__':
    criar_banco()
    
    # Rodar Flask em segundo plano para o Render
    Thread(target=run_flask, daemon=True).start()
    
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Handlers (Onde o bot aprende a responder)
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CallbackQueryHandler(processar_botoes))
    # Esta linha abaixo é a que resolve o travamento do nome:
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, processar_mensagem))
    
    print("🚀 Bot iniciado!")
    # Configuração vital para o Render não dar erro
    app.run_polling(stop_signals=None, drop_pending_updates=True)
