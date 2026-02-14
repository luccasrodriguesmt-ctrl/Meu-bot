"""
🎮 BOT RPG TELEGRAM - VERSÃO MELHORADA
Por: Seu Nome

MELHORIAS IMPLEMENTADAS:
✅ Banco de dados SQLite (dados NÃO se perdem!)
✅ Sistema de XP e Level Up
✅ Combate completo com turnos
✅ Sistema de energia e descanso
✅ Estatísticas de vitórias/derrotas
✅ Monstros que escalam com seu level
✅ Código organizado e comentado
"""

import random
import sqlite3
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

# ============================================
# CONFIGURAÇÕES
# ============================================
TOKEN = "8506567958:AAFn-GXHiZWnXDCn2sVvnZ1aG43aputD2hw"
DB_FILE = "rpg_game.db"

# ============================================
# SERVIDOR FLASK (Manter bot online no Render)
# ============================================
app_flask = Flask('')

@app_flask.route('/')
def home(): 
    return "🎮 RPG Bot está ONLINE!"

def run_flask(): 
    app_flask.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

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
def criar_barra(atual, maximo, char="█", tamanho=10):
    """Cria barra de progresso visual"""
    porcentagem = atual / maximo if maximo > 0 else 0
    cheio = int(porcentagem * tamanho)
    vazio = tamanho - cheio
    return char * cheio + "░" * vazio

def menu_principal(uid):
    """Gera menu principal do jogo"""
    p = carregar_player(uid)
    classe_info = CLASSES[p['classe']]
    
    barra_hp = criar_barra(p['hp_atual'], p['hp_max'], "❤️")
    barra_en = criar_barra(p['energia_atual'], p['energia_max'], "⚡")
    barra_xp = criar_barra(p['xp'], xp_para_proximo_level(p['level']), "⭐")
    
    texto = f"""
🏰 **{p['classe']}** - Level {p['level']}

❤️ HP: {p['hp_atual']}/{p['hp_max']}
{barra_hp}

⚡ Energia: {p['energia_atual']}/{p['energia_max']}
{barra_en}

⭐ XP: {p['xp']}/{xp_para_proximo_level(p['level'])}
{barra_xp}

💰 Gold: {p['gold']}
⚔️ ATK: {p['ataque']} | 🛡️ DEF: {p['defesa']}
🏆 Vitórias: {p['vitorias']} | ☠️ Derrotas: {p['derrotas']}
"""
    
    botoes = [
        [InlineKeyboardButton("⚔️ Caçar Monstros (2 energia)", callback_data='cacar')],
        [InlineKeyboardButton("😴 Descansar", callback_data='descansar')],
        [InlineKeyboardButton("📊 Ver Estatísticas", callback_data='stats')],
        [InlineKeyboardButton("🔄 Resetar Personagem", callback_data='reset')]
    ]
    
    return texto, InlineKeyboardMarkup(botoes), classe_info['img']

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
        
        botoes = []
        for nome, info in CLASSES.items():
            botoes.append([InlineKeyboardButton(
                f"{info['desc']}", 
                callback_data=f'criar_{nome}'
            )])
        
        await context.bot.send_photo(
            chat_id=uid,
            photo=img_inicio,
            caption="✨ **BEM-VINDO AO RPG!**\n\nEscolha sua classe:",
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
    
    # ===== ESTATÍSTICAS =====
    elif q.data == 'stats':
        player = carregar_player(uid)
        
        taxa_vitoria = 0
        total = player['vitorias'] + player['derrotas']
        if total > 0:
            taxa_vitoria = (player['vitorias'] / total) * 100
        
        stats = f"""
📊 **ESTATÍSTICAS**

👤 Classe: {player['classe']}
🏆 Level: {player['level']}
⭐ XP Total: {player['xp']}

⚔️ Total de Batalhas: {total}
✅ Vitórias: {player['vitorias']}
❌ Derrotas: {player['derrotas']}
📈 Taxa de Vitória: {taxa_vitoria:.1f}%

💰 Gold Acumulado: {player['gold']}
"""
        
        botoes = [[InlineKeyboardButton("◀️ Voltar", callback_data='voltar')]]
        
        await q.edit_message_caption(
            caption=stats,
            reply_markup=InlineKeyboardMarkup(botoes),
            parse_mode='Markdown'
        )
    
    # ===== VOLTAR =====
    elif q.data == 'voltar':
        txt, kb, img = menu_principal(uid)
        await q.edit_message_caption(caption=txt, reply_markup=kb, parse_mode='Markdown')
    
    # ===== RESETAR =====
    elif q.data == 'reset':
        deletar_player(uid)
        await q.edit_message_caption(
            caption="🗑️ **Personagem deletado!**\n\nUse /start para criar um novo."
        )

# ============================================
# INICIALIZAÇÃO
# ============================================
if __name__ == '__main__':
    print("🚀 Iniciando RPG Bot...")
    
    # Criar banco de dados
    criar_banco()
    
    # Iniciar servidor Flask
    keep_alive()
    
    # Iniciar bot
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CallbackQueryHandler(processar_botoes))
    
    print("✅ Bot ONLINE!")
    app.run_polling()
