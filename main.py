import os
import random
import sqlite3
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters, ConversationHandler

# Mude para 1.2.3 no GitHub e dê "Clear Cache & Deploy" no Render
VERSAO = "1.2.3 - TeleTofus Style"

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

DB_FILE = "rpg_game.db"
IMG_MENU = "https://i.imgur.com/uP6M8fL.jpeg" 

# Estados
TELA_CLASSE, TELA_NOME = range(2)

# --- BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS players 
                 (id INTEGER PRIMARY KEY, nome TEXT, classe TEXT, hp INTEGER, hp_max INTEGER, 
                  lv INTEGER, exp INTEGER, gold INTEGER, energia INTEGER, energia_max INTEGER)''')
    conn.commit()
    conn.close()

def get_player(uid):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    p = conn.execute("SELECT * FROM players WHERE id = ?", (uid,)).fetchone()
    conn.close()
    return p

# --- BARRAS VISUAIS ---
def gerar_barra(atual, maximo, cor="🟦"):
    if maximo <= 0: return "⬜" * 10
    percent = max(0, min(atual / maximo, 1))
    preenchido = int(percent * 10)
    return cor * preenchido + "⬜" * (10 - preenchido)

# --- INTERFACE PRINCIPAL ---
async def exibir_status(update, context, uid, texto_combate=""):
    p = get_player(uid)
    if not p: return

    b_hp = gerar_barra(p['hp'], p['hp_max'], "🟥")
    b_xp = gerar_barra(p['exp'], p['lv'] * 100, "🟦")

    # Layout TeleTofus
    caption = (
        f"🎮 **Versão:** `{VERSAO}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **{p['nome']}** — *{p['classe']} Lv. {p['lv']}*\n\n"
        f"❤️ **HP:** {p['hp']}/{p['hp_max']}\n"
        f"└ {b_hp}\n\n"
        f"✨ **XP:** {p['exp']}/{p['lv']*100}\n"
        f"└ {b_xp}\n\n"
        f"💰 **Gold:** `{p['gold']}`  |  ⚡ **Energy:** `{p['energia']}/{p['energia_max']}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{texto_combate}"
    )

    # Botões em Grade (2 por linha)
    keyboard = [
        [InlineKeyboardButton("⚔️ Caçar", callback_data='cacar'), InlineKeyboardButton("🗺️ Viajar", callback_data='v')],
        [InlineKeyboardButton("🎒 Mochila", callback_data='i'), InlineKeyboardButton("👤 Status", callback_data='p')],
        [InlineKeyboardButton("🏪 Mercado", callback_data='l'), InlineKeyboardButton("🏰 Masmorra", callback_data='m')],
        [InlineKeyboardButton("⚙️ Ajustes", callback_data='s')]
    ]

    if update.callback_query:
        # Se for um combate, o ideal é editar apenas o texto e manter a imagem
        await update.callback_query.edit_message_caption(
            caption=caption, 
            reply_markup=InlineKeyboardMarkup(keyboard), 
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_photo(
            photo=IMG_MENU, 
            caption=caption, 
            reply_markup=InlineKeyboardMarkup(keyboard), 
            parse_mode='Markdown'
        )

# --- SISTEMA DE COMBATE (CORRIGIDO) ---
async def cacar_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = update.effective_user.id
    p = get_player(uid)

    if not p:
        await query.answer("Crie sua conta primeiro com /start", show_alert=True)
        return

    if p['energia'] < 2:
        await query.answer("🪫 Sem energia!", show_alert=True)
        return

    # Lógica de Ganho
    dano = random.randint(5, 15)
    ouro = random.randint(10, 25)
    xp_ganho = 20
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""UPDATE players SET 
                 hp = MAX(0, hp - ?), 
                 gold = gold + ?, 
                 exp = exp + ?, 
                 energia = energia - 2 
                 WHERE id = ?""", (dano, ouro, xp_ganho, uid))
    conn.commit()
    conn.close()

    res = f"⚔️ **Resultado da Caça:**\n💥 Dano: -{dano} | 💰 Ouro: +{ouro} | ✨ XP: +{xp_ganho}"
    await query.answer(f"Sucesso! +{ouro} Gold")
    await exibir_status(update, context, uid, texto_combate=res)

# --- FLUXO DE CRIAÇÃO ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    kb = [[InlineKeyboardButton("🎮 Começar Aventura", callback_data='ir_para_classes')]]
    await update.message.reply_text(f"✨ **Aventura Rabiscada**\nVersão `{VERSAO}`", reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    return TELA_CLASSE

async def menu_classes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    kb = [
        [InlineKeyboardButton("🛡️ Guerreiro", callback_data='Guerreiro'), InlineKeyboardButton("🏹 Arqueiro", callback_data='Arqueiro')],
        [InlineKeyboardButton("🔮 Bruxa", callback_data='Bruxa'), InlineKeyboardButton("🔥 Mago", callback_data='Mago')]
    ]
    await query.edit_message_text("🎭 **Escolha sua classe:**", reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    return TELA_NOME

async def salvar_nome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    context.user_data['classe'] = query.data
    await query.answer()
    await query.edit_message_text(f"✅ Classe **{query.data}** selecionada!\n\nAgora, digite o **nome** do seu herói:")
    return TELA_NOME # Agora espera o texto

async def finalizar_e_ir_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    nome = update.message.text
    classe = context.user_data.get('classe', 'Guerreiro')

    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT OR REPLACE INTO players VALUES (?, ?, ?, 100, 100, 1, 0, 100, 20, 20)", (uid, nome, classe))
    conn.commit()
    conn.close()

    await update.message.reply_text("✨ Personagem criado!")
    await exibir_status(update, context, uid)
    return ConversationHandler.END

# --- INICIALIZAÇÃO ---
def main():
    init_db()
    token = os.getenv("TELEGRAM_TOKEN")
    app = ApplicationBuilder().token(token).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            TELA_CLASSE: [CallbackQueryHandler(menu_classes, pattern='^ir_para_classes$')],
            TELA_NOME: [
                CallbackQueryHandler(salvar_nome), 
                MessageHandler(filters.TEXT & ~filters.COMMAND, finalizar_e_ir_menu)
            ],
        },
        fallbacks=[CommandHandler('start', start)],
    )

    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(cacar_handler, pattern='^cacar$'))
    
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
