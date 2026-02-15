import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Configuração de Logs
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Estados da Conversa
TELA_CLASSE, TELA_NOME, TELA_MENU = range(3)

# Links das Imagens (Baseados no seu tema)
IMG_BOAS_VINDAS = "https://i.imgur.com/8pS1Xo5.jpeg" 
IMG_CLASSES = "https://i.imgur.com/uP6M8fL.jpeg"
IMG_MENU_PRINCIPAL = "https://i.imgur.com/uP6M8fL.jpeg"

# 1. TELA DE BOAS-VINDAS
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Criar Nova Conta 📝", callback_data='ir_para_classes')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    texto = "✨ **Bem-vindo ao Aventuras Rabiscadas!**\n\nSua jornada épica começa agora. Clique abaixo para iniciar sua história."
    
    if update.message:
        await update.message.reply_text(texto, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.callback_query.message.edit_text(texto, reply_markup=reply_markup, parse_mode='Markdown')
    return TELA_CLASSE

# 2. TELA DE ESCOLHA DE CLASSE
async def menu_classes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("🛡️ Guerreiro", callback_data='Guerreiro'),
         InlineKeyboardButton("🏹 Arqueiro", callback_data='Arqueiro')],
        [InlineKeyboardButton("🔮 Bruxa", callback_data='Bruxa'),
         InlineKeyboardButton("🔥 Mago", callback_data='Mago')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_photo(
        photo=IMG_CLASSES,
        caption="🎭 **Escolha sua Classe:**\nCada uma possui habilidades únicas.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return TELA_NOME

# 3. PEDIR NOME
async def pedir_nome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    context.user_data['classe'] = query.data
    await query.answer()

    await query.message.reply_text(f"Você escolheu **{query.data}**!\n\nAgora, escreva o **nome** do seu personagem:")
    return TELA_MENU

# 4. TELA PRINCIPAL (MENU)
async def menu_principal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nome = update.message.text
    classe = context.user_data.get('classe', 'Aventureiro')
    
    keyboard = [
        [InlineKeyboardButton("⚔️ Caçar", callback_data='c'), InlineKeyboardButton("🗺️ Viajar", callback_data='v')],
        [InlineKeyboardButton("🎒 Inventário", callback_data='i'), InlineKeyboardButton("👤 Perfil", callback_data='p')],
        [InlineKeyboardButton("🏪 Loja", callback_data='l'), InlineKeyboardButton("🏰 Masmorra", callback_data='m')],
        [InlineKeyboardButton("⚙️ Configuração", callback_data='s')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    status = (
        f"📍 **Planície (Lv 1)**\n"
        f"👤 **{nome}** ({classe})\n"
        f"❤️ **HP:** 100/100 🟥🟥🟥🟥\n"
        f"⚡ **Energia:** 20/20 🟩🟩🟩🟩\n"
        f"💰 **Gold:** 250"
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
        entry_points=[CommandHandler('start', start), CallbackQueryHandler(start, pattern='^voltar_inicio$')],
        states={
            TELA_CLASSE: [CallbackQueryHandler(menu_classes, pattern='^ir_para_classes$')],
            TELA_NOME: [CallbackQueryHandler(pedir_nome)],
            TELA_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, menu_principal)],
        },
        fallbacks=[CommandHandler('start', start)],
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()
