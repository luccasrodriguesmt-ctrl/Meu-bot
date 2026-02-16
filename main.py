import os, random, sqlite3, logging, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters, ConversationHandler

VERSAO = "2.2.0 - "
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- SERVIDOR PARA MANTER ONLINE ---
def run_fake_server():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Online!")
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(('0.0.0.0', port), Handler).serve_forever()

threading.Thread(target=run_fake_server, daemon=True).start()

DB_FILE = "rpg_game.db"
IMG = "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/Gemini_Generated_Image_n68a2ln68a2ln68a.png?raw=true"

IMAGENS = {
    "logo": "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/WhatsApp%20Image%202026-02-15%20at%2009.06.10.jpeg?raw=true",
    "sel": "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/Gemini_Generated_Image_l46bisl46bisl46b.png?raw=true",
    "classes": {
        "Guerreiro": "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/Gemini_Generated_Image_n68a2ln68a2ln68a.png?raw=true",
        "Arqueiro": "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/Gemini_Generated_Image_o1dtmio1dtmio1dt.png?raw=true",
        "Bruxa": "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/Gemini_Generated_Image_fyofu7fyofu7fyof.png?raw=true",
        "Mago": "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/Gemini_Generated_Image_8nad348nad348nad.png?raw=true"
    }
}

CLASSES_STATS = {
    "Guerreiro": {"hp": 250, "hp_max": 250, "mana": 0, "mana_max": 0, "def_b": 18, "crit": 0.05},
    "Arqueiro": {"hp": 150, "hp_max": 150, "mana": 0, "mana_max": 0, "def_b": 8, "crit": 0.25},
    "Bruxa": {"hp": 120, "hp_max": 120, "mana": 100, "mana_max": 100, "def_b": 5, "crit": 0.10},
    "Mago": {"hp": 110, "hp_max": 110, "mana": 120, "mana_max": 120, "def_b": 4, "crit": 0.15}
}

MAPAS = {
    1: {"nome": "Planície", "lv": 1, "loc": {"cap": {"nome": "Capital Real", "loja": "normal"}, "v1": {"nome": "Vila Norte", "loja": "normal"}, "v2": {"nome": "Povoado Sul", "loja": "contra"}}},
    2: {"nome": "Floresta", "lv": 5, "loc": {"cap": {"nome": "Forte Floresta", "loja": "normal"}, "v1": {"nome": "Acampamento", "loja": "normal"}, "v2": {"nome": "Refúgio", "loja": "contra"}}},
    3: {"nome": "Caverna", "lv": 10, "loc": {"cap": {"nome": "Cidade Sub", "loja": "normal"}, "v1": {"nome": "Mina", "loja": "contra"}, "v2": {"nome": "Forte Anão", "loja": "normal"}}}
}

INIMIGOS = {
    "Goblin": {"hp": 30, "atk": 8, "def": 2, "xp": 25, "gold": 15, "desc": "Criatura maliciosa", "m": [1]},
    "Lobo": {"hp": 45, "atk": 12, "def": 4, "xp": 40, "gold": 25, "desc": "Predador feroz", "m": [1,2]},
    "Orc": {"hp": 80, "atk": 20, "def": 8, "xp": 80, "gold": 60, "desc": "Guerreiro brutal", "m": [2,3]},
    "Dragão": {"hp": 200, "atk": 40, "def": 15, "xp": 300, "gold": 250, "desc": "Besta lendária", "m": [3]}
}

EQUIPS = {
    "Espada Ferro": {"t": "arma", "atk": 15, "p": 200, "lv": 5, "cls": ["Guerreiro"]},
    "Arco Longo": {"t": "arma", "atk": 20, "p": 250, "lv": 5, "cls": ["Arqueiro"]},
    "Cajado Cristal": {"t": "arma", "atk": 25, "p": 400, "lv": 8, "cls": ["Mago", "Bruxa"]},
    "Arm Couro": {"t": "arm", "def": 5, "p": 50, "lv": 1, "cls": "todos"}
}

ST_CL, ST_NM = range(2)

