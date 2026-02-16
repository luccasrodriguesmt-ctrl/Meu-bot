import os
import random
import sqlite3
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters, ConversationHandler

# Mude para 1.5.0 no GitHub e dê "Clear Cache & Deploy" no Render
VERSAO = "1.5.0 - TeleTofus Style + GitHub Images"

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

DB_FILE = "rpg_game.db"

# ============================================
# 🎨 CONFIGURAÇÃO DE IMAGENS - GITHUB (100% FUNCIONAL)
# ============================================
IMAGENS = {
    # Tela inicial/logo - Menu principal
    "logo": "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/WhatsApp%20Image%202026-02-15%20at%2009.06.10.jpeg?raw=true",
    
    # Tela de seleção de classes (mostrando os 4 personagens)
    "selecao_classes": "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/Gemini_Generated_Image_l46bisl46bisl46b.png?raw=true",
    
    # Menu principal - Mapa da primeira área
    "menu_principal": "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/Gemini_Generated_Image_dxklz9dxklz9dxkl.png?raw=true",
    
    # Imagens individuais de cada classe
    "classes": {
        "Guerreiro": "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/Gemini_Generated_Image_n68a2ln68a2ln68a.png?raw=true",
        "Arqueiro": "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/Gemini_Generated_Image_o1dtmio1dtmio1dt.png?raw=true",
        "Bruxa": "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/Gemini_Generated_Image_fyofu7fyofu7fyof.png?raw=true",
        "Mago": "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/Gemini_Generated_Image_8nad348nad348nad.png?raw=true"
    }
}

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

# --- FUNÇÃO AUXILIAR PARA PEGAR IMAGEM DO PERSONAGEM ---
def get_imagem_personagem(classe):
    """Retorna a imagem específica da classe do jogador"""
    return IMAGENS["classes"].get(classe, IMAGENS["menu_principal"])

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

    # Usa a imagem do personagem específico
    imagem_personagem = get_imagem_personagem(p['classe'])

    if update.callback_query:
        try:
            await update.callback_query.edit_message_caption(
                caption=caption, 
                reply_markup=InlineKeyboardMarkup(keyboard), 
                parse_mode='Markdown'
            )
        except:
            await update.callback_query.message.delete()
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=imagem_personagem,
                caption=caption, 
                reply_markup=InlineKeyboardMarkup(keyboard), 
                parse_mode='Markdown'
            )
    else:
        await update.message.reply_photo(
            photo=imagem_personagem, 
            caption=caption, 
            reply_markup=InlineKeyboardMarkup(keyboard), 
            parse_mode='Markdown'
        )

