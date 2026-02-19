import os, random, logging, threading, psycopg2
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse
import asyncio
from telegram.request import HTTPXRequest

# Configurar timeouts menores
request = HTTPXRequest(connection_pool_size=8, connect_timeout=10, read_timeout=10)

VERSAO = "5.4.0"  # <--- MUDEI AQUI
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def run_fake_server():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"Bot Online!")
        def log_message(self, format, *args): pass
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), Handler)
    logging.info(f"HTTP Server on port {port}")
    server.serve_forever()

threading.Thread(target=run_fake_server, daemon=True).start()

# Configuração PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

def get_db_connection():
    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL, sslmode='require')
    else:
        return psycopg2.connect(
            host=os.getenv("PGHOST"),
            database=os.getenv("PGDATABASE"),
            user=os.getenv("PGUSER"),
            password=os.getenv("PGPASSWORD"),
            port=os.getenv("PGPORT", 5432),
            sslmode='require'
        )

IMG = "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/Gemini_Generated_Image_n68a2ln68a2ln68a.png?raw=true"

IMAGENS = {
    "logo": "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/abertura.jpeg?raw=true",
    "sel": "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/Gemini_Generated_Image_l46bisl46bisl46b.png?raw=true",
    "classes": {
        "Guerreiro": "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/guerreiro.jpeg?raw=true",
        "Arqueiro": "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/arqueira.jpeg?raw=true",
        "Bruxa": "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/bruxa.jpeg?raw=true",
        "Mago": "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/mago.jpeg?raw=true"
    },
    "mapas": {
        1: "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/paisagem%201.jpeg?raw=true",
        2: "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/paisagem%202.jpeg?raw=true",
        3: "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/paisagem%203.jpeg?raw=true"
    },
    "locais": {
        "cap_1": "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/zenite.jpeg?raw=true",
        "v1_1": "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/bragaluna.jpeg?raw=true",
        "v2_1": "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/eterfenda.jpeg?raw=true",
        "cap_2": "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/forte%20floresta.jpeg?raw=true",
        "v1_2": "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/acampamento.jpeg?raw=true",
        "v2_2": "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/refugio.jpeg?raw=true",
        "cap_3": "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/cidade%20subterania.jpeg?raw=true",
        "v1_3": "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/mina%20abandonada.jpeg?raw=true",
        "v2_3": "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/forte%20anao.jpeg?raw=true"
    },
    "lojas": {
        "cap_1": "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/loja%20zenite.jpeg?raw=true",
        "v1_1": "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/loja%20bragaluna.jpeg?raw=true",
        "cap_2": "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/loja%20forte%20floresta.jpeg?raw=true",
        "v1_2": "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/loja%20acampamento.jpeg?raw=true",
        "v2_2": "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/loja%20refugio.jpeg?raw=true",
        "cap_3": "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/loja%20cdd%20subterra.jpeg?raw=true",
        "v2_3": "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/loja%20forte%20anao.jpeg?raw=true"
    },
    "contrabandistas": {
        1: "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/contrabandista%201.jpeg?raw=true",
        2: "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/contrabandista%202.jpeg?raw=true",
        3: "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/contrabandista%203.jpeg?raw=true"
    },
    "combate": "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/Gemini_Generated_Image_n68a2ln68a2ln68a.png?raw=true",
    "elixir": {
        "Poção de Vida": "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/po%C3%A7ao%20vermelhaa.jpeg?raw=true",
        "Poção Grande de Vida": "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/po%C3%A7ao%20rosa.jpeg?raw=true",
        "Poção de Mana": "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/po%C3%A7ao%20azul.jpeg?raw=true",
        "Elixir de Mana": "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/po%C3%A7ao%20amarela.jpeg?raw=true"
    },
    "herois": {
        "heroi1": "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/inghost.jpeg?raw=true",
        "heroi2": "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/biel.jpeg?raw=true",
        "heroi3": "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/zuri.jpeg?raw=true",
        "heroi4": "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/edu.jpeg?raw=true",
        "heroi5": "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/fabio.jpeg?raw=true",
        "heroi6": "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/mateus.jpeg?raw=true"
    },
    "monstros": {
        "Goblin": {
            1: "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/goblin%2001.jpeg?raw=true",
            2: "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/goblin%2002.jpeg?raw=true",
            3: "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/globin%2003.jpeg?raw=true"
        },
        "Lobo": {
            1: "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/lobo%2001.jpeg?raw=true",
            2: "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/lobo%2002.jpeg?raw=true",
            3: "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/lobo%2003.jpeg?raw=true"
        },
        "Orc": {
            1: "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/orc%2001.jpeg?raw=true",
            2: "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/orc%2002.jpeg?raw=true",
            3: "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/orc%2003.jpeg?raw=true"
        },
        "Esqueleto": {
            1: "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/esc%2001.jpeg?raw=true",
            2: "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/esc%2002.jpeg?raw=true",
            3: "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/esc%2003.jpeg?raw=true"
        },
        "Dragão": {
            1: "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/dragao%2001.png?raw=true",
            2: "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/dragao%2002.png?raw=true",
            3: "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/dragao%2003.png?raw=true"
        }
    }
}

# Atributos base por classe
CLASSE_STATS = {
    "Guerreiro": {"hp": 250, "mana": 0, "atk": 8, "def": 18, "crit": 0, "double": False, "especial": None},
    "Arqueiro": {"hp": 120, "mana": 0, "atk": 10, "def": 5, "crit": 25, "double": True, "especial": None},
    "Bruxa": {"hp": 150, "mana": 100, "atk": 9, "def": 8, "crit": 10, "double": False, "especial": "maldição"},
    "Mago": {"hp": 130, "mana": 120, "atk": 6, "def": 6, "crit": 15, "double": False, "especial": "explosão"}
}

MAPAS = {
    1: {"nome": "Planície", "lv": 1, "aviso": "", "loc": {
        "cap": {"nome": "Zênite", "loja": True},
        "v1": {"nome": "Bragaluna", "loja": True},
        "v2": {"nome": "Eterfenda", "loja": False}
    }},
    2: {"nome": "Floresta Sombria", "lv": 5, "aviso": "⚠️ Região Perigosa - Lv 5+", "loc": {
        "cap": {"nome": "Forte Floresta", "loja": True},
        "v1": {"nome": "Acampamento", "loja": True},
        "v2": {"nome": "Refúgio", "loja": False}
    }},
    3: {"nome": "Caverna Profunda", "lv": 10, "aviso": "🔥 Região Mortal - Lv 10+", "loc": {
        "cap": {"nome": "Cidade Subterrânea", "loja": True},
        "v1": {"nome": "Mina Abandonada", "loja": False},
        "v2": {"nome": "Forte Anão", "loja": True}
    }}
}

HEROIS = {
    1: [
        {
            "nome": "Inghost, o Lorde de Bragaluna",
            "img": "heroi1",
            "desc": "Um cavaleiro lendário com armadura reluzente.",
            "fala": "Vejo que enfrenta perigos. Permita-me honrar minha espada ao seu lado!"
        },
        {
            "nome": "GabrielMinaRrj, Almirante-Mor de Eterfenda",
            "img": "heroi2", 
            "desc": "Almirante-Mor de Eterfenda, arqueiro de precisão mortal.",
            "fala": "Esses inimigos são perigosos para enfrentar sozinho. Aceita minha ajuda?"
        }
    ],
    2: [
        {
            "nome": "GuntherZuri, a Druida do Refúgio",
            "img": "heroi3",
            "desc": "Uma druida muito poderosa que cuida de um refúgio.",
            "fala": "As árvores sussurram sobre seus desafios. Deixe a natureza lutar ao seu lado!"
        },
        {
            "nome": "Edu345jamampiro, o Velho Edu",
            "img": "heroi4",
            "desc": "Lord no Forte Floresta, anda acompanhado de um lobo gigante.",
            "fala": "Meu lobo e eu conhecemos bem esses perigos. Juntos somos mais fortes!"
        }
    ],
    3: [
        {
            "nome": "MrKiigsmann, Rei dos Anões",
            "img": "heroi5",
            "desc": "Um anão muito poderoso e rei em Forte Anão.",
            "fala": "Estas profundezas são traiçoeiras, jovem. Deixe este velho lhe guiar!"
        },
        {
            "nome": "X__MATHEUSS_X, a Sombra Noturna",
            "img": "heroi6",
            "desc": "O mais temperamental de todos, sempre de mal humor.",
            "fala": "Tch... seus inimigos não verão a morte chegar. Quer minha lâmina ou não?"
        }
    ]
}

