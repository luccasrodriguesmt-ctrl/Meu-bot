import os
import random
import sqlite3
import asyncio
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

# ============================================
# SERVIDOR WEB (OBRIGATÓRIO PARA O RENDER)
# ============================================
app_flask = Flask('')

@app_flask.route('/')
def home():
    return "RPG Online Ativo!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_flask.run(host='0.0.0.0', port=port)

# ============================================
# CONFIGURAÇÕES E ITENS
# ============================================
TOKEN = "8506567958:AAFn-GXHiZWnXDCn2sVvnZ1aG43aputD2hw"
DB_FILE = "rpg_game.db"

ITENS = {
    "Espada de Madeira": {"tipo": "arma", "ataque": 3, "preco": 20, "desc": "Treino"},
    "Espada de Ferro": {"tipo": "arma", "ataque": 8, "preco": 100, "desc": "Qualidade"},
    "Espada Flamejante": {"tipo": "arma", "ataque": 15, "preco": 350, "desc": "Chamas"},
    "Roupa de Pano": {"tipo": "armadura", "defesa": 2, "preco": 15, "desc": "Simples"},
    "Armadura de Couro": {"tipo": "armadura", "defesa": 6, "preco": 80, "desc": "Leve"},
    "Armadura de Placas": {"tipo": "armadura", "defesa": 12, "preco": 300, "desc": "Pesada"},
    "Poção de Vida": {"tipo": "consumivel", "hp_recupera": 50, "preco": 30, "desc": "Cura 50"},
}

CLASSES = {
    "Guerreiro": {"img": "https://i.ibb.co/S76XpY7/warrior-pixel.png", "hp_base": 120, "energia_base": 20, "ataque_base": 15, "defesa_base": 10, "desc": "🛡️ Tanque"},
    "Bruxa": {"img": "https://i.ibb.co/m0fD8X4/mage-pixel.png", "hp_base": 80, "energia_base": 30, "ataque_base": 20, "defesa_base": 5, "desc": "🔮 Dano alto"},
    "Ladino": {"img": "https://i.ibb.co/L8Nf7yV/archer-pixel.png", "hp_base": 90, "energia_base": 25, "ataque_base": 18, "defesa_base": 7, "desc": "🗡️ Rápido"},
    "Druida": {"img": "https://i.ibb.co/L8Nf7yV/archer-pixel.png", "hp_base": 100, "energia_base": 22, "ataque_base": 12, "defesa_base": 8, "desc": "🌿 Versátil"},
}

MONSTROS = {
    "tier1": [{"nome": "Slime", "hp": 30, "ataque": 5, "gold_min": 5, "gold_max": 15, "xp": 20}],
    "tier2": [{"nome": "Orc", "hp": 80, "ataque": 15, "gold_min": 20, "gold_max": 40, "xp": 70}],
    "tier3": [{"nome": "Demônio", "hp": 120, "ataque": 30, "gold_min": 40, "gold_max": 80, "xp": 120}]
}

