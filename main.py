import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Configuração de Logs
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Estados do Jogo
ESCOLHENDO_CLASSE, DEFININDO_NOME = range(2)

# Imagens (Links temporários, você pode trocar depois)
IMG_BOAS_VINDAS = "https://i.imgur.com/8pS1Xo5.jpeg" 
IMG_CLASSES = "https://i.imgur.com/uP6M8fL.jpeg"
IMG_MENU_PRINCIPAL = "https://i.imgur.com/uP6M8fL.jpeg"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tela 1: Apresentação"""
    keyboard = [[InlineKeyboardButton("Criar Nova Conta 📝", callback_data='tutorial')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "✨ **Bem-vindo ao Aventuras Rabiscadas!**\n\nSua jornada começa aqui. Clique abaixo para criar seu personagem.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def tutorial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tela 2: Escolha de Classe"""
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("Guerreiro 🛡️", callback_data='Guerreiro'),
         InlineKeyboardButton("Mago 🔥", callback_data='Mago')],
        [InlineKeyboardButton("Arqueiro 🏹", callback_data='Arqueiro'),
         InlineKeyboardButton("Bruxa 🔮", callback_data='Bruxa')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_photo(
        photo=IMG_CLASSES,
        caption="🖼️ **Seleção de Classe**\n\nEscolha o caminho que deseja seguir:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return ESCOLHENDO_CLASSE

async def escolher_nome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fase Intermediária: Pedir o Nome"""
    query = update.callback_query
    context.user_data['classe'] = query.data
    await query.answer()

    await query.message.reply_text(f"Ótima escolha! Você agora é um **{query.data}**.\n\nQual será o nome do seu herói?")
    return DEFININDO_NOME

async def menu_principal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tela 3: Menu Principal (Estilo sua imagem)"""
    nome = update.message.text
    classe = context.user_data.get('classe')
    
    keyboard = [
        [InlineKeyboardButton("⚔️ Caçar", callback_data='c'), InlineKeyboardButton("🗺️ Viajar", callback_data='v')],
        [InlineKeyboardButton("🎒 Inventário", callback_data='i'), InlineKeyboardButton("👤 Perfil", callback_data='p')],
        [InlineKeyboardButton("🏪 Loja", callback_data='l'), InlineKeyboardButton("🏰 Masmorra", callback_data='m')],
        [InlineKeyboardButton("⚙️ Configurações", callback_data='s')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    status = (
        f"📍 **Planície (Lv 1)**\n"
        f"👤 **{nome}** ({classe})\n"
        f"❤️ **HP:** 100/100 🟥🟥🟥⬜\n"
        f"⚡ **Energia:** 20/20 🟩🟩🟩⬜\n"
        f"💰 **Ouro:** 250"
    )

    await update.message.reply_photo(
        photo=IMG_MENU_PRINCIPAL,
        caption=status,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return ConversationHandler.END

def main():
    token = os.getenv("TELEGRAM_TOKEN")
    application = Application.builder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(tutorial, pattern='tutorial')],
        states={
            ESCOLHENDO_CLASSE: [CallbackQueryHandler(escolher_nome)],
            DEFININDO_NOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, menu_principal)],
        },
        fallbacks=[CommandHandler('start', start)],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)

    application.run_polling()

if __name__ == '__main__':
    main()
