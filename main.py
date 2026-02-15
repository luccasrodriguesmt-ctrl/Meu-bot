import os
from flask import Flask
from instagrapi import Client
import threading
import time

app = Flask(__name__)

# Configurações do Bot
USERNAME = 'SEU_USUARIO'
PASSWORD = 'SUA_SENHA'

cl = Client()

# Dicionário para salvar o progresso temporário dos usuários
# Em um jogo real, você usaria um Banco de Dados (SQLite ou PostgreSQL)
players = {}

def handle_message(message):
    user_id = message.user_id
    text = message.text.lower().strip()
    
    # Se o jogador não existe, começa a apresentação
    if user_id not in players:
        players[user_id] = {'step': 'welcome'}
        cl.direct_answer(message.id, "⚔️ Bem-vindo ao RPG Aventuras! \nDigite 'jogar' para começar sua jornada.")
        return

    state = players[user_id]

    # TELA 1: Boas-vindas -> Escolha de Classe
    if state['step'] == 'welcome':
        players[user_id]['step'] = 'choose_class'
        msg = ("ESCOLHA SEU PERSONAGEM:\n\n"
               "🛡️ Guerreiro\n"
               "🏹 Arqueiro\n"
               "🔮 Bruxa\n\n"
               "Digite o nome da classe para escolher!")
        cl.direct_answer(message.id, msg)

    # TELA 2: Escolha de Classe -> Nome
    elif state['step'] == 'choose_class':
        classes = ['guerreiro', 'arqueiro', 'bruxa']
        if text in classes:
            players[user_id]['class'] = text
            players[user_id]['step'] = 'choose_name'
            cl.direct_answer(message.id, f"Ótima escolha! Agora, qual será o nome do seu {text}?")
        else:
            cl.direct_answer(message.id, "Por favor, escolha entre: Guerreiro, Arqueiro ou Bruxa.")

    # TELA 3: Nome -> Menu Principal
    elif state['step'] == 'choose_name':
        players[user_id]['name'] = message.text
        players[user_id]['step'] = 'main_menu'
        show_main_menu(message, players[user_id])

    # TELA FINAL: Menu Principal (Interações)
    elif state['step'] == 'main_menu':
        if "caçar" in text:
            cl.direct_answer(message.id, "⚔️ Você saiu para caçar e encontrou um monstro!")
        elif "perfil" in text:
            p = players[user_id]
            cl.direct_answer(message.id, f"👤 PERFIL:\nNome: {p['name']}\nClasse: {p['class']}\nLVL: 1")
        else:
            show_main_menu(message, players[user_id])

def show_main_menu(message, player_data):
    menu = (f"📍 LOCAL: Planície (Lv 1)\n"
            f"👤 Jogador: {player_data['name']}\n"
            f"❤️ HP: 100/100\n"
            "----------------------\n"
            "Escolha uma ação:\n"
            "⚔️ CAÇAR    🌍 VIAJAR\n"
            "🎒 INVENTÁRIO  👤 PERFIL\n"
            "🛒 LOJA    🗝️ MASMORRA\n"
            "⚙️ CONFIGURAÇÃO")
    cl.direct_answer(message.id, menu)

def bot_loop():
    cl.login(USERNAME, PASSWORD)
    print("Bot Logado!")
    while True:
        try:
            messages = cl.direct_threads()
            for thread in messages:
                thread_id = thread.id
                last_msg = thread.messages[0]
                if not last_msg.is_sent_by_viewer: # Responder apenas se não for o bot que enviou
                    handle_message(last_msg)
            time.sleep(10) # Espera 10 segundos para não ser banido
        except Exception as e:
            print(f"Erro: {e}")
            time.sleep(30)

@app.route('/')
def home():
    return "Bot de RPG Rodando!"

if __name__ == "__main__":
    # Inicia o bot em uma thread separada
    threading.Thread(target=bot_loop).start()
    # Inicia o Flask para o Render não dar erro de porta
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
