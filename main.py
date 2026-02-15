"""
🎮 BOT RPG TELEGRAM - VERSÃO FINAL SEM BUG
CORREÇÃO: Nome padrão gerado automaticamente, pode mudar depois no perfil
"""

import os
import random
import sqlite3
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

# ============================================
# CONFIGURAÇÕES
# ============================================
TOKEN = "8506567958:AAEcFC9dkj8iwZSm_RMOJ-hfRDXlLvH2kZM"
DB_FILE = "rpg_game.db"

# Cole todo o resto do código do documento aqui...
# (ITENS, MONSTROS, CLASSES, MAPAS, etc - tudo igual)

# A ÚNICA mudança é no handler de criar personagem:

async def processar_botoes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa cliques nos botões"""
    q = update.callback_query
    uid = q.from_user.id
    await q.answer()
    
    # ===== CRIAR PERSONAGEM (SEM PEDIR NOME) =====
    if q.data.startswith('criar_'):
        classe_nome = q.data.replace('criar_', '')
        classe = CLASSES[classe_nome]
        
        # Gerar nome padrão baseado no ID do usuário
        nome_padrao = f"Guerreiro{uid % 10000}"
        
        # Criar personagem IMEDIATAMENTE
        novo_player = {
            'nome': nome_padrao,
            'classe': classe_nome,
            'level': 1,
            'xp': 0,
            'hp_atual': classe['hp_base'],
            'hp_max': classe['hp_base'],
            'energia_atual': classe['energia_base'],
            'energia_max': classe['energia_base'],
            'ataque': classe['ataque_base'],
            'defesa': classe['defesa_base'],
            'gold': 50,
            'vitorias': 0,
            'derrotas': 0,
            'mapa_atual': 'Planície de Aether',
            'ultima_energia_update': int(time.time())
        }
        
        salvar_player(uid, novo_player)
        
        # Dar itens iniciais
        adicionar_item(uid, "Espada de Madeira", 1)
        adicionar_item(uid, "Roupa de Pano", 1)
        adicionar_item(uid, "Poção de Vida", 3)
        
        txt, kb, img = menu_principal(uid)
        
        await q.edit_message_media(media=InputMediaPhoto(img))
        await q.edit_message_caption(
            caption=f"""✅ **Bem-vindo, {nome_padrao}!**

Você é agora um **{classe_nome}**!

🎁 Itens iniciais recebidos!
💰 Você começa com 50 gold!

💡 **Dica:** Vá em Perfil → Mudar Nome para personalizar!

{txt}""",
            reply_markup=kb,
            parse_mode='Markdown'
        )
        return
    
    # ... resto do código continua igual
