import os, random, sqlite3, logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters, ConversationHandler

VERSAO = "2.0.0 - Sistema Completo"
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
DB_FILE = "rpg_game.db"

# IMAGENS
# Lista com as suas 7 imagens do GitHub para uso aleatório
MINHAS_FOTOS = [
    "https://raw.githubusercontent.com/luccasrodriguesmt-ctrl/Meu-bot/main/images/WhatsApp%20Image%202026-02-15%20at%2009.06.10.jpeg",
    "https://raw.githubusercontent.com/luccasrodriguesmt-ctrl/Meu-bot/main/images/Gemini_Generated_Image_l46bisl46bisl46b.png",
    "https://raw.githubusercontent.com/luccasrodriguesmt-ctrl/Meu-bot/main/images/Gemini_Generated_Image_n68a2ln68a2ln68a.png",
    "https://raw.githubusercontent.com/luccasrodriguesmt-ctrl/Meu-bot/main/images/Gemini_Generated_Image_o1dtmio1dtmio1dt.png",
    "https://raw.githubusercontent.com/luccasrodriguesmt-ctrl/Meu-bot/main/images/Gemini_Generated_Image_fyofu7fyofu7fyof.png",
    "https://raw.githubusercontent.com/luccasrodriguesmt-ctrl/Meu-bot/main/images/Gemini_Generated_Image_8nad348nad348nad.png",
    "https://raw.githubusercontent.com/luccasrodriguesmt-ctrl/Meu-bot/main/images/Gemini_Generated_Image_dxklz9dxklz9dxkl.png"
]

IMAGENS = {
    "logo": MINHAS_FOTOS[0],
    "selecao_classes": MINHAS_FOTOS[1],
    "classes": {
        "Guerreiro": MINHAS_FOTOS[2],
        "Arqueiro": MINHAS_FOTOS[3],
        "Bruxa": MINHAS_FOTOS[4],
        "Mago": MINHAS_FOTOS[5]
    },
    # Aqui o bot escolhe uma das suas 7 fotos ao acaso para cada mapa ou inimigo
    "mapas": {i: random.choice(MINHAS_FOTOS) for i in range(1, 7)},
    "inimigos": {nome: random.choice(MINHAS_FOTOS) for nome in ["Goblin", "Lobo", "Orc", "Esqueleto", "Dragão"]}
}

# DADOS DO JOGO
MAPAS = {
    1: {"nome": "Planície Verdejante", "nivel_min": 1, "xp": 20, "gold": 15},
    2: {"nome": "Floresta Sombria", "nivel_min": 5, "xp": 50, "gold": 35},
    3: {"nome": "Caverna Profunda", "nivel_min": 10, "xp": 100, "gold": 70},
    4: {"nome": "Montanha Gelada", "nivel_min": 15, "xp": 200, "gold": 150},
    5: {"nome": "Vulcão Ardente", "nivel_min": 20, "xp": 350, "gold": 250},
    6: {"nome": "Torre Arcana", "nivel_min": 25, "xp": 500, "gold": 400}
}

INIMIGOS = {
    "Goblin": {"hp": 30, "atk": 8, "xp": 25, "gold": 15, "mapas": [1, 2]},
    "Lobo": {"hp": 45, "atk": 12, "xp": 40, "gold": 25, "mapas": [2, 3]},
    "Orc": {"hp": 80, "atk": 20, "xp": 80, "gold": 60, "mapas": [3, 4]},
    "Esqueleto": {"hp": 60, "atk": 15, "xp": 70, "gold": 50, "mapas": [3, 4, 5]},
    "Dragão": {"hp": 200, "atk": 40, "xp": 300, "gold": 250, "mapas": [5, 6]}
}

EQUIPAMENTOS = {
    "Espada Enferrujada": {"tipo": "arma", "atk": 5, "preco": 50, "lv": 1},
    "Espada de Ferro": {"tipo": "arma", "atk": 15, "preco": 200, "lv": 5},
    "Espada de Aço": {"tipo": "arma", "atk": 30, "preco": 500, "lv": 10},
    "Espada Lendária": {"tipo": "arma", "atk": 60, "preco": 2000, "lv": 20},
    "Armadura de Couro": {"tipo": "armadura", "def": 5, "preco": 50, "lv": 1},
    "Armadura de Ferro": {"tipo": "armadura", "def": 15, "preco": 200, "lv": 5},
    "Armadura de Aço": {"tipo": "armadura", "def": 30, "preco": 500, "lv": 10},
    "Armadura Lendária": {"tipo": "armadura", "def": 60, "preco": 2000, "lv": 20}
}

