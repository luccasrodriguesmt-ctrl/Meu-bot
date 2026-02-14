import random
import sqlite3
import asyncio
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

# --- SERVIDOR FANTASMA PARA O RENDER ---
app_flask = Flask('')
@app_flask.route('/')
def home(): return "RPG Online com Banco de Dados!"

def run_flask(): app_flask.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# ============================================
# CONFIGURAÇÕES
# ============================================
TOKEN = "8506567958:AAFn-GXHiZWnXDCn2sVvnZ1aG43aputD2hw"
DB_FILE = "rpg_game.db"

ITENS = {
    "Espada de Madeira": {"tipo": "arma", "ataque": 3, "preco": 20, "desc": "Treino"},
    "Espada de Ferro": {"tipo": "arma", "ataque": 8, "preco": 100, "desc": "Ferro"},
    "Armadura de Couro": {"tipo": "armadura", "defesa": 6, "preco": 80, "desc": "Leve"},
    "Poção de Vida": {"tipo": "consumivel", "hp_recupera": 50, "preco": 30, "desc": "+50 HP"},
}

# ============================================
# CLASSES DE PERSONAGEM (LISTA COMPLETA)
# ============================================
CLASSES = {
    "Guerreiro": {"img": "https://picsum.photos/seed/knight/400/300", "hp_base": 120, "energia_base": 20, "ataque_base": 15, "defesa_base": 10, "desc": "🛡️ Tanque resistente"},
    "Bruxa": {"img": "https://picsum.photos/seed/witch/400/300", "hp_base": 80, "energia_base": 30, "ataque_base": 20, "defesa_base": 5, "desc": "🔮 Dano mágico alto"},
    "Ladino": {"img": "https://picsum.photos/seed/rogue/400/300", "hp_base": 90, "energia_base": 25, "ataque_base": 18, "defesa_base": 7, "desc": "🗡️ Ágil e crítico"},
    "Druida": {"img": "https://picsum.photos/seed/druid/400/300", "hp_base": 100, "energia_base": 22, "ataque_base": 12, "defesa_base": 8, "desc": "🌿 Equilibrado"},
    "Feiticeiro": {"img": "https://picsum.photos/seed/mage/400/300", "hp_base": 75, "energia_base": 35, "ataque_base": 25, "defesa_base": 4, "desc": "✨ Poder bruto"},
    "Monge": {"img": "https://picsum.photos/seed/monk/400/300", "hp_base": 110, "energia_base": 20, "ataque_base": 16, "defesa_base": 9, "desc": "🧘 Força interior"},
    "Bêbado": {"img": "https://picsum.photos/seed/beer/400/300", "hp_base": 150, "energia_base": 10, "ataque_base": 10, "defesa_base": 12, "desc": "🍺 Resistência bizarra"}
}

MONSTROS = {
    "tier1": [{"nome": "Slime", "hp": 30, "ataque": 5, "gold_min": 5, "gold_max": 15, "xp": 20}],
    "tier2": [{"nome": "Orc", "hp": 80, "ataque": 15, "gold_min": 20, "gold_max": 40, "xp": 70}],
    "tier3": [{"nome": "Dragão", "hp": 150, "ataque": 25, "gold_min": 50, "gold_max": 100, "xp": 150}]
}

