import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Configuração de Logs
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Estados da Conversa
ESCOLHENDO_CLASSE, DEFININDO_NOME = range(2)

# Imagens Temporárias (Substitua pelos seus links)
IMG_BOAS_VINDAS = "https://img.freepik.com/fotos-gratis/fundo-de-paisagem-de-fantasia-com-castelo-e-montanhas_23-2150692731.jpg"
IMG_CLASSES = "https://img.freepik.com/vetores-gratis/personagens-de-rpg-de-design-plano_23-2149293382.jpg"
IMG_MENU = "https://img.freepik.com/fotos-gratis/floresta-mistica-com-nevoeiro-e-luz-solar_23-2150711903.jpg"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Primeira Tela: Bem-vindo"""
    keyboard = [[InlineKeyboardButton("Começar Aventura! ⚔️", callback_query_handler="start_game")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_photo(
        photo=IMG_BOAS_VINDAS,
        caption="✨ **Bem-vindo ao Reino de Aventuras!**\n\nSua jornada épica começa agora. Você está pronto para enfrentar desafios e conquistar tesouros?",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return ConversationHandler.END # Usaremos o callback para avançar

async def selecionar_classe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Segunda Tela: Escolha de Personagem"""
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("Guerreiro 🛡️", callback_data='Guerreiro')],
        [InlineKeyboardButton("Arqueiro 🏹", callback_data='Arqueiro')],
        [InlineKeyboardButton("Bruxa 🔮", callback_data='Bruxa')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_media(
        media=context.bot.send_photo(chat_id=query.message.chat_id, photo=IMG_CLASSES).media # Apenas para simular troca
    )
    await query.edit_message_caption(
        caption="🛡️ **Escolha sua Classe:**\nCada uma possui habilidades únicas para sua jornada.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return ESCOLHENDO_CLASSE

async def classe_escolhida(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    context.user_data['classe'] = query.data
    await query.answer()
    
    await query.edit_message_caption(caption=f"Você escolheu: **{query.data}**!\n\nAgora, diga-me: qual será o seu nome de herói?")
    return DEFININDO_NOME

async def menu_principal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Terceira Tela: O Menu Principal (estilo sua imagem)"""
    nome = update.message.text
    classe = context.user_data.get('classe', 'Aventureiro')
    
    keyboard = [
        [InlineKeyboardButton("⚔️ Caçar", callback_data='cacar'), InlineKeyboardButton("🗺️ Viajar", callback_data='viajar')],
        [InlineKeyboardButton("🎒 Inventário", callback_data='inv'), InlineKeyboardButton("👤 Perfil", callback_data='perfil')],
        [InlineKeyboardButton("🏪 Loja", callback_data='loja'), InlineKeyboardButton("🏰 Masmorra", callback_data='masmorra')],
        [InlineKeyboardButton("⚙️ Configurações", callback_data='config')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    status_msg = (
        f"📍 **Planície (Nível 1)**\n"
        f"👤 **Herói:** {nome} ({classe})\n"
        f"❤️ **HP:** 100/100 [||||||||||]\n"
        f"⚡ **Energia:** 20/20 [||||||||||]\n"
        f"💰 **Ouro:** 0"
    )

    await update.message.reply_photo(
        photo=IMG_MENU,
        caption=status_msg,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return ConversationHandler.END

def main():
    # Pegue o token das variáveis de ambiente
    token = os.getenv("TELEGRAM_TOKEN")
    application = Application.builder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQuery_handler(selecionar_classe, pattern='start_game')],
        states={
            ESCOLHENDO_CLASSE: [CallbackQueryHandler(classe_escolhida)],
            DEFININDO_NOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, menu_principal)],
        },
        fallbacks=[CommandHandler('start', start)],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)

    application.run_polling()

if __name__ == '__main__':
    main()
