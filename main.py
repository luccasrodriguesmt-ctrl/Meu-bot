import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Configuração de Logs
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# Estados da Conversa
TELA_CLASSE, TELA_NOME, TELA_MENU = range(3)

# Links das Imagens (Links diretos das imagens que você mandou)
IMG_BOAS_VINDAS = "https://i.imgur.com/8pS1Xo5.jpeg" 
IMG_CLASSES = "https://i.imgur.com/uP6M8fL.jpeg"
IMG_MENU_PRINCIPAL = "https://i.imgur.com/uP6M8fL.jpeg"

# 1. TELA DE BOAS-VINDAS (Nova Mensagem apenas aqui)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Criar Nova Conta 📝", callback_data='ir_para_classes')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_photo(
        photo=IMG_BOAS_VINDAS,
        caption="✨ **Bem-vindo ao Aventuras Rabiscadas!**\n\nSua jornada épica começa agora.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return TELA_CLASSE

# 2. TELA DE ESCOLHA DE CLASSE (Edita a mensagem anterior)
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

    # Troca a foto e o texto na mesma mensagem
    await query.edit_message_media(
        media=InputMediaPhoto(media=IMG_CLASSES, caption="🎭 **Escolha sua Classe:**"),
        reply_markup=reply_markup
    )
    return TELA_NOME

# 3. PEDIR NOME (Edita para texto puro para facilitar a resposta do usuário)
async def pedir_nome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    context.user_data['classe'] = query.data
    await query.answer()

    # Apaga a mensagem da imagem para o chat não ficar poluído ao pedir texto
    await query.delete_message()
    
    msg = await query.message.reply_text(f"⚔️ Você escolheu **{query.data}**!\n\nAgora, digite o **nome** do seu herói:")
    context.user_data['last_msg_id'] = msg.message_id # Guarda o ID para apagar depois
    return TELA_MENU

# 4. TELA PRINCIPAL (Apaga o pedido de nome e cria o Menu Fixo)
async def menu_principal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nome = update.message.text
    classe = context.user_data.get('classe', 'Aventureiro')
    
    # Apaga o nome que o usuário digitou e a pergunta do bot
    try:
        await update.message.delete()
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=context.user_data['last_msg_id'])
    except:
        pass

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
        entry_points=[CommandHandler('start', start)],
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
