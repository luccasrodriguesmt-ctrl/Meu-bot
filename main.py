import os, random, sqlite3, logging, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters, ConversationHandler

VERSAO = "2.1.0 - Sistema Completo"
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

MAPAS = {
    1: {"nome": "Planície", "lv": 1, "loc": {
        "cap": {"nome": "Capital Real", "loja": "normal"},
        "v1": {"nome": "Vila Norte", "loja": "normal"},
        "v2": {"nome": "Povoado Sul", "loja": "contra"}
    }},
    2: {"nome": "Floresta", "lv": 5, "loc": {
        "cap": {"nome": "Forte Floresta", "loja": "normal"},
        "v1": {"nome": "Acampamento", "loja": "normal"},
        "v2": {"nome": "Refúgio", "loja": "contra"}
    }},
    3: {"nome": "Caverna", "lv": 10, "loc": {
        "cap": {"nome": "Cidade Sub", "loja": "normal"},
        "v1": {"nome": "Mina", "loja": "contra"},
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

EQUIPS = {
    "Espada Enf": {"t": "arma", "atk": 5, "p": 50, "lv": 1},
    "Espada Ferro": {"t": "arma", "atk": 15, "p": 200, "lv": 5},
    "Espada Aço": {"t": "arma", "atk": 30, "p": 500, "lv": 10},
    "Arm Couro": {"t": "arm", "def": 5, "p": 50, "lv": 1},
    "Arm Ferro": {"t": "arm", "def": 15, "p": 200, "lv": 5},
    "Arm Aço": {"t": "arm", "def": 30, "p": 500, "lv": 10}
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
                  lv INTEGER, exp INTEGER, gold INTEGER, energia INTEGER, energia_max INTEGER,
                  mapa INTEGER DEFAULT 1, local TEXT DEFAULT 'cap',
                  arma TEXT, arm TEXT, atk_b INTEGER DEFAULT 0, def_b INTEGER DEFAULT 0)''')
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

def del_p(uid):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    for t in ["players", "inv", "dung"]:
        c.execute(f"DELETE FROM {t} WHERE {'id' if t=='players' else 'pid'} = ?", (uid,))
    conn.commit()
    conn.close()

def barra(a, m, c="🟦"):
    if m <= 0: return "⬜"*10
    p = max(0, min(a/m, 1))
    return c*int(p*10) + "⬜"*(10-int(p*10))

def img_c(c):
    return IMAGENS["classes"].get(c, IMG)

def atk(p):
    return 10 + (p['lv']*2) + p['atk_b']

def deff(p):
    return 5 + p['lv'] + p['def_b']

async def menu(upd, ctx, uid, txt=""):
    p = get_p(uid)
    if not p: return
    mi = MAPAS.get(p['mapa'], {})
    li = mi.get('loc', {}).get(p['local'], {})
    cap = f"🎮 **{VERSAO}**\n{'━'*20}\n👤 **{p['nome']}** — *{p['classe']} Lv. {p['lv']}*\n🗺️ {mi.get('nome','?')} | 📍 {li.get('nome','?')}\n\n❤️ HP: {p['hp']}/{p['hp_max']}\n└ {barra(p['hp'],p['hp_max'],'🟥')}\n✨ XP: {p['exp']}/{p['lv']*100}\n└ {barra(p['exp'],p['lv']*100,'🟦')}\n\n⚔️ ATK: {atk(p)} | 🛡️ DEF: {deff(p)}\n💰 {p['gold']} | ⚡ {p['energia']}/{p['energia_max']}\n{'━'*20}\n{txt}"
    kb = [[InlineKeyboardButton("⚔️ Caçar",callback_data="cacar"),InlineKeyboardButton("🗺️ Mapas",callback_data="mapas")],[InlineKeyboardButton("🏘️ Locais",callback_data="locais"),InlineKeyboardButton("👤 Status",callback_data="perfil")],[InlineKeyboardButton("🏪 Loja",callback_data="loja"),InlineKeyboardButton("🏰 Dungeons",callback_data="dungs")],[InlineKeyboardButton("⚙️ Config",callback_data="cfg")]]
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
    
    inims = [n for n, d in INIMIGOS.items() if p['mapa'] in d['m']]
    if not inims:
        await q.answer("Sem inimigos!", show_alert=True)
        return
    
    inm = random.choice(inims)
    ini = INIMIGOS[inm]
    
    p_atk = atk(p)
    p_def = deff(p)
    i_hp = ini['hp']
    i_atk = ini['atk']
    i_def = ini['def']
    p_hp = p['hp']
    
    log = []
    t = 1
    
    while p_hp > 0 and i_hp > 0 and t <= 10:
        dp = max(1, p_atk - i_def + random.randint(-2,2))
        i_hp -= dp
        log.append(f"↗️ T{t}: Ataque! -{dp}")
        if i_hp <= 0: break
        di = max(1, i_atk - p_def + random.randint(-2,2))
        p_hp -= di
        log.append(f"↘️ T{t}: {inm}! -{di}")
        t += 1
    
    vit = p_hp > 0
    p_hp = max(1, p_hp)
    
    if vit:
        g = ini['gold'] + random.randint(-5,5)
        x = ini['xp'] + random.randint(-5,5)
        conn = sqlite3.connect(DB_FILE)
        conn.execute("UPDATE players SET hp=?,gold=gold+?,exp=exp+?,energia=energia-2 WHERE id=?", (p_hp,g,x,uid))
        conn.commit()
        conn.close()
        res = f"🏆 **VITÓRIA!**\n💰 +{g} | ✨ +{x}"
    else:
        conn = sqlite3.connect(DB_FILE)
        conn.execute("UPDATE players SET hp=1,energia=energia-2 WHERE id=?", (uid,))
        conn.commit()
        conn.close()
        res = "💀 **DERROTA!**"
        g = x = 0
    
    await q.answer("⚔️ Combate!")
    
    cap = f"⚔️ **COMBATE**\n{'━'*20}\n🐺 **{inm}**\n_{ini['desc']}_\n\n❤️ Inimigo: {max(0,i_hp)}/{ini['hp']}\n└ {barra(max(0,i_hp),ini['hp'],'🟥')}\n\n❤️ Você: {p_hp}/{p['hp_max']}\n└ {barra(p_hp,p['hp_max'],'🟥')}\n\n📜 **Histórico:**\n" + "\n".join(log[-6:]) + f"\n\n{res}\n{'━'*20}"
    kb = [[InlineKeyboardButton("🔙 Voltar",callback_data="voltar")]]
    
    try: await q.message.delete()
    except: pass
    await ctx.bot.send_photo(upd.effective_chat.id, IMG, caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

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
        cap += f"{st} {m['nome']}{at}\n"
        if p['lv'] >= m['lv']:
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
    mid = int(q.data.split('_')[1])
    conn = sqlite3.connect(DB_FILE)
    conn.execute("UPDATE players SET mapa=?,local='cap' WHERE id=?", (mid,uid))
    conn.commit()
    conn.close()
    await q.answer("🗺️ Viajou!")
    await menu(upd, ctx, uid, f"🗺️ **{MAPAS[mid]['nome']}!**")

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
    for n, eq in EQUIPS.items():
        pf = int(eq['p'] * desc)
        st = "✅" if p['lv'] >= eq['lv'] else f"🔒 Lv.{eq['lv']}"
        em = "⚔️" if eq['t']=="arma" else "🛡️"
        stat = f"+{eq.get('atk',eq.get('def'))}"
        cap += f"{st} {em} {n} {stat}\n└ 💰 {pf}\n"
        if p['lv'] >= eq['lv'] and p['gold'] >= pf:
            kb.append([InlineKeyboardButton(f"💰 {n}",callback_data=f"comp_{n}_{tlj}")])
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
        await menu(upd, ctx, uid, "🏴‍☠️ **ROUBADO!**\nPerdeu gold sem item!")
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
    cap = f"👤 **PERFIL**\n{'━'*20}\n📛 {p['nome']}\n🎭 {p['classe']}\n⭐ Lv {p['lv']}\n\n❤️ {p['hp']}/{p['hp_max']}\n└ {barra(p['hp'],p['hp_max'],'🟥')}\n✨ {p['exp']}/{p['lv']*100}\n└ {barra(p['exp'],p['lv']*100,'🟦')}\n\n💰 {p['gold']}\n⚡ {p['energia']}/{p['energia_max']}\n⚔️ {atk(p)}\n🛡️ {deff(p)}\n{'━'*20}"
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
    
    # FIX: Vai direto para criação
    ctx.user_data.clear()
    cap = f"✨ **AVENTURA RABISCADA** ✨\n{'━'*20}\nVersão: `{VERSAO}`\n{'━'*20}"
    kb = [[InlineKeyboardButton("🎮 Começar",callback_data="ir_cls")]]
    
    try: await q.message.delete()
    except: pass
    await ctx.bot.send_photo(upd.effective_chat.id, IMAGENS["logo"], caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def ch_lv(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    conn = sqlite3.connect(DB_FILE)
    conn.execute("UPDATE players SET lv=99,exp=0,hp_max=9999,hp=9999,energia_max=999,energia=999 WHERE id=?", (uid,))
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
    await q.answer()
    await menu(upd, ctx, upd.effective_user.id)

async def start(upd, ctx):
    uid = upd.effective_user.id
    p = get_p(uid)
    if p:
        await menu(upd, ctx, uid)
        return ConversationHandler.END
    ctx.user_data.clear()
    cap = f"✨ **AVENTURA RABISCADA** ✨\n{'━'*20}\nVersão: `{VERSAO}`\n{'━'*20}"
    kb = [[InlineKeyboardButton("🎮 Começar",callback_data="ir_cls")]]
    await upd.message.reply_photo(IMAGENS["logo"], caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    return ST_CL

async def menu_cls(upd, ctx):
    q = upd.callback_query
    await q.answer()
    cap = f"🎭 **CLASSES**\n{'━'*20}\n🛡️ Guerreiro\n🏹 Arqueiro\n🔮 Bruxa\n🔥 Mago\n{'━'*20}"
    kb = [[InlineKeyboardButton("🛡️ Guerreiro",callback_data="Guerreiro"),InlineKeyboardButton("🏹 Arqueiro",callback_data="Arqueiro")],[InlineKeyboardButton("🔮 Bruxa",callback_data="Bruxa"),InlineKeyboardButton("🔥 Mago",callback_data="Mago")]]
    try: await q.message.delete()
    except: pass
    await ctx.bot.send_photo(upd.effective_chat.id, IMAGENS["sel"], caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    return ST_NM

async def salv_nm(upd, ctx):
    q = upd.callback_query
    ctx.user_data['classe'] = q.data
    await q.answer()
    cap = f"✅ **{q.data.upper()}**\n{'━'*20}\nNome:"
    try: await q.message.delete()
    except: pass
    await ctx.bot.send_photo(upd.effective_chat.id, img_c(q.data), caption=cap, parse_mode='Markdown')
    return ST_NM

async def fin(upd, ctx):
    uid = upd.effective_user.id
    nome = upd.message.text
    classe = ctx.user_data.get('classe','Guerreiro')
    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT OR REPLACE INTO players VALUES (?,?,?,100,100,1,0,100,20,20,1,'cap',NULL,NULL,0,0)", (uid,nome,classe))
    conn.commit()
    conn.close()
    await upd.message.reply_text(f"✨ **{nome}!**")
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
    app.add_handler(CallbackQueryHandler(mapas, pattern='^mapas$'))
    app.add_handler(CallbackQueryHandler(viajar, pattern='^via_'))
    app.add_handler(CallbackQueryHandler(locais, pattern='^locais$'))
    app.add_handler(CallbackQueryHandler(ir_loc, pattern='^iloc_'))
    app.add_handler(CallbackQueryHandler(perfil, pattern='^perfil$'))
    app.add_handler(CallbackQueryHandler(loja, pattern='^loja$'))
    app.add_handler(CallbackQueryHandler(comprar, pattern='^comp_'))
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
