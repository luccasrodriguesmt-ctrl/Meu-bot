import os, random, sqlite3, logging, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters, ConversationHandler

VERSAO = "3.0.0 - Sistema Avançado"
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def run_fake_server():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"Bot Online!")
        def log_message(self, format, *args): pass
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), Handler)
    logging.info(f"HTTP Server on port {port}")
    server.serve_forever()

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

# Atributos base por classe
CLASSE_STATS = {
    "Guerreiro": {"hp": 250, "mana": 0, "atk": 15, "def": 18, "crit": 0, "double": False, "especial": None},
    "Arqueiro": {"hp": 120, "mana": 0, "atk": 20, "def": 8, "crit": 25, "double": True, "especial": None},
    "Bruxa": {"hp": 150, "mana": 100, "atk": 18, "def": 10, "crit": 10, "double": False, "especial": "maldição"},
    "Mago": {"hp": 130, "mana": 120, "atk": 25, "def": 8, "crit": 15, "double": False, "especial": "explosão"}
}

MAPAS = {
    1: {"nome": "Planície", "lv": 1, "aviso": "", "loc": {
        "cap": {"nome": "Capital Real", "loja": "normal"},
        "v1": {"nome": "Vila Norte", "loja": "normal"},
        "v2": {"nome": "Povoado Sul", "loja": "contra"}
    }},
    2: {"nome": "Floresta Sombria", "lv": 5, "aviso": "⚠️ Região Perigosa - Lv 5+", "loc": {
        "cap": {"nome": "Forte Floresta", "loja": "normal"},
        "v1": {"nome": "Acampamento", "loja": "normal"},
        "v2": {"nome": "Refúgio", "loja": "contra"}
    }},
    3: {"nome": "Caverna Profunda", "lv": 10, "aviso": "🔥 Região Mortal - Lv 10+", "loc": {
        "cap": {"nome": "Cidade Subterrânea", "loja": "normal"},
        "v1": {"nome": "Mina Abandonada", "loja": "contra"},
        "v2": {"nome": "Forte Anão", "loja": "normal"}
    }}
}

INIMIGOS = {
    "Goblin": {"hp": 30, "atk": 8, "def": 2, "xp": 25, "gold": 15, "desc": "Criatura verde maliciosa", "m": [1]},
    "Lobo": {"hp": 45, "atk": 12, "def": 4, "xp": 40, "gold": 25, "desc": "Predador feroz", "m": [1,2]},
    "Orc": {"hp": 80, "atk": 20, "def": 8, "xp": 80, "gold": 60, "desc": "Guerreiro brutal", "m": [2,3]},
    "Esqueleto": {"hp": 60, "atk": 15, "def": 5, "xp": 70, "gold": 50, "desc": "Morto-vivo", "m": [2,3]},
    "Dragão": {"hp": 200, "atk": 40, "def": 15, "xp": 300, "gold": 250, "desc": "Besta lendária", "m": [3]}
}

# Equipamentos específicos por classe
EQUIPS = {
    # Guerreiro
    "Espada Enferrujada": {"t": "arma", "atk": 5, "p": 50, "lv": 1, "cls": ["Guerreiro"]},
    "Espada de Ferro": {"t": "arma", "atk": 15, "p": 200, "lv": 5, "cls": ["Guerreiro"]},
    "Espada de Aço": {"t": "arma", "atk": 30, "p": 500, "lv": 10, "cls": ["Guerreiro"]},
    "Escudo de Madeira": {"t": "arm", "def": 8, "p": 50, "lv": 1, "cls": ["Guerreiro"]},
    "Escudo de Ferro": {"t": "arm", "def": 18, "p": 200, "lv": 5, "cls": ["Guerreiro"]},
    "Escudo de Aço": {"t": "arm", "def": 35, "p": 500, "lv": 10, "cls": ["Guerreiro"]},
    
    # Arqueiro
    "Arco Simples": {"t": "arma", "atk": 8, "p": 50, "lv": 1, "cls": ["Arqueiro"]},
    "Arco Composto": {"t": "arma", "atk": 18, "p": 200, "lv": 5, "cls": ["Arqueiro"]},
    "Arco Élfico": {"t": "arma", "atk": 35, "p": 500, "lv": 10, "cls": ["Arqueiro"]},
    "Armadura Leve": {"t": "arm", "def": 5, "p": 50, "lv": 1, "cls": ["Arqueiro"]},
    "Couro Reforçado": {"t": "arm", "def": 12, "p": 200, "lv": 5, "cls": ["Arqueiro"]},
    "Manto Sombrio": {"t": "arm", "def": 20, "p": 500, "lv": 10, "cls": ["Arqueiro"]},
    
    # Bruxa
    "Cajado Antigo": {"t": "arma", "atk": 7, "p": 50, "lv": 1, "cls": ["Bruxa"]},
    "Cetro Lunar": {"t": "arma", "atk": 17, "p": 200, "lv": 5, "cls": ["Bruxa"]},
    "Varinha das Trevas": {"t": "arma", "atk": 32, "p": 500, "lv": 10, "cls": ["Bruxa"]},
    "Robe Místico": {"t": "arm", "def": 6, "p": 50, "lv": 1, "cls": ["Bruxa"]},
    "Manto Encantado": {"t": "arm", "def": 14, "p": 200, "lv": 5, "cls": ["Bruxa"]},
    "Vestes Arcanas": {"t": "arm", "def": 22, "p": 500, "lv": 10, "cls": ["Bruxa"]},
    
    # Mago
    "Bastão Iniciante": {"t": "arma", "atk": 10, "p": 50, "lv": 1, "cls": ["Mago"]},
    "Orbe de Fogo": {"t": "arma", "atk": 22, "p": 200, "lv": 5, "cls": ["Mago"]},
    "Cetro do Caos": {"t": "arma", "atk": 40, "p": 500, "lv": 10, "cls": ["Mago"]},
    "Túnica Simples": {"t": "arm", "def": 5, "p": 50, "lv": 1, "cls": ["Mago"]},
    "Armadura Mágica": {"t": "arm", "def": 12, "p": 200, "lv": 5, "cls": ["Mago"]},
    "Robe do Arquimago": {"t": "arm", "def": 20, "p": 500, "lv": 10, "cls": ["Mago"]}
}

