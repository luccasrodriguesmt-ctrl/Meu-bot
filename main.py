"""
🎮 BOT RPG TELEGRAM - VERSÃO COMPLETA COM COMBATE EM TURNOS
Por: Seu Nome

NOVAS MELHORIAS:
✅ Sistema de combate em TURNOS com botões
✅ Variedade de monstros + Mini Bosses
✅ Ação de DEFENDER (reduz dano)
✅ Poções com BUFFS temporários
✅ Combate estratégico e interativo
✅ Sistema de raridade de drops
"""

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

# ============================================
# ITENS DO JOGO (EXPANDIDO)
# ============================================
ITENS = {
    # ARMAS
    "Espada de Madeira": {
        "tipo": "arma",
        "ataque": 3,
        "preco": 20,
        "raridade": "comum",
        "desc": "Uma espada simples de treino"
    },
    "Espada de Ferro": {
        "tipo": "arma",
        "ataque": 8,
        "preco": 100,
        "raridade": "comum",
        "desc": "Espada forjada com ferro de qualidade"
    },
    "Espada Flamejante": {
        "tipo": "arma",
        "ataque": 15,
        "preco": 350,
        "raridade": "rara",
        "desc": "Lâmina envolta em chamas"
    },
    "Lâmina Sombria": {
        "tipo": "arma",
        "ataque": 20,
        "preco": 600,
        "raridade": "épica",
        "desc": "Espada forjada nas trevas"
    },
    
    # ARMADURAS
    "Roupa de Pano": {
        "tipo": "armadura",
        "defesa": 2,
        "preco": 15,
        "raridade": "comum",
        "desc": "Roupas simples"
    },
    "Armadura de Couro": {
        "tipo": "armadura",
        "defesa": 6,
        "preco": 80,
        "raridade": "comum",
        "desc": "Armadura leve e resistente"
    },
    "Armadura de Placas": {
        "tipo": "armadura",
        "defesa": 12,
        "preco": 300,
        "raridade": "rara",
        "desc": "Armadura pesada de metal"
    },
    "Armadura Dracônica": {
        "tipo": "armadura",
        "defesa": 18,
        "preco": 700,
        "raridade": "épica",
        "desc": "Feita de escamas de dragão"
    },
    
    # CONSUMÍVEIS - CURA
    "Poção de Vida": {
        "tipo": "consumivel",
        "efeito": "cura",
        "hp_recupera": 50,
        "preco": 30,
        "raridade": "comum",
        "desc": "Restaura 50 HP"
    },
    "Poção Grande": {
        "tipo": "consumivel",
        "efeito": "cura",
        "hp_recupera": 100,
        "preco": 70,
        "raridade": "comum",
        "desc": "Restaura 100 HP"
    },
    "Elixir Supremo": {
        "tipo": "consumivel",
        "efeito": "cura",
        "hp_recupera": 200,
        "preco": 150,
        "raridade": "rara",
        "desc": "Restaura 200 HP"
    },
    
    # CONSUMÍVEIS - BUFFS
    "Poção de Força": {
        "tipo": "consumivel",
        "efeito": "buff_ataque",
        "buff_valor": 10,
        "buff_turnos": 3,
        "preco": 50,
        "raridade": "rara",
        "desc": "🔥 +10 ATK por 3 turnos"
    },
    "Poção de Ferro": {
        "tipo": "consumivel",
        "efeito": "buff_defesa",
        "buff_valor": 8,
        "buff_turnos": 3,
        "preco": 50,
        "raridade": "rara",
        "desc": "🛡️ +8 DEF por 3 turnos"
    },
    "Poção de Fúria": {
        "tipo": "consumivel",
        "efeito": "buff_critico",
        "buff_valor": 30,  # +30% chance de crítico
        "buff_turnos": 4,
        "preco": 80,
        "raridade": "épica",
        "desc": "⚡ +30% Crítico por 4 turnos"
    },
    "Poção de Berserker": {
        "tipo": "consumivel",
        "efeito": "buff_ataque",
        "buff_valor": 20,
        "buff_turnos": 2,
        "preco": 100,
        "raridade": "épica",
        "desc": "💥 +20 ATK por 2 turnos"
    },
}

