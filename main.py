import os
import sqlite3
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# --- CONFIGURAÇÕES E BANCO (Mantenha as funções init_db e get_player que já temos) ---
DB_FILE = "rpg_game.db"

# Dados dos Monstros (Baseado no seu código antigo)
MONSTROS = {
    "Slime": {"hp": 20, "atk": 3, "gold_min": 10, "gold_max": 20, "exp": 15, "tier": 1},
    "Goblin": {"hp": 40, "atk": 6, "gold_min": 20, "gold_max": 40, "exp": 30, "tier": 1},
    "Lobo": {"hp": 30, "atk": 5, "gold_min": 15, "gold_max": 25, "exp": 20, "tier": 1}
}

# --- FUNÇÕES DE LÓGICA DE JOGO ---

def atualizar_stats(uid, hp_mod=0, exp_mod=0, gold_mod=0, energia_mod=0):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Puxa dados atuais
    c.execute("SELECT hp, hp_max, exp, lv, gold, energia, energia_max FROM players WHERE id = ?", (uid,))
    p = list(c.fetchone())
    
    # Aplica modificadores
    new_hp = max(0, min(p[1], p[0] + hp_mod))
    new_exp = p[2] + exp_mod
    new_lv = p[3]
    new_gold = p[4] + gold_mod
    new_energia = max(0, min(p[6], p[5] + energia_mod))
    
    # Sistema de Level Up (XP necessária = Level * 100)
    xp_necessaria = new_lv * 100
    subiu_nivel = False
    if new_exp >= xp_necessaria:
        new_lv += 1
        new_exp = 0
        new_hp = p[1] + 20 # Ganha HP ao subir de nível
        p[1] += 20         # Aumenta HP Máximo
        subiu_nivel = True
        
    c.execute("""UPDATE players SET hp=?, hp_max=?, exp=?, lv=?, gold=?, energia=? 
                 WHERE id=?""", (new_hp, p[1], new_exp, new_lv, new_gold, new_energia, uid))
    conn.commit()
    conn.close()
    return subiu_nivel

# --- HANDLER DE CAÇA ---

async def cacar_comando(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = update.effective_user.id
    await query.answer()

    # Verificar energia no banco
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT energia, hp FROM players WHERE id = ?", (uid,))
    energia, hp = c.fetchone()
    conn.close()

    if energia < 2:
        await query.message.reply_text("🪫 **Energia insuficiente!** Descanse um pouco.")
        return
    if hp <= 0:
        await query.message.reply_text("💀 Você está morto! Use uma poção ou espere reviver.")
        return

    # Selecionar Monstro Aleatório do Tier 1 (Mapa Inicial)
    nome_mob = random.choice([m for m in MONSTROS if MONSTROS[m]['tier'] == 1])
    mob = MONSTROS[nome_mob]
    
    # Simulação rápida de combate (Dano recebido vs Recompensa)
    dano_recebido = random.randint(2, mob['atk'])
    gold_ganho = random.randint(mob['gold_min'], mob['gold_max'])
    xp_ganho = mob['exp']
    
    lv_up = atualizar_stats(uid, hp_mod=-dano_recebido, exp_mod=xp_ganho, gold_mod=gold_ganho, energia_mod=-2)
    
    resultado = (
        f"⚔️ **Combate em: Planície**\n\n"
        f"👾 Você enfrentou um **{nome_mob}**!\n"
        f"💥 Recebeu **{dano_recebido}** de dano.\n"
        f"💰 Ganhou **{gold_ganho}** gold.\n"
        f"📈 Ganhou **{xp_ganho}** XP."
    )
    
    if lv_up:
        resultado += "\n\n🌟 **LEVEL UP!** Você está mais forte e sua vida foi restaurada!"

    # Botão para voltar ao menu
    kb = [[InlineKeyboardButton("Voltar ao Menu 🏠", callback_data='voltar_menu')]]
    
    await query.edit_message_caption(
        caption=resultado,
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode='Markdown'
    )

# --- AJUSTE NO MAIN ---
# Adicione o callback handler no seu main()
# app.add_handler(CallbackQueryHandler(cacar_comando, pattern='^c$'))