DUNGEONS = [
    {"nome": "Covil dos Goblins", "lv": 5, "boss": "Goblin Rei", "xp": 200, "gold": 150},
    {"nome": "Ninho de Lobos", "lv": 10, "boss": "Lobo Alpha", "xp": 400, "gold": 300},
    {"nome": "Fortaleza Orc", "lv": 15, "boss": "Orc Senhor", "xp": 800, "gold": 600},
    {"nome": "Tumba Amaldiçoada", "lv": 20, "boss": "Lich", "xp": 1500, "gold": 1000},
    {"nome": "Covil do Dragão", "lv": 25, "boss": "Dragão Ancião", "xp": 3000, "gold": 2500}
]

TELA_CLASSE, TELA_NOME = range(2)

# DATABASE
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS players 
                 (id INTEGER PRIMARY KEY, nome TEXT, classe TEXT, hp INTEGER, hp_max INTEGER, 
                  lv INTEGER, exp INTEGER, gold INTEGER, energia INTEGER, energia_max INTEGER,
                  mapa_atual INTEGER DEFAULT 1, arma TEXT, armadura TEXT, atk_bonus INTEGER DEFAULT 0, def_bonus INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS inventario (player_id INTEGER, item TEXT, qtd INTEGER DEFAULT 1, PRIMARY KEY (player_id, item))''')
    c.execute('''CREATE TABLE IF NOT EXISTS dungeons_completas (player_id INTEGER, dungeon_id INTEGER, PRIMARY KEY (player_id, dungeon_id))''')
    conn.commit()
    conn.close()

def get_player(uid):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    p = conn.execute("SELECT * FROM players WHERE id = ?", (uid,)).fetchone()
    conn.close()
    return p

def delete_player(uid):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    for table in ["players", "inventario", "dungeons_completas"]:
        c.execute(f"DELETE FROM {table} WHERE {'id' if table=='players' else 'player_id'} = ?", (uid,))
    conn.commit()
    conn.close()

def get_inventario(uid):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    items = conn.execute("SELECT * FROM inventario WHERE player_id = ?", (uid,)).fetchall()
    conn.close()
    return items

def adicionar_item(uid, item, qtd=1):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO inventario (player_id, item, qtd) VALUES (?, ?, ?) ON CONFLICT(player_id, item) DO UPDATE SET qtd = qtd + ?", (uid, item, qtd, qtd))
    conn.commit()
    conn.close()

# UTILS
def barra(atual, total, cor="🟦"):
    if total <= 0: return "⬜"*10
    p = max(0, min(atual/total, 1))
    return cor*int(p*10) + "⬜"*(10-int(p*10))

def img_classe(c):
    return IMAGENS["classes"].get(c, IMAGENS["logo"])

def atk_total(p):
    return 10 + (p['lv']*2) + p['atk_bonus']

def def_total(p):
    return 5 + p['lv'] + p['def_bonus']

# MENU PRINCIPAL
async def menu(upd, ctx, uid, txt=""):
    p = get_player(uid)
    if not p: return
    mapa = MAPAS.get(p['mapa_atual'], {}).get('nome', '?')
    cap = f"🎮 **{VERSAO}**\n{'━'*20}\n👤 **{p['nome']}** — *{p['classe']} Lv. {p['lv']}*\n🗺️ **Local:** {mapa}\n\n❤️ **HP:** {p['hp']}/{p['hp_max']}\n└ {barra(p['hp'],p['hp_max'],'🟥')}\n\n✨ **XP:** {p['exp']}/{p['lv']*100}\n└ {barra(p['exp'],p['lv']*100)}\n\n⚔️ **ATK:** {atk_total(p)} | 🛡️ **DEF:** {def_total(p)}\n💰 **Gold:** `{p['gold']}` | ⚡ **Energy:** `{p['energia']}/{p['energia_max']}`\n{'━'*20}\n{txt}"
    kb = [[InlineKeyboardButton("⚔️ Caçar","cacar"),InlineKeyboardButton("🗺️ Mapas","mapas")],[InlineKeyboardButton("🎒 Mochila","inventario"),InlineKeyboardButton("👤 Status","perfil")],[InlineKeyboardButton("🏪 Loja","loja"),InlineKeyboardButton("🏰 Dungeons","dungeons")],[InlineKeyboardButton("⚙️ Config","config")]]
    img = img_classe(p['classe'])
    if upd.callback_query:
        try:
            await upd.callback_query.edit_message_caption(caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
        except:
            try: await upd.callback_query.message.delete()
            except: pass
            await ctx.bot.send_photo(upd.effective_chat.id, img, caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    else:
        await upd.message.reply_photo(img, caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

# CONFIG MENU
async def config(upd, ctx):
    q = upd.callback_query
    await q.answer()
    cap = f"⚙️ **CONFIGURAÇÕES**\n{'━'*20}\n🔄 **Reset** - Recomeçar\n⚡ **Level MAX** - Level 99\n💰 **Gold MAX** - 999,999 gold\n{'━'*20}"
    kb = [[InlineKeyboardButton("🔄 Reset","reset_conf")],[InlineKeyboardButton("⚡ Level MAX","cheat_lv")],[InlineKeyboardButton("💰 Gold MAX","cheat_gold")],[InlineKeyboardButton("🔙 Voltar","voltar_menu")]]
    try:
        await q.edit_message_caption(caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    except:
        await q.edit_message_text(cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def reset_conf(upd, ctx):
    q = upd.callback_query
    await q.answer()
    cap = f"⚠️ **ATENÇÃO!**\n{'━'*20}\n**DELETAR** personagem?\n❌ **IRREVERSÍVEL**!\nPerderá tudo!\n{'━'*20}"
    kb = [[InlineKeyboardButton("✅ SIM","reset_yes")],[InlineKeyboardButton("❌ NÃO","config")]]
    try:
        await q.edit_message_caption(caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    except:
        await q.edit_message_text(cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def reset_yes(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    delete_player(uid)
    await q.answer("✅ Deletado!", show_alert=True)
    cap = f"✨ **AVENTURA RABISCADA** ✨\n{'━'*20}\nPersonagem deletado.\nCrie um novo!\nVersão: `{VERSAO}`\n{'━'*20}"
    kb = [[InlineKeyboardButton("🎮 Criar Novo","ir_para_classes")]]
    try: await q.message.delete()
    except: pass
    await ctx.bot.send_photo(upd.effective_chat.id, IMAGENS["logo"], caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def cheat_lv(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    conn = sqlite3.connect(DB_FILE)
    conn.execute("UPDATE players SET lv=99,exp=0,hp_max=9999,hp=9999,energia_max=999,energia=999 WHERE id=?", (uid,))
    conn.commit()
    conn.close()
    await q.answer("⚡ LEVEL 99!", show_alert=True)
    await menu(upd, ctx, uid, "⚡ **Level 99 alcançado!**")

async def cheat_gold(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    conn = sqlite3.connect(DB_FILE)
    conn.execute("UPDATE players SET gold=999999 WHERE id=?", (uid,))
    conn.commit()
    conn.close()
    await q.answer("💰 999,999 GOLD!", show_alert=True)
    await menu(upd, ctx, uid, "💰 **999,999 gold recebido!**")

# MAPAS
async def mapas(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    p = get_player(uid)
    await q.answer()
    cap = f"🗺️ **MAPAS DISPONÍVEIS**\n{'━'*20}\n"
    kb = []
    for mid, m in MAPAS.items():
        status = "✅" if p['lv'] >= m['nivel_min'] else f"🔒 Lv.{m['nivel_min']}"
        atual = " 📍" if mid == p['mapa_atual'] else ""
        cap += f"{status} **{m['nome']}**{atual}\n└ XP: {m['xp']} | Gold: {m['gold']}\n"
        if p['lv'] >= m['nivel_min']:
            kb.append([InlineKeyboardButton(f"🗺️ {m['nome']}",f"viajar_{mid}")])
    kb.append([InlineKeyboardButton("🔙 Voltar","voltar_menu")])
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
    conn.execute("UPDATE players SET mapa_atual=? WHERE id=?", (mid,uid))
    conn.commit()
    conn.close()
    await q.answer(f"🗺️ Viajou para {MAPAS[mid]['nome']}!")
    await menu(upd, ctx, uid, f"🗺️ **Chegou em {MAPAS[mid]['nome']}!**")

# CAÇAR
async def cacar(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    p = get_player(uid)
    if not p:
        await q.answer("Crie personagem!", show_alert=True)
        return
    if p['energia'] < 2:
        await q.answer("🪫 Sem energia!", show_alert=True)
        return
    await q.answer("⚔️ Caçando...")
    
    # Inimigos do mapa atual
    inimigos_mapa = [nome for nome, dados in INIMIGOS.items() if p['mapa_atual'] in dados['mapas']]
    if not inimigos_mapa:
        await menu(upd, ctx, uid, "❌ **Nenhum inimigo neste mapa!**")
        return
    
    inimigo_nome = random.choice(inimigos_mapa)
    inimigo = INIMIGOS[inimigo_nome]
    
    # Combate simplificado
    player_atk = atk_total(p)
    player_def = def_total(p)
    
    dano_player = max(1, player_atk - (inimigo['atk']//2))
    dano_inimigo = max(1, inimigo['atk'] - player_def)
    
    turnos = (inimigo['hp'] // dano_player) + 1
    dano_total = dano_inimigo * turnos
    
    novo_hp = max(0, p['hp'] - dano_total)
    gold_ganho = inimigo['gold'] + random.randint(-5, 5)
    xp_ganho = inimigo['xp'] + random.randint(-5, 5)
    
    conn = sqlite3.connect(DB_FILE)
    conn.execute("UPDATE players SET hp=?,gold=gold+?,exp=exp+?,energia=energia-2 WHERE id=?", (novo_hp, gold_ganho, xp_ganho, uid))
    conn.commit()
    conn.close()
    
    resultado = f"⚔️ **Batalha vs {inimigo_nome}!**\n💥 Dano recebido: -{dano_total}\n💰 Gold: +{gold_ganho}\n✨ XP: +{xp_ganho}"
    await menu(upd, ctx, uid, resultado)

# PERFIL
async def perfil(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    p = get_player(uid)
    await q.answer()
    cap = f"👤 **PERFIL**\n{'━'*20}\n📛 {p['nome']}\n🎭 {p['classe']}\n⭐ Level {p['lv']}\n\n❤️ HP: {p['hp']}/{p['hp_max']}\n└ {barra(p['hp'],p['hp_max'],'🟥')}\n\n✨ XP: {p['exp']}/{p['lv']*100}\n└ {barra(p['exp'],p['lv']*100)}\n\n💰 Ouro: {p['gold']}\n⚡ Energia: {p['energia']}/{p['energia_max']}\n⚔️ Ataque: {atk_total(p)}\n🛡️ Defesa: {def_total(p)}\n{'━'*20}"
    kb = [[InlineKeyboardButton("🔙 Voltar","voltar_menu")]]
    try: await q.message.delete()
    except: pass
    await ctx.bot.send_photo(upd.effective_chat.id, img_classe(p['classe']), caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

# INVENTÁRIO
async def inventario(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    p = get_player(uid)
    items = get_inventario(uid)
    await q.answer()
    cap = f"🎒 **MOCHILA DE {p['nome'].upper()}**\n{'━'*20}\n💰 Ouro: {p['gold']}\n⚡ Energia: {p['energia']}/{p['energia_max']}\n\n📦 **Equipamentos:**\n"
    if p['arma']:
        cap += f"⚔️ {p['arma']} (+{EQUIPAMENTOS[p['arma']]['atk']} ATK)\n"
    if p['armadura']:
        cap += f"🛡️ {p['armadura']} (+{EQUIPAMENTOS[p['armadura']]['def']} DEF)\n"
    cap += f"\n📦 **Itens:**\n"
    if items:
        for i in items:
            cap += f"└ {i['item']} x{i['qtd']}\n"
    else:
        cap += "└ _Vazio_\n"
    cap += f"{'━'*20}"
    kb = [[InlineKeyboardButton("🔙 Voltar","voltar_menu")]]
    try: await q.message.delete()
    except: pass
    await ctx.bot.send_photo(upd.effective_chat.id, img_classe(p['classe']), caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

# LOJA
async def loja(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    p = get_player(uid)
    await q.answer()
    cap = f"🏪 **LOJA**\n{'━'*20}\n💰 Seu gold: {p['gold']}\n\n**Equipamentos:**\n"
    kb = []
    for nome, eq in EQUIPAMENTOS.items():
        status = "✅" if p['lv'] >= eq['lv'] else f"🔒 Lv.{eq['lv']}"
        tipo_emoji = "⚔️" if eq['tipo']=="arma" else "🛡️"
        stat = f"+{eq.get('atk',eq.get('def'))}"
        cap += f"{status} {tipo_emoji} **{nome}** {stat}\n└ 💰 {eq['preco']} gold\n"
        if p['lv'] >= eq['lv'] and p['gold'] >= eq['preco']:
            kb.append([InlineKeyboardButton(f"💰 Comprar {nome}",f"comprar_{nome}")])
    kb.append([InlineKeyboardButton("🔙 Voltar","voltar_menu")])
    cap += f"{'━'*20}"
    try:
        await q.edit_message_caption(caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    except:
        await q.edit_message_text(cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def comprar(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    p = get_player(uid)
    item = '_'.join(q.data.split('_')[1:])
    eq = EQUIPAMENTOS[item]
    if p['gold'] < eq['preco']:
        await q.answer("💸 Gold insuficiente!", show_alert=True)
        return
    conn = sqlite3.connect(DB_FILE)
    if eq['tipo']=="arma":
        conn.execute("UPDATE players SET gold=gold-?,arma=?,atk_bonus=? WHERE id=?", (eq['preco'],item,eq['atk'],uid))
    else:
        conn.execute("UPDATE players SET gold=gold-?,armadura=?,def_bonus=? WHERE id=?", (eq['preco'],item,eq['def'],uid))
    conn.commit()
    conn.close()
    await q.answer(f"✅ {item} comprado!", show_alert=True)
    await menu(upd, ctx, uid, f"✅ **{item} equipado!**")

# DUNGEONS
async def dungeons(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    p = get_player(uid)
    await q.answer()
    cap = f"🏰 **DUNGEONS**\n{'━'*20}\n"
    kb = []
    for i, d in enumerate(DUNGEONS):
        status = "✅" if p['lv'] >= d['lv'] else f"🔒 Lv.{d['lv']}"
        cap += f"{status} **{d['nome']}**\n└ Boss: {d['boss']}\n└ XP: {d['xp']} | Gold: {d['gold']}\n"
        if p['lv'] >= d['lv']:
            kb.append([InlineKeyboardButton(f"🏰 {d['nome']}",f"dungeon_{i}")])
    kb.append([InlineKeyboardButton("🔙 Voltar","voltar_menu")])
    cap += f"{'━'*20}"
    try:
        await q.edit_message_caption(caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    except:
        await q.edit_message_text(cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def entrar_dungeon(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    p = get_player(uid)
    did = int(q.data.split('_')[1])
    d = DUNGEONS[did]
    if p['energia'] < 10:
        await q.answer("🪫 Precisa de 10 energia!", show_alert=True)
        return
    await q.answer("🏰 Entrando na dungeon...")
    
    # Combate simplificado com boss
    boss_hp = 500 + (did*200)
    boss_atk = 30 + (did*10)
    player_atk = atk_total(p)
    player_def = def_total(p)
    
    dano = max(1, boss_atk - player_def)
    vitoria = random.choice([True, False]) if p['lv'] >= d['lv'] else False
    
    if vitoria:
        conn = sqlite3.connect(DB_FILE)
        conn.execute("UPDATE players SET gold=gold+?,exp=exp+?,energia=energia-10,hp=MAX(1,hp-?) WHERE id=?", (d['gold'],d['xp'],dano,uid))
        conn.execute("INSERT OR IGNORE INTO dungeons_completas VALUES (?,?)", (uid,did))
        conn.commit()
        conn.close()
        resultado = f"🏆 **VITÓRIA vs {d['boss']}!**\n💥 Dano: -{dano}\n💰 Gold: +{d['gold']}\n✨ XP: +{d['xp']}"
    else:
        conn = sqlite3.connect(DB_FILE)
        conn.execute("UPDATE players SET energia=energia-10,hp=MAX(1,hp-?) WHERE id=?", (dano*2,uid))
        conn.commit()
        conn.close()
        resultado = f"💀 **DERROTA vs {d['boss']}**\n💥 Dano: -{dano*2}\nTente quando estiver mais forte!"
    
    await menu(upd, ctx, uid, resultado)

# VOLTAR
async def voltar_menu(upd, ctx):
    q = upd.callback_query
    await q.answer()
    await menu(upd, ctx, upd.effective_user.id)

# CRIAR PERSONAGEM
async def start(upd, ctx):
    uid = upd.effective_user.id
    p = get_player(uid)
    if p:
        await menu(upd, ctx, uid)
        return ConversationHandler.END
    ctx.user_data.clear()
    cap = f"✨ **AVENTURA RABISCADA** ✨\n{'━'*20}\nUm RPG épico!\nVersão: `{VERSAO}`\n{'━'*20}"
    kb = [[InlineKeyboardButton("🎮 Começar", callback_data="ir_para_classes")]]
    await upd.message.reply_photo(IMAGENS["logo"], caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    return TELA_CLASSE

async def menu_classes(upd, ctx):
    q = upd.callback_query
    await q.answer()
    cap = f"🎭 **ESCOLHA SUA CLASSE**\n{'━'*20}\n🛡️ **Guerreiro** - Forte\n🏹 **Arqueiro** - Ágil\n🔮 **Bruxa** - Sábia\n🔥 **Mago** - Poderoso\n{'━'*20}"
    kb = [[InlineKeyboardButton("🛡️ Guerreiro","Guerreiro"),InlineKeyboardButton("🏹 Arqueiro","Arqueiro")],[InlineKeyboardButton("🔮 Bruxa","Bruxa"),InlineKeyboardButton("🔥 Mago","Mago")]]
    try: await q.message.delete()
    except: pass
    await ctx.bot.send_photo(upd.effective_chat.id, IMAGENS["selecao_classes"], caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    return TELA_NOME

async def salvar_nome(upd, ctx):
    q = upd.callback_query
    ctx.user_data['classe'] = q.data
    await q.answer()
    cap = f"✅ **{q.data.upper()} selecionado!**\n{'━'*20}\nDigite o **nome** do seu herói:"
    try: await q.message.delete()
    except: pass
    await ctx.bot.send_photo(upd.effective_chat.id, img_classe(q.data), caption=cap, parse_mode='Markdown')
    return TELA_NOME

async def finalizar(upd, ctx):
    uid = upd.effective_user.id
    nome = upd.message.text
    classe = ctx.user_data.get('classe','Guerreiro')
    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT OR REPLACE INTO players VALUES (?,?,?,100,100,1,0,100,20,20,1,NULL,NULL,0,0)", (uid,nome,classe))
    conn.commit()
    conn.close()
    await upd.message.reply_text(f"✨ **{nome}** criado!")
    await menu(upd, ctx, uid)
    return ConversationHandler.END

# MAIN
def main():
    init_db()
    token = "8506567958:AAEKQHo-TsjW55WeKGwiqVvLYglEWQusxdg"
    app = ApplicationBuilder().token(token).build()
    
    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            TELA_CLASSE: [CallbackQueryHandler(menu_classes, pattern='^ir_para_classes$')],
            TELA_NOME: [CallbackQueryHandler(salvar_nome), MessageHandler(filters.TEXT & ~filters.COMMAND, finalizar)]
        },
        fallbacks=[CommandHandler('start', start)]
    )
    
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(cacar, pattern='^cacar$'))
    app.add_handler(CallbackQueryHandler(mapas, pattern='^mapas$'))
    app.add_handler(CallbackQueryHandler(viajar, pattern='^viajar_'))
    app.add_handler(CallbackQueryHandler(perfil, pattern='^perfil$'))
    app.add_handler(CallbackQueryHandler(inventario, pattern='^inventario$'))
    app.add_handler(CallbackQueryHandler(loja, pattern='^loja$'))
    app.add_handler(CallbackQueryHandler(comprar, pattern='^comprar_'))
    app.add_handler(CallbackQueryHandler(dungeons, pattern='^dungeons$'))
    app.add_handler(CallbackQueryHandler(entrar_dungeon, pattern='^dungeon_'))
    app.add_handler(CallbackQueryHandler(config, pattern='^config$'))
    app.add_handler(CallbackQueryHandler(reset_conf, pattern='^reset_conf$'))
    app.add_handler(CallbackQueryHandler(reset_yes, pattern='^reset_yes$'))
    app.add_handler(CallbackQueryHandler(cheat_lv, pattern='^cheat_lv$'))
    app.add_handler(CallbackQueryHandler(cheat_gold, pattern='^cheat_gold$'))
    app.add_handler(CallbackQueryHandler(voltar_menu, pattern='^voltar_menu$'))
    
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
