"""
🎮 BOT RPG TELEGRAM - VERSÃO MELHORADA E CORRIGIDA
Por: Seu Nome

MELHORIAS IMPLEMENTADAS:
✅ Banco de dados SQLite (dados NÃO se perdem!)
✅ Sistema de XP e Level Up
✅ Combate completo com turnos
✅ Sistema de energia e descanso
✅ Estatísticas de vitórias/derrotas
✅ Monstros que escalam com seu level
✅ Código organizado e comentado
✅ CORRIGIDO: Erro de asyncio event loop
"""

import random
import sqlite3
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

# ============================================
# CONFIGURAÇÕES
# ============================================
TOKEN = "8506567958:AAFn-GXHiZWnXDCn2sVvnZ1aG43aputD2hw"
DB_FILE = "rpg_game.db"

# ============================================
# ITENS DO JOGO
# ============================================
ITENS = {
    # ARMAS
    "Espada de Madeira": {
        "tipo": "arma",
        "ataque": 3,
        "preco": 20,
        "desc": "Uma espada simples de treino"
    },
    "Espada de Ferro": {
        "tipo": "arma",
        "ataque": 8,
        "preco": 100,
        "desc": "Espada forjada com ferro de qualidade"
    },
    "Espada Flamejante": {
        "tipo": "arma",
        "ataque": 15,
        "preco": 350,
        "desc": "Lâmina envolta em chamas"
    },
    
    # ARMADURAS
    "Roupa de Pano": {
        "tipo": "armadura",
        "defesa": 2,
        "preco": 15,
        "desc": "Roupas simples"
    },
    "Armadura de Couro": {
        "tipo": "armadura",
        "defesa": 6,
        "preco": 80,
        "desc": "Armadura leve e resistente"
    },
    "Armadura de Placas": {
        "tipo": "armadura",
        "defesa": 12,
        "preco": 300,
        "desc": "Armadura pesada de metal"
    },
    
    # CONSUMÍVEIS
    "Poção de Vida": {
        "tipo": "consumivel",
        "hp_recupera": 50,
        "preco": 30,
        "desc": "Restaura 50 HP"
    },
    "Poção Grande": {
        "tipo": "consumivel",
        "hp_recupera": 100,
        "preco": 70,
        "desc": "Restaura 100 HP"
    },
}

# ============================================
# FUNÇÕES DE INVENTÁRIO
# ============================================
def adicionar_item(uid, item_nome, quantidade=1):
    """Adiciona item ao inventário"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    item = ITENS.get(item_nome)
    if not item:
        conn.close()
        return False
    
    # Verificar se já tem o item
    c.execute('SELECT id, quantidade FROM inventario WHERE user_id = ? AND item_nome = ?', 
              (uid, item_nome))
    resultado = c.fetchone()
    
    if resultado:
        # Já tem, aumentar quantidade
        nova_qtd = resultado[1] + quantidade
        c.execute('UPDATE inventario SET quantidade = ? WHERE id = ?', (nova_qtd, resultado[0]))
    else:
        # Não tem, adicionar novo
        c.execute('INSERT INTO inventario (user_id, item_nome, item_tipo, quantidade) VALUES (?, ?, ?, ?)',
                 (uid, item_nome, item['tipo'], quantidade))
    
    conn.commit()
    conn.close()
    return True

def remover_item(uid, item_nome, quantidade=1):
    """Remove item do inventário"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute('SELECT id, quantidade FROM inventario WHERE user_id = ? AND item_nome = ?',
             (uid, item_nome))
    resultado = c.fetchone()
    
    if resultado:
        nova_qtd = resultado[1] - quantidade
        if nova_qtd <= 0:
            c.execute('DELETE FROM inventario WHERE id = ?', (resultado[0],))
        else:
            c.execute('UPDATE inventario SET quantidade = ? WHERE id = ?', (nova_qtd, resultado[0]))
        conn.commit()
        conn.close()
        return True
    
    conn.close()
    return False

