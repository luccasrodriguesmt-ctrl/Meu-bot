import os, random, logging, threading, psycopg2, asyncio, json
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse
from telegram.request import HTTPXRequest
from cachetools import TTLCache
import datetime
import requests

VERSAO = "8.1"  # Atualizada

# Request com timeout otimizado
request = HTTPXRequest(
    connection_pool_size=50,
    connect_timeout=3,
    read_timeout=3,
    pool_timeout=1
)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def run_fake_server():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/health':
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'OK')
                return
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Bot Online</h1></body></html>")
        def log_message(self, format, *args):
            pass
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), Handler)
    logging.info(f"HTTP Server on port {port}")
    server.serve_forever()

# Configuração PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# ===== POOL DE CONEXÕES POR THREAD =====
connection_pool = {}

def get_db_connection():
    thread_id = threading.get_ident()
    if thread_id in connection_pool:
        try:
            connection_pool[thread_id].cursor().execute("SELECT 1")
            return connection_pool[thread_id]
        except:
            try:
                connection_pool[thread_id].close()
            except:
                pass
    if DATABASE_URL:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    else:
        conn = psycopg2.connect(
            host=os.getenv("PGHOST"),
            database=os.getenv("PGDATABASE"),
            user=os.getenv("PGUSER"),
            password=os.getenv("PGPASSWORD"),
            port=os.getenv("PGPORT", 5432),
            sslmode='require'
        )
    conn.autocommit = False
    connection_pool[thread_id] = conn
    return conn

# ===== CACHE LEVE =====
player_cache = TTLCache(maxsize=200, ttl=10)
itens_cache = TTLCache(maxsize=500, ttl=30)

def invalidate_cache(uid):
    player_cache.pop(uid, None)

def barra_rapida(a, m, c="🟦"):
    if m <= 0: return "⬜"*10
    p = max(0, min(a/m, 1))
    return c*int(p*10) + "⬜"*(10-int(p*10))

# ===== DADOS =====
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
    },
    "pensoes": {
        1: "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/cidade%20subterania.jpeg?raw=true",
        2: "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/cidade%20subterania.jpeg?raw=true",
        3: "https://github.com/luccasrodriguesmt-ctrl/Meu-bot/blob/main/images/cidade%20subterania.jpeg?raw=true"
    }
}

CLASSE_STATS = {
    "Guerreiro": {
        "hp": 200,
        "mana": 0,
        "atk": 8,
        "def": 25,
        "crit": 5,
        "double": False,
        "especial": None
    },
    "Arqueiro": {
        "hp": 140,
        "mana": 0,
        "atk": 12,
        "def": 12,
        "crit": 25,
        "double": True,
        "especial": None
    },
    "Bruxa": {
        "hp": 160,
        "mana": 120,
        "atk": 10,
        "def": 15,
        "crit": 10,
        "double": False,
        "especial": "maldição"
    },
    "Mago": {
        "hp": 120,
        "mana": 150,
        "atk": 14,
        "def": 8,
        "crit": 15,
        "double": False,
        "especial": "explosão"
    }
}

MAPAS = {
    1: {"nome": "Planície", "lv": 1, "aviso": "", "loc": {
        "cap": {"nome": "Zênite", "loja": True, "pensao": True},
        "v1": {"nome": "Bragaluna", "loja": True, "acampamento": True},
        "v2": {"nome": "Eterfenda", "loja": False, "acampamento": False}
    }},
    2: {"nome": "Floresta Sombria", "lv": 5, "aviso": "⚠️ Região Perigosa - Lv 5+", "loc": {
        "cap": {"nome": "Forte Floresta", "loja": True, "pensao": True},
        "v1": {"nome": "Acampamento", "loja": True, "acampamento": True},
        "v2": {"nome": "Refúgio", "loja": False, "acampamento": True}
    }},
    3: {"nome": "Caverna Profunda", "lv": 10, "aviso": "🔥 Região Mortal - Lv 10+", "loc": {
        "cap": {"nome": "Cidade Subterrânea", "loja": True, "pensao": True},
        "v1": {"nome": "Mina Abandonada", "loja": False, "acampamento": False},
        "v2": {"nome": "Forte Anão", "loja": True, "acampamento": False}
    }}
}

HEROIS = {
    1: [
        {"nome": "Inghost, o Lorde de Bragaluna", "img": "heroi1", "desc": "Um cavaleiro lendário com armadura reluzente.", "fala": "Vejo que enfrenta perigos. Permita-me honrar minha espada ao seu lado!"},
        {"nome": "GabrielMinaRrj, Almirante-Mor de Eterfenda", "img": "heroi2", "desc": "Almirante-Mor de Eterfenda, arqueiro de precisão mortal.", "fala": "Esses inimigos são perigosos para enfrentar sozinho. Aceita minha ajuda?"}
    ],
    2: [
        {"nome": "GuntherZuri, a Druida do Refúgio", "img": "heroi3", "desc": "Uma druida muito poderosa que cuida de um refúgio.", "fala": "As árvores sussurram sobre seus desafios. Deixe a natureza lutar ao seu lado!"},
        {"nome": "Edu345jamampiro, o Velho Edu", "img": "heroi4", "desc": "Lord no Forte Floresta, anda acompanhado de um lobo gigante.", "fala": "Meu lobo e eu conhecemos bem esses perigos. Juntos somos mais fortes!"}
    ],
    3: [
        {"nome": "MrKiigsmann, Rei dos Anões", "img": "heroi5", "desc": "Um anão muito poderoso e rei em Forte Anão.", "fala": "Estas profundezas são traiçoeiras, jovem. Deixe este velho lhe guiar!"},
        {"nome": "X__MATHEUSS_X, a Sombra Noturna", "img": "heroi6", "desc": "O mais temperamental de todos, sempre de mal humor.", "fala": "Tch... seus inimigos não verão a morte chegar. Quer minha lâmina ou não?"}
    ]
}

# ===== NOVA ESTRUTURA DE ITENS COM ATRIBUTOS ALEATÓRIOS =====
ITENS_BASE = {
    # Armas Guerreiro
    "Espada Enferrujada": {"tipo": "arma", "cls": ["Guerreiro"], "atk_min": 1, "atk_max": 5, "def_min": 0, "def_max": 0, "preco": 50, "lv": 1},
    "Espada de Ferro": {"tipo": "arma", "cls": ["Guerreiro"], "atk_min": 6, "atk_max": 12, "def_min": 0, "def_max": 0, "preco": 200, "lv": 5},
    "Espada de Aço": {"tipo": "arma", "cls": ["Guerreiro"], "atk_min": 15, "atk_max": 25, "def_min": 0, "def_max": 0, "preco": 500, "lv": 10},
    
    # Armaduras Guerreiro
    "Escudo de Madeira": {"tipo": "armadura", "cls": ["Guerreiro"], "atk_min": 0, "atk_max": 0, "def_min": 2, "def_max": 6, "preco": 50, "lv": 1},
    "Escudo de Ferro": {"tipo": "armadura", "cls": ["Guerreiro"], "atk_min": 0, "atk_max": 0, "def_min": 8, "def_max": 15, "preco": 200, "lv": 5},
    "Escudo de Aço": {"tipo": "armadura", "cls": ["Guerreiro"], "atk_min": 0, "atk_max": 0, "def_min": 18, "def_max": 25, "preco": 500, "lv": 10},
    
    # Armas Arqueiro
    "Arco Simples": {"tipo": "arma", "cls": ["Arqueiro"], "atk_min": 2, "atk_max": 6, "def_min": 0, "def_max": 0, "preco": 50, "lv": 1},
    "Arco Composto": {"tipo": "arma", "cls": ["Arqueiro"], "atk_min": 7, "atk_max": 14, "def_min": 0, "def_max": 0, "preco": 200, "lv": 5},
    "Arco Élfico": {"tipo": "arma", "cls": ["Arqueiro"], "atk_min": 18, "atk_max": 28, "def_min": 0, "def_max": 0, "preco": 500, "lv": 10},
    
    # Armaduras Arqueiro
    "Armadura Leve": {"tipo": "armadura", "cls": ["Arqueiro"], "atk_min": 0, "atk_max": 0, "def_min": 1, "def_max": 4, "preco": 50, "lv": 1},
    "Couro Reforçado": {"tipo": "armadura", "cls": ["Arqueiro"], "atk_min": 0, "atk_max": 0, "def_min": 6, "def_max": 12, "preco": 200, "lv": 5},
    "Manto Sombrio": {"tipo": "armadura", "cls": ["Arqueiro"], "atk_min": 0, "atk_max": 0, "def_min": 14, "def_max": 22, "preco": 500, "lv": 10},
    
    # Armas Bruxa
    "Cajado Antigo": {"tipo": "arma", "cls": ["Bruxa"], "atk_min": 1, "atk_max": 5, "def_min": 0, "def_max": 0, "preco": 50, "lv": 1},
    "Cetro Lunar": {"tipo": "arma", "cls": ["Bruxa"], "atk_min": 6, "atk_max": 13, "def_min": 0, "def_max": 0, "preco": 200, "lv": 5},
    "Varinha das Trevas": {"tipo": "arma", "cls": ["Bruxa"], "atk_min": 15, "atk_max": 25, "def_min": 0, "def_max": 0, "preco": 500, "lv": 10},
    
    # Armaduras Bruxa
    "Robe Místico": {"tipo": "armadura", "cls": ["Bruxa"], "atk_min": 0, "atk_max": 0, "def_min": 2, "def_max": 6, "preco": 50, "lv": 1},
    "Manto Encantado": {"tipo": "armadura", "cls": ["Bruxa"], "atk_min": 0, "atk_max": 0, "def_min": 8, "def_max": 14, "preco": 200, "lv": 5},
    "Vestes Arcanas": {"tipo": "armadura", "cls": ["Bruxa"], "atk_min": 0, "atk_max": 0, "def_min": 16, "def_max": 24, "preco": 500, "lv": 10},
    
    # Armas Mago
    "Bastão Iniciante": {"tipo": "arma", "cls": ["Mago"], "atk_min": 2, "atk_max": 6, "def_min": 0, "def_max": 0, "preco": 50, "lv": 1},
    "Orbe de Fogo": {"tipo": "arma", "cls": ["Mago"], "atk_min": 8, "atk_max": 15, "def_min": 0, "def_max": 0, "preco": 200, "lv": 5},
    "Cetro do Caos": {"tipo": "arma", "cls": ["Mago"], "atk_min": 20, "atk_max": 30, "def_min": 0, "def_max": 0, "preco": 500, "lv": 10},
    
    # Armaduras Mago
    "Túnica Simples": {"tipo": "armadura", "cls": ["Mago"], "atk_min": 0, "atk_max": 0, "def_min": 1, "def_max": 4, "preco": 50, "lv": 1},
    "Armadura Mágica": {"tipo": "armadura", "cls": ["Mago"], "atk_min": 0, "atk_max": 0, "def_min": 6, "def_max": 11, "preco": 200, "lv": 5},
    "Robe do Arquimago": {"tipo": "armadura", "cls": ["Mago"], "atk_min": 0, "atk_max": 0, "def_min": 14, "def_max": 22, "preco": 500, "lv": 10}
}

CONSUMIVEIS = {
    "Poção de Vida": {"tipo": "hp", "valor": 50, "preco": 20},
    "Poção Grande de Vida": {"tipo": "hp", "valor": 100, "preco": 50},
    "Poção de Mana": {"tipo": "mana", "valor": 30, "preco": 25},
    "Elixir de Mana": {"tipo": "mana", "valor": 60, "preco": 60}
}

DUNGEONS = [
    {"nome": "Covil Goblin", "lv": 5, "boss": "Rei Goblin", "bhp": 350, "batk": 28, "xp": 250, "g": 200},
    {"nome": "Ninho Lobos", "lv": 10, "boss": "Lobo Alpha", "bhp": 650, "batk": 45, "xp": 500, "g": 400}
]

