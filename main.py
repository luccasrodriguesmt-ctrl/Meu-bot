import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Log para ver erros no Render
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Primeira tela com botão
    keyboard = [[InlineKeyboardButton("Escolher Classe ⚔️", callback_data='menu_classes')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "✨ **Bem-vindo ao RPG!**\n\nClique no botão abaixo para começar.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def menu_classes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("Guerreiro", callback_data='class_g'), 
         InlineKeyboardButton("Arqueiro", callback_data='class_a')],
        [InlineKeyboardButton("Bruxa", callback_data='class_b')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("🛡️ **Escolha sua classe:**", reply_markup=reply_markup, parse_mode='Markdown')

def main():
    # Pega o token do Render
    token = os.getenv("TELEGRAM_TOKEN")
    
    if not token:
        print("ERRO: Variável TELEGRAM_TOKEN não encontrada!")
        return

    app = Application.builder().token(token).build()

    # Comandos básicos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(menu_classes, pattern='menu_classes'))

    print("Bot rodando...")
    app.run_polling()

if __name__ == '__main__':
    main()