# --- HANDLER PARA VER PERFIL ---
async def ver_perfil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = update.effective_user.id
    p = get_player(uid)

    if not p:
        await query.answer("Crie sua conta primeiro com /start", show_alert=True)
        return

    await query.answer()

    b_hp = gerar_barra(p['hp'], p['hp_max'], "🟥")
    b_xp = gerar_barra(p['exp'], p['lv'] * 100, "🟦")

    caption = (
        f"👤 **PERFIL DO HERÓI**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📛 **Nome:** {p['nome']}\n"
        f"🎭 **Classe:** {p['classe']}\n"
        f"⭐ **Level:** {p['lv']}\n\n"
        f"❤️ **HP:** {p['hp']}/{p['hp_max']}\n"
        f"└ {b_hp}\n\n"
        f"✨ **XP:** {p['exp']}/{p['lv']*100}\n"
        f"└ {b_xp}\n\n"
        f"💰 **Ouro:** {p['gold']}\n"
        f"⚡ **Energia:** {p['energia']}/{p['energia_max']}\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )

    keyboard = [[InlineKeyboardButton("🔙 Voltar", callback_data='voltar_menu')]]
    imagem_personagem = get_imagem_personagem(p['classe'])

    try:
        await query.message.delete()
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=imagem_personagem,
            caption=caption,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    except:
        await query.edit_message_caption(
            caption=caption,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

# --- HANDLER PARA INVENTÁRIO ---
async def ver_inventario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = update.effective_user.id
    p = get_player(uid)

    if not p:
        await query.answer("Crie sua conta primeiro com /start", show_alert=True)
        return

    await query.answer()

    caption = (
        f"🎒 **MOCHILA DE {p['nome'].upper()}**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 **Ouro:** {p['gold']}\n"
        f"⚡ **Energia:** {p['energia']}/{p['energia_max']}\n\n"
        f"📦 **Itens:**\n"
        f"└ _Em breve: sistema de itens_\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )

    keyboard = [[InlineKeyboardButton("🔙 Voltar", callback_data='voltar_menu')]]
    imagem_personagem = get_imagem_personagem(p['classe'])

    try:
        await query.message.delete()
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=imagem_personagem,
            caption=caption,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    except:
        await query.edit_message_caption(
            caption=caption,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

# --- VOLTAR AO MENU ---
async def voltar_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = update.effective_user.id
    await exibir_status(update, context, uid)

# --- SISTEMA DE COMBATE ---
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
    """Tela inicial com imagem de menu principal"""
    context.user_data.clear()
    
    caption = (
        f"✨ **AVENTURA RABISCADA** ✨\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Um RPG de aventuras épicas!\n\n"
        f"Versão: `{VERSAO}`\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )
    
    kb = [[InlineKeyboardButton("🎮 Começar Aventura", callback_data='ir_para_classes')]]
    
    await update.message.reply_photo(
        photo=IMAGENS["logo"],
        caption=caption,
        reply_markup=InlineKeyboardMarkup(kb), 
        parse_mode='Markdown'
    )
    return TELA_CLASSE

async def menu_classes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tela de seleção com os 4 personagens"""
    query = update.callback_query
    await query.answer()
    
    caption = (
        f"🎭 **ESCOLHA SUA CLASSE**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🛡️ **Guerreiro** - Forte e resistente\n"
        f"🏹 **Arqueiro** - Ágil e preciso\n"
        f"🔮 **Bruxa** - Misteriosa e sábia\n"
        f"🔥 **Mago** - Poder elemental\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )
    
    kb = [
        [InlineKeyboardButton("🛡️ Guerreiro", callback_data='Guerreiro'), 
         InlineKeyboardButton("🏹 Arqueiro", callback_data='Arqueiro')],
        [InlineKeyboardButton("🔮 Bruxa", callback_data='Bruxa'), 
         InlineKeyboardButton("🔥 Mago", callback_data='Mago')]
    ]
    
    try:
        await query.message.delete()
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=IMAGENS["selecao_classes"],
            caption=caption,
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode='Markdown'
        )
    except Exception as e:
        logging.error(f"Erro ao enviar imagem de seleção: {e}")
        await query.edit_message_text(
            text=caption,
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode='Markdown'
        )
    
    return TELA_NOME

async def salvar_nome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Salva a classe e pede o nome"""
    query = update.callback_query
    classe_escolhida = query.data
    context.user_data['classe'] = classe_escolhida
    await query.answer()
    
    imagem_classe = get_imagem_personagem(classe_escolhida)
    
    caption = (
        f"✅ **Classe {classe_escolhida.upper()} selecionada!**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Agora, digite o **nome** do seu herói:"
    )
    
    try:
        await query.message.delete()
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=imagem_classe,
            caption=caption,
            parse_mode='Markdown'
        )
    except Exception as e:
        logging.error(f"Erro ao enviar imagem da classe: {e}")
        await query.edit_message_text(caption, parse_mode='Markdown')
    
    return TELA_NOME

async def finalizar_e_ir_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cria o personagem e vai pro menu"""
    uid = update.effective_user.id
    nome = update.message.text
    classe = context.user_data.get('classe', 'Guerreiro')

    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT OR REPLACE INTO players VALUES (?, ?, ?, 100, 100, 1, 0, 100, 20, 20)", 
                 (uid, nome, classe))
    conn.commit()
    conn.close()

    await update.message.reply_text(f"✨ **{nome}** foi criado com sucesso!")
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
    app.add_handler(CallbackQueryHandler(ver_perfil, pattern='^p$'))
    app.add_handler(CallbackQueryHandler(ver_inventario, pattern='^i$'))
    app.add_handler(CallbackQueryHandler(voltar_menu, pattern='^voltar_menu$'))
    
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