INIMIGOS = {
    "Goblin da Planície": {"hp": 100, "atk": 15, "def": 8, "xp": 25, "gold": 15, "desc": "Goblin verde", "m": [1], "tipo": "Goblin"},
    "Goblin da Floresta": {"hp": 300, "atk": 45, "def": 24, "xp": 75, "gold": 45, "desc": "Goblin feroz", "m": [2], "tipo": "Goblin"},
    "Goblin da Caverna": {"hp": 900, "atk": 135, "def": 72, "xp": 225, "gold": 135, "desc": "Goblin sombrio", "m": [3], "tipo": "Goblin"},
    "Lobo da Planície": {"hp": 150, "atk": 22, "def": 12, "xp": 40, "gold": 25, "desc": "Lobo selvagem", "m": [1], "tipo": "Lobo"},
    "Lobo da Floresta": {"hp": 450, "atk": 66, "def": 36, "xp": 120, "gold": 75, "desc": "Lobo alfa", "m": [2], "tipo": "Lobo"},
    "Lobo da Caverna": {"hp": 1350, "atk": 198, "def": 108, "xp": 360, "gold": 225, "desc": "Lobo das sombras", "m": [3], "tipo": "Lobo"},
    "Orc da Planície": {"hp": 280, "atk": 38, "def": 20, "xp": 80, "gold": 60, "desc": "Orc guerreiro", "m": [1, 2], "tipo": "Orc"},
    "Orc da Floresta": {"hp": 840, "atk": 114, "def": 60, "xp": 240, "gold": 180, "desc": "Orc berserker", "m": [2, 3], "tipo": "Orc"},
    "Orc da Caverna": {"hp": 2520, "atk": 342, "def": 180, "xp": 720, "gold": 540, "desc": "Orc brutal", "m": [3], "tipo": "Orc"},
    "Esqueleto da Planície": {"hp": 220, "atk": 30, "def": 15, "xp": 70, "gold": 50, "desc": "Esqueleto guerreiro", "m": [1, 2], "tipo": "Esqueleto"},
    "Esqueleto da Floresta": {"hp": 660, "atk": 90, "def": 45, "xp": 210, "gold": 150, "desc": "Esqueleto ancestral", "m": [2, 3], "tipo": "Esqueleto"},
    "Esqueleto da Caverna": {"hp": 1980, "atk": 270, "def": 135, "xp": 630, "gold": 450, "desc": "Esqueleto rei", "m": [3], "tipo": "Esqueleto"},
    "Dragão da Planície": {"hp": 600, "atk": 70, "def": 35, "xp": 300, "gold": 250, "desc": "Dragão jovem", "m": [1], "tipo": "Dragão"},
    "Dragão da Floresta": {"hp": 1800, "atk": 210, "def": 105, "xp": 900, "gold": 750, "desc": "Dragão ancestral", "m": [2], "tipo": "Dragão"},
    "Dragão da Caverna": {"hp": 5400, "atk": 630, "def": 315, "xp": 2700, "gold": 2250, "desc": "Dragão primordial", "m": [3], "tipo": "Dragão"}
}

EQUIPS = {
    "Espada Enferrujada": {"t": "arma", "atk": 5, "p": 50, "lv": 1, "cls": ["Guerreiro"]},
    "Espada de Ferro": {"t": "arma", "atk": 15, "p": 200, "lv": 5, "cls": ["Guerreiro"]},
    "Espada de Aço": {"t": "arma", "atk": 30, "p": 500, "lv": 10, "cls": ["Guerreiro"]},
    "Escudo de Madeira": {"t": "arm", "def": 8, "p": 50, "lv": 1, "cls": ["Guerreiro"]},
    "Escudo de Ferro": {"t": "arm", "def": 18, "p": 200, "lv": 5, "cls": ["Guerreiro"]},
    "Escudo de Aço": {"t": "arm", "def": 35, "p": 500, "lv": 10, "cls": ["Guerreiro"]},
    "Arco Simples": {"t": "arma", "atk": 8, "p": 50, "lv": 1, "cls": ["Arqueiro"]},
    "Arco Composto": {"t": "arma", "atk": 18, "p": 200, "lv": 5, "cls": ["Arqueiro"]},
    "Arco Élfico": {"t": "arma", "atk": 35, "p": 500, "lv": 10, "cls": ["Arqueiro"]},
    "Armadura Leve": {"t": "arm", "def": 5, "p": 50, "lv": 1, "cls": ["Arqueiro"]},
    "Couro Reforçado": {"t": "arm", "def": 12, "p": 200, "lv": 5, "cls": ["Arqueiro"]},
    "Manto Sombrio": {"t": "arm", "def": 20, "p": 500, "lv": 10, "cls": ["Arqueiro"]},
    "Cajado Antigo": {"t": "arma", "atk": 7, "p": 50, "lv": 1, "cls": ["Bruxa"]},
    "Cetro Lunar": {"t": "arma", "atk": 17, "p": 200, "lv": 5, "cls": ["Bruxa"]},
    "Varinha das Trevas": {"t": "arma", "atk": 32, "p": 500, "lv": 10, "cls": ["Bruxa"]},
    "Robe Místico": {"t": "arm", "def": 6, "p": 50, "lv": 1, "cls": ["Bruxa"]},
    "Manto Encantado": {"t": "arm", "def": 14, "p": 200, "lv": 5, "cls": ["Bruxa"]},
    "Vestes Arcanas": {"t": "arm", "def": 22, "p": 500, "lv": 10, "cls": ["Bruxa"]},
    "Bastão Iniciante": {"t": "arma", "atk": 10, "p": 50, "lv": 1, "cls": ["Mago"]},
    "Orbe de Fogo": {"t": "arma", "atk": 22, "p": 200, "lv": 5, "cls": ["Mago"]},
    "Cetro do Caos": {"t": "arma", "atk": 40, "p": 500, "lv": 10, "cls": ["Mago"]},
    "Túnica Simples": {"t": "arm", "def": 5, "p": 50, "lv": 1, "cls": ["Mago"]},
    "Armadura Mágica": {"t": "arm", "def": 12, "p": 200, "lv": 5, "cls": ["Mago"]},
    "Robe do Arquimago": {"t": "arm", "def": 20, "p": 500, "lv": 10, "cls": ["Mago"]}
}

CONSUMIVEIS = {
    "Poção de Vida": {"tipo": "hp", "valor": 50, "preco": 20},
    "Poção Grande de Vida": {"tipo": "hp", "valor": 100, "preco": 50},
    "Poção de Mana": {"tipo": "mana", "valor": 30, "preco": 25},
    "Elixir de Mana": {"tipo": "mana", "valor": 60, "preco": 60}
}

DUNGEONS = [
    {"nome": "Covil Goblin", "lv": 5, "boss": "Rei Goblin", "bhp": 100, "batk": 20, "xp": 200, "g": 150},
    {"nome": "Ninho Lobos", "lv": 10, "boss": "Lobo Alpha", "bhp": 150, "batk": 30, "xp": 400, "g": 300}
]