# --- BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS players 
                 (id INTEGER PRIMARY KEY, nome TEXT, classe TEXT, hp INTEGER, hp_max INTEGER, 
                  lv INTEGER, exp INTEGER, gold INTEGER, energia INTEGER, energia_max INTEGER,
                  mapa INTEGER DEFAULT 1, local TEXT DEFAULT 'cap',
                  arma TEXT, arm TEXT, atk_b INTEGER DEFAULT 0, def_b INTEGER DEFAULT 0)''')
    try:
        c.execute("ALTER TABLE players ADD COLUMN mana INTEGER DEFAULT 0")
        c.execute("ALTER TABLE players ADD COLUMN mana_max INTEGER DEFAULT 0")
    except: pass
    c.execute('''CREATE TABLE IF NOT EXISTS inv (pid INTEGER, item TEXT, qtd INTEGER DEFAULT 1, PRIMARY KEY (pid, item))''')
    c.execute('''CREATE TABLE IF NOT EXISTS dung (pid INTEGER, did INTEGER, PRIMARY KEY (pid, did))''')
    conn.commit()
    conn.close()

def get_p(uid):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    p = conn.execute("SELECT * FROM players WHERE id = ?", (uid,)).fetchone()
    conn.close()
    return p

# --- UTILITÁRIOS ---
def barra(a, m, c="🟦"):
    if m <= 0: return "⬜"*10
    p = max(0, min(a/m, 1))
    return c*int(p*10) + "⬜"*(10-int(p*10))

def atk(p): return 10 + (p['lv']*2) + p['atk_b']
def deff(p): return 5 + p['lv'] + p['def_b']

# --- SISTEMA DE COMBATE ---
async def cacar(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    p = get_p(uid)
    if p['energia'] < 2:
        await q.answer("🪫 Sem energia!", show_alert=True)
        return
    inims = [n for n, d in INIMIGOS.items() if p['mapa'] in d['m']]
    inm_n = random.choice(inims)
    ini = INIMIGOS[inm_n]
    ctx.user_data['luta'] = {'inimigo': inm_n, 'i_hp': ini['hp'], 'i_hp_max': ini['hp'], 'i_atk': ini['atk'], 'i_def': ini['def'], 'turno': 1, 'log': f"⚔️ Um {inm_n} apareceu!"}
    await renderizar_combate(upd, ctx)

async def renderizar_combate(upd, ctx):
    p = get_p(upd.effective_user.id)
    luta = ctx.user_data.get('luta')
    cap = f"⚔️ **TURNO {luta['turno']}**\n{'━'*20}\n👾 **{luta['inimigo']}**\n❤️ HP: {luta['i_hp']}/{luta['i_hp_max']}\n└ {barra(luta['i_hp'], luta['i_hp_max'], '🟥')}\n\n👤 **{p['nome']}**\n❤️ HP: {p['hp']}/{p['hp_max']}\n└ {barra(p['hp'], p['hp_max'], '🟩')}\n"
    if p['mana_max'] > 0:
        cap += f"✨ MP: {p['mana']}/{p['mana_max']}\n└ {barra(p['mana'], p['mana_max'], '🟦')}\n"
    cap += f"\n📜 {luta['log']}"
    kb = [[InlineKeyboardButton("⚔️ Ataque", callback_data="acao_atacar"), InlineKeyboardButton("🛡️ Defesa", callback_data="acao_defender")]]
    if p['mana_max'] > 0: kb.append([InlineKeyboardButton("🔥 Magia", callback_data="acao_especial")])
    kb.append([InlineKeyboardButton("🏳️ Fugir", callback_data="voltar")])
    await upd.callback_query.edit_message_caption(caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def processar_combate(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    p = get_p(uid)
    luta = ctx.user_data.get('luta')
    if not luta: return
    
    msg = ""
    if q.data == "acao_atacar":
        crit = CLASSES_STATS[p['classe']]['crit']
        d = max(1, (atk(p) - luta['i_def']) + random.randint(-2, 2))
        if random.random() < crit: d *= 2; msg = f"🎯 CRÍTICO! Dano: {d}"
        else: msg = f"⚔️ Você causou {d} de dano!"
        luta['i_hp'] -= d

    if luta['i_hp'] > 0:
        di = max(1, (luta['i_atk'] - deff(p)) + random.randint(-2, 2))
        if q.data == "acao_defender": di = int(di * 0.3); msg += "\n🛡️ Defendeu!"
        novo_hp = max(0, p['hp'] - di)
        conn = sqlite3.connect(DB_FILE); conn.execute("UPDATE players SET hp=? WHERE id=?", (novo_hp, uid)); conn.commit(); conn.close()
        msg += f"\n↘️ Dano recebido: {di}"

    luta['log'] = msg; luta['turno'] += 1
    if luta['i_hp'] <= 0: await finalizar_combate(upd, ctx, True)
    elif get_p(uid)['hp'] <= 0: await finalizar_combate(upd, ctx, False)
    else: await renderizar_combate(upd, ctx)

async def acao_especial(upd, ctx):
    uid = upd.effective_user.id
    p = get_p(uid)
    luta = ctx.user_data.get('luta')
    if p['mana'] < 20: await upd.callback_query.answer("Sem Mana!", show_alert=True); return
    d = (atk(p) * 2) + 10
    luta['i_hp'] -= d
    conn = sqlite3.connect(DB_FILE); conn.execute("UPDATE players SET mana=mana-20 WHERE id=?", (uid,)); conn.commit(); conn.close()
    luta['log'] = f"🔥 Magia causou {d} de dano!"; luta['turno'] += 1
    if luta['i_hp'] <= 0: await finalizar_combate(upd, ctx, True)
    else: await renderizar_combate(upd, ctx)

async def finalizar_combate(upd, ctx, vit):
    uid = upd.effective_user.id
    luta = ctx.user_data.get('luta')
    ini = INIMIGOS[luta['inimigo']]
    if vit:
        g, x = ini['gold']+random.randint(-5,5), ini['xp']+random.randint(-5,5)
        conn = sqlite3.connect(DB_FILE); conn.execute("UPDATE players SET gold=gold+?, exp=exp+?, energia=energia-2 WHERE id=?", (g,x,uid)); conn.commit(); conn.close()
        res = f"🏆 Vitória!\n💰 +{g} Gold | ✨ +{x} XP"
    else:
        conn = sqlite3.connect(DB_FILE); conn.execute("UPDATE players SET hp=1, energia=energia-2 WHERE id=?", (uid,)); conn.commit(); conn.close()
        res = "💀 Derrota!"
    ctx.user_data.pop('luta', None)
    await upd.callback_query.edit_message_caption(caption=res, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data="voltar")]]), parse_mode='Markdown')

# --- MENUS E CRIAÇÃO ---
async def start(upd, ctx):
    p = get_p(upd.effective_user.id)
    if p: await menu(upd, ctx, p['id']); return ConversationHandler.END
    await upd.message.reply_photo(IMAGENS["logo"], caption="✨ Bem-vindo!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎮 Começar", callback_data="ir_cls")]]))
    return ST_CL

async def menu_cls(upd, ctx):
    await upd.callback_query.message.delete()
    await ctx.bot.send_photo(upd.effective_chat.id, IMAGENS["sel"], caption="🎭 Classe:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛡️ Guerreiro", callback_data="Guerreiro"), InlineKeyboardButton("🏹 Arqueiro", callback_data="Arqueiro")], [InlineKeyboardButton("🔮 Bruxa", callback_data="Bruxa"), InlineKeyboardButton("🔥 Mago", callback_data="Mago")]]))
    return ST_NM

async def salv_nm(upd, ctx):
    ctx.user_data['classe'] = upd.callback_query.data
    await upd.callback_query.message.delete()
    await ctx.bot.send_photo(upd.effective_chat.id, IMAGENS["classes"][ctx.user_data['classe']], caption="Digite seu nome:")
    return ST_NM

async def fin(upd, ctx):
    uid, nome, cl = upd.effective_user.id, upd.message.text, ctx.user_data['classe']
    s = CLASSES_STATS[cl]
    conn = sqlite3.connect(DB_FILE); conn.execute("INSERT OR REPLACE INTO players (id, nome, classe, hp, hp_max, lv, exp, gold, energia, energia_max, def_b, mana, mana_max) VALUES (?,?,?,?,?,1,0,100,20,20,?,?,?)", (uid, nome, cl, s['hp'], s['hp_max'], s['def_b'], s['mana'], s['mana_max'])); conn.commit(); conn.close()
    await menu(upd, ctx, uid)
    return ConversationHandler.END

async def menu(upd, ctx, uid):
    p = get_p(uid)
    cap = f"👤 **{p['nome']}** ({p['classe']})\n❤️ HP: {p['hp']}/{p['hp_max']}\n{barra(p['hp'],p['hp_max'],'🟥')}\n"
    if p['mana_max'] > 0: cap += f"✨ MP: {p['mana']}/{p['mana_max']}\n{barra(p['mana'],p['mana_max'],'🟦')}\n"
    cap += f"💰 {p['gold']} | ⚡ {p['energia']}"
    kb = [[InlineKeyboardButton("⚔️ Caçar", callback_data="cacar")], [InlineKeyboardButton("⚙️ Reset", callback_data="rst_c")]]
    if upd.callback_query: await upd.callback_query.edit_message_caption(caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    else: await upd.message.reply_photo(IMAGENS["classes"][p['classe']], caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def voltar(upd, ctx): await menu(upd, ctx, upd.effective_user.id)

def main():
    init_db()
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()
    conv = ConversationHandler(entry_points=[CommandHandler('start', start)], states={ST_CL: [CallbackQueryHandler(menu_cls, pattern='^ir_cls$')], ST_NM: [CallbackQueryHandler(salv_nm), MessageHandler(filters.TEXT & ~filters.COMMAND, fin)]}, fallbacks=[CommandHandler('start', start)])
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(cacar, pattern='^cacar$'))
    app.add_handler(CallbackQueryHandler(voltar, pattern='^voltar$'))
    app.add_handler(CallbackQueryHandler(processar_combate, pattern='^acao_atacar$|^acao_defender$'))
    app.add_handler(CallbackQueryHandler(acao_especial, pattern='^acao_especial$'))
    app.run_polling()

if __name__ == '__main__': main()