# ============================================
# BANCO DE DADOS (SQLite)
# ============================================
def criar_banco():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS players (
        user_id INTEGER PRIMARY KEY, classe TEXT, level INTEGER, xp INTEGER, 
        hp_atual INTEGER, hp_max INTEGER, energia_atual INTEGER, energia_max INTEGER,
        ataque INTEGER, defesa INTEGER, gold INTEGER, vitorias INTEGER, derrotas INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS inventario (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, item_nome TEXT, item_tipo TEXT, quantidade INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS equipamentos (user_id INTEGER PRIMARY KEY, arma TEXT, armadura TEXT)''')
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

def salvar_player(uid, d):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO players VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
              (uid, d['classe'], d['level'], d['xp'], d['hp_atual'], d['hp_max'], 
               d['energia_atual'], d['energia_max'], d['ataque'], d['defesa'], d['gold'], d['vitorias'], d['derrotas']))
    conn.commit()
    conn.close()

# ============================================
# LÓGICA VISUAL E MENUS
# ============================================
def criar_barra(atual, maximo, emoji):
    perc = atual / maximo if maximo > 0 else 0
    cheios = int(perc * 5)
    return emoji * cheios + "⬜" * (5 - cheios)

def menu_principal(uid):
    p = carregar_player(uid)
    txt = f"🏰 **Planície** (Lv {p['level']})\n👤 {p['classe']}\n" \
          f"❤️ {p['hp_atual']}/{p['hp_max']} {criar_barra(p['hp_atual'], p['hp_max'], '🟥')}\n" \
          f"⚡ {p['energia_atual']}/{p['energia_max']} {criar_barra(p['energia_atual'], p['energia_max'], '🟩')}\n" \
          f"💰 Gold: {p['gold']} | ⭐ XP: {p['xp']}"
    
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚔️ Caçar", callback_data='cacar'), InlineKeyboardButton("😴 Descansar", callback_data='descansar')],
        [InlineKeyboardButton("🎒 Inventário", callback_data='n'), InlineKeyboardButton("⚙️ Menu", callback_data='menu_config')]
    ])
    return txt, kb, CLASSES[p['classe']]['img']

# ============================================
# HANDLERS
# ============================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    player = carregar_player(uid)
    if player:
        txt, kb, img = menu_principal(uid)
        await context.bot.send_photo(chat_id=uid, photo=img, caption=txt, reply_markup=kb, parse_mode='Markdown')
    else:
        kb = [
            [InlineKeyboardButton("🛡️ Guerreiro", callback_data='criar_Guerreiro'), InlineKeyboardButton("🧙 Bruxa", callback_data='criar_Bruxa')],
            [InlineKeyboardButton("🗡️ Ladino", callback_data='criar_Ladino'), InlineKeyboardButton("🌿 Druida", callback_data='criar_Druida')],
            [InlineKeyboardButton("✨ Feiticeiro", callback_data='criar_Feiticeiro'), InlineKeyboardButton("🧘 Monge", callback_data='criar_Monge')],
            [InlineKeyboardButton("🍺 Bêbado", callback_data='criar_Bêbado')]
        ]
        await context.bot.send_photo(chat_id=uid, photo="https://picsum.photos/seed/start/400/300", 
                                   caption="✨ **RPG BATTLE**\nEscolha sua classe:", reply_markup=InlineKeyboardMarkup(kb))

async def processar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id
    await q.answer()

    if q.data.startswith('criar_'):
        cl_nome = q.data.replace('criar_', '')
        cl = CLASSES[cl_nome]
        salvar_player(uid, {'classe': cl_nome, 'level': 1, 'xp': 0, 'hp_atual': cl['hp_base'], 'hp_max': cl['hp_base'],
                           'energia_atual': cl['energia_base'], 'energia_max': cl['energia_base'],
                           'ataque': cl['ataque_base'], 'defesa': cl['defesa_base'], 'gold': 0, 'vitorias': 0, 'derrotas': 0})
        txt, kb, img = menu_principal(uid)
        await q.edit_message_media(InputMediaPhoto(img))
        await q.edit_message_caption(caption=f"✅ Criado!\n\n{txt}", reply_markup=kb, parse_mode='Markdown')

    elif q.data == 'descansar':
        p = carregar_player(uid)
        p['hp_atual'] = p['hp_max']
        p['energia_atual'] = p['energia_max']
        salvar_player(uid, p)
        txt, kb, _ = menu_principal(uid)
        await q.edit_message_caption(caption="😴 Totalmente recuperado!\n\n"+txt, reply_markup=kb, parse_mode='Markdown')

    elif q.data == 'menu_config':
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Resetar", callback_data='reset')], [InlineKeyboardButton("◀️ Voltar", callback_data='voltar')]])
        await q.edit_message_caption(caption="⚙️ Opções:", reply_markup=kb)

    elif q.data == 'reset':
        conn = sqlite3.connect(DB_FILE)
        conn.cursor().execute('DELETE FROM players WHERE user_id = ?', (uid,))
        conn.commit()
        conn.close()
        await q.edit_message_caption(caption="🗑️ Personagem deletado! Use /start")

    elif q.data == 'voltar':
        txt, kb, _ = menu_principal(uid)
        await q.edit_message_caption(caption=txt, reply_markup=kb, parse_mode='Markdown')

if __name__ == '__main__':
    criar_banco()
    keep_alive()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(processar))
    app.run_polling(close_loop=False)
