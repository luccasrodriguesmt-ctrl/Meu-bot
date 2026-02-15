from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

# --- CONFIG ---
TOKEN = "SEU_TOKEN_AQUI"

players = {}

# Imagens e status das classes
CLASSES = {
    "Guerreiro": {"img": "https://picsum.photos/seed/knight/400/300", "hp": 120, "en": 20},
    "Bruxa": {"img": "https://picsum.photos/seed/wizard/400/300", "hp": 80, "en": 25},
    "Ladino": {"img": "https://picsum.photos/seed/thief/400/300", "hp": 90, "en": 22},
    "Bêbado": {"img": "https://picsum.photos/seed/beer/400/300", "hp": 150, "en": 10}
}


# --- MENU PRINCIPAL ---
def gerar_menu_principal(uid):
    p = players[uid]

    hp_blocos = max(0, min(5, p['hp'] // 30))
    en_blocos = max(0, min(5, p['en'] // 5))

    b_hp = "🟥" * hp_blocos + "⬜" * (5 - hp_blocos)
    b_en = "🟩" * en_blocos + "⬜" * (5 - en_blocos)

    txt = (
        f"🏰 *Planície* (Lv {p['lv']})\n"
        f"🧾 Nome: *{p['nome']}*\n"
        f"👤 Classe: *{p['classe']}*\n"
        f"❤️ HP: {p['hp']} {b_hp}\n"
        f"⚡ Energia: {p['en']} {b_en}\n"
        f"💰 Gold: {p['gold']}"
    )

    kb = [
        [InlineKeyboardButton("⚔️ Caçar", callback_data='c'), InlineKeyboardButton("🗺️ Viajar", callback_data='n')],
        [InlineKeyboardButton("✍️ Definir Nome", callback_data='nome')],
        [InlineKeyboardButton("🎒 Inventário", callback_data='n'), InlineKeyboardButton("👤 Perfil", callback_data='n')],
        [InlineKeyboardButton("🔄 Resetar", callback_data='reset')]
    ]

    return txt, InlineKeyboardMarkup(kb)


# --- /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    # Se já tem personagem
    if uid in players:
        txt, markup = gerar_menu_principal(uid)
        await context.bot.send_photo(
            chat_id=uid,
            photo=players[uid]['img'],
            caption=txt,
            reply_markup=markup,
            parse_mode='Markdown'
        )
        return

    # Se não tem, pede classe
    img_inicio = "https://picsum.photos/seed/start/400/300"
    kb = [
        [InlineKeyboardButton("🛡️ Guerreiro", callback_data='sel_Guerreiro'),
         InlineKeyboardButton("🧙 Bruxa", callback_data='sel_Bruxa')],
        [InlineKeyboardButton("🗡️ Ladino", callback_data='sel_Ladino'),
         InlineKeyboardButton("🍺 Bêbado", callback_data='sel_Bêbado')]
    ]

    await context.bot.send_photo(
        chat_id=uid,
        photo=img_inicio,
        caption="✨ *BEM-VINDO AO RPG*\n\nEscolha sua classe:",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode='Markdown'
    )


# --- CLIQUES DOS BOTÕES ---
async def clique(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id
    await q.answer()

    # --- SELECIONAR CLASSE ---
    if q.data.startswith('sel_'):
        nome_c = q.data.replace("sel_", "")

        c = CLASSES[nome_c]

        players[uid] = {
            "nome": "Sem nome",
            "classe": nome_c,
            "hp": c['hp'],
            "en": c['en'],
            "gold": 0,
            "lv": 1,
            "img": c['img']
        }

        txt, markup = gerar_menu_principal(uid)

        await q.edit_message_media(
            media=InputMediaPhoto(
                media=c["img"],
                caption=f"✅ Você agora é um *{nome_c}*!\n\n{txt}",
                parse_mode="Markdown"
            ),
            reply_markup=markup
        )
        return

    # --- RESET ---
    if q.data == 'reset':
        players.pop(uid, None)
        context.user_data["esperando_nome"] = False
        await q.edit_message_caption(
            caption="🚮 Personagem deletado!\nUse /start para criar outro."
        )
        return

    # --- DEFINIR NOME ---
    if q.data == "nome":
        if uid not in players:
            await q.answer("❌ Crie um personagem primeiro! Use /start.", show_alert=True)
            return

        context.user_data["esperando_nome"] = True
        await q.message.reply_text("✍️ Agora digite o nome do seu personagem:")
        return

    # --- CAÇAR ---
    if q.data == 'c':
        if uid not in players:
            await q.answer("❌ Crie um personagem primeiro!", show_alert=True)
            return

        if players[uid]['en'] < 2:
            await q.answer("⚡ Sem energia!", show_alert=True)
            return

        players[uid]['en'] -= 2
        players[uid]['gold'] += 10

        txt, markup = gerar_menu_principal(uid)
        await q.edit_message_caption(
            caption=txt,
            reply_markup=markup,
            parse_mode='Markdown'
        )
        return

    # --- OUTROS BOTÕES ---
    await q.answer("🚧 Em desenvolvimento!", show_alert=True)


# --- RECEBER TEXTO (NOME DO PERSONAGEM) ---
async def receber_texto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    # Só entra aqui se ele clicou no botão "Definir Nome"
    if context.user_data.get("esperando_nome"):

        # Para não ficar preso
        context.user_data["esperando_nome"] = False

        if uid not in players:
            await update.message.reply_text("❌ Você ainda não criou personagem. Use /start.")
            return

        nome = update.message.text.strip()

        # Validações simples
        if len(nome) < 3:
            await update.message.reply_text("⚠️ Nome muito curto! Digite um nome com pelo menos 3 letras.")
            return

        if len(nome) > 20:
            await update.message.reply_text("⚠️ Nome muito longo! Máximo 20 caracteres.")
            return

        # Salva nome
        players[uid]["nome"] = nome

        txt, markup = gerar_menu_principal(uid)

        await update.message.reply_text(f"✅ Nome definido: *{nome}*", parse_mode="Markdown")

        # Reenvia menu atualizado
        await context.bot.send_photo(
            chat_id=uid,
            photo=players[uid]['img'],
            caption=txt,
            reply_markup=markup,
            parse_mode="Markdown"
        )
        return


# --- MAIN ---
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(clique))

    # Captura texto normal (nome)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receber_texto))

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