ST_CL, ST_NM = range(2)

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS players (
                 id BIGINT PRIMARY KEY, 
                 nome TEXT, 
                 classe TEXT, 
                 hp INTEGER, 
                 hp_max INTEGER,
                 mana INTEGER DEFAULT 0, 
                 mana_max INTEGER DEFAULT 0,
                 lv INTEGER, 
                 exp INTEGER, 
                 gold INTEGER, 
                 energia INTEGER, 
                 energia_max INTEGER,
                 mapa INTEGER DEFAULT 1, 
                 local TEXT DEFAULT 'cap',
                 arma TEXT, 
                 arm TEXT, 
                 atk_b INTEGER DEFAULT 0, 
                 def_b INTEGER DEFAULT 0,
                 crit INTEGER DEFAULT 0, 
                 double_atk INTEGER DEFAULT 0)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS inv (
                 pid BIGINT, 
                 item TEXT, 
                 qtd INTEGER DEFAULT 1, 
                 PRIMARY KEY (pid, item))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS dung (
                 pid BIGINT, 
                 did INTEGER, 
                 PRIMARY KEY (pid, did))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS combate (
                 pid BIGINT PRIMARY KEY, 
                 inimigo TEXT, 
                 i_hp INTEGER, 
                 i_hp_max INTEGER,
                 i_atk INTEGER, 
                 i_def INTEGER, 
                 i_xp INTEGER, 
                 i_gold INTEGER, 
                 turno INTEGER DEFAULT 1,
                 defendendo INTEGER DEFAULT 0, 
                 heroi TEXT DEFAULT NULL, 
                 tipo_monstro TEXT, 
                 mapa_monstro INTEGER)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS heroi_oferta (
                 pid BIGINT PRIMARY KEY, 
                 heroi_nome TEXT, 
                 heroi_img TEXT, 
                 inimigo TEXT, 
                 i_hp INTEGER, 
                 i_atk INTEGER, 
                 i_def INTEGER, 
                 i_xp INTEGER, 
                 i_gold INTEGER,
                 tipo_monstro TEXT, 
                 mapa_monstro INTEGER)''')
    
    conn.commit()
    conn.close()

def get_p(uid):
    conn = get_db_connection()
    c = conn.cursor(cursor_factory=RealDictCursor)
    c.execute("SELECT * FROM players WHERE id = %s", (uid,))
    p = c.fetchone()
    conn.close()
    return p

def get_combate(uid):
    conn = get_db_connection()
    c = conn.cursor(cursor_factory=RealDictCursor)
    c.execute("SELECT * FROM combate WHERE pid = %s", (uid,))
    cb = c.fetchone()
    conn.close()
    return cb

def get_heroi_oferta(uid):
    conn = get_db_connection()
    c = conn.cursor(cursor_factory=RealDictCursor)
    c.execute("SELECT * FROM heroi_oferta WHERE pid = %s", (uid,))
    h = c.fetchone()
    conn.close()
    return h

def del_p(uid):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM heroi_oferta WHERE pid = %s", (uid,))
    c.execute("DELETE FROM combate WHERE pid = %s", (uid,))
    c.execute("DELETE FROM dung WHERE pid = %s", (uid,))
    c.execute("DELETE FROM inv WHERE pid = %s", (uid,))
    c.execute("DELETE FROM players WHERE id = %s", (uid,))
    conn.commit()
    conn.close()

def get_inv(uid):
    conn = get_db_connection()
    c = conn.cursor(cursor_factory=RealDictCursor)
    c.execute("SELECT * FROM inv WHERE pid = %s", (uid,))
    inv = c.fetchall()
    conn.close()
    return {i['item']: i['qtd'] for i in inv}

def add_inv(uid, item, qtd=1):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""INSERT INTO inv (pid, item, qtd) 
                 VALUES (%s, %s, %s) 
                 ON CONFLICT (pid, item) 
                 DO UPDATE SET qtd = inv.qtd + %s""", 
              (uid, item, qtd, qtd))
    conn.commit()
    conn.close()

def use_inv(uid, item):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE inv SET qtd = qtd - 1 WHERE pid = %s AND item = %s", (uid, item))
    c.execute("DELETE FROM inv WHERE qtd <= 0")
    conn.commit()
    conn.close()

def barra(a, m, c="🟦"):
    if m <= 0: return "⬜"*10
    p = max(0, min(a/m, 1))
    return c*int(p*10) + "⬜"*(10-int(p*10))

def img_c(c):
    return IMAGENS["classes"].get(c, IMG)

def atk(p):
    base = CLASSE_STATS[p['classe']]['atk']
    return base + (p['lv']*3) + p['atk_b']

def deff(p):
    base = CLASSE_STATS[p['classe']]['def']
    return base + (p['lv']*2) + p['def_b']

async def menu(upd, ctx, uid, txt=""):
    p = get_p(uid)
    if not p: 
        await start(upd, ctx)
        return
    mi = MAPAS.get(p['mapa'], {})
    li = mi.get('loc', {}).get(p['local'], {})
    
    cap = f"🎮 **{VERSAO}**\n{'━'*20}\n👤 **{p['nome']}** — *{p['classe']} Lv. {p['lv']}*\n🗺️ {mi.get('nome','?')} | 📍 {li.get('nome','?')}\n\n❤️ HP: {p['hp']}/{p['hp_max']}\n└ {barra(p['hp'],p['hp_max'],'🟥')}\n"
    
    if p['mana_max'] > 0:
        cap += f"💙 MANA: {p['mana']}/{p['mana_max']}\n└ {barra(p['mana'],p['mana_max'],'🟦')}\n"
    
    cap += f"✨ XP: {p['exp']}/{p['lv']*100}\n└ {barra(p['exp'],p['lv']*100,'🟩')}\n\n⚔️ ATK: {atk(p)} | 🛡️ DEF: {deff(p)}\n"
    
    if p['crit'] > 0:
        cap += f"💥 CRIT: {p['crit']}%\n"
    if p['double_atk']:
        cap += f"⚡ Ataque Duplo\n"
    
    cap += f"💰 {p['gold']} | ⚡ {p['energia']}/{p['energia_max']}\n{'━'*20}\n{txt}"
    
    kb = [[InlineKeyboardButton("⚔️ Caçar",callback_data="cacar"),InlineKeyboardButton("🗺️ Mapas",callback_data="mapas")],[InlineKeyboardButton("🏘️ Locais",callback_data="locais"),InlineKeyboardButton("👤 Status",callback_data="perfil")],[InlineKeyboardButton("🏪 Loja",callback_data="loja"),InlineKeyboardButton("🎒 Inventário",callback_data="inv")],[InlineKeyboardButton("🏰 Dungeons",callback_data="dungs"),InlineKeyboardButton("⚙️ Config",callback_data="cfg")]]
    img = img_c(p['classe'])
    
    if upd.callback_query:
        # EDITAR a mensagem em vez de deletar e criar nova
        try:
            await upd.callback_query.edit_message_media(
                media=InputMediaPhoto(media=img, caption=cap, parse_mode='Markdown'),
                reply_markup=InlineKeyboardMarkup(kb)
            )
        except:
            # Se não conseguir editar, aí sim deleta e cria nova
            try:
                await upd.callback_query.message.delete()
            except:
                pass
            await ctx.bot.send_photo(upd.effective_chat.id, img, caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    else:
        await upd.message.reply_photo(img, caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def cacar(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    p = get_p(uid)
    if not p:
        await q.answer("Crie personagem!", show_alert=True)
        return
    if p['energia'] < 2:
        await q.answer("🪫 Sem energia!", show_alert=True)
        return
    
    cb = get_combate(uid)
    if cb:
        await q.answer()
        await mostrar_combate(upd, ctx, uid)
        return
    
    inims = [n for n, d in INIMIGOS.items() if p['mapa'] in d['m']]
    if not inims:
        await q.answer("Sem inimigos!", show_alert=True)
        return
    
    inm = random.choice(inims)
    ini = INIMIGOS[inm]
    
    if random.random() < 0.05:
        herois_mapa = HEROIS.get(p['mapa'], [])
        if herois_mapa:
            heroi = random.choice(herois_mapa)
            
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("DELETE FROM heroi_oferta WHERE pid = %s", (uid,))
            c.execute("""INSERT INTO heroi_oferta 
                        (pid, heroi_nome, heroi_img, inimigo, i_hp, i_atk, i_def, i_xp, i_gold, tipo_monstro, mapa_monstro) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", 
                        (uid, heroi['nome'], heroi['img'], inm, ini['hp'], ini['atk'], ini['def'], 
                         ini['xp'], ini['gold'], ini['tipo'], p['mapa']))
            c.execute("UPDATE players SET energia = energia - 2 WHERE id = %s", (uid,))
            conn.commit()
            conn.close()
            
            await q.answer()
            await mostrar_oferta_heroi(upd, ctx, uid, heroi)
            return
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""INSERT INTO combate 
                (pid, inimigo, i_hp, i_hp_max, i_atk, i_def, i_xp, i_gold, turno, defendendo, heroi, tipo_monstro, mapa_monstro) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1, 0, NULL, %s, %s)""", 
                (uid, inm, ini['hp'], ini['hp'], ini['atk'], ini['def'], ini['xp'], ini['gold'], 
                 ini['tipo'], p['mapa']))
    c.execute("UPDATE players SET energia = energia - 2 WHERE id = %s", (uid,))
    conn.commit()
    conn.close()
    
    await q.answer()
    await mostrar_combate(upd, ctx, uid)

async def mostrar_oferta_heroi(upd, ctx, uid, heroi):
    q = upd.callback_query
    h_oferta = get_heroi_oferta(uid)
    
    if not h_oferta:
        await cacar(upd, ctx)
        return
    
    heroi_img = IMAGENS["herois"].get(heroi['img'], IMAGENS["classes"]["Guerreiro"])
    
    cap = f"⭐ **ENCONTRO INESPERADO!** ⭐\n{'━'*20}\n\n🦸 **{heroi['nome']}**\n\n_{heroi['desc']}_\n\n💬 \"{heroi['fala']}\"\n\n{'━'*20}\n⚔️ Inimigo à frente: **{h_oferta['inimigo']}**\n❤️ HP: {h_oferta['i_hp']}\n⚔️ ATK: {h_oferta['i_atk']}\n🛡️ DEF: {h_oferta['i_def']}\n{'━'*20}\n\n**Aceitar ajuda do herói?**"
    
    kb = [
        [InlineKeyboardButton("✅ ACEITAR AJUDA", callback_data="heroi_aceitar")],
        [InlineKeyboardButton("❌ RECUSAR (Lutar sozinho)", callback_data="heroi_recusar")]
    ]
    
    try:
        await q.message.delete()
    except:
        pass
    
    await ctx.bot.send_photo(upd.effective_chat.id, heroi_img, caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def heroi_aceitar(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    h_oferta = get_heroi_oferta(uid)
    
    if not h_oferta:
        await q.answer("Oferta expirada!", show_alert=True)
        await menu(upd, ctx, uid)
        return
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""INSERT INTO combate 
                (pid, inimigo, i_hp, i_hp_max, i_atk, i_def, i_xp, i_gold, turno, defendendo, heroi, tipo_monstro, mapa_monstro) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1, 0, %s, %s, %s)""", 
                (uid, h_oferta['inimigo'], h_oferta['i_hp'], h_oferta['i_hp'], 
                 h_oferta['i_atk'], h_oferta['i_def'], h_oferta['i_xp'], h_oferta['i_gold'], 
                 h_oferta['heroi_nome'], h_oferta['tipo_monstro'], h_oferta['mapa_monstro']))
    c.execute("DELETE FROM heroi_oferta WHERE pid = %s", (uid,))
    conn.commit()
    conn.close()
    
    await q.answer()
    
    try:
        await q.message.delete()
    except:
        pass
    
    await mostrar_combate(upd, ctx, uid)

async def heroi_recusar(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    h_oferta = get_heroi_oferta(uid)
    
    if not h_oferta:
        await q.answer("Oferta expirada!", show_alert=True)
        await menu(upd, ctx, uid)
        return
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""INSERT INTO combate 
                (pid, inimigo, i_hp, i_hp_max, i_atk, i_def, i_xp, i_gold, turno, defendendo, heroi, tipo_monstro, mapa_monstro) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1, 0, NULL, %s, %s)""", 
                (uid, h_oferta['inimigo'], h_oferta['i_hp'], h_oferta['i_hp'], 
                 h_oferta['i_atk'], h_oferta['i_def'], h_oferta['i_xp'], h_oferta['i_gold'],
                 h_oferta['tipo_monstro'], h_oferta['mapa_monstro']))
    c.execute("DELETE FROM heroi_oferta WHERE pid = %s", (uid,))
    conn.commit()
    conn.close()
    
    await q.answer()
    
    try:
        await q.message.delete()
    except:
        pass
    
    await mostrar_combate(upd, ctx, uid)

async def mostrar_combate(upd, ctx, uid):
    p = get_p(uid)
    cb = get_combate(uid)
    
    if not cb:
        await menu(upd, ctx, uid, "⚔️ Combate finalizado!")
        return
    
    inv = get_inv(uid)
    
    cap = f"⚔️ **COMBATE - Turno {cb['turno']}**\n{'━'*20}\n🐺 **{cb['inimigo']}**\n\n❤️ Inimigo: {cb['i_hp']}/{cb['i_hp_max']}\n└ {barra(cb['i_hp'],cb['i_hp_max'],'🟥')}\n\n❤️ Você: {p['hp']}/{p['hp_max']}\n└ {barra(p['hp'],p['hp_max'],'🟥')}\n"
    
    if p['mana_max'] > 0:
        cap += f"💙 Mana: {p['mana']}/{p['mana_max']}\n└ {barra(p['mana'],p['mana_max'],'🟦')}\n"
    
    if cb['heroi']:
        cap += f"\n⭐ **{cb['heroi']} ao seu lado!**\n"
    
    if cb['defendendo']:
        cap += "\n🛡️ **DEFENDENDO**\n"
    
    cap += f"\n⚔️ ATK: {atk(p)} | 🛡️ DEF: {deff(p)}"
    if p['crit'] > 0:
        cap += f" | 💥 {p['crit']}%"
    cap += f"\n{'━'*20}"
    
    kb = [[InlineKeyboardButton("⚔️ Atacar",callback_data="bat_atk"),InlineKeyboardButton("🛡️ Defender",callback_data="bat_def")]]
    
    if p['classe'] == "Bruxa" and p['mana'] >= 20:
        kb.append([InlineKeyboardButton("🔮 Maldição (20 mana)",callback_data="bat_esp")])
    elif p['classe'] == "Mago" and p['mana'] >= 30:
        kb.append([InlineKeyboardButton("🔥 Explosão (30 mana)",callback_data="bat_esp")])
    
    if cb['heroi']:
        kb.append([InlineKeyboardButton("⭐ INVOCAR HERÓI",callback_data="bat_heroi")])
    
    cons_kb = []
    if "Poção de Vida" in inv and inv["Poção de Vida"] > 0:
        cons_kb.append(InlineKeyboardButton(f"💊 Poção HP ({inv['Poção de Vida']})",callback_data="bat_pot_hp"))
    if "Poção Grande de Vida" in inv and inv["Poção Grande de Vida"] > 0:
        cons_kb.append(InlineKeyboardButton(f"💊+ Poção G HP ({inv['Poção Grande de Vida']})",callback_data="bat_pot_hp2"))
    if cons_kb:
        kb.append(cons_kb)
    
    cons_mana = []
    if p['mana_max'] > 0:
        if "Poção de Mana" in inv and inv["Poção de Mana"] > 0:
            cons_mana.append(InlineKeyboardButton(f"🔵 Mana ({inv['Poção de Mana']})",callback_data="bat_pot_mp"))
        if "Elixir de Mana" in inv and inv["Elixir de Mana"] > 0:
            cons_mana.append(InlineKeyboardButton(f"🔵+ Elixir ({inv['Elixir de Mana']})",callback_data="bat_pot_mp2"))
    if cons_mana:
        kb.append(cons_mana)
    
    kb.append([InlineKeyboardButton("🏃 Fugir",callback_data="bat_fug")])
    
    img_monstro = IMAGENS["combate"]
    if cb.get('tipo_monstro') and cb.get('mapa_monstro'):
        tipo = cb['tipo_monstro']
        mapa = cb['mapa_monstro']
        if tipo in IMAGENS["monstros"] and mapa in IMAGENS["monstros"][tipo]:
            img_monstro = IMAGENS["monstros"][tipo][mapa]
    
    try:
        if upd.callback_query and cb['turno'] > 1:
            await upd.callback_query.edit_message_caption(
                caption=cap, 
                reply_markup=InlineKeyboardMarkup(kb), 
                parse_mode='Markdown'
            )
        else:
            if upd.callback_query:
                try:
                    await upd.callback_query.message.delete()
                except:
                    pass
            await ctx.bot.send_photo(upd.effective_chat.id, img_monstro, caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    except Exception as e:
        print(f"Erro ao mostrar combate: {e}")
        try:
            if upd.callback_query:
                try:
                    await upd.callback_query.message.delete()
                except:
                    pass
            await ctx.bot.send_photo(upd.effective_chat.id, img_monstro, caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
        except:
            pass

async def bat_heroi(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    p = get_p(uid)
    cb = get_combate(uid)
    
    if not cb or not cb['heroi']:
        await q.answer("Sem herói!", show_alert=True)
        return
    
    await q.answer(f"⭐ {cb['heroi']} ataca!")
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE players SET gold = gold + %s, exp = exp + %s WHERE id = %s", 
                 (cb['i_gold'], cb['i_xp'], uid))
    c.execute("DELETE FROM combate WHERE pid = %s", (uid,))
    conn.commit()
    conn.close()
    
    heroi_img = IMAGENS["classes"]["Guerreiro"]
    for mapa_herois in HEROIS.values():
        for h in mapa_herois:
            if h['nome'] == cb['heroi']:
                heroi_img = IMAGENS["herois"].get(h['img'], IMAGENS["classes"]["Guerreiro"])
                break
    
    cap = f"⭐ **{cb['heroi']} DEVASTOU O INIMIGO!**\n{'━'*20}\n🐺 {cb['inimigo']} foi obliterado!\n\n💫 O herói usou seu poder máximo!\n\n💰 +{cb['i_gold']} Gold\n✨ +{cb['i_xp']} XP\n{'━'*20}\n\n*O herói desaparece em uma rajada de luz...*"
    kb = [[InlineKeyboardButton("🔙 Voltar",callback_data="voltar")]]
    
    try: await q.message.delete()
    except: pass
    await ctx.bot.send_photo(upd.effective_chat.id, heroi_img, caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def bat_atk(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    p = get_p(uid)
    cb = get_combate(uid)
    
    if not cb:
        await q.answer("Sem combate!")
        return
    
    await q.answer("⚔️ Ataque!")
    
    p_atk = atk(p)
    i_hp = cb['i_hp']
    i_atk = cb['i_atk']
    i_def = cb['i_def']
    p_hp = p['hp']
    
    log = []
    
    is_crit = random.randint(1, 100) <= p['crit']
    num_ataques = 2 if p['double_atk'] else 1
    
    for _ in range(num_ataques):
        dano = max(1, p_atk - i_def + random.randint(-2,2))
        if is_crit:
            dano = int(dano * 1.5)
        i_hp -= dano
        if is_crit:
            log.append(f"💥 CRÍTICO! -{dano} HP")
        else:
            log.append(f"⚔️ Você atacou! -{dano} HP")
        if i_hp <= 0:
            break
    
    if i_hp > 0:
        def_bonus = 0.5 if cb['defendendo'] else 0
        dano_ini = max(1, int((i_atk - deff(p)) * (1 - def_bonus) + random.randint(-2,2)))
        p_hp -= dano_ini
        log.append(f"🐺 {cb['inimigo']} atacou! -{dano_ini} HP")
    
    conn = get_db_connection()
    c = conn.cursor()
    if i_hp <= 0:
        p_hp = max(1, p_hp)
        c.execute("UPDATE players SET hp = %s, gold = gold + %s, exp = exp + %s WHERE id = %s", 
                     (p_hp, cb['i_gold'], cb['i_xp'], uid))
        c.execute("DELETE FROM combate WHERE pid = %s", (uid,))
        conn.commit()
        conn.close()
        
        cap = f"🏆 **VITÓRIA!**\n{'━'*20}\n🐺 {cb['inimigo']} derrotado!\n\n📜 **Batalha:**\n" + "\n".join(log) + f"\n\n💰 +{cb['i_gold']} Gold\n✨ +{cb['i_xp']} XP\n{'━'*20}"
        kb = [[InlineKeyboardButton("🔙 Voltar",callback_data="voltar")]]
        
        try: await q.message.delete()
        except: pass
        await ctx.bot.send_photo(upd.effective_chat.id, img_c(p['classe']), caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    elif p_hp <= 0:
        c.execute("UPDATE players SET hp = 1 WHERE id = %s", (uid,))
        c.execute("DELETE FROM combate WHERE pid = %s", (uid,))
        conn.commit()
        conn.close()
        
        cap = f"💀 **DERROTA!**\n{'━'*20}\n🐺 {cb['inimigo']} venceu!\n\n📜 **Batalha:**\n" + "\n".join(log) + f"\n\nVocê foi derrotado...\n{'━'*20}"
        kb = [[InlineKeyboardButton("🔙 Voltar",callback_data="voltar")]]
        
        try: await q.message.delete()
        except: pass
        await ctx.bot.send_photo(upd.effective_chat.id, img_c(p['classe']), caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    else:
        c.execute("UPDATE combate SET i_hp = %s, turno = turno + 1, defendendo = 0 WHERE pid = %s", (i_hp, uid))
        c.execute("UPDATE players SET hp = %s WHERE id = %s", (p_hp, uid))
        conn.commit()
        conn.close()
        
        await mostrar_combate(upd, ctx, uid)

async def bat_def(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE combate SET defendendo = 1, turno = turno + 1 WHERE pid = %s", (uid,))
    conn.commit()
    conn.close()
    
    await q.answer("🛡️ Defendendo!")
    await mostrar_combate(upd, ctx, uid)

async def bat_esp(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    p = get_p(uid)
    cb = get_combate(uid)
    
    if not cb:
        await q.answer("Sem combate!")
        return
    
    esp = CLASSE_STATS[p['classe']]['especial']
    
    if esp == "maldição" and p['mana'] >= 20:
        dano = int(atk(p) * 1.3)
        i_hp = cb['i_hp'] - dano
        
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("""UPDATE combate 
                    SET i_hp = %s, 
                        i_def = CASE WHEN i_def - 3 < 0 THEN 0 ELSE i_def - 3 END, 
                        turno = turno + 1, 
                        defendendo = 0 
                    WHERE pid = %s""", 
                 (i_hp, uid))
        c.execute("UPDATE players SET mana = mana - 20 WHERE id = %s", (uid,))
        conn.commit()
        conn.close()
        
        await q.answer(f"🔮 Maldição! -{dano} HP")
        
    elif esp == "explosão" and p['mana'] >= 30:
        ja_usou = (cb['turno'] > 1) and (p['mana'] < p['mana_max'] - 30)
        
        if ja_usou:
            await q.answer("⚠️ Já usou a Explosão neste combate!", show_alert=True)
            return
        
        dano_max = int(cb['i_hp_max'] * 0.25)
        dano = min(dano_max, int(atk(p) * 1.5))
        i_hp = cb['i_hp'] - dano
        
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("UPDATE combate SET i_hp = %s, turno = turno + 1, defendendo = 0 WHERE pid = %s", (i_hp, uid))
        c.execute("UPDATE players SET mana = mana - 30 WHERE id = %s", (uid,))
        conn.commit()
        conn.close()
        
        await q.answer(f"🔥 Explosão! -{dano} HP (25% máx)")
    else:
        await q.answer("Sem mana!", show_alert=True)
        return
    
    await mostrar_combate(upd, ctx, uid)

async def bat_pot_hp(upd, ctx):
    await usar_pocao(upd, ctx, "Poção de Vida")

async def bat_pot_hp2(upd, ctx):
    await usar_pocao(upd, ctx, "Poção Grande de Vida")

async def bat_pot_mp(upd, ctx):
    await usar_pocao(upd, ctx, "Poção de Mana")

async def bat_pot_mp2(upd, ctx):
    await usar_pocao(upd, ctx, "Elixir de Mana")

async def usar_pocao(upd, ctx, item):
    q = upd.callback_query
    uid = upd.effective_user.id
    p = get_p(uid)
    inv = get_inv(uid)
    
    if item not in inv or inv[item] <= 0:
        await q.answer("Sem item!", show_alert=True)
        return
    
    cons = CONSUMIVEIS[item]
    
    if cons['tipo'] == 'hp':
        novo_hp = min(p['hp'] + cons['valor'], p['hp_max'])
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("UPDATE players SET hp = %s WHERE id = %s", (novo_hp, uid))
        conn.commit()
        conn.close()
        use_inv(uid, item)
        await q.answer(f"💊 +{cons['valor']} HP!")
    else:
        if p['mana_max'] == 0:
            await q.answer("Você não usa mana!", show_alert=True)
            return
        novo_mana = min(p['mana'] + cons['valor'], p['mana_max'])
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("UPDATE players SET mana = %s WHERE id = %s", (novo_mana, uid))
        conn.commit()
        conn.close()
        use_inv(uid, item)
        await q.answer(f"🔵 +{cons['valor']} Mana!")
    
    cb = get_combate(uid)
    if cb:
        p = get_p(uid)
        dano_ini = max(1, cb['i_atk'] - deff(p) + random.randint(-2,2))
        novo_hp = p['hp'] - dano_ini
        
        conn = get_db_connection()
        c = conn.cursor()
        if novo_hp <= 0:
            c.execute("UPDATE players SET hp = 1 WHERE id = %s", (uid,))
            c.execute("DELETE FROM combate WHERE pid = %s", (uid,))
            conn.commit()
            conn.close()
            await menu(upd, ctx, uid, "💀 **Derrotado!**")
            return
        else:
            c.execute("UPDATE players SET hp = %s WHERE id = %s", (novo_hp, uid))
            c.execute("UPDATE combate SET turno = turno + 1 WHERE pid = %s", (uid,))
            conn.commit()
            conn.close()
    
    await mostrar_combate(upd, ctx, uid)

async def bat_fug(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    
    if random.random() < 0.5:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("DELETE FROM combate WHERE pid = %s", (uid,))
        conn.commit()
        conn.close()
        await q.answer("🏃 Fugiu!")
        await menu(upd, ctx, uid, "🏃 **Você fugiu!**")
    else:
        p = get_p(uid)
        cb = get_combate(uid)
        dano = max(1, cb['i_atk'] - deff(p) + random.randint(0,3))
        novo_hp = p['hp'] - dano
        
        conn = get_db_connection()
        c = conn.cursor()
        if novo_hp <= 0:
            c.execute("UPDATE players SET hp = 1 WHERE id = %s", (uid,))
            c.execute("DELETE FROM combate WHERE pid = %s", (uid,))
            conn.commit()
            conn.close()
            await q.answer(f"❌ Falhou! -{dano} HP", show_alert=True)
            await menu(upd, ctx, uid, "💀 **Derrotado ao fugir!**")
        else:
            c.execute("UPDATE players SET hp = %s WHERE id = %s", (novo_hp, uid))
            c.execute("UPDATE combate SET turno = turno + 1 WHERE pid = %s", (uid,))
            conn.commit()
            conn.close()
            await q.answer(f"❌ Falhou! -{dano} HP", show_alert=True)
            await mostrar_combate(upd, ctx, uid)

async def mapas(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    p = get_p(uid)
    await q.answer()
    cap = f"🗺️ **MAPAS**\n{'━'*20}\n"
    kb = []
    for mid, m in MAPAS.items():
        st = "✅" if p['lv'] >= m['lv'] else f"🔒 Lv.{m['lv']}"
        at = " 📍" if mid == p['mapa'] else ""
        av = f"\n└ {m['aviso']}" if m.get('aviso') and mid != p['mapa'] else ""
        cap += f"{st} {m['nome']}{at}{av}\n"
        kb.append([InlineKeyboardButton(f"🗺️ {m['nome']}",callback_data=f"via_{mid}")])
    kb.append([InlineKeyboardButton("🔙 Voltar",callback_data="voltar")])
    cap += f"{'━'*20}"
    
    img_mapa = IMAGENS["mapas"].get(p['mapa'], IMAGENS["classes"]["Guerreiro"])
    
    try:
        await q.message.delete()
    except:
        pass
    await ctx.bot.send_photo(upd.effective_chat.id, img_mapa, caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def viajar(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    p = get_p(uid)
    mid = int(q.data.split('_')[1])
    
    m = MAPAS[mid]
    if p['lv'] < m['lv'] and m.get('aviso'):
        await q.answer(f"⚠️ {m['aviso']}", show_alert=True)
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE players SET mapa = %s, local = 'cap' WHERE id = %s", (mid, uid))
    conn.commit()
    conn.close()
    
    await q.answer(f"🗺️ {m['nome']}!")
    
    try:
        await q.message.delete()
    except:
        pass
    
    await menu(upd, ctx, uid, f"🗺️ **Viajou para {m['nome']}!**")

async def locais(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    p = get_p(uid)
    await q.answer()
    m = MAPAS.get(p['mapa'], {})
    cap = f"🏘️ **LOCAIS - {m.get('nome','')}**\n{'━'*20}\n"
    kb = []
    for lid, loc in m.get('loc',{}).items():
        at = " 📍" if lid == p['local'] else ""
        lj = " 🏪" if loc.get('loja') else ""
        cap += f"🏠 {loc['nome']}{at}{lj}\n"
        kb.append([InlineKeyboardButton(f"📍 {loc['nome']}",callback_data=f"iloc_{lid}")])
    kb.append([InlineKeyboardButton("🔙 Voltar",callback_data="voltar")])
    cap += f"{'━'*20}"
    
    img_mapa = IMAGENS["mapas"].get(p['mapa'], IMAGENS["classes"]["Guerreiro"])
    
    try:
        await q.message.delete()
    except:
        pass
    await ctx.bot.send_photo(upd.effective_chat.id, img_mapa, caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def ir_loc(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    p = get_p(uid)
    lid = q.data.split('_')[1]
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE players SET local = %s WHERE id = %s", (lid, uid))
    conn.commit()
    conn.close()
    ln = MAPAS[p['mapa']]['loc'][lid]['nome']
    await q.answer(f"📍 {ln}")
    
    chave_local = f"{lid}_{p['mapa']}"
    img_local = IMAGENS["locais"].get(chave_local, IMAGENS["classes"]["Guerreiro"])
    
    p = get_p(uid)
    mi = MAPAS.get(p['mapa'], {})
    li = mi.get('loc', {}).get(p['local'], {})
    
    cap = f"📍 **{ln}**\n{'━'*20}\n🗺️ {mi.get('nome','')}\n\n"
    if li.get('loja'):
        cap += "🏪 Loja disponível\n"
    cap += f"{'━'*20}"
    
    kb = [[InlineKeyboardButton("🔙 Menu",callback_data="voltar")]]
    
    try:
        await q.message.delete()
    except:
        pass
    await ctx.bot.send_photo(upd.effective_chat.id, img_local, caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def loja(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    p = get_p(uid)
    await q.answer()
    
    loc = MAPAS[p['mapa']]['loc'][p['local']]
    
    if not loc.get('loja'):
        await q.answer("🚫 Sem loja aqui!", show_alert=True)
        return
    
    cap = f"🏪 **COMÉRCIO - {loc['nome']}**\n{'━'*20}\n\n📍 Escolha onde comprar:\n\n🏪 **Loja Normal**\n└ Preços justos\n└ Itens garantidos\n\n🏴‍☠️ **Mercado Negro**\n└ 💰 -30% preços\n└ ⚠️ 5% chance de roubo\n{'━'*20}"
    
    kb = [
        [InlineKeyboardButton("🏪 Loja Normal", callback_data="loja_normal")],
        [InlineKeyboardButton("🏴‍☠️ Mercado Negro", callback_data="loja_contra")],
        [InlineKeyboardButton("🔙 Voltar", callback_data="voltar")]
    ]
    
    chave_local = f"{p['local']}_{p['mapa']}"
    img_local = IMAGENS["locais"].get(chave_local, IMAGENS["classes"]["Guerreiro"])
    
    try:
        await q.message.delete()
    except:
        pass
    await ctx.bot.send_photo(upd.effective_chat.id, img_local, caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def loja_normal(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    p = get_p(uid)
    await q.answer()
    
    loc = MAPAS[p['mapa']]['loc'][p['local']]
    
    cap = f"🏪 **LOJA - {loc['nome']}**\n{'━'*20}\n💰 {p['gold']}\n\n"
    
    kb = []
    
    cap += "**⚔️ EQUIPAMENTOS:**\n"
    for n, eq in EQUIPS.items():
        if p['classe'] not in eq['cls']:
            continue
        pf = eq['p']
        st = "✅" if p['lv'] >= eq['lv'] else f"🔒 Lv.{eq['lv']}"
        em = "⚔️" if eq['t']=="arma" else "🛡️"
        stat = f"+{eq.get('atk',eq.get('def'))}"
        cap += f"{st} {em} {n} {stat}\n└ 💰 {pf}\n"
        if p['lv'] >= eq['lv'] and p['gold'] >= pf:
            kb.append([InlineKeyboardButton(f"💰 {n}",callback_data=f"comp_normal_{n}")])
    
    cap += "\n**💊 CONSUMÍVEIS:**\n"
    for n, c in CONSUMIVEIS.items():
        if c['tipo'] == 'mana' and p['mana_max'] == 0:
            continue
        pf = c['preco']
        cap += f"💊 {n} ({c['tipo'].upper()} +{c['valor']})\n└ 💰 {pf}\n"
        if p['gold'] >= pf:
            kb.append([InlineKeyboardButton(f"💊 {n}",callback_data=f"comp_normal_{n}")])
    
    kb.append([InlineKeyboardButton("🔙 Voltar", callback_data="loja")])
    cap += f"{'━'*20}"
    
    chave_loja = f"{p['local']}_{p['mapa']}"
    img_loja = IMAGENS["lojas"].get(chave_loja, IMAGENS["classes"]["Guerreiro"])
    
    try:
        await q.message.delete()
    except:
        pass
    await ctx.bot.send_photo(upd.effective_chat.id, img_loja, caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def loja_contra(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    p = get_p(uid)
    await q.answer()
    
    cap = f"🏴‍☠️ **MERCADO NEGRO**\n{'━'*20}\n💰 {p['gold']}\n⚠️ **-30% preço | 5% roubo**\n\n"
    
    kb = []
    
    cap += "**⚔️ EQUIPAMENTOS:**\n"
    for n, eq in EQUIPS.items():
        if p['classe'] not in eq['cls']:
            continue
        pf = int(eq['p'] * 0.7)
        st = "✅" if p['lv'] >= eq['lv'] else f"🔒 Lv.{eq['lv']}"
        em = "⚔️" if eq['t']=="arma" else "🛡️"
        stat = f"+{eq.get('atk',eq.get('def'))}"
        cap += f"{st} {em} {n} {stat}\n└ 💰 ~~{eq['p']}~~ {pf}\n"
        if p['lv'] >= eq['lv'] and p['gold'] >= pf:
            kb.append([InlineKeyboardButton(f"💰 {n}",callback_data=f"comp_contra_{n}")])
    
    cap += "\n**💊 CONSUMÍVEIS:**\n"
    for n, c in CONSUMIVEIS.items():
        if c['tipo'] == 'mana' and p['mana_max'] == 0:
            continue
        pf = int(c['preco'] * 0.7)
        cap += f"💊 {n} ({c['tipo'].upper()} +{c['valor']})\n└ 💰 ~~{c['preco']}~~ {pf}\n"
        if p['gold'] >= pf:
            kb.append([InlineKeyboardButton(f"💊 {n}",callback_data=f"comp_contra_{n}")])
    
    kb.append([InlineKeyboardButton("🔙 Voltar", callback_data="loja")])
    cap += f"{'━'*20}"
    
    img_contra = IMAGENS["contrabandistas"].get(p['mapa'], IMAGENS["classes"]["Guerreiro"])
    
    try:
        await q.message.delete()
    except:
        pass
    await ctx.bot.send_photo(upd.effective_chat.id, img_contra, caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def comprar(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    p = get_p(uid)
    
    parts = q.data.split('_')
    tipo_loja = parts[1]
    item = '_'.join(parts[2:])
    
    desconto = 0.7 if tipo_loja == "contra" else 1.0
    
    if item in EQUIPS:
        eq = EQUIPS[item]
        preco = int(eq['p'] * desconto)
        
        if p['gold'] < preco:
            await q.answer("💸 Sem gold!", show_alert=True)
            return
        
        if tipo_loja == "contra" and random.random() < 0.05:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("UPDATE players SET gold = gold - %s WHERE id = %s", (preco, uid))
            conn.commit()
            conn.close()
            await q.answer("🏴‍☠️ Roubado!", show_alert=True)
            await loja(upd, ctx)
            return
        
        conn = get_db_connection()
        c = conn.cursor()
        if eq['t'] == "arma":
            c.execute("UPDATE players SET gold = gold - %s, arma = %s, atk_b = %s WHERE id = %s", 
                     (preco, item, eq['atk'], uid))
        else:
            c.execute("UPDATE players SET gold = gold - %s, arm = %s, def_b = %s WHERE id = %s", 
                     (preco, item, eq['def'], uid))
        conn.commit()
        conn.close()
        await q.answer(f"✅ {item}!", show_alert=True)
        await menu(upd, ctx, uid, f"✅ **{item}!**")
        
    elif item in CONSUMIVEIS:
        cons = CONSUMIVEIS[item]
        preco = int(cons['preco'] * desconto)
        
        if p['gold'] < preco:
            await q.answer("💸 Sem gold!", show_alert=True)
            return
        
        img_pocao = IMAGENS["elixir"].get(item, IMAGENS["elixir"]["Poção de Vida"])
        
        cap = f"💊 **{item}**\n{'━'*20}\n🔮 {cons['tipo'].upper()} +{cons['valor']}\n💰 {preco} Gold\n"
        if tipo_loja == "contra":
            cap += f"\n⚠️ Contrabandista\n└ 5% chance de roubo\n"
        cap += f"\n**Confirmar compra?**\n{'━'*20}"
        kb = [
            [InlineKeyboardButton("✅ Comprar",callback_data=f"conf_{tipo_loja}_{item}")],
            [InlineKeyboardButton("❌ Cancelar",callback_data=f"loja_{tipo_loja}")]
        ]
        
        try:
            await q.message.delete()
        except:
            pass
        await ctx.bot.send_photo(upd.effective_chat.id, img_pocao, caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def confirmar_compra(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    p = get_p(uid)
    
    parts = q.data.split('_')
    tipo_loja = parts[1]
    item = '_'.join(parts[2:])
    
    cons = CONSUMIVEIS[item]
    desconto = 0.7 if tipo_loja == "contra" else 1.0
    preco = int(cons['preco'] * desconto)
    
    if p['gold'] < preco:
        await q.answer("💸 Sem gold!", show_alert=True)
        if tipo_loja == "normal":
            await loja_normal(upd, ctx)
        else:
            await loja_contra(upd, ctx)
        return
    
    if tipo_loja == "contra" and random.random() < 0.05:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("UPDATE players SET gold = gold - %s WHERE id = %s", (preco, uid))
        conn.commit()
        conn.close()
        await q.answer("🏴‍☠️ Roubado!", show_alert=True)
        await loja(upd, ctx)
        return
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE players SET gold = gold - %s WHERE id = %s", (preco, uid))
    conn.commit()
    conn.close()
    add_inv(uid, item, 1)
    await q.answer(f"✅ {item}!", show_alert=True)
    
    if tipo_loja == "normal":
        await loja_normal(upd, ctx)
    else:
        await loja_contra(upd, ctx)

async def inv(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    p = get_p(uid)
    await q.answer()
    
    inv_data = get_inv(uid)
    
    cap = f"🎒 **INVENTÁRIO**\n{'━'*20}\n"
    if not inv_data:
        cap += "Vazio\n"
    else:
        for item, qtd in inv_data.items():
            cap += f"💊 {item} x{qtd}\n"
    cap += f"{'━'*20}"
    
    kb = [[InlineKeyboardButton("🔙 Voltar",callback_data="voltar")]]
    
    try:
        await q.message.delete()
    except:
        pass
    await ctx.bot.send_photo(upd.effective_chat.id, img_c(p['classe']), caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def dungs(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    p = get_p(uid)
    await q.answer()
    cap = f"🏰 **DUNGEONS**\n{'━'*20}\n"
    kb = []
    for i, d in enumerate(DUNGEONS):
        st = "✅" if p['lv'] >= d['lv'] else f"🔒 Lv.{d['lv']}"
        cap += f"{st} {d['nome']}\n└ {d['boss']}\n└ XP: {d['xp']} | Gold: {d['g']}\n"
        if p['lv'] >= d['lv']:
            kb.append([InlineKeyboardButton(f"🏰 {d['nome']}",callback_data=f"dung_{i}")])
    kb.append([InlineKeyboardButton("🔙 Voltar",callback_data="voltar")])
    cap += f"{'━'*20}"
    try:
        await q.message.delete()
    except:
        pass
    await ctx.bot.send_photo(upd.effective_chat.id, IMAGENS["combate"], caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def dung(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    p = get_p(uid)
    did = int(q.data.split('_')[1])
    d = DUNGEONS[did]
    if p['energia'] < 10:
        await q.answer("🪫 10 energia!", show_alert=True)
        return
    
    await q.answer("🏰 Entrando...")
    
    p_atk = atk(p)
    p_def = deff(p)
    bhp = d['bhp']
    batk = d['batk']
    php = p['hp']
    
    log = []
    t = 1
    
    while php > 0 and bhp > 0 and t <= 15:
        dp = max(1, p_atk - 5 + random.randint(-3,3))
        bhp -= dp
        log.append(f"↗️ T{t}: -{dp}")
        if bhp <= 0: break
        db = max(1, batk - p_def + random.randint(-3,3))
        php -= db
        log.append(f"↘️ T{t}: -{db}")
        t += 1
    
    vit = php > 0
    php = max(1, php)
    
    if vit:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("UPDATE players SET gold = gold + %s, exp = exp + %s, energia = energia - 10, hp = %s WHERE id = %s", 
                 (d['g'], d['xp'], php, uid))
        c.execute("INSERT INTO dung (pid, did) VALUES (%s, %s) ON CONFLICT (pid, did) DO NOTHING", (uid, did))
        conn.commit()
        conn.close()
        res = f"🏆 **VIT!**\n💰 +{d['g']} | ✨ +{d['xp']}"
    else:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("UPDATE players SET energia = energia - 10, hp = 1 WHERE id = %s", (uid,))
        conn.commit()
        conn.close()
        res = "💀 **DERROT!**"
    
    cap = f"🏰 **{d['nome']}**\n{'━'*20}\n👹 {d['boss']}\n\n❤️ Boss: {max(0,bhp)}/{d['bhp']}\n└ {barra(max(0,bhp),d['bhp'],'🟥')}\n\n❤️ Você: {php}/{p['hp_max']}\n└ {barra(php,p['hp_max'],'🟥')}\n\n📜:\n" + "\n".join(log[-6:]) + f"\n\n{res}\n{'━'*20}"
    kb = [[InlineKeyboardButton("🔙 Voltar",callback_data="voltar")]]
    
    try: await q.message.delete()
    except: pass
    await ctx.bot.send_photo(upd.effective_chat.id, img_c(p['classe']), caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def perfil(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    p = get_p(uid)
    await q.answer()
    
    cap = f"👤 **PERFIL**\n{'━'*20}\n📛 {p['nome']}\n🎭 {p['classe']}\n⭐ Lv {p['lv']}\n\n❤️ {p['hp']}/{p['hp_max']}\n└ {barra(p['hp'],p['hp_max'],'🟥')}\n"
    
    if p['mana_max'] > 0:
        cap += f"💙 {p['mana']}/{p['mana_max']}\n└ {barra(p['mana'],p['mana_max'],'🟦')}\n"
    
    cap += f"✨ {p['exp']}/{p['lv']*100}\n└ {barra(p['exp'],p['lv']*100,'🟩')}\n\n💰 {p['gold']}\n⚡ {p['energia']}/{p['energia_max']}\n⚔️ {atk(p)}\n🛡️ {deff(p)}\n"
    
    if p['crit'] > 0:
        cap += f"💥 Crítico: {p['crit']}%\n"
    if p['double_atk']:
        cap += f"⚡ Ataque Duplo\n"
    
    cap += f"{'━'*20}"
    
    if p['arma']:
        cap += f"\n⚔️ {p['arma']}"
    if p['arm']:
        cap += f"\n🛡️ {p['arm']}"
    
    kb = [[InlineKeyboardButton("🔙 Voltar",callback_data="voltar")]]
    try: await q.message.delete()
    except: pass
    await ctx.bot.send_photo(upd.effective_chat.id, img_c(p['classe']), caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def cfg(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    p = get_p(uid)
    await q.answer()
    cap = f"⚙️ **CONFIG**\n{'━'*20}\n🔄 Reset\n⚡ Lv MAX\n💰 Gold MAX\n{'━'*20}"
    kb = [[InlineKeyboardButton("🔄 Reset",callback_data="rst_c")],[InlineKeyboardButton("⚡ Lv MAX",callback_data="ch_lv")],[InlineKeyboardButton("💰 Gold MAX",callback_data="ch_g")],[InlineKeyboardButton("🔙 Voltar",callback_data="voltar")]]
    try:
        await q.message.delete()
    except:
        pass
    await ctx.bot.send_photo(upd.effective_chat.id, img_c(p['classe']), caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def rst_c(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    p = get_p(uid)
    await q.answer()
    cap = f"⚠️ **DELETAR?**\n{'━'*20}\n❌ IRREVERSÍVEL\n{'━'*20}"
    kb = [[InlineKeyboardButton("✅ SIM",callback_data="rst_y")],[InlineKeyboardButton("❌ NÃO",callback_data="cfg")]]
    try:
        await q.message.delete()
    except:
        pass
    await ctx.bot.send_photo(upd.effective_chat.id, img_c(p['classe']), caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def rst_y(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    del_p(uid)
    await q.answer("✅ Personagem deletado!", show_alert=True)
    
    ctx.user_data.clear()
    
    # INVÉS DE MOSTRAR TELA MORTA, CHAMA O START DIRETO!
    await start(upd, ctx)
    
    # NÃO PRECISA DESSAS LINHAS:
    # cap = f"✨ **AVENTURA RABISCADA** ✨\n{'━'*20}\nVersão: `{VERSAO}`\n{'━'*20}"
    # kb = [[InlineKeyboardButton("🎮 Começar",callback_data="ir_cls")]]
    # await ctx.bot.send_photo(upd.effective_chat.id, IMAGENS["logo"], caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def ch_lv(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    p = get_p(uid)
    
    conn = get_db_connection()
    c = conn.cursor()
    hp_max = CLASSE_STATS[p['classe']]['hp'] * 10
    mana_max = CLASSE_STATS[p['classe']]['mana'] * 10 if CLASSE_STATS[p['classe']]['mana'] > 0 else 0
    c.execute("UPDATE players SET lv = 99, exp = 0, hp_max = %s, hp = %s, mana_max = %s, mana = %s, energia_max = 999, energia = 999 WHERE id = %s", 
                 (hp_max, hp_max, mana_max, mana_max, uid))
    conn.commit()
    conn.close()
    await q.answer("⚡ 99!", show_alert=True)
    await menu(upd, ctx, uid, "⚡ **Lv 99!**")

async def ch_g(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE players SET gold = 999999 WHERE id = %s", (uid,))
    conn.commit()
    conn.close()
    await q.answer("💰 999,999!", show_alert=True)
    await menu(upd, ctx, uid, "💰 **999,999!**")

async def voltar(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM combate WHERE pid = %s", (uid,))
    conn.commit()
    conn.close()
    
    await q.answer()
    await menu(upd, ctx, uid)

async def start(upd, ctx):
    uid = upd.effective_user.id
    p = get_p(uid)
    if p:
        await menu(upd, ctx, uid)
        return ConversationHandler.END
    ctx.user_data.clear()
    cap = f"✨ **AVENTURA RABISCADA** ✨\n{'━'*20}\nVersão: `{VERSAO}`\n\n🎮 **NOVIDADES:**\n⚔️ Combate Manual\n🎭 Classes Únicas\n💊 Sistema de Consumíveis\n🔮 Habilidades Especiais\n💙 Sistema de Mana\n{'━'*20}"
    kb = [[InlineKeyboardButton("🎮 Começar",callback_data="ir_cls")]]
    await upd.message.reply_photo(IMAGENS["logo"], caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    return ST_CL

async def menu_cls(upd, ctx):
    q = upd.callback_query
    await q.answer()
    cap = f"🎭 **ESCOLHA SUA CLASSE**\n{'━'*20}\n\n🛡️ **Guerreiro**\n└ HP Alto | Defesa Máxima\n└ ❤️ 250 HP | 🛡️ 18 DEF\n\n🏹 **Arqueiro**\n└ Crítico | Ataque Duplo\n└ ❤️ 120 HP | 💥 25% CRIT\n\n🔮 **Bruxa**\n└ Maldição | Dano Mágico\n└ ❤️ 150 HP | 💙 100 MANA\n\n🔥 **Mago**\n└ Explosão | Poder Máximo\n└ ❤️ 130 HP | 💙 120 MANA\n{'━'*20}"
    kb = [[InlineKeyboardButton("🛡️ Guerreiro",callback_data="Guerreiro"),InlineKeyboardButton("🏹 Arqueiro",callback_data="Arqueiro")],[InlineKeyboardButton("🔮 Bruxa",callback_data="Bruxa"),InlineKeyboardButton("🔥 Mago",callback_data="Mago")]]
    try: await q.message.delete()
    except: pass
    await ctx.bot.send_photo(upd.effective_chat.id, IMAGENS["sel"], caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    return ST_NM

async def salv_nm(upd, ctx):
    q = upd.callback_query
    ctx.user_data['classe'] = q.data
    await q.answer()
    
    stats = CLASSE_STATS[q.data]
    cap = f"✅ **{q.data.upper()}**\n{'━'*20}\n❤️ HP: {stats['hp']}\n🛡️ DEF: {stats['def']}\n⚔️ ATK: {stats['atk']}\n"
    if stats['mana'] > 0:
        cap += f"💙 MANA: {stats['mana']}\n"
    if stats['crit'] > 0:
        cap += f"💥 CRIT: {stats['crit']}%\n"
    if stats['double']:
        cap += f"⚡ Ataque Duplo\n"
    if stats['especial']:
        cap += f"🌟 {stats['especial'].title()}\n"
    cap += f"{'━'*20}\n📝 **Digite seu nome:**"
    
    try: await q.message.delete()
    except: pass
    await ctx.bot.send_photo(upd.effective_chat.id, img_c(q.data), caption=cap, parse_mode='Markdown')
    return ST_NM

async def fin(upd, ctx):
    uid = upd.effective_user.id
    nome = upd.message.text
    classe = ctx.user_data.get('classe','Guerreiro')
    
    stats = CLASSE_STATS[classe]
    
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("""INSERT INTO players 
                (id, nome, classe, hp, hp_max, mana, mana_max, lv, exp, gold, energia, energia_max, mapa, local, arma, arm, atk_b, def_b, crit, double_atk)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                nome = EXCLUDED.nome, classe = EXCLUDED.classe, hp = EXCLUDED.hp, hp_max = EXCLUDED.hp_max,
                mana = EXCLUDED.mana, mana_max = EXCLUDED.mana_max, lv = EXCLUDED.lv, exp = EXCLUDED.exp,
                gold = EXCLUDED.gold, energia = EXCLUDED.energia, energia_max = EXCLUDED.energia_max,
                mapa = EXCLUDED.mapa, local = EXCLUDED.local, arma = EXCLUDED.arma, arm = EXCLUDED.arm,
                atk_b = EXCLUDED.atk_b, def_b = EXCLUDED.def_b, crit = EXCLUDED.crit, double_atk = EXCLUDED.double_atk""",
                (uid, nome, classe, stats['hp'], stats['hp'], stats['mana'], stats['mana'],
                 1, 0, 100, 20, 20, 1, 'cap', None, None, 0, 0,
                 stats['crit'], 1 if stats['double'] else 0))
    
    conn.commit()
    conn.close()
    
    await upd.message.reply_text(f"✨ **{nome}!**\nBem-vindo, {classe}!")
    await menu(upd, ctx, uid)
    return ConversationHandler.END

def main():
    init_db()
    token = os.getenv("TELEGRAM_TOKEN")
    
    # Forçar o Telegram a esquecer conexões antigas
    import requests
    try:
        requests.get(f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true")
    except:
        pass
    
    # Criar app com request configurado
    app = ApplicationBuilder().token(token).request(request).build()
    
    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ST_CL: [CallbackQueryHandler(menu_cls, pattern='^ir_cls$')],
            ST_NM: [CallbackQueryHandler(salv_nm), MessageHandler(filters.TEXT & ~filters.COMMAND, fin)]
        },
        fallbacks=[CommandHandler('start', start)]
    )
    
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(cacar, pattern='^cacar$'))
    app.add_handler(CallbackQueryHandler(heroi_aceitar, pattern='^heroi_aceitar$'))
    app.add_handler(CallbackQueryHandler(heroi_recusar, pattern='^heroi_recusar$'))
    app.add_handler(CallbackQueryHandler(bat_atk, pattern='^bat_atk$'))
    app.add_handler(CallbackQueryHandler(bat_def, pattern='^bat_def$'))
    app.add_handler(CallbackQueryHandler(bat_esp, pattern='^bat_esp$'))
    app.add_handler(CallbackQueryHandler(bat_heroi, pattern='^bat_heroi$'))
    app.add_handler(CallbackQueryHandler(bat_pot_hp, pattern='^bat_pot_hp$'))
    app.add_handler(CallbackQueryHandler(bat_pot_hp2, pattern='^bat_pot_hp2$'))
    app.add_handler(CallbackQueryHandler(bat_pot_mp, pattern='^bat_pot_mp$'))
    app.add_handler(CallbackQueryHandler(bat_pot_mp2, pattern='^bat_pot_mp2$'))
    app.add_handler(CallbackQueryHandler(bat_fug, pattern='^bat_fug$'))
    app.add_handler(CallbackQueryHandler(mapas, pattern='^mapas$'))
    app.add_handler(CallbackQueryHandler(viajar, pattern='^via_'))
    app.add_handler(CallbackQueryHandler(locais, pattern='^locais$'))
    app.add_handler(CallbackQueryHandler(ir_loc, pattern='^iloc_'))
    app.add_handler(CallbackQueryHandler(perfil, pattern='^perfil$'))
    app.add_handler(CallbackQueryHandler(loja, pattern='^loja$'))
    app.add_handler(CallbackQueryHandler(loja_normal, pattern='^loja_normal$'))
    app.add_handler(CallbackQueryHandler(loja_contra, pattern='^loja_contra$'))
    app.add_handler(CallbackQueryHandler(confirmar_compra, pattern='^conf_'))
    app.add_handler(CallbackQueryHandler(comprar, pattern='^comp_'))
    app.add_handler(CallbackQueryHandler(inv, pattern='^inv$'))
    app.add_handler(CallbackQueryHandler(dungs, pattern='^dungs$'))
    app.add_handler(CallbackQueryHandler(dung, pattern='^dung_'))
    app.add_handler(CallbackQueryHandler(cfg, pattern='^cfg$'))
    app.add_handler(CallbackQueryHandler(rst_c, pattern='^rst_c$'))
    app.add_handler(CallbackQueryHandler(rst_y, pattern='^rst_y$'))
    app.add_handler(CallbackQueryHandler(ch_lv, pattern='^ch_lv$'))
    app.add_handler(CallbackQueryHandler(ch_g, pattern='^ch_g$'))
    app.add_handler(CallbackQueryHandler(menu_cls, pattern='^ir_cls$'))
    app.add_handler(CallbackQueryHandler(voltar, pattern='^voltar$'))
    
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