def obter_inventario(uid):
    """Retorna inventário do player"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute('SELECT item_nome, item_tipo, quantidade FROM inventario WHERE user_id = ?', (uid,))
    itens = c.fetchall()
    conn.close()
    
    return [{"nome": i[0], "tipo": i[1], "quantidade": i[2]} for i in itens]

def equipar_item(uid, item_nome):
    """Equipa arma ou armadura"""
    if item_nome not in ITENS:
        return False
    
    item = ITENS[item_nome]
    
    # Verificar se tem o item no inventário
    inventario = obter_inventario(uid)
    if not any(i['nome'] == item_nome for i in inventario):
        return False
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    if item['tipo'] == 'arma':
        c.execute('INSERT OR REPLACE INTO equipamentos (user_id, arma) VALUES (?, ?)',
                 (uid, item_nome))
    elif item['tipo'] == 'armadura':
        c.execute('INSERT OR REPLACE INTO equipamentos (user_id, armadura) VALUES (?, ?)',
                 (uid, item_nome))
    
    conn.commit()
    conn.close()
    return True

def obter_equipamentos(uid):
    """Retorna equipamentos do player"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute('SELECT arma, armadura FROM equipamentos WHERE user_id = ?', (uid,))
    resultado = c.fetchone()
    conn.close()
    
    if resultado:
        return {"arma": resultado[0], "armadura": resultado[1]}
    return {"arma": None, "armadura": None}

def calcular_bonus_equipamentos(uid):
    """Calcula bônus dos equipamentos"""
    equip = obter_equipamentos(uid)
    bonus_atk = 0
    bonus_def = 0
    
    if equip['arma'] and equip['arma'] in ITENS:
        bonus_atk = ITENS[equip['arma']].get('ataque', 0)
    
    if equip['armadura'] and equip['armadura'] in ITENS:
        bonus_def = ITENS[equip['armadura']].get('defesa', 0)
    
    return bonus_atk, bonus_def

# ============================================
# CLASSES DE PERSONAGEM
# ============================================
CLASSES = {
    "Guerreiro": {
        "img": "https://picsum.photos/seed/knight/400/300",
        "hp_base": 120,
        "energia_base": 20,
        "ataque_base": 15,
        "defesa_base": 10,
        "desc": "🛡️ Tanque resistente com muito HP"
    },
    "Bruxa": {
        "img": "https://picsum.photos/seed/witch/400/300",
        "hp_base": 80,
        "energia_base": 30,
        "ataque_base": 20,
        "defesa_base": 5,
        "desc": "🔮 Dano alto, mas frágil"
    },
    "Ladino": {
        "img": "https://picsum.photos/seed/rogue/400/300",
        "hp_base": 90,
        "energia_base": 25,
        "ataque_base": 18,
        "defesa_base": 7,
        "desc": "🗡️ Rápido com críticos frequentes"
    },
    "Druida": {
        "img": "https://picsum.photos/seed/druid/400/300",
        "hp_base": 100,
        "energia_base": 22,
        "ataque_base": 12,
        "defesa_base": 8,
        "desc": "🌿 Equilibrado e versátil"
    },
}

# ============================================
# MONSTROS (Aumentam de dificuldade)
# ============================================
MONSTROS = {
    # Level 1-3
    "tier1": [
        {"nome": "Slime", "hp": 30, "ataque": 5, "gold_min": 5, "gold_max": 15, "xp": 20},
        {"nome": "Goblin", "hp": 40, "ataque": 8, "gold_min": 8, "gold_max": 20, "xp": 30},
    ],
    # Level 4-7
    "tier2": [
        {"nome": "Lobo", "hp": 60, "ataque": 12, "gold_min": 15, "gold_max": 30, "xp": 50},
        {"nome": "Orc", "hp": 80, "ataque": 15, "gold_min": 20, "gold_max": 40, "xp": 70},
    ],
    # Level 8+
    "tier3": [
        {"nome": "Dragão Jovem", "hp": 150, "ataque": 25, "gold_min": 50, "gold_max": 100, "xp": 150},
        {"nome": "Demônio", "hp": 120, "ataque": 30, "gold_min": 40, "gold_max": 80, "xp": 120},
    ]
}