# Drops por mapa
DROPS_POR_MAPA = {
    1: [  # Planície - Itens comuns
        {"item": "Espada Enferrujada", "chance": 0.02},
        {"item": "Escudo de Madeira", "chance": 0.02},
        {"item": "Arco Simples", "chance": 0.02},
        {"item": "Armadura Leve", "chance": 0.02},
        {"item": "Cajado Antigo", "chance": 0.02},
        {"item": "Robe Místico", "chance": 0.02},
        {"item": "Bastão Iniciante", "chance": 0.02},
        {"item": "Túnica Simples", "chance": 0.02},
        {"item": "Poção de Vida", "chance": 0.15},
        {"item": "Poção de Mana", "chance": 0.10}
    ],
    2: [  # Floresta - Itens médios
        {"item": "Espada de Ferro", "chance": 0.03},
        {"item": "Escudo de Ferro", "chance": 0.03},
        {"item": "Arco Composto", "chance": 0.03},
        {"item": "Couro Reforçado", "chance": 0.03},
        {"item": "Cetro Lunar", "chance": 0.03},
        {"item": "Manto Encantado", "chance": 0.03},
        {"item": "Orbe de Fogo", "chance": 0.03},
        {"item": "Armadura Mágica", "chance": 0.03},
        {"item": "Poção Grande de Vida", "chance": 0.10},
        {"item": "Elixir de Mana", "chance": 0.08}
    ],
    3: [  # Caverna - Itens avançados
        {"item": "Espada de Aço", "chance": 0.04},
        {"item": "Escudo de Aço", "chance": 0.04},
        {"item": "Arco Élfico", "chance": 0.04},
        {"item": "Manto Sombrio", "chance": 0.04},
        {"item": "Varinha das Trevas", "chance": 0.04},
        {"item": "Vestes Arcanas", "chance": 0.04},
        {"item": "Cetro do Caos", "chance": 0.04},
        {"item": "Robe do Arquimago", "chance": 0.04},
        {"item": "Poção Grande de Vida", "chance": 0.15},
        {"item": "Elixir de Mana", "chance": 0.12}
    ]
}

ST_CL, ST_NM = range(2)