# ============================================
# FUNÇÕES DE BANCO DE DADOS (CORRIGIDAS)
# ============================================
def criar_banco():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS players (
        user_id INTEGER PRIMARY KEY, classe TEXT, level INTEGER, xp INTEGER, 
        hp_atual INTEGER, hp_max INTEGER, energia_atual INTEGER, energia_max INTEGER,
        ataque INTEGER, defesa INTEGER, gold INTEGER, vitorias INTEGER, derrotas INTEGER)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS inventario (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, item_nome TEXT, 
        item_tipo TEXT, quantidade INTEGER)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS equipamentos (
        user_id INTEGER PRIMARY KEY, arma TEXT, armadura TEXT)''')
    conn.commit()
    conn.close()

def carregar_player(uid):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT * FROM players WHERE user_id = ?', (uid,))
    row = c.fetchone()
    conn.close()
    if row:
        return {'classe': row[1], 'level': row[2], 'xp': row[3], 'hp_atual': row[4], 'hp_max': row[5],
                'energia_atual': row[6], 'energia_max': row[7], 'ataque': row[8], 'defesa': row[9],
                'gold': row[10], 'vitorias': row[11], 'derrotas': row[12]}
    return None

def salvar_player(uid, p):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO players VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
              (uid, p['classe'], p['level'], p['xp'], p['hp_atual'], p['hp_max'], 
               p['energia_atual'], p['energia_max'], p['ataque'], p['defesa'], 
               p['gold'], p['vitorias'], p['derrotas']))
    conn.commit()
    conn.close()

# Funções auxiliares de equipamentos
def obter_equipamentos(uid):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT arma, armadura FROM equipamentos WHERE user_id = ?', (uid,))
    res = c.fetchone()
    conn.close()
    return {"arma": res[0] if res else None, "armadura": res[1] if res else None}

def obter_inventario(uid):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT item_nome, item_tipo, quantidade FROM inventario WHERE user_id = ?', (uid,))
    itens = c.fetchall()
    conn.close()
    return [{"nome": i[0], "tipo": i[1], "quantidade": i[2]} for i in itens]

# ============================================
# LÓGICA VISUAL E MENUS
# ============================================
def criar_barra(atual, maximo, emoji):
    perc = max(0, min(1, atual / maximo))
    blocos = int(perc * 5)
    return emoji * blocos + "⬜" * (5 - blocos)

def menu_principal(uid):
    p = carregar_player(uid)
    equip = obter_equipamentos(uid)
    
    # Cálculo de bônus simplificado para o menu
    bonus_atk = ITENS[equip['arma']]['ataque'] if equip['arma'] else 0
    bonus_def = ITENS[equip['armadura']]['defesa'] if equip['armadura'] else 0

    txt = f"🏰 **PERSONAGEM** (Lv {p['level']})\n"
    txt += f"❤️ HP: {p['hp_atual']}/{p['hp_max']} {criar_barra(p['hp_atual'], p['hp_max'], '🟥')}\n"
    txt += f"⚡ EN: {p['energia_atual']}/{p['energia_max']} {criar_barra(p['energia_atual'], p['energia_max'], '🟩')}\n"
    txt += f"⚔️ ATK: {p['ataque'] + bonus_atk} | 🛡️ DEF: {p['defesa'] + bonus_def}\n💰 Gold: {p['gold']}"
    
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚔️ Caçar", callback_data='cacar'), InlineKeyboardButton("😴 Descansar", callback_data='descansar')],
        [InlineKeyboardButton("🎒 Mochila", callback_data='inventario'), InlineKeyboardButton("⚙️ Opções", callback_data='menu_config')]
    ])
    return txt, kb, CLASSES[p['classe']]['img']

# ============================================
# HANDLERS (CORREÇÃO DE MEDIA EDIT)
# ============================================
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if carregar_player(uid):
        txt, kb, img = menu_principal(uid)
        await update.message.reply_photo(photo=img, caption=txt, reply_markup=kb, parse_mode='Markdown')
    else:
        kb = InlineKeyboardMarkup([[InlineKeyboardButton(f"🛡️ {c}", callback_data=f'criar_{c}') for c in list(CLASSES.keys())[:2]],
                                   [InlineKeyboardButton(f"🔮 {c}", callback_data=f'criar_{c}') for c in list(CLASSES.keys())[2:]]])
        await update.message.reply_text("✨ **BEM-VINDO!**\nEscolha sua classe inicial:", reply_markup=kb, parse_mode='Markdown')

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id
    data = q.data
    await q.answer()

    if data.startswith('criar_'):
        cls_n = data.split('_')[1]
        c = CLASSES[cls_n]
        p = {'classe': cls_n, 'level': 1, 'xp': 0, 'hp_atual': c['hp_base'], 'hp_max': c['hp_base'],
             'energia_atual': c['energia_base'], 'energia_max': c['energia_base'], 'ataque': c['ataque_base'],
             'defesa': c['defesa_base'], 'gold': 0, 'vitorias': 0, 'derrotas': 0}
        salvar_player(uid, p)
        txt, kb, img = menu_principal(uid)
        await q.message.reply_photo(photo=img, caption=f"✅ Criado!\n\n{txt}", reply_markup=kb, parse_mode='Markdown')
        await q.message.delete()

    elif data == 'voltar':
        txt, kb, img = menu_principal(uid)
        # Tenta editar a mídia, se falhar (mesma imagem), edita apenas o texto
        try:
            await q.edit_message_media(media=InputMediaPhoto(img, caption=txt, parse_mode='Markdown'), reply_markup=kb)
        except:
            await q.edit_message_caption(caption=txt, reply_markup=kb, parse_mode='Markdown')

# ============================================
# EXECUÇÃO FINAL
# ============================================
if __name__ == '__main__':
    criar_banco()
    
    # Rodar Flask em uma thread separada
    Thread(target=run_flask, daemon=True).start()
    
    # Iniciar Bot
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CallbackQueryHandler(callback_handler))
    
    print("🚀 Bot rodando...")
    # O segredo para o Render: stop_signals=None
    app.run_polling(stop_signals=None, drop_pending_updates=True)