# ============================================
# BANCO DE DADOS
# ============================================
def criar_banco():
    """Cria o banco de dados se não existir"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS players (
        user_id INTEGER PRIMARY KEY,
        classe TEXT NOT NULL,
        level INTEGER DEFAULT 1,
        xp INTEGER DEFAULT 0,
        hp_atual INTEGER NOT NULL,
        hp_max INTEGER NOT NULL,
        energia_atual INTEGER NOT NULL,
        energia_max INTEGER NOT NULL,
        ataque INTEGER NOT NULL,
        defesa INTEGER NOT NULL,
        gold INTEGER DEFAULT 0,
        vitorias INTEGER DEFAULT 0,
        derrotas INTEGER DEFAULT 0
    )''')
    
    # Tabela de inventário
    c.execute('''CREATE TABLE IF NOT EXISTS inventario (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        item_nome TEXT NOT NULL,
        item_tipo TEXT NOT NULL,
        quantidade INTEGER DEFAULT 1,
        FOREIGN KEY (user_id) REFERENCES players (user_id)
    )''')
    
    # Tabela de equipamentos
    c.execute('''CREATE TABLE IF NOT EXISTS equipamentos (
        user_id INTEGER PRIMARY KEY,
        arma TEXT,
        armadura TEXT,
        FOREIGN KEY (user_id) REFERENCES players (user_id)
    )''')
    
    conn.commit()
    conn.close()
    print("✅ Banco de dados criado!")

def salvar_player(uid, dados):
    """Salva dados do player no banco"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute('''INSERT OR REPLACE INTO players 
                 (user_id, classe, level, xp, hp_atual, hp_max, energia_atual, 
                  energia_max, ataque, defesa, gold, vitorias, derrotas)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (uid, dados['classe'], dados['level'], dados['xp'], 
               dados['hp_atual'], dados['hp_max'], dados['energia_atual'],
               dados['energia_max'], dados['ataque'], dados['defesa'],
               dados['gold'], dados['vitorias'], dados['derrotas']))
    
    conn.commit()
    conn.close()

def carregar_player(uid):
    """Carrega dados do player do banco"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute('SELECT * FROM players WHERE user_id = ?', (uid,))
    row = c.fetchone()
    conn.close()
    
    if row:
        return {
            'classe': row[1],
            'level': row[2],
            'xp': row[3],
            'hp_atual': row[4],
            'hp_max': row[5],
            'energia_atual': row[6],
            'energia_max': row[7],
            'ataque': row[8],
            'defesa': row[9],
            'gold': row[10],
            'vitorias': row[11],
            'derrotas': row[12]
        }
    return None

def deletar_player(uid):
    """Deleta player do banco"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('DELETE FROM players WHERE user_id = ?', (uid,))
    conn.commit()
    conn.close()

# ============================================
# SISTEMA DE PROGRESSÃO
# ============================================
def xp_para_proximo_level(level):
    """Calcula XP necessário para próximo level"""
    return int(100 * (level ** 1.5))

def aplicar_level_up(uid):
    """Verifica e aplica level ups"""
    player = carregar_player(uid)
    msgs = []
    
    while player['xp'] >= xp_para_proximo_level(player['level']):
        player['xp'] -= xp_para_proximo_level(player['level'])
        player['level'] += 1
        
        # Aumentar stats
        player['hp_max'] += 20
        player['energia_max'] += 5
        player['ataque'] += 3
        player['defesa'] += 2
        
        # Restaurar HP e energia
        player['hp_atual'] = player['hp_max']
        player['energia_atual'] = player['energia_max']
        
        msgs.append(f"🎉 LEVEL UP! Agora você é Level {player['level']}!")
        msgs.append(f"📈 +20 HP | +5 Energia | +3 ATK | +2 DEF")
    
    salvar_player(uid, player)
    return msgs

# ============================================
# SISTEMA DE COMBATE
# ============================================
def escolher_monstro(player_level):
    """Escolhe monstro apropriado para o level"""
    if player_level <= 3:
        tier = "tier1"
    elif player_level <= 7:
        tier = "tier2"
    else:
        tier = "tier3"
    
    monstro = random.choice(MONSTROS[tier]).copy()
    return monstro