# ===== BANCO DE DADOS ATUALIZADO =====
def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Tabela de players (removido arma/arm fixas)
    c.execute('''CREATE TABLE IF NOT EXISTS players (
                 id BIGINT PRIMARY KEY, nome TEXT, classe TEXT,
                 hp INTEGER, hp_max INTEGER,
                 mana INTEGER DEFAULT 0, mana_max INTEGER DEFAULT 0,
                 lv INTEGER, exp INTEGER, gold INTEGER,
                 energia INTEGER, energia_max INTEGER,
                 mapa INTEGER DEFAULT 1, local TEXT DEFAULT 'cap',
                 arma_equipada INTEGER DEFAULT NULL,
                 armadura_equipada INTEGER DEFAULT NULL,
                 crit INTEGER DEFAULT 0, double_atk INTEGER DEFAULT 0)''')
    
    # NOVA: Tabela de itens dos jogadores
    c.execute('''CREATE TABLE IF NOT EXISTS itens (
                 id SERIAL PRIMARY KEY,
                 pid BIGINT REFERENCES players(id) ON DELETE CASCADE,
                 nome TEXT NOT NULL,
                 tipo TEXT NOT NULL,
                 atk INTEGER DEFAULT 0,
                 def INTEGER DEFAULT 0,
                 quantidade INTEGER DEFAULT 1,
                 data_aquisicao TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Índices para consultas rápidas
    c.execute('CREATE INDEX IF NOT EXISTS idx_itens_pid ON itens(pid)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_itens_nome ON itens(nome)')
    
    c.execute('''CREATE TABLE IF NOT EXISTS inv (
                 pid BIGINT, item TEXT, qtd INTEGER DEFAULT 1,
                 PRIMARY KEY (pid, item))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS dung (
                 pid BIGINT, did INTEGER, PRIMARY KEY (pid, did))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS combate (
                 pid BIGINT PRIMARY KEY, inimigo TEXT,
                 i_hp INTEGER, i_hp_max INTEGER,
                 i_atk INTEGER, i_def INTEGER, i_xp INTEGER, i_gold INTEGER,
                 turno INTEGER DEFAULT 1, defendendo INTEGER DEFAULT 0,
                 heroi TEXT DEFAULT NULL, tipo_monstro TEXT, mapa_monstro INTEGER)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS heroi_oferta (
                 pid BIGINT PRIMARY KEY, heroi_nome TEXT, heroi_img TEXT,
                 inimigo TEXT, i_hp INTEGER, i_atk INTEGER, i_def INTEGER,
                 i_xp INTEGER, i_gold INTEGER, tipo_monstro TEXT, mapa_monstro INTEGER)''')
    
    conn.commit()

# ===== FUNÇÕES PARA ITENS =====
def criar_item_aleatorio(nome_base, pid):
    """Cria um item com atributos aleatórios baseado no nome base"""
    if nome_base not in ITENS_BASE:
        return None
    
    base = ITENS_BASE[nome_base]
    atk = random.randint(base['atk_min'], base['atk_max'])
    defesa = random.randint(base['def_min'], base['def_max'])
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO itens (pid, nome, tipo, atk, def, quantidade)
        VALUES (%s, %s, %s, %s, %s, 1)
        RETURNING id
    """, (pid, nome_base, base['tipo'], atk, defesa))
    item_id = c.fetchone()[0]
    conn.commit()
    invalidate_cache(pid)
    return item_id

def get_itens_jogador(pid):
    """Retorna todos os itens do jogador agrupados por nome com contagem de slots"""
    conn = get_db_connection()
    c = conn.cursor(cursor_factory=RealDictCursor)
    c.execute("""
        SELECT * FROM itens 
        WHERE pid = %s 
        ORDER BY 
            CASE 
                WHEN tipo = 'arma' THEN 1
                WHEN tipo = 'armadura' THEN 2
                ELSE 3
            END,
            nome
    """, (pid,))
    itens = c.fetchall()
    
    # Calcular slots (15 itens por slot)
    slots_por_item = {}
    for item in itens:
        nome = item['nome']
        if nome not in slots_por_item:
            slots_por_item[nome] = {
                'itens': [],
                'total': 0,
                'slots': 0
            }
        slots_por_item[nome]['itens'].append(item)
        slots_por_item[nome]['total'] += 1
    
    for nome, data in slots_por_item.items():
        data['slots'] = (data['total'] + 14) // 15  # Arredonda para cima
    
    return itens, slots_por_item

def get_item_por_id(item_id):
    """Retorna um item específico pelo ID"""
    conn = get_db_connection()
    c = conn.cursor(cursor_factory=RealDictCursor)
    c.execute("SELECT * FROM itens WHERE id = %s", (item_id,))
    return c.fetchone()

def get_item_equipado(pid, tipo):
    """Retorna o ID do item equipado de um tipo específico"""
    conn = get_db_connection()
    c = conn.cursor()
    if tipo == 'arma':
        c.execute("SELECT arma_equipada FROM players WHERE id = %s", (pid,))
    else:
        c.execute("SELECT armadura_equipada FROM players WHERE id = %s", (pid,))
    return c.fetchone()[0]

def equipar_item(pid, item_id):
    """Equipa um item do inventário"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Pega o item
    item = get_item_por_id(item_id)
    if not item or item['pid'] != pid:
        return False, "Item não encontrado!"
    
    # Verifica se a classe pode usar
    base = ITENS_BASE.get(item['nome'])
    if not base:
        return False, "Item inválido!"
    
    c.execute("SELECT classe FROM players WHERE id = %s", (pid,))
    classe = c.fetchone()[0]
    if classe not in base['cls']:
        return False, "Sua classe não pode usar este item!"
    
    # Equipa
    if item['tipo'] == 'arma':
        c.execute("UPDATE players SET arma_equipada = %s WHERE id = %s", (item_id, pid))
    else:
        c.execute("UPDATE players SET armadura_equipada = %s WHERE id = %s", (item_id, pid))
    
    conn.commit()
    invalidate_cache(pid)
    return True, f"✅ {item['nome']} equipado!"

def vender_item(pid, item_id, preco_venda):
    """Vende um item (usado apenas na loja)"""
    conn = get_db_connection()
    c = conn.cursor()
    
    item = get_item_por_id(item_id)
    if not item or item['pid'] != pid:
        return False, "Item não encontrado!"
    
    # Remove o item
    c.execute("DELETE FROM itens WHERE id = %s", (item_id,))
    
    # Se era item equipado, remove do equipamento
    c.execute("SELECT arma_equipada, armadura_equipada FROM players WHERE id = %s", (pid,))
    arma_eq, armadura_eq = c.fetchone()
    
    if arma_eq == item_id:
        c.execute("UPDATE players SET arma_equipada = NULL WHERE id = %s", (pid,))
    elif armadura_eq == item_id:
        c.execute("UPDATE players SET armadura_equipada = NULL WHERE id = %s", (pid,))
    
    # Adiciona gold
    c.execute("UPDATE players SET gold = gold + %s WHERE id = %s", (preco_venda, pid))
    
    conn.commit()
    invalidate_cache(pid)
    return True, f"💰 Vendido por {preco_venda} gold!"

def descartar_item(pid, item_id):
    """Descarta um item do inventário"""
    conn = get_db_connection()
    c = conn.cursor()
    
    item = get_item_por_id(item_id)
    if not item or item['pid'] != pid:
        return False, "Item não encontrado!"
    
    # Remove o item
    c.execute("DELETE FROM itens WHERE id = %s", (item_id,))
    
    # Se era item equipado, remove do equipamento
    c.execute("SELECT arma_equipada, armadura_equipada FROM players WHERE id = %s", (pid,))
    arma_eq, armadura_eq = c.fetchone()
    
    if arma_eq == item_id:
        c.execute("UPDATE players SET arma_equipada = NULL WHERE id = %s", (pid,))
    elif armadura_eq == item_id:
        c.execute("UPDATE players SET armadura_equipada = NULL WHERE id = %s", (pid,))
    
    conn.commit()
    invalidate_cache(pid)
    return True, f"🗑️ {item['nome']} descartado!"

def usar_consumivel(pid, item_nome):
    """Usa um item consumível"""
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("SELECT id FROM itens WHERE pid = %s AND nome = %s LIMIT 1", (pid, item_nome))
    result = c.fetchone()
    if not result:
        return False, "Item não encontrado!"
    
    item_id = result[0]
    c.execute("DELETE FROM itens WHERE id = %s", (item_id,))
    conn.commit()
    invalidate_cache(pid)
    return True, f"💊 {item_nome} usado!"

# ===== FUNÇÕES DE CÁLCULO =====
def calc_atk(dados):
    """Calcula ataque final (base + nível + equip)"""
    base = CLASSE_STATS[dados['classe']]['atk']
    atk_equip = 0
    
    if dados.get('arma_equipada'):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT atk FROM itens WHERE id = %s", (dados['arma_equipada'],))
        result = c.fetchone()
        if result:
            atk_equip = result[0]
    
    return base + (dados['lv'] * 3) + atk_equip

def calc_def(dados):
    """Calcula defesa final (base + nível + equip)"""
    base = CLASSE_STATS[dados['classe']]['def']
    def_equip = 0
    
    if dados.get('armadura_equipada'):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT def FROM itens WHERE id = %s", (dados['armadura_equipada'],))
        result = c.fetchone()
        if result:
            def_equip = result[0]
    
    return base + def_equip

def get_tudo(uid):
    if uid in player_cache:
        return player_cache[uid]

    conn = get_db_connection()
    c = conn.cursor(cursor_factory=RealDictCursor)
    c.execute("""
        SELECT 
            p.*,
            cb.inimigo, cb.i_hp, cb.i_hp_max, cb.i_atk, cb.i_def,
            cb.i_xp, cb.i_gold, cb.turno, cb.defendendo, cb.heroi,
            cb.tipo_monstro, cb.mapa_monstro
        FROM players p
        LEFT JOIN combate cb ON cb.pid = p.id
        WHERE p.id = %s
    """, (uid,))
    row = c.fetchone()
    if row:
        player_cache[uid] = dict(row)
    return dict(row) if row else None

def del_p(uid):
    invalidate_cache(uid)
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM heroi_oferta WHERE pid = %s", (uid,))
    c.execute("DELETE FROM combate WHERE pid = %s", (uid,))
    c.execute("DELETE FROM dung WHERE pid = %s", (uid,))
    c.execute("DELETE FROM itens WHERE pid = %s", (uid,))
    c.execute("DELETE FROM inv WHERE pid = %s", (uid,))
    c.execute("DELETE FROM players WHERE id = %s", (uid,))
    conn.commit()

def img_c(cl):
    return IMAGENS["classes"].get(cl, IMG)

# ===== MENU PRINCIPAL =====
async def menu(upd, ctx, uid, txt=""):
    dados = get_tudo(uid)
    if not dados:
        await start(upd, ctx)
        return

    mi = MAPAS.get(dados['mapa'], {})
    li = mi.get('loc', {}).get(dados['local'], {})

    cap = (f"🎮 **{VERSAO}**\n{'━'*20}\n"
           f"👤 **{dados['nome']}** — *{dados['classe']} Lv. {dados['lv']}*\n"
           f"🗺️ {mi.get('nome','?')} | 📍 {li.get('nome','?')}\n\n"
           f"❤️ HP: {dados['hp']}/{dados['hp_max']}\n"
           f"└ {barra_rapida(dados['hp'], dados['hp_max'], '🟥')}\n")

    if dados['mana_max'] > 0:
        cap += f"💙 MANA: {dados['mana']}/{dados['mana_max']}\n└ {barra_rapida(dados['mana'], dados['mana_max'], '🟦')}\n"

    cap += (f"✨ XP: {dados['exp']}/{dados['lv']*100}\n"
            f"└ {barra_rapida(dados['exp'], dados['lv']*100, '🟩')}\n\n"
            f"⚔️ ATK: {calc_atk(dados)} | 🛡️ DEF: {calc_def(dados)}\n")

    if dados['crit'] > 0:
        cap += f"💥 CRIT: {dados['crit']}%\n"
    if dados['double_atk']:
        cap += f"⚡ Ataque Duplo\n"

    cap += f"💰 {dados['gold']} | ⚡ {dados['energia']}/{dados['energia_max']}\n{'━'*20}\n{txt}"

    kb = [
        [InlineKeyboardButton("⚔️ Caçar", callback_data="cacar"), InlineKeyboardButton("🗺️ Mapas", callback_data="mapas")],
        [InlineKeyboardButton("🏘️ Locais", callback_data="locais"), InlineKeyboardButton("👤 Status", callback_data="perfil")],
        [InlineKeyboardButton("🏪 Loja", callback_data="loja"), InlineKeyboardButton("🎒 Inventário", callback_data="inv")],
        [InlineKeyboardButton("🏰 Dungeons", callback_data="dungs"), InlineKeyboardButton("⚙️ Config", callback_data="cfg")]
    ]

    img_mapa = IMAGENS["mapas"].get(dados['mapa'], IMAGENS["classes"]["Guerreiro"])

    try:
        if upd.callback_query:
            await upd.callback_query.edit_message_media(
                media=InputMediaPhoto(media=img_mapa, caption=cap, parse_mode='Markdown'),
                reply_markup=InlineKeyboardMarkup(kb)
            )
        else:
            await upd.message.reply_photo(img_mapa, caption=cap, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    except:
        try:
            await ctx.bot.send_photo(upd.effective_chat.id, img_mapa, caption=cap,
                                     reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
        except:
            pass

# ===== DESCANSO =====
async def descansar(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    dados = get_tudo(uid)
    
    tipo = q.data.split('_')[1]
    
    if tipo == "acampamento":
        custo = 20
        recupera = 10
        if dados['gold'] < custo:
            await q.answer("💰 Sem gold!", show_alert=True)
            return
        
        nova_energia = min(dados['energia'] + recupera, dados['energia_max'])
        
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("UPDATE players SET gold = gold - %s, energia = %s WHERE id = %s",
                  (custo, nova_energia, uid))
        conn.commit()
        invalidate_cache(uid)
        
        await q.answer(f"🏕️ Descansou! +{recupera} energia")
        await menu(upd, ctx, uid, f"🏕️ **Descansou no acampamento!**\n⚡ +{recupera} energia")
        
    elif tipo == "pensao":
        custo = 90  # Valor médio entre 80-100
        if dados['gold'] < custo:
            await q.answer("💰 Sem gold!", show_alert=True)
            return
        
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("UPDATE players SET gold = gold - %s, energia = energia_max WHERE id = %s",
                  (custo, uid))
        conn.commit()
        invalidate_cache(uid)
        
        img_pensao = IMAGENS["pensoes"].get(dados['mapa'], IMAGENS["pensoes"][1])
        cap = (f"🏨 **PENSÃO**\n{'━'*20}\n"
               f"💤 Você dormiu profundamente...\n\n"
               f"⚡ Energia recuperada!\n💰 -{custo} gold\n{'━'*20}")
        kb = [[InlineKeyboardButton("🔙 Voltar", callback_data="voltar")]]
        
        try:
            await q.message.delete()
        except:
            pass
        await ctx.bot.send_photo(upd.effective_chat.id, img_pensao, caption=cap,
                                 reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

# ===== CAÇAR =====
async def cacar(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    await q.answer("🔍 Procurando...")

    dados = get_tudo(uid)
    if not dados:
        return

    if dados['energia'] < 2:
        await q.answer("🪫 Sem energia!", show_alert=True)
        return

    if dados.get('inimigo'):
        await exibir_combate(upd, ctx, dados)
        return

    inims = [n for n, d in INIMIGOS.items() if dados['mapa'] in d['m']]
    if not inims:
        await menu(upd, ctx, uid, "❌ Sem inimigos!")
        return

    inm = random.choice(inims)
    ini = INIMIGOS[inm]

    conn = get_db_connection()
    c = conn.cursor()

    # Chance de herói aumentada para 10%
    if random.random() < 0.10:
        herois_mapa = HEROIS.get(dados['mapa'], [])
        if herois_mapa:
            heroi = random.choice(herois_mapa)
            c.execute("DELETE FROM heroi_oferta WHERE pid = %s", (uid,))
            c.execute("""INSERT INTO heroi_oferta
                        (pid, heroi_nome, heroi_img, inimigo, i_hp, i_atk, i_def, i_xp, i_gold, tipo_monstro, mapa_monstro)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                      (uid, heroi['nome'], heroi['img'], inm, ini['hp'], ini['atk'], ini['def'],
                       ini['xp'], ini['gold'], ini['tipo'], dados['mapa']))
            c.execute("UPDATE players SET energia = energia - 2 WHERE id = %s", (uid,))
            conn.commit()
            invalidate_cache(uid)

            heroi_img = IMAGENS["herois"].get(heroi['img'], IMAGENS["classes"]["Guerreiro"])
            cap = (f"⭐ **ENCONTRO INESPERADO!** ⭐\n{'━'*20}\n\n"
                   f"🦸 **{heroi['nome']}**\n\n_{heroi['desc']}_\n\n"
                   f"💬 \"{heroi['fala']}\"\n\n{'━'*20}\n"
                   f"⚔️ Inimigo à frente: **{inm}**\n"
                   f"❤️ HP: {ini['hp']} | ⚔️ ATK: {ini['atk']} | 🛡️ DEF: {ini['def']}\n{'━'*20}\n\n"
                   f"**Aceitar ajuda do herói?**")
            kb = [
                [InlineKeyboardButton("✅ ACEITAR AJUDA", callback_data="heroi_aceitar")],
                [InlineKeyboardButton("❌ RECUSAR (Lutar sozinho)", callback_data="heroi_recusar")]
            ]
            try:
                await q.message.delete()
            except:
                pass
            await ctx.bot.send_photo(upd.effective_chat.id, heroi_img, caption=cap,
                                     reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
            return

    # Combate normal
    c.execute("""INSERT INTO combate
                (pid, inimigo, i_hp, i_hp_max, i_atk, i_def, i_xp, i_gold, turno, defendendo, heroi, tipo_monstro, mapa_monstro)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1, 0, NULL, %s, %s)""",
              (uid, inm, ini['hp'], ini['hp'], ini['atk'], ini['def'], ini['xp'], ini['gold'],
               ini['tipo'], dados['mapa']))
    c.execute("UPDATE players SET energia = energia - 2 WHERE id = %s", (uid,))
    conn.commit()
    invalidate_cache(uid)

    dados.update({
        'inimigo': inm, 'i_hp': ini['hp'], 'i_hp_max': ini['hp'],
        'i_atk': ini['atk'], 'i_def': ini['def'], 'i_xp': ini['xp'],
        'i_gold': ini['gold'], 'turno': 1, 'defendendo': 0, 'heroi': None,
        'tipo_monstro': ini['tipo'], 'mapa_monstro': dados['mapa'],
        'energia': dados['energia'] - 2
    })
    await exibir_combate(upd, ctx, dados)

# ===== MONTA TELA DE COMBATE =====
def montar_cap_combate(dados):
    p_atk = calc_atk(dados)
    p_def = calc_def(dados)

    cap = (f"⚔️ **COMBATE - Turno {dados['turno']}**\n{'━'*20}\n"
           f"🐺 **{dados['inimigo']}**\n\n"
           f"❤️ Inimigo: {dados['i_hp']}/{dados['i_hp_max']}\n"
           f"└ {barra_rapida(dados['i_hp'], dados['i_hp_max'], '🟥')}\n\n"
           f"❤️ Você: {dados['hp']}/{dados['hp_max']}\n"
           f"└ {barra_rapida(dados['hp'], dados['hp_max'], '🟥')}\n")

    if dados['mana_max'] > 0:
        cap += f"💙 Mana: {dados['mana']}/{dados['mana_max']}\n└ {barra_rapida(dados['mana'], dados['mana_max'], '🟦')}\n"

    if dados.get('heroi'):
        cap += f"\n⭐ **{dados['heroi']} ao seu lado!**\n"

    if dados.get('defendendo'):
        cap += "\n🛡️ **DEFENDENDO**\n"

    cap += f"\n⚔️ ATK: {p_atk} | 🛡️ DEF: {p_def}"
    if dados['crit'] > 0:
        cap += f" | 💥 {dados['crit']}%"
    cap += f"\n{'━'*20}"

    # Botões
    kb = [[
        InlineKeyboardButton("⚔️ Atacar", callback_data="bat_atk"),
        InlineKeyboardButton("🛡️ Defender", callback_data="bat_def")
    ]]

    if dados['classe'] == "Bruxa" and dados['mana'] >= 20:
        kb.append([InlineKeyboardButton("🔮 Maldição (20 mana)", callback_data="bat_esp")])
    elif dados['classe'] == "Mago" and dados['mana'] >= 30:
        kb.append([InlineKeyboardButton("🔥 Explosão (30 mana)", callback_data="bat_esp")])

    if dados.get('heroi'):
        kb.append([InlineKeyboardButton("⭐ INVOCAR HERÓI", callback_data="bat_heroi")])

    # Consumíveis (agora via tabela itens)
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT nome, COUNT(*) FROM itens WHERE pid = %s AND nome LIKE 'Poção%' GROUP BY nome", (dados['id'],))
    consumiveis = {row[0]: row[1] for row in c.fetchall()}

    cons_hp = []
    if consumiveis.get("Poção de Vida", 0) > 0:
        cons_hp.append(InlineKeyboardButton(f"💊 Poção HP ({consumiveis['Poção de Vida']})", callback_data="bat_pot_hp"))
    if consumiveis.get("Poção Grande de Vida", 0) > 0:
        cons_hp.append(InlineKeyboardButton(f"💊+ Grande ({consumiveis['Poção Grande de Vida']})", callback_data="bat_pot_hp2"))
    if cons_hp:
        kb.append(cons_hp)

    if dados['mana_max'] > 0:
        cons_mp = []
        if consumiveis.get("Poção de Mana", 0) > 0:
            cons_mp.append(InlineKeyboardButton(f"🔵 Mana ({consumiveis['Poção de Mana']})", callback_data="bat_pot_mp"))
        if consumiveis.get("Elixir de Mana", 0) > 0:
            cons_mp.append(InlineKeyboardButton(f"🔵+ Elixir ({consumiveis['Elixir de Mana']})", callback_data="bat_pot_mp2"))
        if cons_mp:
            kb.append(cons_mp)

    kb.append([InlineKeyboardButton("🏃 Fugir", callback_data="bat_fug")])

    img = IMAGENS["combate"]
    tipo = dados.get('tipo_monstro')
    mapa = dados.get('mapa_monstro')
    if tipo and mapa and tipo in IMAGENS["monstros"] and mapa in IMAGENS["monstros"][tipo]:
        img = IMAGENS["monstros"][tipo][mapa]

    return cap, kb, img

async def exibir_combate(upd, ctx, dados):
    cap, kb, img = montar_cap_combate(dados)
    try:
        await upd.callback_query.edit_message_media(
            media=InputMediaPhoto(media=img, caption=cap, parse_mode='Markdown'),
            reply_markup=InlineKeyboardMarkup(kb)
        )
    except:
        try:
            await ctx.bot.send_photo(upd.effective_chat.id, img, caption=cap,
                                     reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
        except:
            pass

# ===== HERÓI =====
async def heroi_aceitar(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    await q.answer()

    conn = get_db_connection()
    c = conn.cursor(cursor_factory=RealDictCursor)
    c.execute("SELECT * FROM heroi_oferta WHERE pid = %s", (uid,))
    h = c.fetchone()
    if not h:
        await menu(upd, ctx, uid)
        return

    c.execute("""INSERT INTO combate
                (pid, inimigo, i_hp, i_hp_max, i_atk, i_def, i_xp, i_gold, turno, defendendo, heroi, tipo_monstro, mapa_monstro)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1, 0, %s, %s, %s)""",
              (uid, h['inimigo'], h['i_hp'], h['i_hp'], h['i_atk'], h['i_def'],
               h['i_xp'], h['i_gold'], h['heroi_nome'], h['tipo_monstro'], h['mapa_monstro']))
    c.execute("DELETE FROM heroi_oferta WHERE pid = %s", (uid,))
    conn.commit()
    invalidate_cache(uid)

    try:
        await q.message.delete()
    except:
        pass
    dados = get_tudo(uid)
    await exibir_combate(upd, ctx, dados)

async def heroi_recusar(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    await q.answer()

    conn = get_db_connection()
    c = conn.cursor(cursor_factory=RealDictCursor)
    c.execute("SELECT * FROM heroi_oferta WHERE pid = %s", (uid,))
    h = c.fetchone()
    if not h:
        await menu(upd, ctx, uid)
        return

    c.execute("""INSERT INTO combate
                (pid, inimigo, i_hp, i_hp_max, i_atk, i_def, i_xp, i_gold, turno, defendendo, heroi, tipo_monstro, mapa_monstro)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1, 0, NULL, %s, %s)""",
              (uid, h['inimigo'], h['i_hp'], h['i_hp'], h['i_atk'], h['i_def'],
               h['i_xp'], h['i_gold'], h['tipo_monstro'], h['mapa_monstro']))
    c.execute("DELETE FROM heroi_oferta WHERE pid = %s", (uid,))
    conn.commit()
    invalidate_cache(uid)

    try:
        await q.message.delete()
    except:
        pass
    dados = get_tudo(uid)
    await exibir_combate(upd, ctx, dados)

# ===== COMBATE: ATACAR =====
async def bat_atk(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    await q.answer("⚔️!")

    conn = get_db_connection()
    c = conn.cursor(cursor_factory=RealDictCursor)

    c.execute("""
        SELECT p.*, cb.inimigo, cb.i_hp, cb.i_hp_max, cb.i_atk, cb.i_def,
               cb.i_xp, cb.i_gold, cb.turno, cb.defendendo, cb.heroi,
               cb.tipo_monstro, cb.mapa_monstro
        FROM players p
        JOIN combate cb ON cb.pid = p.id
        WHERE p.id = %s
    """, (uid,))
    dados = c.fetchone()
    if not dados:
        return

    dados = dict(dados)
    p_atk = calc_atk(dados)
    p_def = calc_def(dados)
    i_hp = dados['i_hp']
    p_hp = dados['hp']
    log = []

    is_crit = random.randint(1, 100) <= dados['crit']
    num_ataques = 2 if dados['double_atk'] else 1

    for _ in range(num_ataques):
        dano_base = int(p_atk * (100 / (100 + dados['i_def'])))
        dano = max(1, dano_base + random.randint(-2, 2))

        if is_crit:
            dano = int(dano * 1.5)
            i_hp -= dano
            log.append(f"💥 CRÍTICO! -{dano} HP")
        else:
            i_hp -= dano
            log.append(f"⚔️ Ataque! -{dano} HP")

        if i_hp <= 0:
            break

    resultado = None

    if i_hp <= 0:
        # Vitória
        c.execute("UPDATE players SET hp=%s, gold=gold+%s, exp=exp+%s WHERE id=%s",
                  (p_hp, dados['i_gold'], dados['i_xp'], uid))
        conn.commit()

        # Verifica level up
        c.execute("SELECT lv, exp, classe FROM players WHERE id=%s", (uid,))
        player_atual = c.fetchone()

        if player_atual:
            lv_atual = player_atual['lv']
            exp_atual = player_atual['exp']
            classe = player_atual['classe']
            xp_necessario = lv_atual * 100

            if exp_atual >= xp_necessario:
                novo_lv = lv_atual + 1
                exp_restante = exp_atual - xp_necessario
                stats = CLASSE_STATS[classe]
                novo_hp_max = stats['hp'] * novo_lv
                novo_mana_max = stats['mana'] * novo_lv if stats['mana'] > 0 else 0

                c.execute("""
                    UPDATE players SET 
                        lv = %s, exp = %s, hp_max = %s, hp = %s,
                        mana_max = %s, mana = %s
                    WHERE id = %s
                """, (novo_lv, exp_restante, novo_hp_max, novo_hp_max,
                      novo_mana_max, novo_mana_max, uid))
                conn.commit()

                log.append(f"\n🎉 **SUBIU PARA NÍVEL {novo_lv}!**")

        # Chance de drop de item
        mapa = dados['mapa_monstro']
        if mapa in DROPS_POR_MAPA:
            for drop in DROPS_POR_MAPA[mapa]:
                if random.random() < drop['chance']:
                    item_id = criar_item_aleatorio(drop['item'], uid)
                    if item_id:
                        log.append(f"\n🎁 **Dropou: {drop['item']}!**")
                    break  # Apenas um drop por vitória

        c.execute("DELETE FROM combate WHERE pid=%s", (uid,))
        conn.commit()
        invalidate_cache(uid)
        resultado = "vitoria"

    else:
        # Contra-ataque
        dano_ini = max(1, dados['i_atk'] - p_def + random.randint(-2, 2))

        if dados.get('defendendo'):
            dano_ini = max(1, dano_ini // 2)
            log.append(f"🛡️ Defendeu! Inimigo causou -{dano_ini} HP")
        else:
            log.append(f"🐺 Inimigo atacou! -{dano_ini} HP")

        p_hp -= dano_ini

        if p_hp <= 0:
            c.execute("UPDATE players SET hp=1 WHERE id=%s", (uid,))
            c.execute("DELETE FROM combate WHERE pid=%s", (uid,))
            conn.commit()
            invalidate_cache(uid)
            resultado = "derrota"
        else:
            c.execute("UPDATE players SET hp=%s WHERE id=%s", (p_hp, uid))
            c.execute("UPDATE combate SET i_hp=%s, turno=turno+1, defendendo=0 WHERE pid=%s", (i_hp, uid))
            conn.commit()
            invalidate_cache(uid)

    if resultado == "vitoria":
        cap = (f"🏆 **VITÓRIA!**\n{'━'*20}\n🐺 {dados['inimigo']} derrotado!\n\n"
               + "\n".join(log) + f"\n\n💰 +{dados['i_gold']} Gold\n✨ +{dados['i_xp']} XP\n{'━'*20}")
        kb = [[InlineKeyboardButton("🔙 Voltar", callback_data="voltar")]]
        try:
            await q.message.delete()
        except:
            pass
        await ctx.bot.send_photo(upd.effective_chat.id, img_c(dados['classe']), caption=cap,
                                 reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    elif resultado == "derrota":
        cap = (f"💀 **DERROTA!**\n{'━'*20}\n🐺 {dados['inimigo']} venceu!\n\n"
               + "\n".join(log) + f"\n\nVocê foi derrotado...\n{'━'*20}")
        kb = [[InlineKeyboardButton("🔙 Voltar", callback_data="voltar")]]
        try:
            await q.message.delete()
        except:
            pass
        await ctx.bot.send_photo(upd.effective_chat.id, img_c(dados['classe']), caption=cap,
                                 reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    else:
        dados['hp'] = p_hp
        dados['i_hp'] = i_hp
        dados['turno'] = dados['turno'] + 1
        dados['defendendo'] = 0
        await exibir_combate(upd, ctx, dados)

# ===== COMBATE: DEFENDER =====
async def bat_def(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    await q.answer("🛡️ Defendendo!")

    conn = get_db_connection()
    c = conn.cursor(cursor_factory=RealDictCursor)
    c.execute("""
        SELECT p.*, cb.inimigo, cb.i_hp, cb.i_hp_max, cb.i_atk, cb.i_def,
               cb.i_xp, cb.i_gold, cb.turno, cb.defendendo, cb.heroi,
               cb.tipo_monstro, cb.mapa_monstro
        FROM players p
        JOIN combate cb ON cb.pid = p.id
        WHERE p.id = %s
    """, (uid,))
    dados = c.fetchone()
    if not dados:
        return
    dados = dict(dados)

    p_def = calc_def(dados)
    dano_ini = max(1, dados['i_atk'] - p_def + random.randint(-2, 2))
    dano_reduzido = max(1, dano_ini // 2)
    novo_hp = dados['hp'] - dano_reduzido

    if novo_hp <= 0:
        c.execute("UPDATE players SET hp=1 WHERE id=%s", (uid,))
        c.execute("DELETE FROM combate WHERE pid=%s", (uid,))
        conn.commit()
        invalidate_cache(uid)
        cap = (f"💀 **DERROTA!**\n{'━'*20}\n🐺 {dados['inimigo']} venceu!\n\n"
               f"🛡️ Defendeu mas não aguentou!\n{'━'*20}")
        kb = [[InlineKeyboardButton("🔙 Voltar", callback_data="voltar")]]
        try:
            await q.message.delete()
        except:
            pass
        await ctx.bot.send_photo(upd.effective_chat.id, img_c(dados['classe']), caption=cap,
                                 reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
        return

    c.execute("UPDATE players SET hp=%s WHERE id=%s", (novo_hp, uid))
    c.execute("UPDATE combate SET defendendo=1, turno=turno+1 WHERE pid=%s", (uid,))
    conn.commit()
    invalidate_cache(uid)

    dados['defendendo'] = 1
    dados['turno'] = dados['turno'] + 1
    dados['hp'] = novo_hp
    await exibir_combate(upd, ctx, dados)

# ===== COMBATE: ESPECIAL =====
async def bat_esp(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id

    conn = get_db_connection()
    c = conn.cursor(cursor_factory=RealDictCursor)
    c.execute("""
        SELECT p.*, cb.inimigo, cb.i_hp, cb.i_hp_max, cb.i_atk, cb.i_def,
               cb.i_xp, cb.i_gold, cb.turno, cb.defendendo, cb.heroi,
               cb.tipo_monstro, cb.mapa_monstro
        FROM players p
        JOIN combate cb ON cb.pid = p.id
        WHERE p.id = %s
    """, (uid,))
    dados = c.fetchone()
    if not dados:
        return
    dados = dict(dados)

    esp = CLASSE_STATS[dados['classe']]['especial']
    p_atk = calc_atk(dados)
    p_def = calc_def(dados)
    i_hp = dados['i_hp']

    if esp == "maldição" and dados['mana'] >= 20:
        dano = int(p_atk * 1.3)
        i_hp -= dano
        dano_ini = max(1, dados['i_atk'] - p_def + random.randint(-2, 2))
        novo_hp = dados['hp'] - dano_ini

        if i_hp <= 0:
            c.execute("UPDATE players SET gold=gold+%s, exp=exp+%s, mana=mana-20 WHERE id=%s",
                      (dados['i_gold'], dados['i_xp'], uid))
            c.execute("DELETE FROM combate WHERE pid=%s", (uid,))
            conn.commit()
            invalidate_cache(uid)
            await q.answer(f"🔮 Maldição! -{dano} HP - VITÓRIA!")
            cap = (f"🏆 **VITÓRIA!**\n{'━'*20}\n🔮 Maldição destruiu o inimigo!\n\n"
                   f"💰 +{dados['i_gold']} Gold\n✨ +{dados['i_xp']} XP\n{'━'*20}")
            kb = [[InlineKeyboardButton("🔙 Voltar", callback_data="voltar")]]
            try:
                await q.message.delete()
            except:
                pass
            await ctx.bot.send_photo(upd.effective_chat.id, img_c(dados['classe']), caption=cap,
                                     reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
            return

        if novo_hp <= 0:
            c.execute("UPDATE players SET hp=1, mana=mana-20 WHERE id=%s", (uid,))
            c.execute("DELETE FROM combate WHERE pid=%s", (uid,))
            conn.commit()
            invalidate_cache(uid)
            await q.answer("Derrota!", show_alert=True)
            await menu(upd, ctx, uid, "💀 **Derrotado!**")
            return

        c.execute("""UPDATE combate SET i_hp=%s, i_def=GREATEST(i_def-3,0), turno=turno+1, defendendo=0 WHERE pid=%s""",
                  (i_hp, uid))
        c.execute("UPDATE players SET mana=mana-20, hp=%s WHERE id=%s", (novo_hp, uid))
        await q.answer(f"🔮 Maldição! -{dano} HP")
        dados['mana'] -= 20
        dados['hp'] = novo_hp

    elif esp == "explosão" and dados['mana'] >= 30:
        dano_max = int(dados['i_hp_max'] * 0.25)
        dano = min(dano_max, int(p_atk * 1.5))
        i_hp -= dano
        dano_ini = max(1, dados['i_atk'] - p_def + random.randint(-2, 2))
        novo_hp = dados['hp'] - dano_ini

        if i_hp <= 0:
            c.execute("UPDATE players SET gold=gold+%s, exp=exp+%s, mana=mana-30 WHERE id=%s",
                      (dados['i_gold'], dados['i_xp'], uid))
            c.execute("DELETE FROM combate WHERE pid=%s", (uid,))
            conn.commit()
            invalidate_cache(uid)
            await q.answer(f"🔥 Explosão! -{dano} HP - VITÓRIA!")
            cap = (f"🏆 **VITÓRIA!**\n{'━'*20}\n🔥 Explosão destruiu o inimigo!\n\n"
                   f"💰 +{dados['i_gold']} Gold\n✨ +{dados['i_xp']} XP\n{'━'*20}")
            kb = [[InlineKeyboardButton("🔙 Voltar", callback_data="voltar")]]
            try:
                await q.message.delete()
            except:
                pass
            await ctx.bot.send_photo(upd.effective_chat.id, img_c(dados['classe']), caption=cap,
                                     reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
            return

        if novo_hp <= 0:
            c.execute("UPDATE players SET hp=1, mana=mana-30 WHERE id=%s", (uid,))
            c.execute("DELETE FROM combate WHERE pid=%s", (uid,))
            conn.commit()
            invalidate_cache(uid)
            await q.answer("Derrota!", show_alert=True)
            await menu(upd, ctx, uid, "💀 **Derrotado!**")
            return

        c.execute("UPDATE combate SET i_hp=%s, turno=turno+1, defendendo=0 WHERE pid=%s", (i_hp, uid))
        c.execute("UPDATE players SET mana=mana-30, hp=%s WHERE id=%s", (novo_hp, uid))
        await q.answer(f"🔥 Explosão! -{dano} HP")
        dados['mana'] -= 30
        dados['hp'] = novo_hp
    else:
        await q.answer("Sem mana!", show_alert=True)
        return

    conn.commit()
    invalidate_cache(uid)

    dados['i_hp'] = i_hp
    dados['turno'] = dados['turno'] + 1
    dados['defendendo'] = 0
    await exibir_combate(upd, ctx, dados)

# ===== COMBATE: HERÓI =====
async def bat_heroi(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id

    conn = get_db_connection()
    c = conn.cursor(cursor_factory=RealDictCursor)
    c.execute("SELECT p.classe, cb.inimigo, cb.i_gold, cb.i_xp, cb.heroi FROM players p JOIN combate cb ON cb.pid=p.id WHERE p.id=%s", (uid,))
    dados = c.fetchone()
    if not dados or not dados['heroi']:
        await q.answer("Sem herói!", show_alert=True)
        return

    await q.answer(f"⭐ {dados['heroi']} ataca!")

    c.execute("UPDATE players SET gold=gold+%s, exp=exp+%s WHERE id=%s", (dados['i_gold'], dados['i_xp'], uid))
    c.execute("DELETE FROM combate WHERE pid=%s", (uid,))
    conn.commit()
    invalidate_cache(uid)

    heroi_img = IMAGENS["classes"]["Guerreiro"]
    for mapa_herois in HEROIS.values():
        for h in mapa_herois:
            if h['nome'] == dados['heroi']:
                heroi_img = IMAGENS["herois"].get(h['img'], IMAGENS["classes"]["Guerreiro"])
                break

    cap = (f"⭐ **{dados['heroi']} DEVASTOU O INIMIGO!**\n{'━'*20}\n"
           f"🐺 {dados['inimigo']} foi obliterado!\n\n💫 O herói usou seu poder máximo!\n\n"
           f"💰 +{dados['i_gold']} Gold\n✨ +{dados['i_xp']} XP\n{'━'*20}\n\n"
           f"*O herói desaparece em uma rajada de luz...*")
    kb = [[InlineKeyboardButton("🔙 Voltar", callback_data="voltar")]]
    try:
        await q.message.delete()
    except:
        pass
    await ctx.bot.send_photo(upd.effective_chat.id, heroi_img, caption=cap,
                             reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

# ===== COMBATE: POÇÕES =====
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

    conn = get_db_connection()
    c = conn.cursor(cursor_factory=RealDictCursor)
    c.execute("""
        SELECT p.*, cb.inimigo, cb.i_hp, cb.i_hp_max, cb.i_atk, cb.i_def,
               cb.i_xp, cb.i_gold, cb.turno, cb.defendendo, cb.heroi,
               cb.tipo_monstro, cb.mapa_monstro
        FROM players p
        JOIN combate cb ON cb.pid = p.id
        WHERE p.id = %s
    """, (uid,))
    dados = c.fetchone()
    if not dados:
        return
    dados = dict(dados)

    # Verifica se tem a poção
    c.execute("SELECT id FROM itens WHERE pid = %s AND nome = %s LIMIT 1", (uid, item))
    result = c.fetchone()
    if not result:
        await q.answer("Sem item!", show_alert=True)
        return

    item_id = result['id']
    cons = CONSUMIVEIS[item]
    p_def = calc_def(dados)

    if cons['tipo'] == 'hp':
        novo_hp = min(dados['hp'] + cons['valor'], dados['hp_max'])
        c.execute("UPDATE players SET hp=%s WHERE id=%s", (novo_hp, uid))
        await q.answer(f"💊 +{cons['valor']} HP!")
        dados['hp'] = novo_hp
    else:
        if dados['mana_max'] == 0:
            await q.answer("Você não usa mana!", show_alert=True)
            return
        novo_mana = min(dados['mana'] + cons['valor'], dados['mana_max'])
        c.execute("UPDATE players SET mana=%s WHERE id=%s", (novo_mana, uid))
        await q.answer(f"🔵 +{cons['valor']} Mana!")
        dados['mana'] = novo_mana

    # Remove a poção usada
    c.execute("DELETE FROM itens WHERE id = %s", (item_id,))

    dano_ini = max(1, dados['i_atk'] - p_def + random.randint(-2, 2))
    novo_p_hp = dados['hp'] - dano_ini
    c.execute("UPDATE combate SET turno=turno+1 WHERE pid=%s", (uid,))

    if novo_p_hp <= 0:
        c.execute("UPDATE players SET hp=1 WHERE id=%s", (uid,))
        c.execute("DELETE FROM combate WHERE pid=%s", (uid,))
        conn.commit()
        invalidate_cache(uid)
        await menu(upd, ctx, uid, "💀 **Derrotado!**")
        return

    c.execute("UPDATE players SET hp=%s WHERE id=%s", (novo_p_hp, uid))
    conn.commit()
    invalidate_cache(uid)

    dados['hp'] = novo_p_hp
    dados['turno'] = dados['turno'] + 1
    await exibir_combate(upd, ctx, dados)

# ===== COMBATE: FUGIR =====
async def bat_fug(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id

    if random.random() < 0.5:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("DELETE FROM combate WHERE pid=%s", (uid,))
        conn.commit()
        invalidate_cache(uid)
        await q.answer("🏃 Fugiu!")
        await menu(upd, ctx, uid, "🏃 **Você fugiu!**")
    else:
        conn = get_db_connection()
        c = conn.cursor(cursor_factory=RealDictCursor)
        c.execute("""SELECT p.hp, p.hp_max, p.classe, p.lv, p.armadura_equipada,
                            cb.i_atk, cb.i_hp, cb.i_hp_max, cb.inimigo,
                            cb.i_def, cb.i_xp, cb.i_gold, cb.turno, cb.defendendo,
                            cb.heroi, cb.tipo_monstro, cb.mapa_monstro,
                            p.mana, p.mana_max, p.crit, p.double_atk
                     FROM players p JOIN combate cb ON cb.pid=p.id WHERE p.id=%s""", (uid,))
        dados = c.fetchone()
        if not dados:
            return
        dados = dict(dados)
        p_def = calc_def(dados)
        dano = max(1, dados['i_atk'] - p_def + random.randint(0, 3))
        novo_hp = dados['hp'] - dano

        if novo_hp <= 0:
            c.execute("UPDATE players SET hp=1 WHERE id=%s", (uid,))
            c.execute("DELETE FROM combate WHERE pid=%s", (uid,))
            conn.commit()
            invalidate_cache(uid)
            await q.answer(f"❌ Falhou! -{dano} HP", show_alert=True)
            await menu(upd, ctx, uid, "💀 **Derrotado ao fugir!**")
        else:
            c.execute("UPDATE players SET hp=%s WHERE id=%s", (novo_hp, uid))
            c.execute("UPDATE combate SET turno=turno+1 WHERE pid=%s", (uid,))
            conn.commit()
            invalidate_cache(uid)
            await q.answer(f"❌ Falhou! -{dano} HP", show_alert=True)
            dados['hp'] = novo_hp
            dados['turno'] = dados['turno'] + 1
            await exibir_combate(upd, ctx, dados)

# ===== MAPAS E LOCAIS =====
async def mapas(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    dados = get_tudo(uid)
    await q.answer()

    cap = f"🗺️ **MAPAS**\n{'━'*20}\n"
    kb = []
    for mid, m in MAPAS.items():
        st = "✅" if dados['lv'] >= m['lv'] else f"🔒 Lv.{m['lv']}"
        at = " 📍" if mid == dados['mapa'] else ""
        av = f"\n└ {m['aviso']}" if m.get('aviso') and mid != dados['mapa'] else ""
        cap += f"{st} {m['nome']}{at}{av}\n"
        kb.append([InlineKeyboardButton(f"🗺️ {m['nome']}", callback_data=f"via_{mid}")])
    kb.append([InlineKeyboardButton("🔙 Voltar", callback_data="voltar")])
    cap += f"{'━'*20}"

    img_mapa = IMAGENS["mapas"].get(dados['mapa'], IMAGENS["classes"]["Guerreiro"])
    try:
        await q.message.delete()
    except:
        pass
    await ctx.bot.send_photo(upd.effective_chat.id, img_mapa, caption=cap,
                             reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def viajar(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    dados = get_tudo(uid)
    mid = int(q.data.split('_')[1])
    m = MAPAS[mid]

    if dados['lv'] < m['lv'] and m.get('aviso'):
        await q.answer(f"⚠️ {m['aviso']}", show_alert=True)

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE players SET mapa=%s, local='cap' WHERE id=%s", (mid, uid))
    conn.commit()
    invalidate_cache(uid)
    await q.answer(f"🗺️ {m['nome']}!")
    try:
        await q.message.delete()
    except:
        pass
    await menu(upd, ctx, uid, f"🗺️ **Viajou para {m['nome']}!**")

async def locais(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    dados = get_tudo(uid)
    await q.answer()

    m = MAPAS.get(dados['mapa'], {})
    cap = f"🏘️ **LOCAIS - {m.get('nome','')}**\n{'━'*20}\n"
    kb = []
    for lid, loc in m.get('loc', {}).items():
        at = " 📍" if lid == dados['local'] else ""
        lj = " 🏪" if loc.get('loja') else ""
        ac = " 🏕️" if loc.get('acampamento') else ""
        pe = " 🏨" if loc.get('pensao') else ""
        cap += f"🏠 {loc['nome']}{at}{lj}{ac}{pe}\n"
        
        # Botões de ação
        botoes = []
        botoes.append(InlineKeyboardButton(f"📍 Ir", callback_data=f"iloc_{lid}"))
        if loc.get('acampamento'):
            botoes.append(InlineKeyboardButton(f"🏕️ Descansar (20⚡)", callback_data=f"descansar_acampamento"))
        if loc.get('pensao'):
            botoes.append(InlineKeyboardButton(f"🏨 Pensão (90💰)", callback_data=f"descansar_pensao"))
        kb.append(botoes)
    
    kb.append([InlineKeyboardButton("🔙 Voltar", callback_data="voltar")])
    cap += f"{'━'*20}"

    img_mapa = IMAGENS["mapas"].get(dados['mapa'], IMAGENS["classes"]["Guerreiro"])
    try:
        await q.message.delete()
    except:
        pass
    await ctx.bot.send_photo(upd.effective_chat.id, img_mapa, caption=cap,
                             reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def ir_loc(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    dados = get_tudo(uid)
    lid = q.data.split('_')[1]

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE players SET local=%s WHERE id=%s", (lid, uid))
    conn.commit()
    invalidate_cache(uid)

    ln = MAPAS[dados['mapa']]['loc'][lid]['nome']
    await q.answer(f"📍 {ln}")

    chave_local = f"{lid}_{dados['mapa']}"
    img_local = IMAGENS["locais"].get(chave_local, IMAGENS["classes"]["Guerreiro"])

    li = MAPAS[dados['mapa']]['loc'][lid]
    cap = f"📍 **{ln}**\n{'━'*20}\n🗺️ {MAPAS[dados['mapa']]['nome']}\n\n"
    if li.get('loja'):
        cap += "🏪 Loja disponível\n"
    if li.get('acampamento'):
        cap += "🏕️ Acampamento (descanso: 20💰 = +10⚡)\n"
    if li.get('pensao'):
        cap += "🏨 Pensão (90💰 = recuperar toda ⚡)\n"
    cap += f"{'━'*20}"
    
    kb = []
    if li.get('acampamento'):
        kb.append([InlineKeyboardButton("🏕️ Descansar (20💰)", callback_data="descansar_acampamento")])
    if li.get('pensao'):
        kb.append([InlineKeyboardButton("🏨 Dormir (90💰)", callback_data="descansar_pensao")])
    kb.append([InlineKeyboardButton("🔙 Menu", callback_data="voltar")])
    
    try:
        await q.message.delete()
    except:
        pass
    await ctx.bot.send_photo(upd.effective_chat.id, img_local, caption=cap,
                             reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

# ===== LOJA =====
async def loja(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    dados = get_tudo(uid)
    await q.answer()

    loc = MAPAS[dados['mapa']]['loc'][dados['local']]
    if not loc.get('loja'):
        await q.answer("🚫 Sem loja aqui!", show_alert=True)
        return

    cap = (f"🏪 **COMÉRCIO - {loc['nome']}**\n{'━'*20}\n\n"
           f"📍 Escolha onde comprar:\n\n"
           f"🏪 **Loja Normal**\n└ Preços justos\n└ Itens garantidos\n\n"
           f"🏴‍☠️ **Mercado Negro**\n└ 💰 -30% preços\n└ ⚠️ 5% chance de roubo\n\n"
           f"💰 **Vender Itens**\n└ Venda seus equipamentos (50% do valor)")
    kb = [
        [InlineKeyboardButton("🏪 Loja Normal", callback_data="loja_normal")],
        [InlineKeyboardButton("🏴‍☠️ Mercado Negro", callback_data="loja_contra")],
        [InlineKeyboardButton("💰 Vender Itens", callback_data="loja_vender")],
        [InlineKeyboardButton("🔙 Voltar", callback_data="voltar")]
    ]
    chave_local = f"{dados['local']}_{dados['mapa']}"
    img_local = IMAGENS["locais"].get(chave_local, IMAGENS["classes"]["Guerreiro"])
    try:
        await q.message.delete()
    except:
        pass
    await ctx.bot.send_photo(upd.effective_chat.id, img_local, caption=cap,
                             reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def loja_normal(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    dados = get_tudo(uid)
    await q.answer()

    loc = MAPAS[dados['mapa']]['loc'][dados['local']]
    cap = f"🏪 **LOJA NORMAL - {loc['nome']}**\n{'━'*20}\n💰 {dados['gold']}\n\n**⚔️ EQUIPAMENTOS:**\n"
    kb = []

    # Itens disponíveis para a classe do jogador
    for n, base in ITENS_BASE.items():
        if dados['classe'] not in base['cls']:
            continue
        if base['lv'] > dados['lv']:
            continue
            
        preco = base['preco']
        em = "⚔️" if base['tipo'] == "arma" else "🛡️"
        atk_info = f"ATK {base['atk_min']}-{base['atk_max']}" if base['atk_max'] > 0 else ""
        def_info = f"DEF {base['def_min']}-{base['def_max']}" if base['def_max'] > 0 else ""
        stats = f"{atk_info} {def_info}".strip()
        
        cap += f"{em} {n}\n└ {stats} | 💰 {preco}\n"
        if dados['gold'] >= preco:
            kb.append([InlineKeyboardButton(f"💰 Comprar {n}", callback_data=f"comprar_normal_{n}")])

    cap += "\n**💊 CONSUMÍVEIS:**\n"
    for n, cs in CONSUMIVEIS.items():
        if cs['tipo'] == 'mana' and dados['mana_max'] == 0:
            continue
        cap += f"💊 {n} ({cs['tipo'].upper()} +{cs['valor']})\n└ 💰 {cs['preco']}\n"
        if dados['gold'] >= cs['preco']:
            kb.append([InlineKeyboardButton(f"💊 Comprar {n}", callback_data=f"comprar_consumivel_{n}")])

    kb.append([InlineKeyboardButton("🔙 Voltar", callback_data="loja")])
    cap += f"{'━'*20}"

    chave_loja = f"{dados['local']}_{dados['mapa']}"
    img_loja = IMAGENS["lojas"].get(chave_loja, IMAGENS["classes"]["Guerreiro"])
    try:
        await q.message.delete()
    except:
        pass
    await ctx.bot.send_photo(upd.effective_chat.id, img_loja, caption=cap,
                             reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def loja_contra(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    dados = get_tudo(uid)
    await q.answer()

    cap = f"🏴‍☠️ **MERCADO NEGRO**\n{'━'*20}\n💰 {dados['gold']}\n⚠️ **-30% preço | 5% roubo**\n\n**⚔️ EQUIPAMENTOS:**\n"
    kb = []

    for n, base in ITENS_BASE.items():
        if dados['classe'] not in base['cls']:
            continue
        if base['lv'] > dados['lv']:
            continue
            
        preco = int(base['preco'] * 0.7)
        em = "⚔️" if base['tipo'] == "arma" else "🛡️"
        atk_info = f"ATK {base['atk_min']}-{base['atk_max']}" if base['atk_max'] > 0 else ""
        def_info = f"DEF {base['def_min']}-{base['def_max']}" if base['def_max'] > 0 else ""
        stats = f"{atk_info} {def_info}".strip()
        
        cap += f"{em} {n}\n└ {stats} | 💰 {preco}\n"
        if dados['gold'] >= preco:
            kb.append([InlineKeyboardButton(f"💰 Comprar {n}", callback_data=f"comprar_contra_{n}")])

    cap += "\n**💊 CONSUMÍVEIS:**\n"
    for n, cs in CONSUMIVEIS.items():
        if cs['tipo'] == 'mana' and dados['mana_max'] == 0:
            continue
        preco = int(cs['preco'] * 0.7)
        cap += f"💊 {n} ({cs['tipo'].upper()} +{cs['valor']})\n└ 💰 {preco}\n"
        if dados['gold'] >= preco:
            kb.append([InlineKeyboardButton(f"💊 Comprar {n}", callback_data=f"comprar_contra_consumivel_{n}")])

    kb.append([InlineKeyboardButton("🔙 Voltar", callback_data="loja")])
    cap += f"{'━'*20}"

    img_contra = IMAGENS["contrabandistas"].get(dados['mapa'], IMAGENS["classes"]["Guerreiro"])
    try:
        await q.message.delete()
    except:
        pass
    await ctx.bot.send_photo(upd.effective_chat.id, img_contra, caption=cap,
                             reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def loja_vender(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    await q.answer()
    
    itens, _ = get_itens_jogador(uid)
    
    if not itens:
        cap = "💰 **VENDER ITENS**\n{'━'*20}\nVocê não tem itens para vender!\n{'━'*20}"
        kb = [[InlineKeyboardButton("🔙 Voltar", callback_data="loja")]]
        try:
            await q.message.delete()
        except:
            pass
        await ctx.bot.send_photo(upd.effective_chat.id, IMAGENS["classes"]["Guerreiro"], caption=cap,
                                 reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
        return
    
    cap = f"💰 **VENDER ITENS**\n{'━'*20}\n⚠️ Venda por 50% do valor\n\n"
    kb = []
    
    for item in itens[:10]:  # Mostra apenas 10 itens para não poluir
        if item['tipo'] == 'consumivel':
            continue  # Consumíveis não podem ser vendidos (ou pode?)
        
        base = ITENS_BASE.get(item['nome'])
        if base:
            preco_venda = int(base['preco'] * 0.5)
            emoji = "⚔️" if item['tipo'] == 'arma' else "🛡️"
            stats = f"ATK{item['atk']}" if item['atk'] > 0 else f"DEF{item['def']}"
            equipado = ""
            if (item['tipo'] == 'arma' and dados.get('arma_equipada') == item['id']) or \
               (item['tipo'] == 'armadura' and dados.get('armadura_equipada') == item['id']):
                equipado = " ✓"
            cap += f"{emoji} {item['nome']} {stats}{equipado}\n└ 💰 {preco_venda}\n"
            kb.append([InlineKeyboardButton(f"💰 Vender {item['nome']}", callback_data=f"vender_{item['id']}")])
    
    if len(itens) > 10:
        cap += f"\n... e mais {len(itens)-10} itens"
    
    kb.append([InlineKeyboardButton("🔙 Voltar", callback_data="loja")])
    cap += f"{'━'*20}"
    
    try:
        await q.message.delete()
    except:
        pass
    await ctx.bot.send_photo(upd.effective_chat.id, IMAGENS["classes"]["Guerreiro"], caption=cap,
                             reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def comprar_item(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    dados = get_tudo(uid)
    
    parts = q.data.split('_')
    tipo_loja = parts[1]  # normal ou contra
    item_nome = '_'.join(parts[2:])
    
    # Verifica se é consumível
    if item_nome in CONSUMIVEIS:
        cons = CONSUMIVEIS[item_nome]
        preco = int(cons['preco'] * (0.7 if tipo_loja == "contra" else 1.0))
        
        if dados['gold'] < preco:
            await q.answer("💸 Sem gold!", show_alert=True)
            return
            
        if tipo_loja == "contra" and random.random() < 0.05:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("UPDATE players SET gold = gold - %s WHERE id = %s", (preco, uid))
            conn.commit()
            invalidate_cache(uid)
            await q.answer("🏴‍☠️ Roubado!", show_alert=True)
            await loja(upd, ctx)
            return
        
        # Adiciona consumível como item
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO itens (pid, nome, tipo, atk, def, quantidade)
            VALUES (%s, %s, 'consumivel', 0, 0, 1)
        """, (uid, item_nome))
        c.execute("UPDATE players SET gold = gold - %s WHERE id = %s", (preco, uid))
        conn.commit()
        invalidate_cache(uid)
        
        await q.answer(f"✅ {item_nome} comprado!")
        
    else:
        # É equipamento
        base = ITENS_BASE.get(item_nome)
        if not base:
            await q.answer("Item inválido!", show_alert=True)
            return
            
        preco = int(base['preco'] * (0.7 if tipo_loja == "contra" else 1.0))
        
        if dados['gold'] < preco:
            await q.answer("💸 Sem gold!", show_alert=True)
            return
            
        if tipo_loja == "contra" and random.random() < 0.05:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("UPDATE players SET gold = gold - %s WHERE id = %s", (preco, uid))
            conn.commit()
            invalidate_cache(uid)
            await q.answer("🏴‍☠️ Roubado!", show_alert=True)
            await loja(upd, ctx)
            return
        
        # Cria item com stats aleatórios
        item_id = criar_item_aleatorio(item_nome, uid)
        if item_id:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("UPDATE players SET gold = gold - %s WHERE id = %s", (preco, uid))
            conn.commit()
            invalidate_cache(uid)
            await q.answer(f"✅ {item_nome} comprado!")
    
    if tipo_loja == "normal":
        await loja_normal(upd, ctx)
    else:
        await loja_contra(upd, ctx)

async def vender_item(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    dados = get_tudo(uid)
    
    item_id = int(q.data.split('_')[1])
    
    item = get_item_por_id(item_id)
    if not item or item['pid'] != uid:
        await q.answer("Item não encontrado!", show_alert=True)
        return
    
    if item['tipo'] == 'consumivel':
        await q.answer("Consumíveis não podem ser vendidos!", show_alert=True)
        return
    
    base = ITENS_BASE.get(item['nome'])
    if not base:
        await q.answer("Item inválido!", show_alert=True)
        return
    
    preco_venda = int(base['preco'] * 0.5)
    
    sucesso, msg = vender_item(uid, item_id, preco_venda)
    await q.answer(msg, show_alert=True)
    
    if sucesso:
        await loja_vender(upd, ctx)

# ===== INVENTÁRIO =====
async def inv(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    dados = get_tudo(uid)
    await q.answer()
    
    itens, slots_por_item = get_itens_jogador(uid)
    
    cap = f"🎒 **INVENTÁRIO**\n{'━'*20}\n"
    cap += f"📦 Slots: {len(slots_por_item)} itens diferentes\n"
    cap += f"💰 Gold: {dados['gold']}\n\n"
    
    if not itens:
        cap += "Vazio\n"
    else:
        # Agrupa por tipo
        armas = [i for i in itens if i['tipo'] == 'arma']
        armaduras = [i for i in itens if i['tipo'] == 'armadura']
        consumiveis = [i for i in itens if i['tipo'] == 'consumivel']
        
        if armas:
            cap += "**⚔️ ARMAS:**\n"
            for item in armas[:5]:
                equipado = " ✓" if dados.get('arma_equipada') == item['id'] else ""
                cap += f"└ {item['nome']} (ATK{item['atk']}){equipado}\n"
            if len(armas) > 5:
                cap += f"└ ... e mais {len(armas)-5}\n"
            cap += "\n"
        
        if armaduras:
            cap += "**🛡️ ARMADURAS:**\n"
            for item in armaduras[:5]:
                equipado = " ✓" if dados.get('armadura_equipada') == item['id'] else ""
                cap += f"└ {item['nome']} (DEF{item['def']}){equipado}\n"
            if len(armaduras) > 5:
                cap += f"└ ... e mais {len(armaduras)-5}\n"
            cap += "\n"
        
        if consumiveis:
            cap += "**💊 CONSUMÍVEIS:**\n"
            # Agrupa consumíveis por nome
            cons_dict = {}
            for item in consumiveis:
                if item['nome'] not in cons_dict:
                    cons_dict[item['nome']] = 0
                cons_dict[item['nome']] += 1
            
            for nome, qtd in list(cons_dict.items())[:5]:
                cap += f"└ {nome} x{qtd}\n"
            if len(cons_dict) > 5:
                cap += f"└ ... e mais {len(cons_dict)-5} tipos\n"
    
    cap += f"{'━'*20}"
    
    kb = [
        [InlineKeyboardButton("⚔️ Ver Armas", callback_data="inv_armas")],
        [InlineKeyboardButton("🛡️ Ver Armaduras", callback_data="inv_armaduras")],
        [InlineKeyboardButton("💊 Ver Consumíveis", callback_data="inv_consumiveis")],
        [InlineKeyboardButton("🗑️ Descartar Item", callback_data="inv_descartar")],
        [InlineKeyboardButton("🔙 Voltar", callback_data="voltar")]
    ]
    
    try:
        await q.message.delete()
    except:
        pass
    await ctx.bot.send_photo(upd.effective_chat.id, img_c(dados['classe']), caption=cap,
                             reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def inv_armas(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    dados = get_tudo(uid)
    await q.answer()
    
    itens, _ = get_itens_jogador(uid)
    armas = [i for i in itens if i['tipo'] == 'arma']
    
    cap = f"⚔️ **ARMAS**\n{'━'*20}\n"
    kb = []
    
    for arma in armas:
        equipado = " ✓" if dados.get('arma_equipada') == arma['id'] else ""
        cap += f"🔹 {arma['nome']} (ATK{arma['atk']}){equipado}\n"
        kb.append([InlineKeyboardButton(f"⚔️ Equipar {arma['nome']}", callback_data=f"equipar_{arma['id']}")])
    
    if not armas:
        cap += "Você não tem armas!\n"
    
    kb.append([InlineKeyboardButton("🔙 Voltar", callback_data="inv")])
    cap += f"{'━'*20}"
    
    try:
        await q.message.delete()
    except:
        pass
    await ctx.bot.send_photo(upd.effective_chat.id, img_c(dados['classe']), caption=cap,
                             reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def inv_armaduras(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    dados = get_tudo(uid)
    await q.answer()
    
    itens, _ = get_itens_jogador(uid)
    armaduras = [i for i in itens if i['tipo'] == 'armadura']
    
    cap = f"🛡️ **ARMADURAS**\n{'━'*20}\n"
    kb = []
    
    for arm in armaduras:
        equipado = " ✓" if dados.get('armadura_equipada') == arm['id'] else ""
        cap += f"🔹 {arm['nome']} (DEF{arm['def']}){equipado}\n"
        kb.append([InlineKeyboardButton(f"🛡️ Equipar {arm['nome']}", callback_data=f"equipar_{arm['id']}")])
    
    if not armaduras:
        cap += "Você não tem armaduras!\n"
    
    kb.append([InlineKeyboardButton("🔙 Voltar", callback_data="inv")])
    cap += f"{'━'*20}"
    
    try:
        await q.message.delete()
    except:
        pass
    await ctx.bot.send_photo(upd.effective_chat.id, img_c(dados['classe']), caption=cap,
                             reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def inv_consumiveis(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    dados = get_tudo(uid)
    await q.answer()
    
    itens, _ = get_itens_jogador(uid)
    consumiveis = [i for i in itens if i['tipo'] == 'consumivel']
    
    # Agrupa por nome
    cons_dict = {}
    for item in consumiveis:
        if item['nome'] not in cons_dict:
            cons_dict[item['nome']] = 0
        cons_dict[item['nome']] += 1
    
    cap = f"💊 **CONSUMÍVEIS**\n{'━'*20}\n"
    kb = []
    
    for nome, qtd in cons_dict.items():
        cap += f"🔹 {nome} x{qtd}\n"
        if nome in CONSUMIVEIS:
            cons = CONSUMIVEIS[nome]
            cap += f"   └ {cons['tipo'].upper()} +{cons['valor']}\n"
    
    if not consumiveis:
        cap += "Você não tem consumíveis!\n"
    
    kb.append([InlineKeyboardButton("🔙 Voltar", callback_data="inv")])
    cap += f"{'━'*20}"
    
    try:
        await q.message.delete()
    except:
        pass
    await ctx.bot.send_photo(upd.effective_chat.id, img_c(dados['classe']), caption=cap,
                             reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def inv_descartar(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    dados = get_tudo(uid)
    await q.answer()
    
    itens, _ = get_itens_jogador(uid)
    
    if not itens:
        cap = "🗑️ **DESCARTAR**\n{'━'*20}\nVocê não tem itens para descartar!\n{'━'*20}"
        kb = [[InlineKeyboardButton("🔙 Voltar", callback_data="inv")]]
        try:
            await q.message.delete()
        except:
            pass
        await ctx.bot.send_photo(upd.effective_chat.id, img_c(dados['classe']), caption=cap,
                                 reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
        return
    
    cap = f"🗑️ **DESCARTAR ITEM**\n{'━'*20}\n⚠️ Itens descartados são perdidos!\n\n"
    kb = []
    
    for item in itens[:10]:
        emoji = "⚔️" if item['tipo'] == 'arma' else "🛡️" if item['tipo'] == 'armadura' else "💊"
        stats = f"ATK{item['atk']}" if item['atk'] > 0 else f"DEF{item['def']}" if item['def'] > 0 else ""
        cap += f"{emoji} {item['nome']} {stats}\n"
        kb.append([InlineKeyboardButton(f"🗑️ Descartar {item['nome']}", callback_data=f"descartar_{item['id']}")])
    
    if len(itens) > 10:
        cap += f"\n... e mais {len(itens)-10} itens"
    
    kb.append([InlineKeyboardButton("🔙 Voltar", callback_data="inv")])
    cap += f"{'━'*20}"
    
    try:
        await q.message.delete()
    except:
        pass
    await ctx.bot.send_photo(upd.effective_chat.id, img_c(dados['classe']), caption=cap,
                             reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def equipar(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    
    item_id = int(q.data.split('_')[1])
    
    sucesso, msg = equipar_item(uid, item_id)
    await q.answer(msg, show_alert=True)
    
    if sucesso:
        await inv(upd, ctx)

async def descartar(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    
    item_id = int(q.data.split('_')[1])
    
    sucesso, msg = descartar_item(uid, item_id)
    await q.answer(msg, show_alert=True)
    
    if sucesso:
        await inv(upd, ctx)

# ===== DUNGEONS =====
async def dungs(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    dados = get_tudo(uid)
    await q.answer()

    cap = f"🏰 **DUNGEONS**\n{'━'*20}\n"
    kb = []
    for i, d in enumerate(DUNGEONS):
        st = "✅" if dados['lv'] >= d['lv'] else f"🔒 Lv.{d['lv']}"
        cap += f"{st} {d['nome']}\n└ {d['boss']}\n└ XP: {d['xp']} | Gold: {d['g']}\n"
        if dados['lv'] >= d['lv']:
            kb.append([InlineKeyboardButton(f"🏰 {d['nome']}", callback_data=f"dung_{i}")])
    kb.append([InlineKeyboardButton("🔙 Voltar", callback_data="voltar")])
    cap += f"{'━'*20}"
    try:
        await q.message.delete()
    except:
        pass
    await ctx.bot.send_photo(upd.effective_chat.id, IMAGENS["combate"], caption=cap,
                             reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def dung(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    dados = get_tudo(uid)
    did = int(q.data.split('_')[1])
    d = DUNGEONS[did]

    if dados['energia'] < 10:
        await q.answer("🪫 10 energia!", show_alert=True)
        return

    await q.answer("🏰 Entrando...")

    p_atk = calc_atk(dados)
    p_def = calc_def(dados)
    bhp = d['bhp']
    batk = d['batk']
    php = dados['hp']
    log = []
    t = 1

    while php > 0 and bhp > 0 and t <= 15:
        dp = max(1, p_atk - 5 + random.randint(-3, 3))
        bhp -= dp
        log.append(f"↗️ T{t}: -{dp}")
        if bhp <= 0:
            break
        db = max(1, batk - p_def + random.randint(-3, 3))
        php -= db
        log.append(f"↘️ T{t}: -{db}")
        t += 1

    vit = php > 0
    php = max(1, php)

    conn = get_db_connection()
    c = conn.cursor()
    if vit:
        c.execute("UPDATE players SET gold=gold+%s, exp=exp+%s, energia=energia-10, hp=%s WHERE id=%s",
                  (d['g'], d['xp'], php, uid))
        c.execute("INSERT INTO dung (pid, did) VALUES (%s,%s) ON CONFLICT DO NOTHING", (uid, did))
        
        # Chance de drop ao vencer dungeon
        if random.random() < 0.3:  # 30% chance de drop raro
            mapa = dados['mapa']
            if mapa in DROPS_POR_MAPA:
                drops_possiveis = [d for d in DROPS_POR_MAPA[mapa] if 'Espada' in d['item'] or 'Arco' in d['item']]
                if drops_possiveis:
                    drop = random.choice(drops_possiveis)
                    item_id = criar_item_aleatorio(drop['item'], uid)
                    if item_id:
                        log.append(f"\n🎁 **Drop raro: {drop['item']}!**")
        
        res = f"🏆 **VIT!**\n💰 +{d['g']} | ✨ +{d['xp']}"
    else:
        c.execute("UPDATE players SET energia=energia-10, hp=1 WHERE id=%s", (uid,))
        res = "💀 **DERROT!**"
    conn.commit()
    invalidate_cache(uid)

    cap = (f"🏰 **{d['nome']}**\n{'━'*20}\n👹 {d['boss']}\n\n"
           f"❤️ Boss: {max(0,bhp)}/{d['bhp']}\n└ {barra_rapida(max(0,bhp),d['bhp'],'🟥')}\n\n"
           f"❤️ Você: {php}/{dados['hp_max']}\n└ {barra_rapida(php,dados['hp_max'],'🟥')}\n\n"
           f"📜:\n" + "\n".join(log[-6:]) + f"\n\n{res}\n{'━'*20}")
    kb = [[InlineKeyboardButton("🔙 Voltar", callback_data="voltar")]]
    try:
        await q.message.delete()
    except:
        pass
    await ctx.bot.send_photo(upd.effective_chat.id, img_c(dados['classe']), caption=cap,
                             reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

# ===== PERFIL =====
async def perfil(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    dados = get_tudo(uid)
    await q.answer()

    cap = (f"👤 **PERFIL**\n{'━'*20}\n"
           f"📛 {dados['nome']}\n🎭 {dados['classe']}\n⭐ Lv {dados['lv']}\n\n"
           f"❤️ {dados['hp']}/{dados['hp_max']}\n└ {barra_rapida(dados['hp'],dados['hp_max'],'🟥')}\n")
    if dados['mana_max'] > 0:
        cap += f"💙 {dados['mana']}/{dados['mana_max']}\n└ {barra_rapida(dados['mana'],dados['mana_max'],'🟦')}\n"
    cap += (f"✨ {dados['exp']}/{dados['lv']*100}\n└ {barra_rapida(dados['exp'],dados['lv']*100,'🟩')}\n\n"
            f"💰 {dados['gold']}\n⚡ {dados['energia']}/{dados['energia_max']}\n"
            f"⚔️ {calc_atk(dados)}\n🛡️ {calc_def(dados)}\n")
    if dados['crit'] > 0:
        cap += f"💥 Crítico: {dados['crit']}%\n"
    if dados['double_atk']:
        cap += f"⚡ Ataque Duplo\n"
    cap += f"{'━'*20}\n"
    
    # Mostra equipamentos atuais
    if dados.get('arma_equipada'):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT nome, atk FROM itens WHERE id = %s", (dados['arma_equipada'],))
        arma = c.fetchone()
        if arma:
            cap += f"\n⚔️ Equipado: {arma[0]} (ATK{arma[1]})"
    
    if dados.get('armadura_equipada'):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT nome, def FROM itens WHERE id = %s", (dados['armadura_equipada'],))
        arm = c.fetchone()
        if arm:
            cap += f"\n🛡️ Equipado: {arm[0]} (DEF{arm[1]})"

    kb = [[InlineKeyboardButton("🔙 Voltar", callback_data="voltar")]]
    try:
        await q.message.delete()
    except:
        pass
    await ctx.bot.send_photo(upd.effective_chat.id, img_c(dados['classe']), caption=cap,
                             reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

# ===== CONFIG =====
async def cfg(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    dados = get_tudo(uid)
    await q.answer()
    cap = f"⚙️ **CONFIG**\n{'━'*20}\n🔄 Reset\n⚡ Lv MAX\n💰 Gold MAX\n{'━'*20}"
    kb = [
        [InlineKeyboardButton("🔄 Reset", callback_data="rst_c")],
        [InlineKeyboardButton("⚡ Lv MAX", callback_data="ch_lv")],
        [InlineKeyboardButton("💰 Gold MAX", callback_data="ch_g")],
        [InlineKeyboardButton("🔙 Voltar", callback_data="voltar")]
    ]
    try:
        await q.message.delete()
    except:
        pass
    await ctx.bot.send_photo(upd.effective_chat.id, img_c(dados['classe']), caption=cap,
                             reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def rst_c(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    dados = get_tudo(uid)
    await q.answer()
    cap = f"⚠️ **DELETAR?**\n{'━'*20}\n❌ IRREVERSÍVEL\n{'━'*20}"
    kb = [
        [InlineKeyboardButton("✅ SIM", callback_data="rst_y")],
        [InlineKeyboardButton("❌ NÃO", callback_data="cfg")]
    ]
    try:
        await q.message.delete()
    except:
        pass
    await ctx.bot.send_photo(upd.effective_chat.id, img_c(dados['classe']), caption=cap,
                             reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def rst_y(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    invalidate_cache(uid)
    del_p(uid)
    await q.answer("✅ Personagem deletado!", show_alert=True)

    cap = (f"🎭 **ESCOLHA SUA CLASSE**\n{'━'*20}\n\n"
           f"🛡️ **Guerreiro**\n└ HP Alto | Defesa Máxima\n└ ❤️ 200 HP | 🛡️ 25 DEF\n\n"
           f"🏹 **Arqueiro**\n└ Crítico | Ataque Duplo\n└ ❤️ 140 HP | 💥 25% CRIT\n\n"
           f"🔮 **Bruxa**\n└ Maldição | Dano Mágico\n└ ❤️ 160 HP | 💙 120 MANA\n\n"
           f"🔥 **Mago**\n└ Explosão | Poder Máximo\n└ ❤️ 120 HP | 💙 150 MANA\n{'━'*20}")
    kb = [
        [InlineKeyboardButton("🛡️ Guerreiro", callback_data="Guerreiro"),
         InlineKeyboardButton("🏹 Arqueiro", callback_data="Arqueiro")],
        [InlineKeyboardButton("🔮 Bruxa", callback_data="Bruxa"),
         InlineKeyboardButton("🔥 Mago", callback_data="Mago")]
    ]
    try:
        await q.message.delete()
    except:
        pass
    await ctx.bot.send_photo(upd.effective_chat.id, IMAGENS["sel"], caption=cap,
                             reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    return ST_NM

async def ch_lv(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    dados = get_tudo(uid)

    conn = get_db_connection()
    c = conn.cursor()
    hp_max = CLASSE_STATS[dados['classe']]['hp'] * 10
    mana_max = CLASSE_STATS[dados['classe']]['mana'] * 10 if CLASSE_STATS[dados['classe']]['mana'] > 0 else 0
    c.execute("UPDATE players SET lv=99, exp=0, hp_max=%s, hp=%s, mana_max=%s, mana=%s, energia_max=999, energia=999 WHERE id=%s",
              (hp_max, hp_max, mana_max, mana_max, uid))
    conn.commit()
    invalidate_cache(uid)
    await q.answer("⚡ 99!", show_alert=True)
    await menu(upd, ctx, uid, "⚡ **Lv 99!**")

async def ch_g(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE players SET gold=999999 WHERE id=%s", (uid,))
    conn.commit()
    invalidate_cache(uid)
    await q.answer("💰 999,999!", show_alert=True)
    await menu(upd, ctx, uid, "💰 **999,999!**")

async def voltar(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM combate WHERE pid=%s", (uid,))
    conn.commit()
    invalidate_cache(uid)
    await q.answer()
    await menu(upd, ctx, uid)

# ===== INÍCIO / CRIAÇÃO DE PERSONAGEM =====
async def start(upd, ctx):
    ctx.user_data.clear()
    cap = (f"✨ **AVENTURA RABISCADA** ✨\n{'━'*20}\n"
           f"Versão: `{VERSAO}`\n\n"
           f"🎮 **BEM-VINDO!**\n⚔️ Combate Manual\n🎭 Classes Únicas\n"
           f"💊 Sistema de Consumíveis\n🔮 Habilidades Especiais\n💙 Sistema de Mana\n"
           f"🎁 Drops de Itens\n🏕️ Sistema de Descanso\n{'━'*20}")
    kb = [[InlineKeyboardButton("🎮 Começar", callback_data="ir_cls")]]

    uid = upd.effective_user.id
    jogador = get_tudo(uid)

    if jogador:
        await menu(upd, ctx, uid, "🔄 Bem-vindo de volta!")
        return ConversationHandler.END

    await upd.message.reply_photo(IMAGENS["logo"], caption=cap,
                                  reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    return ST_CL

async def menu_cls(upd, ctx):
    q = upd.callback_query
    await q.answer()
    cap = (f"🎭 **ESCOLHA SUA CLASSE**\n{'━'*20}\n\n"
           f"🛡️ **Guerreiro**\n└ HP Alto | Defesa Máxima\n└ ❤️ 200 HP | 🛡️ 25 DEF\n\n"
           f"🏹 **Arqueiro**\n└ Crítico | Ataque Duplo\n└ ❤️ 140 HP | 💥 25% CRIT\n\n"
           f"🔮 **Bruxa**\n└ Maldição | Dano Mágico\n└ ❤️ 160 HP | 💙 120 MANA\n\n"
           f"🔥 **Mago**\n└ Explosão | Poder Máximo\n└ ❤️ 120 HP | 💙 150 MANA\n{'━'*20}")
    kb = [
        [InlineKeyboardButton("🛡️ Guerreiro", callback_data="Guerreiro"),
         InlineKeyboardButton("🏹 Arqueiro", callback_data="Arqueiro")],
        [InlineKeyboardButton("🔮 Bruxa", callback_data="Bruxa"),
         InlineKeyboardButton("🔥 Mago", callback_data="Mago")]
    ]
    try:
        await q.message.delete()
    except:
        pass
    await ctx.bot.send_photo(upd.effective_chat.id, IMAGENS["sel"], caption=cap,
                             reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
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
    if stats.get('especial'):
        cap += f"🌟 {stats['especial'].title()}\n"
    cap += f"{'━'*20}\n📝 **Digite seu nome:**"

    try:
        await q.message.delete()
    except:
        pass
    await ctx.bot.send_photo(upd.effective_chat.id, img_c(q.data), caption=cap, parse_mode='Markdown')
    return ST_NM

async def fin(upd, ctx):
    uid = upd.effective_user.id
    nome = upd.message.text.strip()

    if not nome or len(nome) > 30:
        await upd.message.reply_text("❌ Nome inválido! Digite um nome entre 1 e 30 caracteres.")
        return ST_NM

    classe = ctx.user_data.get('classe', 'Guerreiro')
    stats = CLASSE_STATS[classe]

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""INSERT INTO players
                (id, nome, classe, hp, hp_max, mana, mana_max, lv, exp, gold,
                 energia, energia_max, mapa, local, arma_equipada, armadura_equipada, crit, double_atk)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (id) DO UPDATE SET
                nome=EXCLUDED.nome, classe=EXCLUDED.classe, hp=EXCLUDED.hp, hp_max=EXCLUDED.hp_max,
                mana=EXCLUDED.mana, mana_max=EXCLUDED.mana_max, lv=EXCLUDED.lv, exp=EXCLUDED.exp,
                gold=EXCLUDED.gold, energia=EXCLUDED.energia, energia_max=EXCLUDED.energia_max,
                mapa=EXCLUDED.mapa, local=EXCLUDED.local, arma_equipada=EXCLUDED.arma_equipada,
                armadura_equipada=EXCLUDED.armadura_equipada, crit=EXCLUDED.crit, double_atk=EXCLUDED.double_atk""",
              (uid, nome, classe, stats['hp'], stats['hp'], stats['mana'], stats['mana'],
               1, 0, 100, 20, 20, 1, 'cap', None, None,
               stats['crit'], 1 if stats['double'] else 0))
    conn.commit()
    invalidate_cache(uid)

    await upd.message.reply_text(f"✨ **{nome}** criado!\nBem-vindo, {classe}! 🎮", parse_mode='Markdown')
    await menu(upd, ctx, uid)
    return ConversationHandler.END

def main():
    init_db()
    token = os.getenv("TELEGRAM_TOKEN")

    try:
        requests.get(f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true", timeout=5)
    except:
        pass

    t = threading.Thread(target=run_fake_server, daemon=True)
    t.start()

    app = ApplicationBuilder().token(token).request(request).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ST_CL: [CallbackQueryHandler(menu_cls, pattern='^ir_cls$')],
            ST_NM: [
                CallbackQueryHandler(salv_nm, pattern='^(Guerreiro|Arqueiro|Bruxa|Mago)$'),
                MessageHandler(filters.TEXT & ~filters.COMMAND, fin)
            ]
        },
        fallbacks=[CommandHandler('start', start)]
    )

    # Handlers de combate
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
    
    # Handlers de mapa e locais
    app.add_handler(CallbackQueryHandler(mapas, pattern='^mapas$'))
    app.add_handler(CallbackQueryHandler(viajar, pattern='^via_'))
    app.add_handler(CallbackQueryHandler(locais, pattern='^locais$'))
    app.add_handler(CallbackQueryHandler(ir_loc, pattern='^iloc_'))
    
    # Handlers de descanso
    app.add_handler(CallbackQueryHandler(descansar, pattern='^descansar_'))
    
    # Handlers de loja
    app.add_handler(CallbackQueryHandler(perfil, pattern='^perfil$'))
    app.add_handler(CallbackQueryHandler(loja, pattern='^loja$'))
    app.add_handler(CallbackQueryHandler(loja_normal, pattern='^loja_normal$'))
    app.add_handler(CallbackQueryHandler(loja_contra, pattern='^loja_contra$'))
    app.add_handler(CallbackQueryHandler(loja_vender, pattern='^loja_vender$'))
    app.add_handler(CallbackQueryHandler(comprar_item, pattern='^comprar_'))
    app.add_handler(CallbackQueryHandler(vender_item, pattern='^vender_'))
    
    # Handlers de inventário
    app.add_handler(CallbackQueryHandler(inv, pattern='^inv$'))
    app.add_handler(CallbackQueryHandler(inv_armas, pattern='^inv_armas$'))
    app.add_handler(CallbackQueryHandler(inv_armaduras, pattern='^inv_armaduras$'))
    app.add_handler(CallbackQueryHandler(inv_consumiveis, pattern='^inv_consumiveis$'))
    app.add_handler(CallbackQueryHandler(inv_descartar, pattern='^inv_descartar$'))
    app.add_handler(CallbackQueryHandler(equipar, pattern='^equipar_'))
    app.add_handler(CallbackQueryHandler(descartar, pattern='^descartar_'))
    
    # Handlers de dungeon
    app.add_handler(CallbackQueryHandler(dungs, pattern='^dungs$'))
    app.add_handler(CallbackQueryHandler(dung, pattern='^dung_'))
    
    # Handlers de configuração
    app.add_handler(CallbackQueryHandler(cfg, pattern='^cfg$'))
    app.add_handler(CallbackQueryHandler(rst_c, pattern='^rst_c$'))
    app.add_handler(CallbackQueryHandler(rst_y, pattern='^rst_y$'))
    app.add_handler(CallbackQueryHandler(ch_lv, pattern='^ch_lv$'))
    app.add_handler(CallbackQueryHandler(ch_g, pattern='^ch_g$'))
    app.add_handler(CallbackQueryHandler(menu_cls, pattern='^ir_cls$'))
    app.add_handler(CallbackQueryHandler(voltar, pattern='^voltar$'))

    logging.info(f"Bot {VERSAO} iniciado com sistema de itens e descanso!")
    app.run_polling(drop_pending_updates=True, poll_interval=0.5, timeout=10)

if __name__ == '__main__':
    main()
