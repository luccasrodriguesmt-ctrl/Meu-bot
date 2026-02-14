from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

TOKEN = "SEU_TOKEN_AQUI"
players = {}

CLASSES = {
    "Guerreiro": {"img": "https://picsum.photos/seed/knight/400/300", "hp": 120, "en": 20},
    "Bruxa": {"img": "https://picsum.photos/seed/wizard/400/300", "hp": 80, "en": 25},
    "Ladino": {"img": "https://picsum.photos/seed/thief/400/300", "hp": 90, "en": 22},
    "Bêbado": {"img": "https://picsum.photos/seed/beer/400/300", "hp": 150, "en": 10}
}

def gerar_menu_principal(uid):
    p = players[uid]

    hp_blocos = max(0, min(5, p['hp'] // 30))
    en_blocos = max(0, min(5, p['en'] // 5))

    b_hp = "🟥" * hp_blocos + "⬜" * (5 - hp_blocos)
    b_en = "🟩" * en_blocos + "⬜" * (5 - en_blocos)

    txt = (
        f"🏰 *Planície* (Lv {p['lv']})\n"
        f"👤 Classe: *{p['classe']}*\n"
        f"❤️ HP: {p['hp']} {b_hp}\n"
        f"⚡ Energia: {p['en']} {b_en}\n"
        f"💰 Gold: {p['gold']}"
    )

    kb = [
        [InlineKeyboardButton("⚔️ Caçar", callback_data='c'), InlineKeyboardButton("🗺️ Viajar", callback_data='n')],
        [InlineKeyboardButton("🎒 Inventário", callback_data='n'), InlineKeyboardButton("👤 Perfil", callback_data='n')],
        [InlineKeyboardButton("🔄 Resetar", callback_data='reset')]
    ]

    return txt, InlineKeyboardMarkup(kb)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid in players:
        txt, markup = gerar_menu_principal(uid)
        await context.bot.send_photo(chat_id=uid, photo=players[uid]['img'], caption=txt, reply_markup=markup, parse_mode="Markdown")
    else:
        img_inicio = "https://picsum.photos/seed/start/400/300"
        kb = [
            [InlineKeyboardButton("🛡️ Guerreiro", callback_data='sel_Guerreiro'), InlineKeyboardButton("🧙 Bruxa", callback_data='sel_Bruxa')],
            [InlineKeyboardButton("🗡️ Ladino", callback_data='sel_Ladino'), InlineKeyboardButton("🍺 Bêbado", callback_data='sel_Bêbado')]
        ]
        await context.bot.send_photo(chat_id=uid, photo=img_inicio, caption="✨ *BEM-VINDO*\nEscolha sua classe:", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def clique(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id
    await q.answer()

    if q.data.startswith("sel_"):
        nome_c = q.data.replace("sel_", "")

        c = CLASSES[nome_c]
        players[uid] = {"classe": nome_c, "hp": c['hp'], "en": c['en'], "gold": 0, "lv": 1, "img": c['img']}

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

    if q.data == "reset":
        players.pop(uid, None)
        await q.edit_message_caption(caption="🚮 Personagem deletado! Use /start para criar outro.")
        return

    if q.data == "c":
        if uid not in players:
            await q.answer("❌ Crie um personagem primeiro!", show_alert=True)
            return

        if players[uid]["en"] < 2:
            await q.answer("⚡ Sem energia!", show_alert=True)
            return

        players[uid]["en"] -= 2
        players[uid]["gold"] += 10

        txt, markup = gerar_menu_principal(uid)
        await q.edit_message_caption(caption=txt, reply_markup=markup, parse_mode="Markdown")
        return

    await q.answer("🚧 Em desenvolvimento!", show_alert=True)

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(clique))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