# Consumíveis
CONSUMIVEIS = {
    "Poção de Vida": {"tipo": "hp", "valor": 50, "preco": 20},
    "Poção Grande de Vida": {"tipo": "hp", "valor": 100, "preco": 50},
    "Poção de Mana": {"tipo": "mana", "valor": 30, "preco": 25},
    "Elixir de Mana": {"tipo": "mana", "valor": 60, "preco": 60}
}

DUNGEONS = [
    {"nome": "Covil Goblin", "lv": 5, "boss": "Rei Goblin", "bhp": 100, "batk": 20, "xp": 200, "g": 150},
    {"nome": "Ninho Lobos", "lv": 10, "boss": "Lobo Alpha", "bhp": 150, "batk": 30, "xp": 400, "g": 300}
]

ST_CL, ST_NM = range(2)

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS players 
                 (id INTEGER PRIMARY KEY, nome TEXT, classe TEXT, hp INTEGER, hp_max INTEGER, 
                  mana INTEGER DEFAULT 0, mana_max INTEGER DEFAULT 0,
                  lv INTEGER, exp INTEGER, gold INTEGER, energia INTEGER, energia_max INTEGER,
                  mapa INTEGER DEFAULT 1, local TEXT DEFAULT 'cap',
                  arma TEXT, arm TEXT, atk_b INTEGER DEFAULT 0, def_b INTEGER DEFAULT 0,
                  crit INTEGER DEFAULT 0, double_atk INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS inv (pid INTEGER, item TEXT, qtd INTEGER DEFAULT 1, PRIMARY KEY (pid, item))''')
    c.execute('''CREATE TABLE IF NOT EXISTS dung (pid INTEGER, did INTEGER, PRIMARY KEY (pid, did))''')
    c.execute('''CREATE TABLE IF NOT EXISTS combate 
                 (pid INTEGER PRIMARY KEY, inimigo TEXT, i_hp INTEGER, i_hp_max INTEGER,
                  i_atk INTEGER, i_def INTEGER, i_xp INTEGER, i_gold INTEGER, turno INTEGER DEFAULT 1,
                  defendendo INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

def get_p(uid):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    p = conn.execute("SELECT * FROM players WHERE id = ?", (uid,)).fetchone()
    conn.close()
    return p

def get_combate(uid):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.execute("SELECT * FROM combate WHERE pid = ?", (uid,)).fetchone()
    conn.close()
    return c

def del_p(uid):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    for t in ["players", "inv", "dung", "combate"]:
        c.execute(f"DELETE FROM {t} WHERE {'id' if t=='players' else 'pid'} = ?", (uid,))
    conn.commit()
    conn.close()

def get_inv(uid):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    inv = conn.execute("SELECT * FROM inv WHERE pid = ?", (uid,)).fetchall()
    conn.close()
    return {i['item']: i['qtd'] for i in inv}

def add_inv(uid, item, qtd=1):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO inv VALUES (?,?,?) ON CONFLICT(pid,item) DO UPDATE SET qtd=qtd+?", (uid,item,qtd,qtd))
    conn.commit()
    conn.close()

def use_inv(uid, item):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE inv SET qtd=qtd-1 WHERE pid=? AND item=?", (uid,item))
    c.execute("DELETE FROM inv WHERE qtd<=0")
    conn.commit()
    conn.close()

def barra(a, m, c="🟦"):
    if m <= 0: return "⬜"*10
    p = max(0, min(a/m, 1))
    return c*int(p*10) + "⬜"*(10-int(p*10))

def img_c(c):
    return IMAGENS["classes"].get(c, IMG)

def atk(p):
    base = CLASSE_STATS[p['classe']]['atk']
    return base + (p['lv']*2) + p['atk_b']

def deff(p):
    base = CLASSE_STATS[p['classe']]['def']
    return base + p['lv'] + p['def_b']

async def menu(upd, ctx, uid, txt=""):
    p = get_p(uid)
    if not p: return
    mi = MAPAS.get(p['mapa'], {})
    li = mi.get('loc', {}).get(p['local'], {})
    
    cap = f"🎮 **{VERSAO}**\n{'━'*20}\n👤 **{p['nome']}** — *{p['classe']} Lv. {p['lv']}*\n🗺️ {mi.get('nome','?')} | 📍 {li.get('nome','?')}\n\n❤️ HP: {p['hp']}/{p['hp_max']}\n└ {barra(p['hp'],p['hp_max'],'🟥')}\n"
    
    # Mostrar mana se classe usar
    if p['mana_max'] > 0:
        cap += f"💙 MANA: {p['mana']}/{p['mana_max']}\n└ {barra(p['mana'],p['mana_max'],'🟦')}\n"
    
    cap += f"✨ XP: {p['exp']}/{p['lv']*100}\n└ {barra(p['exp'],p['lv']*100,'🟩')}\n\n⚔️ ATK: {atk(p)} | 🛡️ DEF: {deff(p)}\n"
    
    if p['crit'] > 0:
        cap += f"💥 CRIT: {p['crit']}%\n"
    if p['double_atk']:
        cap += f"⚡ Ataque Duplo\n"
    
    cap += f"💰 {p['gold']} | ⚡ {p['energia']}/{p['energia_max']}\n{'━'*20}\n{txt}"
    
    kb = [[InlineKeyboardButton("⚔️ Caçar",callback_data="cacar"),InlineKeyboardButton("🗺️ Mapas",callback_data="mapas")],[InlineKeyboardButton("🏘️ Locais",callback_data="locais"),InlineKeyboardButton("👤 Status",callback_data="perfil")],[InlineKeyboardButton("🏪 Loja",callback_data="loja"),InlineKeyboardButton("🎒 Inventário",callback_data="inv")],[InlineKeyboardButton("🏰 Dungeons",callback_data="dungs"),InlineKeyboardButton("⚙️ Config",callback_data="cfg")]]
    img = img_c(p['classe'])
    if upd.callback_query:
        try:
            await upd.callback_query.edit_message_caption(caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
        except:
            try: await upd.callback_query.message.delete()
            except: pass
            await ctx.bot.send_photo(upd.effective_chat.id, img, caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    else:
        await upd.message.reply_photo(img, caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def cacar(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    p = get_p(uid)
    if not p:
        await q.answer("Crie personagem!", show_alert=True)
        return
    if p['energia'] < 2:
        await q.answer("🪫 Sem energia!", show_alert=True)
        return
    
    # Verificar se já está em combate
    cb = get_combate(uid)
    if cb:
        await q.answer("⚔️ Já em combate!")
        await mostrar_combate(upd, ctx, uid)
        return
    
    inims = [n for n, d in INIMIGOS.items() if p['mapa'] in d['m']]
    if not inims:
        await q.answer("Sem inimigos!", show_alert=True)
        return
    
    inm = random.choice(inims)
    ini = INIMIGOS[inm]
    
    # Criar combate
    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT INTO combate VALUES (?,?,?,?,?,?,?,?,1,0)", 
                 (uid, inm, ini['hp'], ini['hp'], ini['atk'], ini['def'], ini['xp'], ini['gold']))
    conn.execute("UPDATE players SET energia=energia-2 WHERE id=?", (uid,))
    conn.commit()
    conn.close()
    
    await q.answer("⚔️ Combate iniciado!")
    await mostrar_combate(upd, ctx, uid)

async def mostrar_combate(upd, ctx, uid):
    p = get_p(uid)
    cb = get_combate(uid)
    if not cb:
        await menu(upd, ctx, uid)
        return
    
    inv = get_inv(uid)
    
    cap = f"⚔️ **COMBATE - Turno {cb['turno']}**\n{'━'*20}\n🐺 **{cb['inimigo']}**\n\n❤️ Inimigo: {cb['i_hp']}/{cb['i_hp_max']}\n└ {barra(cb['i_hp'],cb['i_hp_max'],'🟥')}\n\n❤️ Você: {p['hp']}/{p['hp_max']}\n└ {barra(p['hp'],p['hp_max'],'🟥')}\n"
    
    if p['mana_max'] > 0:
        cap += f"💙 Mana: {p['mana']}/{p['mana_max']}\n└ {barra(p['mana'],p['mana_max'],'🟦')}\n"
    
    if cb['defendendo']:
        cap += "\n🛡️ **DEFENDENDO**\n"
    
    cap += f"\n⚔️ ATK: {atk(p)} | 🛡️ DEF: {deff(p)}"
    if p['crit'] > 0:
        cap += f" | 💥 {p['crit']}%"
    cap += f"\n{'━'*20}"
    
    kb = [[InlineKeyboardButton("⚔️ Atacar",callback_data="bat_atk"),InlineKeyboardButton("🛡️ Defender",callback_data="bat_def")]]
    
    # Habilidades especiais
    if p['classe'] == "Bruxa" and p['mana'] >= 20:
        kb.append([InlineKeyboardButton("🔮 Maldição (20 mana)",callback_data="bat_esp")])
    elif p['classe'] == "Mago" and p['mana'] >= 30:
        kb.append([InlineKeyboardButton("🔥 Explosão (30 mana)",callback_data="bat_esp")])
    
    # Consumíveis
    cons_kb = []
    if "Poção de Vida" in inv and inv["Poção de Vida"] > 0:
        cons_kb.append(InlineKeyboardButton(f"💊 Poção HP ({inv['Poção de Vida']})",callback_data="bat_pot_hp"))
    if "Poção Grande de Vida" in inv and inv["Poção Grande de Vida"] > 0:
        cons_kb.append(InlineKeyboardButton(f"💊+ Poção G HP ({inv['Poção Grande de Vida']})",callback_data="bat_pot_hp2"))
    if cons_kb:
        kb.append(cons_kb)
    
    cons_mana = []
    if p['mana_max'] > 0:
        if "Poção de Mana" in inv and inv["Poção de Mana"] > 0:
            cons_mana.append(InlineKeyboardButton(f"🔵 Mana ({inv['Poção de Mana']})",callback_data="bat_pot_mp"))
        if "Elixir de Mana" in inv and inv["Elixir de Mana"] > 0:
            cons_mana.append(InlineKeyboardButton(f"🔵+ Elixir ({inv['Elixir de Mana']})",callback_data="bat_pot_mp2"))
    if cons_mana:
        kb.append(cons_mana)
    
    kb.append([InlineKeyboardButton("🏃 Fugir",callback_data="bat_fug")])
    
    if upd.callback_query:
        try: await upd.callback_query.message.delete()
        except: pass
    
    await ctx.bot.send_photo(upd.effective_chat.id, IMG, caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def bat_atk(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    p = get_p(uid)
    cb = get_combate(uid)
    
    if not cb:
        await q.answer("Sem combate!")
        return
    
    await q.answer("⚔️ Ataque!")
    
    # Calcular dano do jogador
    p_atk = atk(p)
    i_hp = cb['i_hp']
    i_atk = cb['i_atk']
    i_def = cb['i_def']
    p_hp = p['hp']
    
    log = []
    
    # Ataque do jogador
    is_crit = random.randint(1, 100) <= p['crit']
    num_ataques = 2 if p['double_atk'] else 1
    
    for _ in range(num_ataques):
        dano = max(1, p_atk - i_def + random.randint(-2,2))
        if is_crit:
            dano = int(dano * 1.5)
        i_hp -= dano
        if is_crit:
            log.append(f"💥 CRÍTICO! -{dano} HP")
        else:
            log.append(f"⚔️ Você atacou! -{dano} HP")
        if i_hp <= 0:
            break
    
    # Contra-ataque se inimigo vivo
    if i_hp > 0:
        def_bonus = 0.5 if cb['defendendo'] else 0
        dano_ini = max(1, int((i_atk - deff(p)) * (1 - def_bonus) + random.randint(-2,2)))
        p_hp -= dano_ini
        log.append(f"🐺 {cb['inimigo']} atacou! -{dano_ini} HP")
    
    # Atualizar DB
    conn = sqlite3.connect(DB_FILE)
    if i_hp <= 0:
        # Vitória
        p_hp = max(1, p_hp)
        conn.execute("UPDATE players SET hp=?,gold=gold+?,exp=exp+? WHERE id=?", 
                     (p_hp, cb['i_gold'], cb['i_xp'], uid))
        conn.execute("DELETE FROM combate WHERE pid=?", (uid,))
        conn.commit()
        conn.close()
        
        cap = f"🏆 **VITÓRIA!**\n{'━'*20}\n🐺 {cb['inimigo']} derrotado!\n\n📜 **Batalha:**\n" + "\n".join(log) + f"\n\n💰 +{cb['i_gold']} Gold\n✨ +{cb['i_xp']} XP\n{'━'*20}"
        kb = [[InlineKeyboardButton("🔙 Voltar",callback_data="voltar")]]
        
        try: await q.message.delete()
        except: pass
        await ctx.bot.send_photo(upd.effective_chat.id, IMG, caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    elif p_hp <= 0:
        # Derrota
        conn.execute("UPDATE players SET hp=1 WHERE id=?", (uid,))
        conn.execute("DELETE FROM combate WHERE pid=?", (uid,))
        conn.commit()
        conn.close()
        
        cap = f"💀 **DERROTA!**\n{'━'*20}\n🐺 {cb['inimigo']} venceu!\n\n📜 **Batalha:**\n" + "\n".join(log) + f"\n\nVocê foi derrotado...\n{'━'*20}"
        kb = [[InlineKeyboardButton("🔙 Voltar",callback_data="voltar")]]
        
        try: await q.message.delete()
        except: pass
        await ctx.bot.send_photo(upd.effective_chat.id, IMG, caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    else:
        # Continua
        conn.execute("UPDATE combate SET i_hp=?,turno=turno+1,defendendo=0 WHERE pid=?", (i_hp, uid))
        conn.execute("UPDATE players SET hp=? WHERE id=?", (p_hp, uid))
        conn.commit()
        conn.close()
        
        await mostrar_combate(upd, ctx, uid)

async def bat_def(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    
    conn = sqlite3.connect(DB_FILE)
    conn.execute("UPDATE combate SET defendendo=1,turno=turno+1 WHERE pid=?", (uid,))
    conn.commit()
    conn.close()
    
    await q.answer("🛡️ Defendendo!")
    await mostrar_combate(upd, ctx, uid)

async def bat_esp(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    p = get_p(uid)
    cb = get_combate(uid)
    
    if not cb:
        await q.answer("Sem combate!")
        return
    
    esp = CLASSE_STATS[p['classe']]['especial']
    
    if esp == "maldição" and p['mana'] >= 20:
        # Bruxa: Dano ao longo do tempo + reduz defesa
        dano = int(atk(p) * 1.3)
        i_hp = cb['i_hp'] - dano
        
        conn = sqlite3.connect(DB_FILE)
        conn.execute("UPDATE combate SET i_hp=?,i_def=i_def-3,turno=turno+1,defendendo=0 WHERE pid=?", (i_hp, uid))
        conn.execute("UPDATE players SET mana=mana-20 WHERE id=?", (uid,))
        conn.commit()
        conn.close()
        
        await q.answer(f"🔮 Maldição! -{dano} HP")
        
    elif esp == "explosão" and p['mana'] >= 30:
        # Mago: Dano massivo ignorando defesa
        dano = int(atk(p) * 2)
        i_hp = cb['i_hp'] - dano
        
        conn = sqlite3.connect(DB_FILE)
        conn.execute("UPDATE combate SET i_hp=?,turno=turno+1,defendendo=0 WHERE pid=?", (i_hp, uid))
        conn.execute("UPDATE players SET mana=mana-30 WHERE id=?", (uid,))
        conn.commit()
        conn.close()
        
        await q.answer(f"🔥 Explosão! -{dano} HP")
    else:
        await q.answer("Sem mana!", show_alert=True)
        return
    
    await mostrar_combate(upd, ctx, uid)

async def bat_pot_hp(upd, ctx):
    await usar_pocao(upd, ctx, "Poção de Vida")

async def bat_pot_hp2(upd, ctx):
    await usar_pocao(upd, ctx, "Poção Grande de Vida")

async def bat_pot_mp(upd, ctx):
    await usar_pocao(upd, ctx, "Poção de Mana")

async def bat_pot_mp2(upd, ctx):
    await usar_pocao(upd, ctx, "Elixir de Mana")

async def usar_pocao(upd, ctx, item):
    q = upd.callback_query
    uid = upd.effective_user.id
    p = get_p(uid)
    inv = get_inv(uid)
    
    if item not in inv or inv[item] <= 0:
        await q.answer("Sem item!", show_alert=True)
        return
    
    cons = CONSUMIVEIS[item]
    
    if cons['tipo'] == 'hp':
        novo_hp = min(p['hp'] + cons['valor'], p['hp_max'])
        conn = sqlite3.connect(DB_FILE)
        conn.execute("UPDATE players SET hp=? WHERE id=?", (novo_hp, uid))
        conn.commit()
        conn.close()
        use_inv(uid, item)
        await q.answer(f"💊 +{cons['valor']} HP!")
    else:  # mana
        if p['mana_max'] == 0:
            await q.answer("Você não usa mana!", show_alert=True)
            return
        novo_mana = min(p['mana'] + cons['valor'], p['mana_max'])
        conn = sqlite3.connect(DB_FILE)
        conn.execute("UPDATE players SET mana=? WHERE id=?", (novo_mana, uid))
        conn.commit()
        conn.close()
        use_inv(uid, item)
        await q.answer(f"🔵 +{cons['valor']} Mana!")
    
    # Turno do inimigo
    cb = get_combate(uid)
    if cb:
        p = get_p(uid)
        dano_ini = max(1, cb['i_atk'] - deff(p) + random.randint(-2,2))
        novo_hp = p['hp'] - dano_ini
        
        conn = sqlite3.connect(DB_FILE)
        if novo_hp <= 0:
            conn.execute("UPDATE players SET hp=1 WHERE id=?", (uid,))
            conn.execute("DELETE FROM combate WHERE pid=?", (uid,))
            conn.commit()
            conn.close()
            await menu(upd, ctx, uid, "💀 **Derrotado!**")
            return
        else:
            conn.execute("UPDATE players SET hp=? WHERE id=?", (novo_hp, uid))
            conn.execute("UPDATE combate SET turno=turno+1 WHERE pid=?", (uid,))
            conn.commit()
            conn.close()
    
    await mostrar_combate(upd, ctx, uid)

async def bat_fug(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    
    if random.random() < 0.5:
        conn = sqlite3.connect(DB_FILE)
        conn.execute("DELETE FROM combate WHERE pid=?", (uid,))
        conn.commit()
        conn.close()
        await q.answer("🏃 Fugiu!")
        await menu(upd, ctx, uid, "🏃 **Você fugiu!**")
    else:
        # Falhou, inimigo ataca
        p = get_p(uid)
        cb = get_combate(uid)
        dano = max(1, cb['i_atk'] - deff(p) + random.randint(0,3))
        novo_hp = p['hp'] - dano
        
        conn = sqlite3.connect(DB_FILE)
        if novo_hp <= 0:
            conn.execute("UPDATE players SET hp=1 WHERE id=?", (uid,))
            conn.execute("DELETE FROM combate WHERE pid=?", (uid,))
            conn.commit()
            conn.close()
            await q.answer(f"❌ Falhou! -{dano} HP", show_alert=True)
            await menu(upd, ctx, uid, "💀 **Derrotado ao fugir!**")
        else:
            conn.execute("UPDATE players SET hp=? WHERE id=?", (novo_hp, uid))
            conn.execute("UPDATE combate SET turno=turno+1 WHERE pid=?", (uid,))
            conn.commit()
            conn.close()
            await q.answer(f"❌ Falhou! -{dano} HP", show_alert=True)
            await mostrar_combate(upd, ctx, uid)

async def mapas(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    p = get_p(uid)
    await q.answer()
    cap = f"🗺️ **MAPAS**\n{'━'*20}\n"
    kb = []
    for mid, m in MAPAS.items():
        st = "✅" if p['lv'] >= m['lv'] else f"🔒 Lv.{m['lv']}"
        at = " 📍" if mid == p['mapa'] else ""
        av = f"\n└ {m['aviso']}" if m.get('aviso') and mid != p['mapa'] else ""
        cap += f"{st} {m['nome']}{at}{av}\n"
        # Permitir viajar mesmo sem nível
        kb.append([InlineKeyboardButton(f"🗺️ {m['nome']}",callback_data=f"via_{mid}")])
    kb.append([InlineKeyboardButton("🔙 Voltar",callback_data="voltar")])
    cap += f"{'━'*20}"
    try:
        await q.edit_message_caption(caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    except:
        await q.edit_message_text(cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def viajar(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    p = get_p(uid)
    mid = int(q.data.split('_')[1])
    
    m = MAPAS[mid]
    if p['lv'] < m['lv'] and m.get('aviso'):
        await q.answer(f"⚠️ {m['aviso']}", show_alert=True)
        # Mas ainda permite viajar
    
    conn = sqlite3.connect(DB_FILE)
    conn.execute("UPDATE players SET mapa=?,local='cap' WHERE id=?", (mid,uid))
    conn.commit()
    conn.close()
    await q.answer(f"🗺️ {m['nome']}!")
    await menu(upd, ctx, uid, f"🗺️ **{m['nome']}!**")

async def locais(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    p = get_p(uid)
    await q.answer()
    m = MAPAS.get(p['mapa'], {})
    cap = f"🏘️ **LOCAIS**\n{'━'*20}\n"
    kb = []
    for lid, loc in m.get('loc',{}).items():
        at = " 📍" if lid == p['local'] else ""
        cap += f"🏠 {loc['nome']}{at}\n"
        kb.append([InlineKeyboardButton(f"📍 {loc['nome']}",callback_data=f"iloc_{lid}")])
    kb.append([InlineKeyboardButton("🔙 Voltar",callback_data="voltar")])
    cap += f"{'━'*20}"
    try:
        await q.edit_message_caption(caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    except:
        await q.edit_message_text(cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def ir_loc(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    p = get_p(uid)
    lid = q.data.split('_')[1]
    conn = sqlite3.connect(DB_FILE)
    conn.execute("UPDATE players SET local=? WHERE id=?", (lid,uid))
    conn.commit()
    conn.close()
    ln = MAPAS[p['mapa']]['loc'][lid]['nome']
    await q.answer(f"📍 {ln}")
    await menu(upd, ctx, uid, f"📍 **{ln}**")

async def loja(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    p = get_p(uid)
    await q.answer()
    
    loc = MAPAS[p['mapa']]['loc'][p['local']]
    tlj = loc.get('loja','normal')
    
    if tlj == "contra":
        cap = f"🏴‍☠️ **CONTRABANDISTA**\n{'━'*20}\n💰 {p['gold']}\n⚠️ **-30% preço**\n❗ **5% roubo**\n\n"
        desc = 0.7
    else:
        cap = f"🏪 **LOJA**\n{'━'*20}\n💰 {p['gold']}\n\n"
        desc = 1.0
    
    kb = []
    
    # Equipamentos
    cap += "**⚔️ EQUIPAMENTOS:**\n"
    for n, eq in EQUIPS.items():
        if p['classe'] not in eq['cls']:
            continue
        pf = int(eq['p'] * desc)
        st = "✅" if p['lv'] >= eq['lv'] else f"🔒 Lv.{eq['lv']}"
        em = "⚔️" if eq['t']=="arma" else "🛡️"
        stat = f"+{eq.get('atk',eq.get('def'))}"
        cap += f"{st} {em} {n} {stat}\n└ 💰 {pf}\n"
        if p['lv'] >= eq['lv'] and p['gold'] >= pf:
            kb.append([InlineKeyboardButton(f"💰 {n}",callback_data=f"comp_{n}_{tlj}")])
    
    # Consumíveis
    cap += "\n**💊 CONSUMÍVEIS:**\n"
    for n, c in CONSUMIVEIS.items():
        # Não mostrar poções de mana para classes sem mana
        if c['tipo'] == 'mana' and p['mana_max'] == 0:
            continue
        pf = int(c['preco'] * desc)
        cap += f"💊 {n} ({c['tipo'].upper()} +{c['valor']})\n└ 💰 {pf}\n"
        if p['gold'] >= pf:
            kb.append([InlineKeyboardButton(f"💊 {n}",callback_data=f"comp_{n}_{tlj}")])
    
    kb.append([InlineKeyboardButton("🔙 Voltar",callback_data="voltar")])
    cap += f"{'━'*20}"
    try:
        await q.edit_message_caption(caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    except:
        await q.edit_message_text(cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def comprar(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    p = get_p(uid)
    pts = q.data.split('_')
    item = '_'.join(pts[1:-1])
    tlj = pts[-1]
    
    # Verificar se é equipamento ou consumível
    if item in EQUIPS:
        eq = EQUIPS[item]
        desc = 0.7 if tlj == "contra" else 1.0
        preco = int(eq['p'] * desc)
        
        if p['gold'] < preco:
            await q.answer("💸 Sem gold!", show_alert=True)
            return
        
        if tlj == "contra" and random.random() < 0.05:
            conn = sqlite3.connect(DB_FILE)
            conn.execute("UPDATE players SET gold=gold-? WHERE id=?", (preco,uid))
            conn.commit()
            conn.close()
            await q.answer("🏴‍☠️ Roubado!", show_alert=True)
            await menu(upd, ctx, uid, "🏴‍☠️ **ROUBADO!**")
            return
        
        conn = sqlite3.connect(DB_FILE)
        if eq['t']=="arma":
            conn.execute("UPDATE players SET gold=gold-?,arma=?,atk_b=? WHERE id=?", (preco,item,eq['atk'],uid))
        else:
            conn.execute("UPDATE players SET gold=gold-?,arm=?,def_b=? WHERE id=?", (preco,item,eq['def'],uid))
        conn.commit()
        conn.close()
        await q.answer(f"✅ {item}!", show_alert=True)
        await menu(upd, ctx, uid, f"✅ **{item}!**")
        
    elif item in CONSUMIVEIS:
        cons = CONSUMIVEIS[item]
        desc = 0.7 if tlj == "contra" else 1.0
        preco = int(cons['preco'] * desc)
        
        if p['gold'] < preco:
            await q.answer("💸 Sem gold!", show_alert=True)
            return
        
        if tlj == "contra" and random.random() < 0.05:
            conn = sqlite3.connect(DB_FILE)
            conn.execute("UPDATE players SET gold=gold-? WHERE id=?", (preco,uid))
            conn.commit()
            conn.close()
            await q.answer("🏴‍☠️ Roubado!", show_alert=True)
            await menu(upd, ctx, uid, "🏴‍☠️ **ROUBADO!**")
            return
        
        conn = sqlite3.connect(DB_FILE)
        conn.execute("UPDATE players SET gold=gold-? WHERE id=?", (preco,uid))
        conn.commit()
        conn.close()
        add_inv(uid, item, 1)
        await q.answer(f"✅ {item}!", show_alert=True)
        await loja(upd, ctx)

async def inv(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    await q.answer()
    
    inv_data = get_inv(uid)
    
    cap = f"🎒 **INVENTÁRIO**\n{'━'*20}\n"
    if not inv_data:
        cap += "Vazio\n"
    else:
        for item, qtd in inv_data.items():
            cap += f"💊 {item} x{qtd}\n"
    cap += f"{'━'*20}"
    
    kb = [[InlineKeyboardButton("🔙 Voltar",callback_data="voltar")]]
    
    try:
        await q.edit_message_caption(caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    except:
        await q.edit_message_text(cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def dungs(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    p = get_p(uid)
    await q.answer()
    cap = f"🏰 **DUNGEONS**\n{'━'*20}\n"
    kb = []
    for i, d in enumerate(DUNGEONS):
        st = "✅" if p['lv'] >= d['lv'] else f"🔒 Lv.{d['lv']}"
        cap += f"{st} {d['nome']}\n└ {d['boss']}\n└ XP: {d['xp']} | Gold: {d['g']}\n"
        if p['lv'] >= d['lv']:
            kb.append([InlineKeyboardButton(f"🏰 {d['nome']}",callback_data=f"dung_{i}")])
    kb.append([InlineKeyboardButton("🔙 Voltar",callback_data="voltar")])
    cap += f"{'━'*20}"
    try:
        await q.edit_message_caption(caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    except:
        await q.edit_message_text(cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def dung(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    p = get_p(uid)
    did = int(q.data.split('_')[1])
    d = DUNGEONS[did]
    if p['energia'] < 10:
        await q.answer("🪫 10 energia!", show_alert=True)
        return
    
    await q.answer("🏰 Entrando...")
    
    p_atk = atk(p)
    p_def = deff(p)
    bhp = d['bhp']
    batk = d['batk']
    php = p['hp']
    
    log = []
    t = 1
    
    while php > 0 and bhp > 0 and t <= 15:
        dp = max(1, p_atk - 5 + random.randint(-3,3))
        bhp -= dp
        log.append(f"↗️ T{t}: -{dp}")
        if bhp <= 0: break
        db = max(1, batk - p_def + random.randint(-3,3))
        php -= db
        log.append(f"↘️ T{t}: -{db}")
        t += 1
    
    vit = php > 0
    php = max(1, php)
    
    if vit:
        conn = sqlite3.connect(DB_FILE)
        conn.execute("UPDATE players SET gold=gold+?,exp=exp+?,energia=energia-10,hp=? WHERE id=?", (d['g'],d['xp'],php,uid))
        conn.execute("INSERT OR IGNORE INTO dung VALUES (?,?)", (uid,did))
        conn.commit()
        conn.close()
        res = f"🏆 **VIT!**\n💰 +{d['g']} | ✨ +{d['xp']}"
    else:
        conn = sqlite3.connect(DB_FILE)
        conn.execute("UPDATE players SET energia=energia-10,hp=1 WHERE id=?", (uid,))
        conn.commit()
        conn.close()
        res = "💀 **DERROT!**"
    
    cap = f"🏰 **{d['nome']}**\n{'━'*20}\n👹 {d['boss']}\n\n❤️ Boss: {max(0,bhp)}/{d['bhp']}\n└ {barra(max(0,bhp),d['bhp'],'🟥')}\n\n❤️ Você: {php}/{p['hp_max']}\n└ {barra(php,p['hp_max'],'🟥')}\n\n📜:\n" + "\n".join(log[-6:]) + f"\n\n{res}\n{'━'*20}"
    kb = [[InlineKeyboardButton("🔙 Voltar",callback_data="voltar")]]
    
    try: await q.message.delete()
    except: pass
    await ctx.bot.send_photo(upd.effective_chat.id, IMG, caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def perfil(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    p = get_p(uid)
    await q.answer()
    
    cap = f"👤 **PERFIL**\n{'━'*20}\n📛 {p['nome']}\n🎭 {p['classe']}\n⭐ Lv {p['lv']}\n\n❤️ {p['hp']}/{p['hp_max']}\n└ {barra(p['hp'],p['hp_max'],'🟥')}\n"
    
    if p['mana_max'] > 0:
        cap += f"💙 {p['mana']}/{p['mana_max']}\n└ {barra(p['mana'],p['mana_max'],'🟦')}\n"
    
    cap += f"✨ {p['exp']}/{p['lv']*100}\n└ {barra(p['exp'],p['lv']*100,'🟩')}\n\n💰 {p['gold']}\n⚡ {p['energia']}/{p['energia_max']}\n⚔️ {atk(p)}\n🛡️ {deff(p)}\n"
    
    if p['crit'] > 0:
        cap += f"💥 Crítico: {p['crit']}%\n"
    if p['double_atk']:
        cap += f"⚡ Ataque Duplo\n"
    
    cap += f"{'━'*20}"
    
    if p['arma']:
        cap += f"\n⚔️ {p['arma']}"
    if p['arm']:
        cap += f"\n🛡️ {p['arm']}"
    
    kb = [[InlineKeyboardButton("🔙 Voltar",callback_data="voltar")]]
    try: await q.message.delete()
    except: pass
    await ctx.bot.send_photo(upd.effective_chat.id, img_c(p['classe']), caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def cfg(upd, ctx):
    q = upd.callback_query
    await q.answer()
    cap = f"⚙️ **CONFIG**\n{'━'*20}\n🔄 Reset\n⚡ Lv MAX\n💰 Gold MAX\n{'━'*20}"
    kb = [[InlineKeyboardButton("🔄 Reset",callback_data="rst_c")],[InlineKeyboardButton("⚡ Lv MAX",callback_data="ch_lv")],[InlineKeyboardButton("💰 Gold MAX",callback_data="ch_g")],[InlineKeyboardButton("🔙 Voltar",callback_data="voltar")]]
    try:
        await q.edit_message_caption(caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    except:
        await q.edit_message_text(cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def rst_c(upd, ctx):
    q = upd.callback_query
    await q.answer()
    cap = f"⚠️ **DELETAR?**\n{'━'*20}\n❌ IRREVERSÍVEL\n{'━'*20}"
    kb = [[InlineKeyboardButton("✅ SIM",callback_data="rst_y")],[InlineKeyboardButton("❌ NÃO",callback_data="cfg")]]
    try:
        await q.edit_message_caption(caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    except:
        await q.edit_message_text(cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def rst_y(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    del_p(uid)
    await q.answer("✅ Deletado!", show_alert=True)
    
    ctx.user_data.clear()
    cap = f"✨ **AVENTURA RABISCADA** ✨\n{'━'*20}\nVersão: `{VERSAO}`\n{'━'*20}"
    kb = [[InlineKeyboardButton("🎮 Começar",callback_data="ir_cls")]]
    
    try: await q.message.delete()
    except: pass
    await ctx.bot.send_photo(upd.effective_chat.id, IMAGENS["logo"], caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def ch_lv(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    p = get_p(uid)
    
    conn = sqlite3.connect(DB_FILE)
    hp_max = CLASSE_STATS[p['classe']]['hp'] * 10
    mana_max = CLASSE_STATS[p['classe']]['mana'] * 10 if CLASSE_STATS[p['classe']]['mana'] > 0 else 0
    conn.execute("UPDATE players SET lv=99,exp=0,hp_max=?,hp=?,mana_max=?,mana=?,energia_max=999,energia=999 WHERE id=?", 
                 (hp_max, hp_max, mana_max, mana_max, uid))
    conn.commit()
    conn.close()
    await q.answer("⚡ 99!", show_alert=True)
    await menu(upd, ctx, uid, "⚡ **Lv 99!**")

async def ch_g(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    conn = sqlite3.connect(DB_FILE)
    conn.execute("UPDATE players SET gold=999999 WHERE id=?", (uid,))
    conn.commit()
    conn.close()
    await q.answer("💰 999,999!", show_alert=True)
    await menu(upd, ctx, uid, "💰 **999,999!**")

async def voltar(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    
    # Se estava em combate, cancela
    conn = sqlite3.connect(DB_FILE)
    conn.execute("DELETE FROM combate WHERE pid=?", (uid,))
    conn.commit()
    conn.close()
    
    await q.answer()
    await menu(upd, ctx, uid)

async def start(upd, ctx):
    uid = upd.effective_user.id
    p = get_p(uid)
    if p:
        await menu(upd, ctx, uid)
        return ConversationHandler.END
    ctx.user_data.clear()
    cap = f"✨ **AVENTURA RABISCADA** ✨\n{'━'*20}\nVersão: `{VERSAO}`\n\n🎮 **NOVIDADES:**\n⚔️ Combate Manual\n🎭 Classes Únicas\n💊 Sistema de Consumíveis\n🔮 Habilidades Especiais\n💙 Sistema de Mana\n{'━'*20}"
    kb = [[InlineKeyboardButton("🎮 Começar",callback_data="ir_cls")]]
    await upd.message.reply_photo(IMAGENS["logo"], caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    return ST_CL

async def menu_cls(upd, ctx):
    q = upd.callback_query
    await q.answer()
    cap = f"🎭 **ESCOLHA SUA CLASSE**\n{'━'*20}\n\n🛡️ **Guerreiro**\n└ HP Alto | Defesa Máxima\n└ ❤️ 250 HP | 🛡️ 18 DEF\n\n🏹 **Arqueiro**\n└ Crítico | Ataque Duplo\n└ ❤️ 120 HP | 💥 25% CRIT\n\n🔮 **Bruxa**\n└ Maldição | Dano Mágico\n└ ❤️ 150 HP | 💙 100 MANA\n\n🔥 **Mago**\n└ Explosão | Poder Máximo\n└ ❤️ 130 HP | 💙 120 MANA\n{'━'*20}"
    kb = [[InlineKeyboardButton("🛡️ Guerreiro",callback_data="Guerreiro"),InlineKeyboardButton("🏹 Arqueiro",callback_data="Arqueiro")],[InlineKeyboardButton("🔮 Bruxa",callback_data="Bruxa"),InlineKeyboardButton("🔥 Mago",callback_data="Mago")]]
    try: await q.message.delete()
    except: pass
    await ctx.bot.send_photo(upd.effective_chat.id, IMAGENS["sel"], caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    return ST_NM

async def salv_nm(upd, ctx):
    q = upd.callback_query
    ctx.user_data['classe'] = q.data
    await q.answer()
    
    stats = CLASSE_STATS[q.data]
    cap = f"✅ **{q.data.upper()}**\n{'━'*20}\n❤️ HP: {stats['hp']}\n🛡️ DEF: {stats['def']}\n⚔️ ATK: {stats['atk']}\n"
    if stats['mana'] > 0:
        cap += f"💙 MANA: {stats['mana']}\n"
    if stats['crit'] > 0:
        cap += f"💥 CRIT: {stats['crit']}%\n"
    if stats['double']:
        cap += f"⚡ Ataque Duplo\n"
    if stats['especial']:
        cap += f"🌟 {stats['especial'].title()}\n"
    cap += f"{'━'*20}\n📝 **Digite seu nome:**"
    
    try: await q.message.delete()
    except: pass
    await ctx.bot.send_photo(upd.effective_chat.id, img_c(q.data), caption=cap, parse_mode='Markdown')
    return ST_NM

async def fin(upd, ctx):
    uid = upd.effective_user.id
    nome = upd.message.text
    classe = ctx.user_data.get('classe','Guerreiro')
    
    stats = CLASSE_STATS[classe]
    
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""INSERT OR REPLACE INTO players 
                    VALUES (?,?,?,?,?,?,?,1,0,100,20,20,1,'cap',NULL,NULL,0,0,?,?)""", 
                 (uid, nome, classe, stats['hp'], stats['hp'], stats['mana'], stats['mana'],
                  stats['crit'], 1 if stats['double'] else 0))
    conn.commit()
    conn.close()
    
    await upd.message.reply_text(f"✨ **{nome}!**\nBem-vindo, {classe}!")
    await menu(upd, ctx, uid)
    return ConversationHandler.END

def main():
    init_db()
    token = os.getenv("TELEGRAM_TOKEN")
    app = ApplicationBuilder().token(token).build()
    
    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ST_CL: [CallbackQueryHandler(menu_cls, pattern='^ir_cls$')],
            ST_NM: [CallbackQueryHandler(salv_nm), MessageHandler(filters.TEXT & ~filters.COMMAND, fin)]
        },
        fallbacks=[CommandHandler('start', start)]
    )
    
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(cacar, pattern='^cacar$'))
    app.add_handler(CallbackQueryHandler(bat_atk, pattern='^bat_atk$'))
    app.add_handler(CallbackQueryHandler(bat_def, pattern='^bat_def$'))
    app.add_handler(CallbackQueryHandler(bat_esp, pattern='^bat_esp$'))
    app.add_handler(CallbackQueryHandler(bat_pot_hp, pattern='^bat_pot_hp$'))
    app.add_handler(CallbackQueryHandler(bat_pot_hp2, pattern='^bat_pot_hp2$'))
    app.add_handler(CallbackQueryHandler(bat_pot_mp, pattern='^bat_pot_mp$'))
    app.add_handler(CallbackQueryHandler(bat_pot_mp2, pattern='^bat_pot_mp2$'))
    app.add_handler(CallbackQueryHandler(bat_fug, pattern='^bat_fug$'))
    app.add_handler(CallbackQueryHandler(mapas, pattern='^mapas$'))
    app.add_handler(CallbackQueryHandler(viajar, pattern='^via_'))
    app.add_handler(CallbackQueryHandler(locais, pattern='^locais$'))
    app.add_handler(CallbackQueryHandler(ir_loc, pattern='^iloc_'))
    app.add_handler(CallbackQueryHandler(perfil, pattern='^perfil$'))
    app.add_handler(CallbackQueryHandler(loja, pattern='^loja$'))
    app.add_handler(CallbackQueryHandler(comprar, pattern='^comp_'))
    app.add_handler(CallbackQueryHandler(inv, pattern='^inv$'))
    app.add_handler(CallbackQueryHandler(dungs, pattern='^dungs$'))
    app.add_handler(CallbackQueryHandler(dung, pattern='^dung_'))
    app.add_handler(CallbackQueryHandler(cfg, pattern='^cfg$'))
    app.add_handler(CallbackQueryHandler(rst_c, pattern='^rst_c$'))
    app.add_handler(CallbackQueryHandler(rst_y, pattern='^rst_y$'))
    app.add_handler(CallbackQueryHandler(ch_lv, pattern='^ch_lv$'))
    app.add_handler(CallbackQueryHandler(ch_g, pattern='^ch_g$'))
    app.add_handler(CallbackQueryHandler(voltar, pattern='^voltar$'))
    
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