# ============================================
# MONSTROS EXPANDIDOS (com mais variedade)
# ============================================
MONSTROS = {
    # Level 1-3 - Fáceis
    "tier1": [
        {
            "nome": "Slime Verde",
            "hp": 30,
            "ataque": 5,
            "defesa": 2,
            "gold_min": 5,
            "gold_max": 15,
            "xp": 20,
            "tipo": "comum",
            "img": "https://picsum.photos/seed/slime/400/300"
        },
        {
            "nome": "Goblin Ladrão",
            "hp": 40,
            "ataque": 8,
            "defesa": 3,
            "gold_min": 8,
            "gold_max": 20,
            "xp": 30,
            "tipo": "comum",
            "img": "https://picsum.photos/seed/goblin/400/300"
        },
        {
            "nome": "Rato Gigante",
            "hp": 35,
            "ataque": 6,
            "defesa": 2,
            "gold_min": 5,
            "gold_max": 12,
            "xp": 25,
            "tipo": "comum",
            "img": "https://picsum.photos/seed/rat/400/300"
        },
    ],
    
    # Level 4-7 - Médios
    "tier2": [
        {
            "nome": "Lobo Selvagem",
            "hp": 70,
            "ataque": 12,
            "defesa": 5,
            "gold_min": 15,
            "gold_max": 30,
            "xp": 50,
            "tipo": "comum",
            "img": "https://picsum.photos/seed/wolf/400/300"
        },
        {
            "nome": "Orc Guerreiro",
            "hp": 90,
            "ataque": 15,
            "defesa": 8,
            "gold_min": 20,
            "gold_max": 40,
            "xp": 70,
            "tipo": "comum",
            "img": "https://picsum.photos/seed/orc/400/300"
        },
        {
            "nome": "Aranha Venenosa",
            "hp": 60,
            "ataque": 14,
            "defesa": 4,
            "gold_min": 18,
            "gold_max": 35,
            "xp": 60,
            "tipo": "comum",
            "img": "https://picsum.photos/seed/spider/400/300"
        },
        {
            "nome": "Bandido Mascarado",
            "hp": 75,
            "ataque": 13,
            "defesa": 6,
            "gold_min": 25,
            "gold_max": 50,
            "xp": 65,
            "tipo": "comum",
            "img": "https://picsum.photos/seed/bandit/400/300"
        },
    ],
    
    # Level 8+ - Difíceis
    "tier3": [
        {
            "nome": "Dragão Jovem",
            "hp": 150,
            "ataque": 25,
            "defesa": 12,
            "gold_min": 50,
            "gold_max": 100,
            "xp": 150,
            "tipo": "comum",
            "img": "https://picsum.photos/seed/dragon/400/300"
        },
        {
            "nome": "Demônio Menor",
            "hp": 120,
            "ataque": 30,
            "defesa": 10,
            "gold_min": 40,
            "gold_max": 80,
            "xp": 120,
            "tipo": "comum",
            "img": "https://picsum.photos/seed/demon/400/300"
        },
        {
            "nome": "Cavaleiro das Trevas",
            "hp": 140,
            "ataque": 28,
            "defesa": 15,
            "gold_min": 60,
            "gold_max": 120,
            "xp": 140,
            "tipo": "comum",
            "img": "https://picsum.photos/seed/darkknight/400/300"
        },
    ],
    
    # MINI BOSSES (10% de chance)
    "miniboss1": [
        {
            "nome": "👑 Rei Goblin",
            "hp": 100,
            "ataque": 18,
            "defesa": 8,
            "gold_min": 50,
            "gold_max": 100,
            "xp": 100,
            "tipo": "miniboss",
            "img": "https://picsum.photos/seed/goblinboss/400/300"
        },
    ],
    "miniboss2": [
        {
            "nome": "👑 Alfa Selvagem",
            "hp": 150,
            "ataque": 25,
            "defesa": 12,
            "gold_min": 80,
            "gold_max": 150,
            "xp": 150,
            "tipo": "miniboss",
            "img": "https://picsum.photos/seed/alphaboss/400/300"
        },
    ],
    "miniboss3": [
        {
            "nome": "👑 Senhor Demônio",
            "hp": 250,
            "ataque": 40,
            "defesa": 20,
            "gold_min": 150,
            "gold_max": 300,
            "xp": 250,
            "tipo": "miniboss",
            "img": "https://picsum.photos/seed/demonlord/400/300"
        },
    ],
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
    
    c.execute('SELECT id, quantidade FROM inventario WHERE user_id = ? AND item_nome = ?', 
              (uid, item_nome))
    resultado = c.fetchone()
    
    if resultado:
        nova_qtd = resultado[1] + quantidade
        c.execute('UPDATE inventario SET quantidade = ? WHERE id = ?', (nova_qtd, resultado[0]))
    else:
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
# SISTEMA DE MAPAS E LOCALIZAÇÕES
# ============================================
MAPAS = {
    "Planície de Aether": {
        "nivel_recomendado": 1,
        "tier_monstros": "tier1",
        "miniboss_tier": "miniboss1",
        "img": "https://picsum.photos/seed/plains/400/300",
        "desc": "Terras planas e verdejantes, ótimas para iniciantes",
        "vilas": ["Vila Inicial", "Povoado Verde"],
        "capital": "Castelo de Lumina"
    },
    "Floresta Sombria": {
        "nivel_recomendado": 4,
        "tier_monstros": "tier2",
        "miniboss_tier": "miniboss2",
        "img": "https://picsum.photos/seed/darkforest/400/300",
        "desc": "Floresta densa com criaturas perigosas",
        "vilas": ["Aldeia dos Caçadores"],
        "capital": "Fortaleza da Madeira"
    },
    "Montanhas Gélidas": {
        "nivel_recomendado": 8,
        "tier_monstros": "tier3",
        "miniboss_tier": "miniboss3",
        "img": "https://picsum.photos/seed/icymountain/400/300",
        "desc": "Picos nevados repletos de perigos mortais",
        "vilas": ["Refúgio do Norte", "Acampamento Gélido"],
        "capital": "Cidadela de Cristal"
    },
    "Deserto Ardente": {
        "nivel_recomendado": 7,
        "tier_monstros": "tier3",
        "miniboss_tier": "miniboss3",
        "img": "https://picsum.photos/seed/desert/400/300",
        "desc": "Areias escaldantes com tesouros escondidos",
        "vilas": ["Oásis Perdido"],
        "capital": "Palácio das Dunas"
    },
    "Pântano Maldito": {
        "nivel_recomendado": 5,
        "tier_monstros": "tier2",
        "miniboss_tier": "miniboss2",
        "img": "https://picsum.photos/seed/swamp/400/300",
        "desc": "Terras alagadas com criaturas venenosas",
        "vilas": ["Cabana do Pântano", "Porto Sombrio"],
        "capital": None
    },
    "Ruínas Antigas": {
        "nivel_recomendado": 10,
        "tier_monstros": "tier3",
        "miniboss_tier": "miniboss3",
        "img": "https://picsum.photos/seed/ruins/400/300",
        "desc": "Estruturas antigas repletas de mistérios",
        "vilas": ["Acampamento dos Exploradores"],
        "capital": "Torre do Saber"
    }
}

# ============================================
# TIPOS DE DESCANSO
# ============================================
TIPOS_DESCANSO = {
    "Acampamento": {
        "hp_recupera": 30,
        "energia_recupera": 10,
        "custo": 20,
        "emoji": "⛺",
        "desc": "Descanse em uma tenda simples"
    },
    "Casa": {
        "hp_recupera": 50,
        "energia_recupera": 20,
        "custo": 50,
        "emoji": "🏠",
        "desc": "Descanse confortavelmente em uma casa"
    },
    "Pousada": {
        "hp_recupera": 100,
        "energia_recupera": 30,
        "custo": 100,
        "emoji": "🏨",
        "desc": "Luxo e descanso completo"
    }
}

# ============================================
# LOJAS - Cada localização tem itens diferentes
# ============================================
LOJA_ITENS = {
    # LOJA DE VILAS (itens básicos e médios)
    "vila": {
        "Espada de Madeira": {"preco": 20, "nivel_req": 1},
        "Espada de Ferro": {"preco": 100, "nivel_req": 3},
        "Roupa de Pano": {"preco": 15, "nivel_req": 1},
        "Armadura de Couro": {"preco": 80, "nivel_req": 3},
        "Poção de Vida": {"preco": 30, "nivel_req": 1},
        "Poção Grande": {"preco": 70, "nivel_req": 3},
        "Poção de Força": {"preco": 50, "nivel_req": 4},
        "Poção de Ferro": {"preco": 50, "nivel_req": 4},
    },
    
    # LOJA DE CAPITAL (itens avançados)
    "capital": {
        "Espada de Ferro": {"preco": 100, "nivel_req": 3},
        "Espada Flamejante": {"preco": 350, "nivel_req": 6},
        "Lâmina Sombria": {"preco": 600, "nivel_req": 9},
        "Armadura de Couro": {"preco": 80, "nivel_req": 3},
        "Armadura de Placas": {"preco": 300, "nivel_req": 6},
        "Armadura Dracônica": {"preco": 700, "nivel_req": 9},
        "Poção Grande": {"preco": 70, "nivel_req": 3},
        "Elixir Supremo": {"preco": 150, "nivel_req": 6},
        "Poção de Força": {"preco": 50, "nivel_req": 4},
        "Poção de Ferro": {"preco": 50, "nivel_req": 4},
        "Poção de Fúria": {"preco": 80, "nivel_req": 6},
    },
    
    # CONTRABANDISTA (itens raros com desconto, mas preço em gold alto)
    "contrabandista": {
        "Espada Flamejante": {"preco": 280, "nivel_req": 5},  # Mais barato mas ainda caro
        "Lâmina Sombria": {"preco": 500, "nivel_req": 8},
        "Armadura de Placas": {"preco": 250, "nivel_req": 5},
        "Armadura Dracônica": {"preco": 600, "nivel_req": 8},
        "Elixir Supremo": {"preco": 120, "nivel_req": 5},
        "Poção de Fúria": {"preco": 65, "nivel_req": 5},
        "Poção de Berserker": {"preco": 85, "nivel_req": 7},
    }
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
        nome TEXT NOT NULL,
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
        derrotas INTEGER DEFAULT 0,
        mapa_atual TEXT DEFAULT 'Planície de Aether',
        ultima_energia_update INTEGER DEFAULT 0
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS inventario (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        item_nome TEXT NOT NULL,
        item_tipo TEXT NOT NULL,
        quantidade INTEGER DEFAULT 1,
        FOREIGN KEY (user_id) REFERENCES players (user_id)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS equipamentos (
        user_id INTEGER PRIMARY KEY,
        arma TEXT,
        armadura TEXT,
        FOREIGN KEY (user_id) REFERENCES players (user_id)
    )''')
    
    # Nova tabela para combate em andamento
    c.execute('''CREATE TABLE IF NOT EXISTS combate_atual (
        user_id INTEGER PRIMARY KEY,
        monstro_nome TEXT NOT NULL,
        monstro_hp_max INTEGER NOT NULL,
        monstro_hp_atual INTEGER NOT NULL,
        monstro_ataque INTEGER NOT NULL,
        monstro_defesa INTEGER NOT NULL,
        monstro_gold_min INTEGER NOT NULL,
        monstro_gold_max INTEGER NOT NULL,
        monstro_xp INTEGER NOT NULL,
        monstro_tipo TEXT NOT NULL,
        monstro_img TEXT NOT NULL,
        player_hp_inicio INTEGER NOT NULL,
        defendendo INTEGER DEFAULT 0,
        buff_ataque INTEGER DEFAULT 0,
        buff_ataque_turnos INTEGER DEFAULT 0,
        buff_defesa INTEGER DEFAULT 0,
        buff_defesa_turnos INTEGER DEFAULT 0,
        buff_critico INTEGER DEFAULT 0,
        buff_critico_turnos INTEGER DEFAULT 0,
        turno INTEGER DEFAULT 1,
        FOREIGN KEY (user_id) REFERENCES players (user_id)
    )''')
    
    conn.commit()
    conn.close()
    print("✅ Banco de dados criado!")

def salvar_player(uid, dados):
    """Salva dados do player no banco"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    ultima_update = dados.get('ultima_energia_update', int(time.time()))
    
    c.execute('''INSERT OR REPLACE INTO players 
                 (user_id, nome, classe, level, xp, hp_atual, hp_max, energia_atual, 
                  energia_max, ataque, defesa, gold, vitorias, derrotas, mapa_atual, ultima_energia_update)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (uid, dados.get('nome', 'Aventureiro'), dados['classe'], dados['level'], dados['xp'], 
               dados['hp_atual'], dados['hp_max'], dados['energia_atual'],
               dados['energia_max'], dados['ataque'], dados['defesa'],
               dados['gold'], dados['vitorias'], dados['derrotas'],
               dados.get('mapa_atual', 'Planície de Aether'), ultima_update))
    
    conn.commit()
    conn.close()

def carregar_player(uid):
    """Carrega dados do player do banco e atualiza energia automática"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute('SELECT * FROM players WHERE user_id = ?', (uid,))
    row = c.fetchone()
    conn.close()
    
    if row:
        tempo_atual = int(time.time())
        ultima_update = row[14] if len(row) > 14 else tempo_atual
        
        # Calcular energia regenerada (1 energia a cada 5 minutos = 300 segundos)
        tempo_passado = tempo_atual - ultima_update
        energia_regenerada = tempo_passado // 300  # 5 minutos por energia
        
        energia_atual = min(row[7] + energia_regenerada, row[8])  # Não ultrapassar máximo
        
        player = {
            'nome': row[1] if len(row) > 1 else 'Aventureiro',
            'classe': row[2],
            'level': row[3],
            'xp': row[4],
            'hp_atual': row[5],
            'hp_max': row[6],
            'energia_atual': energia_atual,
            'energia_max': row[8],
            'ataque': row[9],
            'defesa': row[10],
            'gold': row[11],
            'vitorias': row[12],
            'derrotas': row[13],
            'mapa_atual': row[14] if len(row) > 14 else 'Planície de Aether',
            'ultima_energia_update': tempo_atual
        }
        
        # Se regenerou energia, salvar nova timestamp
        if energia_regenerada > 0:
            salvar_player(uid, player)
        
        return player
    return None

def deletar_player(uid):
    """Deleta player do banco"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('DELETE FROM players WHERE user_id = ?', (uid,))
    c.execute('DELETE FROM combate_atual WHERE user_id = ?', (uid,))
    conn.commit()
    conn.close()

# ============================================
# FUNÇÕES DE COMBATE
# ============================================
def salvar_combate(uid, dados_combate):
    """Salva estado do combate"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute('''INSERT OR REPLACE INTO combate_atual 
                 (user_id, monstro_nome, monstro_hp_max, monstro_hp_atual,
                  monstro_ataque, monstro_defesa, monstro_gold_min, monstro_gold_max,
                  monstro_xp, monstro_tipo, monstro_img, player_hp_inicio,
                  defendendo, buff_ataque, buff_ataque_turnos, buff_defesa, 
                  buff_defesa_turnos, buff_critico, buff_critico_turnos, turno)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (uid, dados_combate['monstro_nome'], dados_combate['monstro_hp_max'],
               dados_combate['monstro_hp_atual'], dados_combate['monstro_ataque'],
               dados_combate['monstro_defesa'], dados_combate['monstro_gold_min'],
               dados_combate['monstro_gold_max'], dados_combate['monstro_xp'],
               dados_combate['monstro_tipo'], dados_combate['monstro_img'],
               dados_combate['player_hp_inicio'], dados_combate.get('defendendo', 0),
               dados_combate.get('buff_ataque', 0), dados_combate.get('buff_ataque_turnos', 0),
               dados_combate.get('buff_defesa', 0), dados_combate.get('buff_defesa_turnos', 0),
               dados_combate.get('buff_critico', 0), dados_combate.get('buff_critico_turnos', 0),
               dados_combate.get('turno', 1)))
    
    conn.commit()
    conn.close()

def carregar_combate(uid):
    """Carrega estado do combate"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute('SELECT * FROM combate_atual WHERE user_id = ?', (uid,))
    row = c.fetchone()
    conn.close()
    
    if row:
        return {
            'monstro_nome': row[1],
            'monstro_hp_max': row[2],
            'monstro_hp_atual': row[3],
            'monstro_ataque': row[4],
            'monstro_defesa': row[5],
            'monstro_gold_min': row[6],
            'monstro_gold_max': row[7],
            'monstro_xp': row[8],
            'monstro_tipo': row[9],
            'monstro_img': row[10],
            'player_hp_inicio': row[11],
            'defendendo': row[12],
            'buff_ataque': row[13],
            'buff_ataque_turnos': row[14],
            'buff_defesa': row[15],
            'buff_defesa_turnos': row[16],
            'buff_critico': row[17],
            'buff_critico_turnos': row[18],
            'turno': row[19]
        }
    return None

def deletar_combate(uid):
    """Remove combate do banco"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('DELETE FROM combate_atual WHERE user_id = ?', (uid,))
    conn.commit()
    conn.close()

def escolher_monstro(player_level, mapa_nome):
    """Escolhe monstro apropriado baseado no mapa (com chance de miniboss)"""
    mapa_info = MAPAS.get(mapa_nome, MAPAS["Planície de Aether"])
    
    # 10% de chance de miniboss
    if random.random() < 0.10:
        monstro = random.choice(MONSTROS[mapa_info["miniboss_tier"]]).copy()
    else:
        # Monstro normal do mapa
        monstro = random.choice(MONSTROS[mapa_info["tier_monstros"]]).copy()
    
    # Escalar monstro com level do player
    nivel_multiplicador = 1 + (player_level - 1) * 0.1
    monstro['hp'] = int(monstro['hp'] * nivel_multiplicador)
    monstro['ataque'] = int(monstro['ataque'] * nivel_multiplicador)
    monstro['defesa'] = int(monstro['defesa'] * nivel_multiplicador)
    
    return monstro

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
        
        player['hp_max'] += 20
        player['energia_max'] += 5
        player['ataque'] += 3
        player['defesa'] += 2
        
        player['hp_atual'] = player['hp_max']
        player['energia_atual'] = player['energia_max']
        
        msgs.append(f"🎉 LEVEL UP! Agora você é Level {player['level']}!")
        msgs.append(f"📈 +20 HP | +5 Energia | +3 ATK | +2 DEF")
    
    salvar_player(uid, player)
    return msgs

# ============================================
# INTERFACE - MENUS
# ============================================
def criar_barra(atual, maximo, tipo="hp"):
    """Cria barra de progresso visual"""
    porcentagem = atual / maximo if maximo > 0 else 0
    cheios = int(porcentagem * 5)
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
    mapa_info = MAPAS[p['mapa_atual']]
    
    bonus_atk, bonus_def = calcular_bonus_equipamentos(uid)
    atk_total = p['ataque'] + bonus_atk
    def_total = p['defesa'] + bonus_def
    
    barra_hp = criar_barra(p['hp_atual'], p['hp_max'], "hp")
    barra_en = criar_barra(p['energia_atual'], p['energia_max'], "energia")
    barra_xp = criar_barra(p['xp'], xp_para_proximo_level(p['level']), "xp")
    
    texto = f"""🗺️ **{p['mapa_atual']}** (Lv {mapa_info['nivel_recomendado']}+)
_{mapa_info['desc']}_

👤 {p['classe']} - Level {p['level']}
❤️ HP: {p['hp_atual']}/{p['hp_max']} {barra_hp}
⚡ Energia: {p['energia_atual']}/{p['energia_max']} {barra_en}
✨ XP: {p['xp']}/{xp_para_proximo_level(p['level'])} {barra_xp}
💰 Gold: {p['gold']}
"""
    
    if bonus_atk > 0 or bonus_def > 0:
        texto += f"⚔️ ATK: {p['ataque']} (+{bonus_atk}) | 🛡️ DEF: {p['defesa']} (+{bonus_def})\n"
    else:
        texto += f"⚔️ ATK: {atk_total} | 🛡️ DEF: {def_total}\n"
    
    botoes = [
        [InlineKeyboardButton("⚔️ Caçar", callback_data='cacar'),
         InlineKeyboardButton("😴 Descansar", callback_data='descansar')],
        [InlineKeyboardButton("🏘️ Ir para Vila/Capital", callback_data='menu_vilas'),
         InlineKeyboardButton("🗺️ Viajar", callback_data='menu_mapas')],
        [InlineKeyboardButton("🎒 Inventário", callback_data='inventario'),
         InlineKeyboardButton("👤 Perfil", callback_data='perfil')],
        [InlineKeyboardButton("⚙️ Menu", callback_data='menu_config')]
    ]
    
    return texto, InlineKeyboardMarkup(botoes), mapa_info['img']

def menu_combate(uid):
    """Menu de combate em turno"""
    player = carregar_player(uid)
    combate = carregar_combate(uid)
    
    if not combate:
        return None, None, None
    
    bonus_atk, bonus_def = calcular_bonus_equipamentos(uid)
    
    # Aplicar buffs
    atk_total = player['ataque'] + bonus_atk + combate.get('buff_ataque', 0)
    def_total = player['defesa'] + bonus_def + combate.get('buff_defesa', 0)
    
    barra_player = criar_barra(player['hp_atual'], player['hp_max'], "hp")
    barra_monstro = criar_barra(combate['monstro_hp_atual'], combate['monstro_hp_max'], "hp")
    
    tipo_emoji = "👑" if combate['monstro_tipo'] == "miniboss" else "⚔️"
    
    texto = f"""{tipo_emoji} **COMBATE - Turno {combate['turno']}**

**Você:**
❤️ HP: {player['hp_atual']}/{player['hp_max']} {barra_player}
⚔️ ATK: {atk_total} | 🛡️ DEF: {def_total}
"""
    
    # Mostrar buffs ativos
    buffs_ativos = []
    if combate.get('buff_ataque_turnos', 0) > 0:
        buffs_ativos.append(f"🔥 +{combate['buff_ataque']} ATK ({combate['buff_ataque_turnos']} turnos)")
    if combate.get('buff_defesa_turnos', 0) > 0:
        buffs_ativos.append(f"🛡️ +{combate['buff_defesa']} DEF ({combate['buff_defesa_turnos']} turnos)")
    if combate.get('buff_critico_turnos', 0) > 0:
        buffs_ativos.append(f"⚡ +{combate['buff_critico']}% Crítico ({combate['buff_critico_turnos']} turnos)")
    if combate.get('defendendo', 0) == 1:
        buffs_ativos.append("🛡️ DEFENDENDO")
    
    if buffs_ativos:
        texto += "💫 Buffs: " + " | ".join(buffs_ativos) + "\n"
    
    texto += f"""
**{combate['monstro_nome']}:**
❤️ HP: {combate['monstro_hp_atual']}/{combate['monstro_hp_max']} {barra_monstro}
⚔️ ATK: {combate['monstro_ataque']} | 🛡️ DEF: {combate['monstro_defesa']}

━━━━━━━━━━━━━━━━
**Sua ação:**"""
    
    botoes = [
        [InlineKeyboardButton("⚔️ Atacar", callback_data='combate_atacar'),
         InlineKeyboardButton("🛡️ Defender", callback_data='combate_defender')],
        [InlineKeyboardButton("🧪 Usar Item", callback_data='combate_itens')],
        [InlineKeyboardButton("🏃 Fugir", callback_data='combate_fugir')]
    ]
    
    return texto, InlineKeyboardMarkup(botoes), combate['monstro_img']

def menu_itens_combate(uid):
    """Menu de itens durante combate"""
    inventario = obter_inventario(uid)
    consumiveis = [i for i in inventario if i['tipo'] == 'consumivel']
    
    if not consumiveis:
        texto = "🎒 **INVENTÁRIO**\n\nVocê não tem itens consumíveis!"
    else:
        texto = "🎒 **INVENTÁRIO**\n\nEscolha um item para usar:\n\n"
        for item in consumiveis:
            info = ITENS.get(item['nome'], {})
            texto += f"• {item['nome']} x{item['quantidade']}\n"
            texto += f"  {info.get('desc', '')}\n\n"
    
    botoes = []
    for item in consumiveis:
        botoes.append([InlineKeyboardButton(
            f"🧪 {item['nome']} (x{item['quantidade']})",
            callback_data=f"usar_combate_{item['nome']}"
        )])
    
    botoes.append([InlineKeyboardButton("◀️ Voltar ao Combate", callback_data='voltar_combate')])
    
    return texto, InlineKeyboardMarkup(botoes)

def menu_inventario(uid):
    """Menu do inventário"""
    inventario = obter_inventario(uid)
    equip = obter_equipamentos(uid)
    
    if not inventario:
        texto = "🎒 **INVENTÁRIO VAZIO**\n\nVocê não tem itens ainda.\nDerrote monstros para conseguir drops!"
    else:
        texto = "🎒 **INVENTÁRIO**\n\n"
        
        if equip['arma']:
            texto += f"⚔️ Equipado: **{equip['arma']}**\n"
        if equip['armadura']:
            texto += f"🛡️ Equipado: **{equip['armadura']}**\n"
        
        texto += "\n**Seus Itens:**\n"
        
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
                texto += f"  • {item['nome']} x{item['quantidade']}\n"
                texto += f"    {info.get('desc', '')}\n"
    
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

**Nome:** {p['nome']}

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
    
    botoes = [
        [InlineKeyboardButton("✏️ Mudar Nome", callback_data='mudar_nome')],
        [InlineKeyboardButton("◀️ Voltar", callback_data='voltar')]
    ]
    
    return texto, InlineKeyboardMarkup(botoes)

def menu_descansar(uid):
    """Menu de opções de descanso"""
    p = carregar_player(uid)
    
    texto = f"""😴 **OPÇÕES DE DESCANSO**

💰 Seu Gold: {p['gold']}
❤️ HP Atual: {p['hp_atual']}/{p['hp_max']}
⚡ Energia: {p['energia_atual']}/{p['energia_max']}

**Escolha onde descansar:**
"""
    
    botoes = []
    
    for nome, info in TIPOS_DESCANSO.items():
        pode_pagar = "✅" if p['gold'] >= info['custo'] else "❌"
        botoes.append([InlineKeyboardButton(
            f"{info['emoji']} {nome} - {info['custo']} gold {pode_pagar}",
            callback_data=f"descansar_{nome}"
        )])
        
        texto += f"\n{info['emoji']} **{nome}** ({info['custo']} gold)"
        texto += f"\n  {info['desc']}"
        texto += f"\n  ❤️ +{info['hp_recupera']} HP | ⚡ +{info['energia_recupera']} Energia\n"
    
    # Opção grátis (regeneração natural)
    texto += f"\n💤 **Aguardar Regeneração Natural**"
    texto += f"\n  Sua energia regenera 1 ponto a cada 5 minutos"
    botoes.append([InlineKeyboardButton("💤 Esperar Regeneração (Grátis)", callback_data='descansar_gratis')])
    
    botoes.append([InlineKeyboardButton("◀️ Voltar", callback_data='voltar')])
    
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

def menu_mapas(uid):
    """Menu de seleção de mapas"""
    p = carregar_player(uid)
    
    texto = f"""🗺️ **VIAJAR PARA OUTRO MAPA**

📍 Local atual: **{p['mapa_atual']}**
⭐ Seu level: {p['level']}

Escolha seu destino:
"""
    
    botoes = []
    for nome_mapa, info in MAPAS.items():
        emoji = "✅" if nome_mapa == p['mapa_atual'] else "🗺️"
        nivel_texto = f"(Lv {info['nivel_recomendado']}+)"
        
        # Verificar se pode viajar
        if p['level'] < info['nivel_recomendado'] - 2:
            emoji = "🔒"
        
        botoes.append([InlineKeyboardButton(
            f"{emoji} {nome_mapa} {nivel_texto}",
            callback_data=f"viajar_{nome_mapa}"
        )])
    
    botoes.append([InlineKeyboardButton("◀️ Voltar", callback_data='voltar')])
    
    return texto, InlineKeyboardMarkup(botoes)

def menu_vilas(uid):
    """Menu de vilas do mapa atual"""
    p = carregar_player(uid)
    mapa_info = MAPAS[p['mapa_atual']]
    
    texto = f"""🏘️ **VILAS E CIDADES**
📍 Mapa: {p['mapa_atual']}

Onde deseja ir?
"""
    
    botoes = []
    
    # Adicionar vilas
    for vila in mapa_info['vilas']:
        botoes.append([InlineKeyboardButton(
            f"🏘️ {vila}",
            callback_data=f"vila_{vila}"
        )])
    
    # Adicionar capital se existir
    if mapa_info['capital']:
        botoes.append([InlineKeyboardButton(
            f"🏰 {mapa_info['capital']}",
            callback_data=f"capital_{mapa_info['capital']}"
        )])
    
    # Adicionar contrabandista (sempre disponível)
    botoes.append([InlineKeyboardButton(
        "🎭 Procurar Contrabandista",
        callback_data="contrabandista"
    )])
    
    botoes.append([InlineKeyboardButton("◀️ Voltar", callback_data='voltar')])
    
    return texto, InlineKeyboardMarkup(botoes)

def menu_loja(uid, tipo_loja, nome_local):
    """Menu de loja (vila, capital ou contrabandista)"""
    p = carregar_player(uid)
    
    if tipo_loja == "contrabandista":
        texto = f"""🎭 **CONTRABANDISTA**
_"Tenho itens... especiais. Não pergunte de onde vieram."_

💰 Seu Gold: {p['gold']}
⭐ Level: {p['level']}

**Itens Disponíveis:**
"""
    elif tipo_loja == "capital":
        texto = f"""🏰 **{nome_local}**
_Loja da Capital - Itens de Alta Qualidade_

💰 Seu Gold: {p['gold']}
⭐ Level: {p['level']}

**Itens Disponíveis:**
"""
    else:  # vila
        texto = f"""🏘️ **{nome_local}**
_Loja da Vila - Itens Essenciais_

💰 Seu Gold: {p['gold']}
⭐ Level: {p['level']}

**Itens Disponíveis:**
"""
    
    itens_loja = LOJA_ITENS[tipo_loja if tipo_loja == "contrabandista" else tipo_loja]
    
    for item_nome, config in itens_loja.items():
        item_info = ITENS[item_nome]
        raridade_emoji = {"comum": "⚪", "rara": "🔵", "épica": "🟣"}.get(item_info.get('raridade', 'comum'), "⚪")
        
        preco = config['preco']
        nivel_req = config['nivel_req']
        
        pode_comprar = "✅" if p['gold'] >= preco and p['level'] >= nivel_req else "❌"
        
        texto += f"\n{raridade_emoji} **{item_nome}**"
        texto += f"\n  💰 {preco} gold | Lv {nivel_req}+"
        
        if item_info['tipo'] == 'arma':
            texto += f" | ⚔️ +{item_info['ataque']} ATK"
        elif item_info['tipo'] == 'armadura':
            texto += f" | 🛡️ +{item_info['defesa']} DEF"
        
        texto += f"\n  {pode_comprar} _{ item_info['desc']}_\n"
    
    # Botões de compra
    botoes = []
    for item_nome, config in itens_loja.items():
        if p['gold'] >= config['preco'] and p['level'] >= config['nivel_req']:
            botoes.append([InlineKeyboardButton(
                f"💰 Comprar {item_nome} ({config['preco']} gold)",
                callback_data=f"comprar_{tipo_loja}_{item_nome}"
            )])
    
    botoes.append([InlineKeyboardButton("◀️ Voltar", callback_data='menu_vilas')])
    
    return texto, InlineKeyboardMarkup(botoes)

# ============================================
# HANDLERS DO BOT
# ============================================
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    uid = update.effective_user.id
    player = carregar_player(uid)
    
    if player:
        txt, kb, img = menu_principal(uid)
        await context.bot.send_photo(
            chat_id=uid,
            photo=img,
            caption=txt,
            reply_markup=kb,
            parse_mode='Markdown'
        )
    else:
        img_inicio = "https://picsum.photos/seed/rpgstart/400/300"
        
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

async def processar_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa mensagens de texto (para nome do personagem)"""
    uid = update.effective_user.id
    texto = update.message.text.strip()
    
    # Verificar se está criando personagem
    if 'classe_escolhida' in context.user_data:
        classe_nome = context.user_data['classe_escolhida']
        classe = CLASSES[classe_nome]
        
        # Validar nome
        if len(texto) < 3 or len(texto) > 20:
            await update.message.reply_text(
                "❌ Nome inválido! Use entre 3 e 20 caracteres.\n\nTente novamente:"
            )
            return
        
        # Criar personagem
        novo_player = {
            'nome': texto,
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
        
        del context.user_data['classe_escolhida']
        
        txt, kb, img = menu_principal(uid)
        
        await update.message.reply_photo(
            photo=img,
            caption=f"""✅ **Bem-vindo, {texto}!**

Você é agora um **{classe_nome}**!

🎁 Itens iniciais recebidos!
💰 Você começa com 50 gold!

{txt}""",
            reply_markup=kb,
            parse_mode='Markdown'
        )
        return
    
    # Verificar se está mudando nome
    if context.user_data.get('mudando_nome'):
        player = carregar_player(uid)
        
        if len(texto) < 3 or len(texto) > 20:
            await update.message.reply_text(
                "❌ Nome inválido! Use entre 3 e 20 caracteres.\n\nTente novamente:"
            )
            return
        
        player['nome'] = texto
        salvar_player(uid, player)
        
        context.user_data['mudando_nome'] = False
        
        txt, kb = menu_perfil(uid)
        
        await update.message.reply_text(
            f"✅ Nome alterado para **{texto}**!\n\n{txt}",
            reply_markup=kb,
            parse_mode='Markdown'
        )
        return
    
    # Cheat Code secreto
    if texto.lower() == '/maxpower':
        player = carregar_player(uid)
        
        if not player:
            await update.message.reply_text("❌ Crie um personagem primeiro!")
            return
        
        botoes = [[InlineKeyboardButton("🔥 ATIVAR MODO GOD", callback_data='cheat_maxpower')]]
        
        await update.message.reply_text(
            """🔓 **CHEAT CODE DETECTADO!**

Isso vai deixar seu personagem no nível MÁXIMO com stats e gold infinitos.

⚠️ Use apenas para TESTES!

Deseja ativar?""",
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
        # Salvar classe temporariamente e pedir nome
        context.user_data['classe_escolhida'] = classe_nome
        
        await q.edit_message_caption(
            caption=f"""✨ **Você escolheu: {classe_nome}!**

Agora, me diga:
**Qual será o nome do seu personagem?**

Digite o nome e envie como mensagem.""",
            parse_mode='Markdown'
        )
        return
    
    # ===== CAÇAR - INICIAR COMBATE =====
    elif q.data == 'cacar':
        player = carregar_player(uid)
        
        if player['energia_atual'] < 2:
            await q.answer("⚡ Energia insuficiente! Descanse primeiro.", show_alert=True)
            return
        
        # Gastar energia
        player['energia_atual'] -= 2
        salvar_player(uid, player)
        
        # Escolher monstro baseado no mapa atual
        monstro = escolher_monstro(player['level'], player['mapa_atual'])
        
        # Criar combate
        dados_combate = {
            'monstro_nome': monstro['nome'],
            'monstro_hp_max': monstro['hp'],
            'monstro_hp_atual': monstro['hp'],
            'monstro_ataque': monstro['ataque'],
            'monstro_defesa': monstro['defesa'],
            'monstro_gold_min': monstro['gold_min'],
            'monstro_gold_max': monstro['gold_max'],
            'monstro_xp': monstro['xp'],
            'monstro_tipo': monstro['tipo'],
            'monstro_img': monstro['img'],
            'player_hp_inicio': player['hp_atual'],
            'defendendo': 0,
            'buff_ataque': 0,
            'buff_ataque_turnos': 0,
            'buff_defesa': 0,
            'buff_defesa_turnos': 0,
            'buff_critico': 0,
            'buff_critico_turnos': 0,
            'turno': 1
        }
        
        salvar_combate(uid, dados_combate)
        
        txt, kb, img = menu_combate(uid)
        
        tipo_msg = "⚠️ **UM MINI BOSS APARECEU!**" if monstro['tipo'] == 'miniboss' else "⚔️ **Um inimigo apareceu!**"
        
        await q.edit_message_media(media=InputMediaPhoto(img))
        await q.edit_message_caption(
            caption=f"{tipo_msg}\n\n{txt}",
            reply_markup=kb,
            parse_mode='Markdown'
        )
    
    # ===== COMBATE - ATACAR =====
    elif q.data == 'combate_atacar':
        player = carregar_player(uid)
        combate = carregar_combate(uid)
        
        bonus_atk, bonus_def = calcular_bonus_equipamentos(uid)
        
        # Calcular dano do player
        atk_base = player['ataque'] + bonus_atk + combate.get('buff_ataque', 0)
        dano_player = max(1, atk_base - (combate['monstro_defesa'] // 2))
        dano_player += random.randint(-2, 5)
        
        # Chance de crítico (15% base + buff)
        chance_critico = 0.15 + (combate.get('buff_critico', 0) / 100)
        critico = random.random() < chance_critico
        
        if critico:
            dano_player = int(dano_player * 1.8)
            msg_ataque = f"⚡ **CRÍTICO!** Você causou {dano_player} de dano!"
        else:
            msg_ataque = f"⚔️ Você causou {dano_player} de dano!"
        
        combate['monstro_hp_atual'] -= dano_player
        
        # Verificar se monstro morreu
        if combate['monstro_hp_atual'] <= 0:
            gold_ganho = random.randint(combate['monstro_gold_min'], combate['monstro_gold_max'])
            xp_ganho = combate['monstro_xp']
            
            player['gold'] += gold_ganho
            player['xp'] += xp_ganho
            player['vitorias'] += 1
            
            resultado = f"""🎉 **VITÓRIA!**

{msg_ataque}

{combate['monstro_nome']} foi derrotado!

💰 +{gold_ganho} gold
⭐ +{xp_ganho} XP
"""
            
            # Sistema de drops melhorado
            chance_drop = 0.5 if combate['monstro_tipo'] == 'miniboss' else 0.3
            
            if random.random() < chance_drop:
                itens_drop = []
                
                for nome, item in ITENS.items():
                    raridade = item.get('raridade', 'comum')
                    
                    if combate['monstro_tipo'] == 'miniboss':
                        # Miniboss dropa itens melhores
                        if raridade in ['rara', 'épica']:
                            itens_drop.append(nome)
                    else:
                        # Monstros normais dropam baseado no level
                        if player['level'] <= 3 and raridade == 'comum':
                            itens_drop.append(nome)
                        elif player['level'] <= 7 and raridade in ['comum', 'rara']:
                            itens_drop.append(nome)
                        elif player['level'] > 7:
                            itens_drop.append(nome)
                
                if itens_drop:
                    item_dropado = random.choice(itens_drop)
                    adicionar_item(uid, item_dropado)
                    raridade_emoji = {"comum": "⚪", "rara": "🔵", "épica": "🟣"}.get(
                        ITENS[item_dropado].get('raridade', 'comum'), "⚪"
                    )
                    resultado += f"\n{raridade_emoji} **Item dropado:** {item_dropado}!"
            
            salvar_player(uid, player)
            deletar_combate(uid)
            
            msgs_levelup = aplicar_level_up(uid)
            if msgs_levelup:
                resultado += "\n\n" + "\n".join(msgs_levelup)
            
            txt, kb, img = menu_principal(uid)
            
            await q.edit_message_caption(
                caption=resultado + "\n\n━━━━━━━━━━\n" + txt,
                reply_markup=kb,
                parse_mode='Markdown'
            )
            return
        
        # Turno do monstro
        def_base = player['defesa'] + bonus_def + combate.get('buff_defesa', 0)
        
        # Se estava defendendo, dobra a defesa
        if combate.get('defendendo', 0) == 1:
            def_base = int(def_base * 2)
            combate['defendendo'] = 0
            msg_defesa = "\n🛡️ Você defendeu! Defesa dobrada!"
        else:
            msg_defesa = ""
        
        dano_monstro = max(1, combate['monstro_ataque'] - (def_base // 2))
        dano_monstro += random.randint(-1, 3)
        
        player['hp_atual'] -= dano_monstro
        msg_monstro = f"\n💥 {combate['monstro_nome']} causou {dano_monstro} de dano!"
        
        # Reduzir turnos dos buffs
        if combate.get('buff_ataque_turnos', 0) > 0:
            combate['buff_ataque_turnos'] -= 1
            if combate['buff_ataque_turnos'] <= 0:
                combate['buff_ataque'] = 0
        
        if combate.get('buff_defesa_turnos', 0) > 0:
            combate['buff_defesa_turnos'] -= 1
            if combate['buff_defesa_turnos'] <= 0:
                combate['buff_defesa'] = 0
        
        if combate.get('buff_critico_turnos', 0) > 0:
            combate['buff_critico_turnos'] -= 1
            if combate['buff_critico_turnos'] <= 0:
                combate['buff_critico'] = 0
        
        # Verificar se player morreu
        if player['hp_atual'] <= 0:
            player['hp_atual'] = player['hp_max'] // 2
            player['derrotas'] += 1
            
            resultado = f"""☠️ **DERROTA!**

{msg_ataque}{msg_defesa}{msg_monstro}

Você foi derrotado e fugiu!
HP restaurado para {player['hp_atual']}.
"""
            
            salvar_player(uid, player)
            deletar_combate(uid)
            
            txt, kb, img = menu_principal(uid)
            
            await q.edit_message_caption(
                caption=resultado + "\n\n━━━━━━━━━━\n" + txt,
                reply_markup=kb,
                parse_mode='Markdown'
            )
            return
        
        combate['turno'] += 1
        salvar_player(uid, player)
        salvar_combate(uid, combate)
        
        txt, kb, img = menu_combate(uid)
        
        await q.edit_message_caption(
            caption=f"{msg_ataque}{msg_defesa}{msg_monstro}\n\n{txt}",
            reply_markup=kb,
            parse_mode='Markdown'
        )
    
    # ===== COMBATE - DEFENDER =====
    elif q.data == 'combate_defender':
        combate = carregar_combate(uid)
        combate['defendendo'] = 1
        
        # Turno do monstro (mas player vai defender no próximo ataque)
        player = carregar_player(uid)
        bonus_atk, bonus_def = calcular_bonus_equipamentos(uid)
        
        def_base = player['defesa'] + bonus_def + combate.get('buff_defesa', 0)
        dano_monstro = max(1, combate['monstro_ataque'] - def_base)
        dano_monstro += random.randint(-1, 2)
        
        player['hp_atual'] -= dano_monstro
        msg = f"🛡️ Você se preparou para defender!\n💥 {combate['monstro_nome']} causou {dano_monstro} de dano!"
        
        # Reduzir buffs
        if combate.get('buff_ataque_turnos', 0) > 0:
            combate['buff_ataque_turnos'] -= 1
            if combate['buff_ataque_turnos'] <= 0:
                combate['buff_ataque'] = 0
        
        if combate.get('buff_defesa_turnos', 0) > 0:
            combate['buff_defesa_turnos'] -= 1
            if combate['buff_defesa_turnos'] <= 0:
                combate['buff_defesa'] = 0
        
        if combate.get('buff_critico_turnos', 0) > 0:
            combate['buff_critico_turnos'] -= 1
            if combate['buff_critico_turnos'] <= 0:
                combate['buff_critico'] = 0
        
        if player['hp_atual'] <= 0:
            player['hp_atual'] = player['hp_max'] // 2
            player['derrotas'] += 1
            
            resultado = f"""☠️ **DERROTA!**

{msg}

Você foi derrotado!
HP restaurado para {player['hp_atual']}.
"""
            
            salvar_player(uid, player)
            deletar_combate(uid)
            
            txt, kb, img = menu_principal(uid)
            
            await q.edit_message_caption(
                caption=resultado + "\n\n━━━━━━━━━━\n" + txt,
                reply_markup=kb,
                parse_mode='Markdown'
            )
            return
        
        combate['turno'] += 1
        salvar_player(uid, player)
        salvar_combate(uid, combate)
        
        txt, kb, img = menu_combate(uid)
        
        await q.edit_message_caption(
            caption=f"{msg}\n\n{txt}",
            reply_markup=kb,
            parse_mode='Markdown'
        )
    
    # ===== COMBATE - USAR ITENS =====
    elif q.data == 'combate_itens':
        txt, kb = menu_itens_combate(uid)
        await q.edit_message_caption(caption=txt, reply_markup=kb, parse_mode='Markdown')
    
    # ===== USAR ITEM NO COMBATE =====
    elif q.data.startswith('usar_combate_'):
        item_nome = q.data.replace('usar_combate_', '')
        item = ITENS.get(item_nome)
        
        if not item:
            await q.answer("❌ Item não encontrado!", show_alert=True)
            return
        
        player = carregar_player(uid)
        combate = carregar_combate(uid)
        
        efeito = item.get('efeito')
        msg_efeito = ""
        
        if efeito == 'cura':
            hp_antes = player['hp_atual']
            player['hp_atual'] = min(player['hp_max'], player['hp_atual'] + item['hp_recupera'])
            hp_ganho = player['hp_atual'] - hp_antes
            msg_efeito = f"❤️ Você usou **{item_nome}**!\nRecuperou {hp_ganho} HP!"
        
        elif efeito == 'buff_ataque':
            combate['buff_ataque'] = item['buff_valor']
            combate['buff_ataque_turnos'] = item['buff_turnos']
            msg_efeito = f"🔥 Você usou **{item_nome}**!\n+{item['buff_valor']} ATK por {item['buff_turnos']} turnos!"
        
        elif efeito == 'buff_defesa':
            combate['buff_defesa'] = item['buff_valor']
            combate['buff_defesa_turnos'] = item['buff_turnos']
            msg_efeito = f"🛡️ Você usou **{item_nome}**!\n+{item['buff_valor']} DEF por {item['buff_turnos']} turnos!"
        
        elif efeito == 'buff_critico':
            combate['buff_critico'] = item['buff_valor']
            combate['buff_critico_turnos'] = item['buff_turnos']
            msg_efeito = f"⚡ Você usou **{item_nome}**!\n+{item['buff_valor']}% Crítico por {item['buff_turnos']} turnos!"
        
        remover_item(uid, item_nome)
        
        # Turno do monstro
        bonus_atk, bonus_def = calcular_bonus_equipamentos(uid)
        def_base = player['defesa'] + bonus_def + combate.get('buff_defesa', 0)
        
        dano_monstro = max(1, combate['monstro_ataque'] - (def_base // 2))
        dano_monstro += random.randint(-1, 3)
        player['hp_atual'] -= dano_monstro
        
        msg_monstro = f"\n💥 {combate['monstro_nome']} causou {dano_monstro} de dano!"
        
        if player['hp_atual'] <= 0:
            player['hp_atual'] = player['hp_max'] // 2
            player['derrotas'] += 1
            
            resultado = f"""☠️ **DERROTA!**

{msg_efeito}{msg_monstro}

Você foi derrotado!
"""
            
            salvar_player(uid, player)
            deletar_combate(uid)
            
            txt, kb, img = menu_principal(uid)
            
            await q.edit_message_caption(
                caption=resultado + "\n\n━━━━━━━━━━\n" + txt,
                reply_markup=kb,
                parse_mode='Markdown'
            )
            return
        
        combate['turno'] += 1
        salvar_player(uid, player)
        salvar_combate(uid, combate)
        
        txt, kb, img = menu_combate(uid)
        
        await q.edit_message_caption(
            caption=f"{msg_efeito}{msg_monstro}\n\n{txt}",
            reply_markup=kb,
            parse_mode='Markdown'
        )
    
    # ===== COMBATE - FUGIR =====
    elif q.data == 'combate_fugir':
        # 70% de chance de fugir
        if random.random() < 0.7:
            deletar_combate(uid)
            txt, kb, img = menu_principal(uid)
            
            await q.edit_message_caption(
                caption="🏃 **Você fugiu da batalha!**\n\n" + txt,
                reply_markup=kb,
                parse_mode='Markdown'
            )
        else:
            player = carregar_player(uid)
            combate = carregar_combate(uid)
            
            # Falhou ao fugir, monstro ataca
            bonus_atk, bonus_def = calcular_bonus_equipamentos(uid)
            def_base = player['defesa'] + bonus_def
            
            dano = max(1, combate['monstro_ataque'] - (def_base // 2))
            player['hp_atual'] -= dano
            
            if player['hp_atual'] <= 0:
                player['hp_atual'] = player['hp_max'] // 2
                player['derrotas'] += 1
                deletar_combate(uid)
                
                salvar_player(uid, player)
                txt, kb, img = menu_principal(uid)
                
                await q.edit_message_caption(
                    caption=f"❌ **Falha ao fugir!**\n\n💥 {combate['monstro_nome']} te atacou causando {dano} de dano!\n\nVocê foi derrotado!\n\n" + txt,
                    reply_markup=kb,
                    parse_mode='Markdown'
                )
            else:
                salvar_player(uid, player)
                txt, kb, img = menu_combate(uid)
                
                await q.edit_message_caption(
                    caption=f"❌ **Falha ao fugir!**\n\n💥 {combate['monstro_nome']} te atacou causando {dano} de dano!\n\n{txt}",
                    reply_markup=kb,
                    parse_mode='Markdown'
                )
    
    # ===== VOLTAR AO COMBATE =====
    elif q.data == 'voltar_combate':
        txt, kb, img = menu_combate(uid)
        await q.edit_message_caption(caption=txt, reply_markup=kb, parse_mode='Markdown')
    
    # ===== DESCANSAR =====
    elif q.data == 'descansar':
        txt, kb = menu_descansar(uid)
        await q.edit_message_caption(caption=txt, reply_markup=kb, parse_mode='Markdown')
    
    # ===== DESCANSAR PAGO =====
    elif q.data.startswith('descansar_'):
        tipo = q.data.replace('descansar_', '')
        
        if tipo == 'gratis':
            await q.answer(
                "⏰ Sua energia regenera naturalmente!\n1 energia a cada 5 minutos.",
                show_alert=True
            )
            txt, kb, img = menu_principal(uid)
            await q.edit_message_caption(caption=txt, reply_markup=kb, parse_mode='Markdown')
            return
        
        player = carregar_player(uid)
        info = TIPOS_DESCANSO.get(tipo)
        
        if not info:
            await q.answer("❌ Tipo de descanso inválido!", show_alert=True)
            return
        
        # Verificar gold
        if player['gold'] < info['custo']:
            await q.answer(
                f"❌ Gold insuficiente! Você precisa de {info['custo']} gold.",
                show_alert=True
            )
            return
        
        # Descansar
        player['gold'] -= info['custo']
        hp_rec = min(info['hp_recupera'], player['hp_max'] - player['hp_atual'])
        en_rec = min(info['energia_recupera'], player['energia_max'] - player['energia_atual'])
        
        player['hp_atual'] += hp_rec
        player['energia_atual'] += en_rec
        
        salvar_player(uid, player)
        txt, kb, img = menu_principal(uid)
        
        await q.edit_message_caption(
            caption=f"""{info['emoji']} **Você descansou em {tipo}!**
💰 -{info['custo']} gold
❤️ +{hp_rec} HP
⚡ +{en_rec} Energia

{txt}""",
            reply_markup=kb,
            parse_mode='Markdown'
        )
    
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
    
    # ===== USAR CONSUMÍVEL FORA DE COMBATE =====
    elif q.data.startswith('usar_'):
        item_nome = q.data.replace('usar_', '')
        item = ITENS.get(item_nome)
        
        if item and item['tipo'] == 'consumivel':
            player = carregar_player(uid)
            msg = ""
            
            if item.get('efeito') == 'cura':
                hp_antes = player['hp_atual']
                player['hp_atual'] = min(player['hp_max'], player['hp_atual'] + item['hp_recupera'])
                hp_ganho = player['hp_atual'] - hp_antes
                msg = f"❤️ Recuperou {hp_ganho} HP!"
            else:
                msg = "⚠️ Este item só pode ser usado em combate!"
                await q.answer(msg, show_alert=True)
                return
            
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
    
    # ===== MUDAR NOME =====
    elif q.data == 'mudar_nome':
        context.user_data['mudando_nome'] = True
        await q.edit_message_caption(
            caption="✏️ **Digite o novo nome do seu personagem:**\n\nEnvie o nome como mensagem."
        )
    
    # ===== CHEAT CODE =====
    elif q.data == 'cheat_maxpower':
        player = carregar_player(uid)
        
        # Maxar tudo
        player['level'] = 99
        player['xp'] = 0
        player['hp_max'] = 9999
        player['hp_atual'] = 9999
        player['energia_max'] = 999
        player['energia_atual'] = 999
        player['ataque'] = 500
        player['defesa'] = 300
        player['gold'] = 999999
        
        salvar_player(uid, player)
        
        txt, kb, img = menu_principal(uid)
        
        await q.edit_message_caption(
            caption=f"""🔥 **CHEAT CODE ATIVADO!**

⭐ Level: 99
❤️ HP: 9999
⚡ Energia: 999
⚔️ Ataque: 500
🛡️ Defesa: 300
💰 Gold: 999,999

{txt}""",
            reply_markup=kb,
            parse_mode='Markdown'
        )
    
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
        c.execute('DELETE FROM combate_atual WHERE user_id = ?', (uid,))
        conn.commit()
        conn.close()
        
        await q.edit_message_caption(
            caption="🗑️ **Personagem deletado!**\n\nTodos os seus itens e progresso foram perdidos.\n\nUse /start para criar um novo."
        )
    
    # ===== AJUDA =====
    elif q.data == 'ajuda':
        ajuda = """❓ **GUIA DO JOGO**

**⚔️ Caçar:**
Gasta 2 energia. Enfrente monstros em combate por turnos!

**🎮 Combate:**
• **Atacar** - Causa dano no inimigo
• **Defender** - Dobra sua defesa no próximo turno
• **Usar Item** - Use poções de cura ou buffs
• **Fugir** - 70% de chance de escapar

**🧪 Poções:**
• Cura - Restaura HP
• Buffs - Aumentam ATK/DEF/Crítico temporariamente

**💡 Dicas:**
• Equipe armas e armaduras melhores
• Use poções de buff em combates difíceis
• Defenda quando estiver com HP baixo
• Mini-bosses (👑) dão rewards melhores!"""
        
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
    
    # ===== MENU MAPAS =====
    elif q.data == 'menu_mapas':
        txt, kb = menu_mapas(uid)
        await q.edit_message_caption(caption=txt, reply_markup=kb, parse_mode='Markdown')
    
    # ===== VIAJAR PARA MAPA =====
    elif q.data.startswith('viajar_'):
        nome_mapa = q.data.replace('viajar_', '')
        player = carregar_player(uid)
        mapa_info = MAPAS.get(nome_mapa)
        
        if not mapa_info:
            await q.answer("❌ Mapa não encontrado!", show_alert=True)
            return
        
        # Verificar level
        if player['level'] < mapa_info['nivel_recomendado'] - 2:
            await q.answer(
                f"🔒 Você precisa ser level {mapa_info['nivel_recomendado'] - 2}+ para viajar para este mapa!",
                show_alert=True
            )
            return
        
        # Já está neste mapa?
        if player['mapa_atual'] == nome_mapa:
            await q.answer("📍 Você já está neste mapa!", show_alert=True)
            return
        
        # Viajar
        player['mapa_atual'] = nome_mapa
        salvar_player(uid, player)
        
        txt, kb, img = menu_principal(uid)
        await q.edit_message_media(media=InputMediaPhoto(img))
        await q.edit_message_caption(
            caption=f"🗺️ **Você viajou para {nome_mapa}!**\n\n{txt}",
            reply_markup=kb,
            parse_mode='Markdown'
        )
    
    # ===== MENU VILAS =====
    elif q.data == 'menu_vilas':
        txt, kb = menu_vilas(uid)
        await q.edit_message_caption(caption=txt, reply_markup=kb, parse_mode='Markdown')
    
    # ===== ENTRAR EM VILA =====
    elif q.data.startswith('vila_'):
        nome_vila = q.data.replace('vila_', '')
        txt, kb = menu_loja(uid, 'vila', nome_vila)
        await q.edit_message_caption(caption=txt, reply_markup=kb, parse_mode='Markdown')
    
    # ===== ENTRAR EM CAPITAL =====
    elif q.data.startswith('capital_'):
        nome_capital = q.data.replace('capital_', '')
        txt, kb = menu_loja(uid, 'capital', nome_capital)
        await q.edit_message_caption(caption=txt, reply_markup=kb, parse_mode='Markdown')
    
    # ===== CONTRABANDISTA =====
    elif q.data == 'contrabandista':
        txt, kb = menu_loja(uid, 'contrabandista', 'Contrabandista')
        await q.edit_message_caption(caption=txt, reply_markup=kb, parse_mode='Markdown')
    
    # ===== COMPRAR ITEM =====
    elif q.data.startswith('comprar_'):
        partes = q.data.replace('comprar_', '').split('_', 1)
        tipo_loja = partes[0]
        item_nome = partes[1]
        
        player = carregar_player(uid)
        
        # Verificar se item existe na loja
        if tipo_loja == "contrabandista":
            loja = LOJA_ITENS["contrabandista"]
        else:
            loja = LOJA_ITENS[tipo_loja]
        
        if item_nome not in loja:
            await q.answer("❌ Item não disponível!", show_alert=True)
            return
        
        config = loja[item_nome]
        preco = config['preco']
        nivel_req = config['nivel_req']
        
        # Verificar requisitos
        if player['level'] < nivel_req:
            await q.answer(f"❌ Você precisa ser level {nivel_req}+!", show_alert=True)
            return
        
        if player['gold'] < preco:
            await q.answer(f"❌ Gold insuficiente! Faltam {preco - player['gold']} gold.", show_alert=True)
            return
        
        # Comprar
        player['gold'] -= preco
        salvar_player(uid, player)
        adicionar_item(uid, item_nome, 1)
        
        await q.answer(f"✅ Você comprou {item_nome}!", show_alert=True)
        
        # Atualizar menu da loja
        nome_local = "Contrabandista" if tipo_loja == "contrabandista" else "Loja"
        txt, kb = menu_loja(uid, tipo_loja, nome_local)
        await q.edit_message_caption(caption=txt, reply_markup=kb, parse_mode='Markdown')
    
    # ===== VOLTAR =====
    elif q.data == 'voltar':
        txt, kb, img = menu_principal(uid)
        await q.edit_message_caption(caption=txt, reply_markup=kb, parse_mode='Markdown')

# ============================================
# INICIALIZAÇÃO
# ============================================
if __name__ == '__main__':
    print("🚀 Iniciando RPG Bot Melhorado...")
    
    criar_banco()
    
    print("✅ Configurando bot...")
    
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CallbackQueryHandler(processar_botoes))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, processar_mensagem))
    
    print("✅ Bot ONLINE com sistema de combate em turnos!")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🎮 Features Completas:")
    print("  ✓ Sistema de NOME personalizado")
    print("  ✓ Combate em turnos (Atacar/Defender/Item)")
    print("  ✓ 10+ tipos de monstros diferentes")
    print("  ✓ Mini-bosses com 10% de chance")
    print("  ✓ Poções com buffs temporários")
    print("  ✓ 6 mapas diferentes com vilas e capitais")
    print("  ✓ Sistema de LOJAS (Vila/Capital/Contrabandista)")
    print("  ✓ Energia REGENERA automaticamente (1/5min)")
    print("  ✓ Descanso PAGO (Acampamento/Casa/Pousada)")
    print("  ✓ Cheat code: /maxpower (para testes)")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    app.run_polling(drop_pending_updates=True)