def simular_combate(player, monstro):
    """Simula combate completo"""
    hp_player = player['hp_atual']
    hp_monstro = monstro['hp']
    log = []
    
    turno = 1
    while hp_player > 0 and hp_monstro > 0 and turno <= 20:
        # Turno do player
        dano = max(1, player['ataque'] - (monstro.get('defesa', 0) // 2))
        dano += random.randint(-2, 5)  # Variação
        
        # Chance de crítico (15%)
        if random.random() < 0.15:
            dano = int(dano * 1.5)
            log.append(f"⚔️ Você deu {dano} CRÍTICO!")
        else:
            log.append(f"⚔️ Você deu {dano} de dano")
        
        hp_monstro -= dano
        
        if hp_monstro <= 0:
            break
        
        # Turno do monstro
        dano_monstro = max(1, monstro['ataque'] - (player['defesa'] // 2))
        dano_monstro += random.randint(-1, 3)
        hp_player -= dano_monstro
        
        log.append(f"💥 {monstro['nome']} causou {dano_monstro} de dano")
        
        turno += 1
    
    vitoria = hp_player > 0
    return vitoria, hp_player, log

# ============================================
# INTERFACE - MENUS
# ============================================
def criar_barra(atual, maximo, tipo="hp"):
    """Cria barra de progresso visual BONITA"""
    porcentagem = atual / maximo if maximo > 0 else 0
    cheios = int(porcentagem * 5)  # 5 blocos
    vazios = 5 - cheios
    
    if tipo == "hp":
        return "🟥" * cheios + "⬜" * vazios
    elif tipo == "energia":
        return "🟩" * cheios + "⬜" * vazios
    elif tipo == "xp":
        return "🟨" * cheios + "⬜" * vazios

def menu_principal(uid):
    """Gera menu principal do jogo"""
    p = carregar_player(uid)
    classe_info = CLASSES[p['classe']]
    
    # Calcular bônus de equipamentos
    bonus_atk, bonus_def = calcular_bonus_equipamentos(uid)
    atk_total = p['ataque'] + bonus_atk
    def_total = p['defesa'] + bonus_def
    
    # Barras BONITAS com emojis coloridos
    barra_hp = criar_barra(p['hp_atual'], p['hp_max'], "hp")
    barra_en = criar_barra(p['energia_atual'], p['energia_max'], "energia")
    barra_xp = criar_barra(p['xp'], xp_para_proximo_level(p['level']), "xp")
    
    texto = f"""🏰 **Planície** (Lv {p['level']})
👤 Classe: {p['classe']}
❤️ HP: {p['hp_atual']}/{p['hp_max']} {barra_hp}
⚡ Energia: {p['energia_atual']}/{p['energia_max']} {barra_en}
✨ XP: {p['xp']}/{xp_para_proximo_level(p['level'])} {barra_xp}
💰 Gold: {p['gold']}
"""
    
    # Mostrar equipamentos se tiver
    if bonus_atk > 0 or bonus_def > 0:
        texto += f"⚔️ ATK: {p['ataque']} (+{bonus_atk}) | 🛡️ DEF: {p['defesa']} (+{bonus_def})\n"
    else:
        texto += f"⚔️ ATK: {atk_total} | 🛡️ DEF: {def_total}\n"
    
    botoes = [
        [InlineKeyboardButton("⚔️ Caçar", callback_data='cacar'),
         InlineKeyboardButton("😴 Descansar", callback_data='descansar')],
        [InlineKeyboardButton("🎒 Inventário", callback_data='inventario'),
         InlineKeyboardButton("👤 Perfil", callback_data='perfil')],
        [InlineKeyboardButton("⚙️ Menu", callback_data='menu_config')]
    ]
    
    return texto, InlineKeyboardMarkup(botoes), classe_info['img']

def menu_inventario(uid):
    """Menu do inventário"""
    inventario = obter_inventario(uid)
    equip = obter_equipamentos(uid)
    
    if not inventario:
        texto = "🎒 **INVENTÁRIO VAZIO**\n\nVocê não tem itens ainda.\nDerrote monstros para conseguir drops!"
    else:
        texto = "🎒 **INVENTÁRIO**\n\n"
        
        # Mostrar equipados
        if equip['arma']:
            texto += f"⚔️ Equipado: **{equip['arma']}**\n"
        if equip['armadura']:
            texto += f"🛡️ Equipado: **{equip['armadura']}**\n"
        
        texto += "\n**Seus Itens:**\n"
        
        # Agrupar por tipo
        armas = [i for i in inventario if i['tipo'] == 'arma']
        armaduras = [i for i in inventario if i['tipo'] == 'armadura']
        consumiveis = [i for i in inventario if i['tipo'] == 'consumivel']
        
        if armas:
            texto += "\n⚔️ **Armas:**\n"
            for item in armas:
                info = ITENS.get(item['nome'], {})
                texto += f"  • {item['nome']} x{item['quantidade']}"
                if 'ataque' in info:
                    texto += f" (ATK +{info['ataque']})"
                texto += "\n"
        
        if armaduras:
            texto += "\n🛡️ **Armaduras:**\n"
            for item in armaduras:
                info = ITENS.get(item['nome'], {})
                texto += f"  • {item['nome']} x{item['quantidade']}"
                if 'defesa' in info:
                    texto += f" (DEF +{info['defesa']})"
                texto += "\n"
        
        if consumiveis:
            texto += "\n🧪 **Consumíveis:**\n"
            for item in consumiveis:
                info = ITENS.get(item['nome'], {})
                texto += f"  • {item['nome']} x{item['quantidade']}"
                if 'hp_recupera' in info:
                    texto += f" (+{info['hp_recupera']} HP)"
                texto += "\n"
    
    # Botões para cada item
    botoes = []
    for item in inventario:
        if item['tipo'] in ['arma', 'armadura']:
            botoes.append([InlineKeyboardButton(
                f"⚡ Equipar {item['nome']}", 
                callback_data=f"equipar_{item['nome']}"
            )])
        elif item['tipo'] == 'consumivel':
            botoes.append([InlineKeyboardButton(
                f"🧪 Usar {item['nome']}", 
                callback_data=f"usar_{item['nome']}"
            )])
    
    botoes.append([InlineKeyboardButton("◀️ Voltar", callback_data='voltar')])
    
    return texto, InlineKeyboardMarkup(botoes)

def menu_perfil(uid):
    """Menu do perfil completo"""
    p = carregar_player(uid)
    equip = obter_equipamentos(uid)
    bonus_atk, bonus_def = calcular_bonus_equipamentos(uid)
    
    taxa_vitoria = 0
    total = p['vitorias'] + p['derrotas']
    if total > 0:
        taxa_vitoria = (p['vitorias'] / total) * 100
    
    texto = f"""👤 **PERFIL DO PERSONAGEM**

**Informações Básicas:**
🎭 Classe: {p['classe']}
⭐ Level: {p['level']}
✨ XP: {p['xp']}/{xp_para_proximo_level(p['level'])}

**Atributos:**
❤️ HP: {p['hp_max']}
⚡ Energia: {p['energia_max']}
⚔️ Ataque: {p['ataque']} (+{bonus_atk}) = **{p['ataque'] + bonus_atk}**
🛡️ Defesa: {p['defesa']} (+{bonus_def}) = **{p['defesa'] + bonus_def}**

**Equipamentos:**
⚔️ Arma: {equip['arma'] or 'Nenhuma'}
🛡️ Armadura: {equip['armadura'] or 'Nenhuma'}

**Estatísticas de Combate:**
🏆 Vitórias: {p['vitorias']}
☠️ Derrotas: {p['derrotas']}
📊 Taxa de Vitória: {taxa_vitoria:.1f}%

**Riqueza:**
💰 Gold Total: {p['gold']}
"""
    
    botoes = [[InlineKeyboardButton("◀️ Voltar", callback_data='voltar')]]
    
    return texto, InlineKeyboardMarkup(botoes)

def menu_configuracoes(uid):
    """Menu de configurações"""
    texto = """⚙️ **MENU DE CONFIGURAÇÕES**

Escolha uma opção:"""
    
    botoes = [
        [InlineKeyboardButton("🔄 Resetar Personagem", callback_data='confirmar_reset')],
        [InlineKeyboardButton("📊 Estatísticas", callback_data='stats')],
        [InlineKeyboardButton("❓ Ajuda", callback_data='ajuda')],
        [InlineKeyboardButton("◀️ Voltar", callback_data='voltar')]
    ]
    
    return texto, InlineKeyboardMarkup(botoes)

def menu_confirmar_reset(uid):
    """Menu de confirmação de reset"""
    p = carregar_player(uid)
    
    texto = f"""⚠️ **ATENÇÃO!**

Você está prestes a deletar seu personagem:

👤 **{p['classe']}** - Level {p['level']}
💰 Gold: {p['gold']}
🏆 Vitórias: {p['vitorias']}

**TODOS os seus pertences e progresso serão PERDIDOS!**

Tem certeza que deseja continuar?"""
    
    botoes = [
        [InlineKeyboardButton("✅ SIM, deletar tudo", callback_data='reset_confirmado')],
        [InlineKeyboardButton("❌ NÃO, voltar", callback_data='voltar')]
    ]
    
    return texto, InlineKeyboardMarkup(botoes)

# ============================================
# HANDLERS DO BOT
# ============================================
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    uid = update.effective_user.id
    player = carregar_player(uid)
    
    if player:
        # Player existe, mostrar menu
        txt, kb, img = menu_principal(uid)
        await context.bot.send_photo(
            chat_id=uid,
            photo=img,
            caption=txt,
            reply_markup=kb,
            parse_mode='Markdown'
        )
    else:
        # Novo player, escolher classe
        img_inicio = "https://picsum.photos/seed/rpgstart/400/300"
        
        # Texto de apresentação
        texto_inicial = "✨ **BEM-VINDO AO RPG!**\n\nEscolha sua classe:\n\n"
        
        for nome, info in CLASSES.items():
            texto_inicial += f"**{nome}** - {info['desc']}\n"
        
        botoes = [
            [InlineKeyboardButton("🛡️ Guerreiro", callback_data='criar_Guerreiro'),
             InlineKeyboardButton("🔮 Bruxa", callback_data='criar_Bruxa')],
            [InlineKeyboardButton("🗡️ Ladino", callback_data='criar_Ladino'),
             InlineKeyboardButton("🌿 Druida", callback_data='criar_Druida')]
        ]
        
        await context.bot.send_photo(
            chat_id=uid,
            photo=img_inicio,
            caption=texto_inicial,
            reply_markup=InlineKeyboardMarkup(botoes),
            parse_mode='Markdown'
        )

async def processar_botoes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa cliques nos botões"""
    q = update.callback_query
    uid = q.from_user.id
    await q.answer()
    
    # ===== CRIAR PERSONAGEM =====
    if q.data.startswith('criar_'):
        classe_nome = q.data.replace('criar_', '')
        classe = CLASSES[classe_nome]
        
        novo_player = {
            'classe': classe_nome,
            'level': 1,
            'xp': 0,
            'hp_atual': classe['hp_base'],
            'hp_max': classe['hp_base'],
            'energia_atual': classe['energia_base'],
            'energia_max': classe['energia_base'],
            'ataque': classe['ataque_base'],
            'defesa': classe['defesa_base'],
            'gold': 0,
            'vitorias': 0,
            'derrotas': 0
        }
        
        salvar_player(uid, novo_player)
        txt, kb, img = menu_principal(uid)
        
        await q.edit_message_media(media=InputMediaPhoto(classe['img']))
        await q.edit_message_caption(
            caption=f"✅ Você é agora um **{classe_nome}**!\n\n{txt}",
            reply_markup=kb,
            parse_mode='Markdown'
        )
    
    # ===== CAÇAR MONSTROS =====
    elif q.data == 'cacar':
        player = carregar_player(uid)
        
        if player['energia_atual'] < 2:
            await q.answer("⚡ Energia insuficiente! Descanse primeiro.", show_alert=True)
            return
        
        # Gastar energia
        player['energia_atual'] -= 2
        
        # Escolher monstro
        monstro = escolher_monstro(player['level'])
        
        # Combate!
        vitoria, hp_final, log_combate = simular_combate(player, monstro)
        
        resultado = f"⚔️ **COMBATE vs {monstro['nome']}**\n\n"
        resultado += "\n".join(log_combate[:6])  # Mostrar alguns turnos
        
        if vitoria:
            gold_ganho = random.randint(monstro['gold_min'], monstro['gold_max'])
            xp_ganho = monstro['xp']
            
            player['hp_atual'] = hp_final
            player['gold'] += gold_ganho
            player['xp'] += xp_ganho
            player['vitorias'] += 1
            
            resultado += f"\n\n✅ **VITÓRIA!**\n💰 +{gold_ganho} gold\n⭐ +{xp_ganho} XP"
            
            # Sistema de drops (30% de chance)
            if random.random() < 0.3:
                # Escolher item baseado no level
                itens_drop = []
                for nome, item in ITENS.items():
                    if item['tipo'] in ['arma', 'armadura']:
                        # Só dropar itens apropriados pro level
                        if player['level'] <= 3 and ('Madeira' in nome or 'Pano' in nome):
                            itens_drop.append(nome)
                        elif player['level'] <= 7 and ('Ferro' in nome or 'Couro' in nome):
                            itens_drop.append(nome)
                        elif player['level'] > 7:
                            itens_drop.append(nome)
                    elif item['tipo'] == 'consumivel':
                        itens_drop.append(nome)
                
                if itens_drop:
                    item_dropado = random.choice(itens_drop)
                    adicionar_item(uid, item_dropado)
                    resultado += f"\n🎁 Item dropado: **{item_dropado}**!"
            
            salvar_player(uid, player)
            msgs_levelup = aplicar_level_up(uid)
            
            if msgs_levelup:
                resultado += "\n\n" + "\n".join(msgs_levelup)
        else:
            player['hp_atual'] = player['hp_max'] // 2
            player['derrotas'] += 1
            resultado += f"\n\n☠️ **DERROTA!**\nVocê fugiu com {player['hp_atual']} HP"
            salvar_player(uid, player)
        
        txt, kb, img = menu_principal(uid)
        
        await q.edit_message_caption(
            caption=resultado + "\n\n━━━━━━━━━━\n" + txt,
            reply_markup=kb,
            parse_mode='Markdown'
        )
    
    # ===== DESCANSAR =====
    elif q.data == 'descansar':
        player = carregar_player(uid)
        
        hp_rec = min(30, player['hp_max'] - player['hp_atual'])
        en_rec = min(10, player['energia_max'] - player['energia_atual'])
        
        player['hp_atual'] += hp_rec
        player['energia_atual'] += en_rec
        
        salvar_player(uid, player)
        txt, kb, img = menu_principal(uid)
        
        await q.edit_message_caption(
            caption=f"😴 **Você descansou!**\n❤️ +{hp_rec} HP\n⚡ +{en_rec} Energia\n\n{txt}",
            reply_markup=kb,
            parse_mode='Markdown'
        )
    
    # ===== VIAJAR (em breve) =====
    elif q.data == 'viajar':
        await q.answer("🗺️ Em breve! Novas áreas virão...", show_alert=True)
    
    # ===== INVENTÁRIO =====
    elif q.data == 'inventario':
        txt, kb = menu_inventario(uid)
        await q.edit_message_caption(caption=txt, reply_markup=kb, parse_mode='Markdown')
    
    # ===== EQUIPAR ITEM =====
    elif q.data.startswith('equipar_'):
        item_nome = q.data.replace('equipar_', '')
        if equipar_item(uid, item_nome):
            txt, kb = menu_inventario(uid)
            await q.answer(f"⚡ {item_nome} equipado!", show_alert=True)
            await q.edit_message_caption(caption=txt, reply_markup=kb, parse_mode='Markdown')
        else:
            await q.answer("❌ Erro ao equipar item!", show_alert=True)
    
    # ===== USAR CONSUMÍVEL =====
    elif q.data.startswith('usar_'):
        item_nome = q.data.replace('usar_', '')
        item = ITENS.get(item_nome)
        
        if item and item['tipo'] == 'consumivel':
            player = carregar_player(uid)
            
            if 'hp_recupera' in item:
                hp_antes = player['hp_atual']
                player['hp_atual'] = min(player['hp_max'], player['hp_atual'] + item['hp_recupera'])
                hp_ganho = player['hp_atual'] - hp_antes
                msg = f"❤️ Recuperou {hp_ganho} HP!"
            
            remover_item(uid, item_nome)
            salvar_player(uid, player)
            
            txt, kb = menu_inventario(uid)
            await q.answer(msg, show_alert=True)
            await q.edit_message_caption(caption=txt, reply_markup=kb, parse_mode='Markdown')
        else:
            await q.answer("❌ Item não encontrado!", show_alert=True)
    
    # ===== PERFIL =====
    elif q.data == 'perfil':
        txt, kb = menu_perfil(uid)
        await q.edit_message_caption(caption=txt, reply_markup=kb, parse_mode='Markdown')
    
    # ===== MENU CONFIGURAÇÕES =====
    elif q.data == 'menu_config':
        txt, kb = menu_configuracoes(uid)
        await q.edit_message_caption(caption=txt, reply_markup=kb, parse_mode='Markdown')
    
    # ===== CONFIRMAR RESET =====
    elif q.data == 'confirmar_reset':
        txt, kb = menu_confirmar_reset(uid)
        await q.edit_message_caption(caption=txt, reply_markup=kb, parse_mode='Markdown')
    
    # ===== RESET CONFIRMADO =====
    elif q.data == 'reset_confirmado':
        deletar_player(uid)
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('DELETE FROM inventario WHERE user_id = ?', (uid,))
        c.execute('DELETE FROM equipamentos WHERE user_id = ?', (uid,))
        conn.commit()
        conn.close()
        
        await q.edit_message_caption(
            caption="🗑️ **Personagem deletado!**\n\nTodos os seus itens e progresso foram perdidos.\n\nUse /start para criar um novo."
        )
    
    # ===== AJUDA =====
    elif q.data == 'ajuda':
        ajuda = """❓ **GUIA DO JOGO**

**⚔️ Caçar:**
Gasta 2 energia para batalhar. Ganhe XP, gold e itens!

**😴 Descansar:**
Recupera HP e energia.

**🎒 Inventário:**
Equipe armas/armaduras, use consumíveis.

**👤 Perfil:**
Veja todas as estatísticas.

**💡 Dica:**
Equipe itens para ficar mais forte!"""
        
        botoes = [[InlineKeyboardButton("◀️ Voltar", callback_data='menu_config')]]
        await q.edit_message_caption(caption=ajuda, reply_markup=InlineKeyboardMarkup(botoes), parse_mode='Markdown')
    
    # ===== STATS =====
    elif q.data == 'stats':
        player = carregar_player(uid)
        
        taxa_vitoria = 0
        total = player['vitorias'] + player['derrotas']
        if total > 0:
            taxa_vitoria = (player['vitorias'] / total) * 100
        
        stats = f"""📊 **ESTATÍSTICAS**

⚔️ Batalhas: {total}
🏆 Vitórias: {player['vitorias']}
☠️ Derrotas: {player['derrotas']}
📈 Taxa: {taxa_vitoria:.1f}%

💰 Gold: {player['gold']}
⭐ XP: {player['xp']}"""
        
        botoes = [[InlineKeyboardButton("◀️ Voltar", callback_data='menu_config')]]
        await q.edit_message_caption(caption=stats, reply_markup=InlineKeyboardMarkup(botoes), parse_mode='Markdown')
    
    # ===== VOLTAR =====
    elif q.data == 'voltar':
        txt, kb, img = menu_principal(uid)
        await q.edit_message_caption(caption=txt, reply_markup=kb, parse_mode='Markdown')

# ============================================
# FUNÇÃO MAIN - CORRIGIDA
# ============================================
async def main():
    """Função principal assíncrona"""
    print("🚀 Iniciando RPG Bot...")
    
    # Criar banco de dados
    criar_banco()
    
    # Iniciar bot Telegram
    print("✅ Configurando bot...")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CallbackQueryHandler(processar_botoes))
    
    print("✅ Bot ONLINE!")
    print("📱 Envie /start no Telegram para começar!")
    print("🛑 Pressione Ctrl+C para parar o bot")
    
    # Executar o bot
    await app.run_polling(drop_pending_updates=True)

# ============================================
# INICIALIZAÇÃO - CORRIGIDA
# ============================================
if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot finalizado pelo usuário!")
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
