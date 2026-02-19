import os, random, logging, threading, psycopg2, asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse
from telegram.request import HTTPXRequest
from cachetools import TTLCache
import datetime
import requests

VERSAO = "7.1.0 - equilibrio"

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
    }
}

CLASSE_STATS = {
    "Guerreiro": {"hp": 180, "mana": 0, "atk": 7, "def": 10, "crit": 0, "double": False, "especial": None},
    "Arqueiro": {"hp": 130, "mana": 0, "atk": 9, "def": 6, "crit": 25, "double": True, "especial": None},
    "Bruxa": {"hp": 140, "mana": 100, "atk": 8, "def": 7, "crit": 10, "double": False, "especial": "maldição"},
    "Mago": {"hp": 120, "mana": 120, "atk": 10, "def": 5, "crit": 15, "double": False, "especial": "explosão"}
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

INIMIGOS = {
    # ===== PLANÍCIE (FÁCIL) =====
    "Goblin da Planície": {"hp": 60, "atk": 8, "def": 3, "xp": 15, "gold": 8, "desc": "Goblin verde", "m": [1], "tipo": "Goblin"},
    "Lobo da Planície": {"hp": 80, "atk": 10, "def": 4, "xp": 20, "gold": 12, "desc": "Lobo selvagem", "m": [1], "tipo": "Lobo"},
    "Orc da Planície": {"hp": 120, "atk": 14, "def": 6, "xp": 30, "gold": 20, "desc": "Orc guerreiro", "m": [1, 2], "tipo": "Orc"},
    "Esqueleto da Planície": {"hp": 100, "atk": 12, "def": 5, "xp": 25, "gold": 15, "desc": "Esqueleto guerreiro", "m": [1, 2], "tipo": "Esqueleto"},
    "Dragão da Planície": {"hp": 200, "atk": 18, "def": 8, "xp": 50, "gold": 40, "desc": "Dragão jovem", "m": [1], "tipo": "Dragão"},
    
    # ===== FLORESTA (MÉDIO) =====
    "Goblin da Floresta": {"hp": 180, "atk": 22, "def": 10, "xp": 45, "gold": 25, "desc": "Goblin feroz", "m": [2], "tipo": "Goblin"},
    "Lobo da Floresta": {"hp": 250, "atk": 28, "def": 14, "xp": 60, "gold": 35, "desc": "Lobo alfa", "m": [2], "tipo": "Lobo"},
    "Orc da Floresta": {"hp": 350, "atk": 35, "def": 18, "xp": 90, "gold": 55, "desc": "Orc berserker", "m": [2, 3], "tipo": "Orc"},
    "Esqueleto da Floresta": {"hp": 300, "atk": 32, "def": 16, "xp": 75, "gold": 45, "desc": "Esqueleto ancestral", "m": [2, 3], "tipo": "Esqueleto"},
    "Dragão da Floresta": {"hp": 500, "atk": 45, "def": 22, "xp": 150, "gold": 120, "desc": "Dragão ancestral", "m": [2], "tipo": "Dragão"},
    
    # ===== CAVERNA (DIFÍCIL) =====
    "Goblin da Caverna": {"hp": 400, "atk": 48, "def": 24, "xp": 120, "gold": 70, "desc": "Goblin sombrio", "m": [3], "tipo": "Goblin"},
    "Lobo da Caverna": {"hp": 550, "atk": 60, "def": 30, "xp": 160, "gold": 95, "desc": "Lobo das sombras", "m": [3], "tipo": "Lobo"},
    "Orc da Caverna": {"hp": 750, "atk": 75, "def": 38, "xp": 240, "gold": 140, "desc": "Orc brutal", "m": [3], "tipo": "Orc"},
    "Esqueleto da Caverna": {"hp": 650, "atk": 68, "def": 34, "xp": 200, "gold": 120, "desc": "Esqueleto rei", "m": [3], "tipo": "Esqueleto"},
    "Dragão da Caverna": {"hp": 1200, "atk": 90, "def": 45, "xp": 400, "gold": 300, "desc": "Dragão primordial", "m": [3], "tipo": "Dragão"}
}
EQUIPS = {
    # ===== GUERREIRO =====
    "Espada Enferrujada": {"t": "arma", "atk": 3, "p": 50, "lv": 1, "cls": ["Guerreiro"]},
    "Espada de Ferro": {"t": "arma", "atk": 10, "p": 200, "lv": 5, "cls": ["Guerreiro"]},
    "Espada de Aço": {"t": "arma", "atk": 22, "p": 500, "lv": 10, "cls": ["Guerreiro"]},
    "Escudo de Madeira": {"t": "arm", "def": 4, "p": 50, "lv": 1, "cls": ["Guerreiro"]},
    "Escudo de Ferro": {"t": "arm", "def": 12, "p": 200, "lv": 5, "cls": ["Guerreiro"]},
    "Escudo de Aço": {"t": "arm", "def": 22, "p": 500, "lv": 10, "cls": ["Guerreiro"]},
    
    # ===== ARQUEIRO =====
    "Arco Simples": {"t": "arma", "atk": 4, "p": 50, "lv": 1, "cls": ["Arqueiro"]},
    "Arco Composto": {"t": "arma", "atk": 11, "p": 200, "lv": 5, "cls": ["Arqueiro"]},
    "Arco Élfico": {"t": "arma", "atk": 24, "p": 500, "lv": 10, "cls": ["Arqueiro"]},
    "Armadura Leve": {"t": "arm", "def": 3, "p": 50, "lv": 1, "cls": ["Arqueiro"]},
    "Couro Reforçado": {"t": "arm", "def": 9, "p": 200, "lv": 5, "cls": ["Arqueiro"]},
    "Manto Sombrio": {"t": "arm", "def": 18, "p": 500, "lv": 10, "cls": ["Arqueiro"]},
    
    # ===== BRUXA =====
    "Cajado Antigo": {"t": "arma", "atk": 3, "p": 50, "lv": 1, "cls": ["Bruxa"]},
    "Cetro Lunar": {"t": "arma", "atk": 10, "p": 200, "lv": 5, "cls": ["Bruxa"]},
    "Varinha das Trevas": {"t": "arma", "atk": 22, "p": 500, "lv": 10, "cls": ["Bruxa"]},
    "Robe Místico": {"t": "arm", "def": 4, "p": 50, "lv": 1, "cls": ["Bruxa"]},
    "Manto Encantado": {"t": "arm", "def": 11, "p": 200, "lv": 5, "cls": ["Bruxa"]},
    "Vestes Arcanas": {"t": "arm", "def": 20, "p": 500, "lv": 10, "cls": ["Bruxa"]},
    
    # ===== MAGO =====
    "Bastão Iniciante": {"t": "arma", "atk": 4, "p": 50, "lv": 1, "cls": ["Mago"]},
    "Orbe de Fogo": {"t": "arma", "atk": 12, "p": 200, "lv": 5, "cls": ["Mago"]},
    "Cetro do Caos": {"t": "arma", "atk": 25, "p": 500, "lv": 10, "cls": ["Mago"]},
    "Túnica Simples": {"t": "arm", "def": 3, "p": 50, "lv": 1, "cls": ["Mago"]},
    "Armadura Mágica": {"t": "arm", "def": 9, "p": 200, "lv": 5, "cls": ["Mago"]},
    "Robe do Arquimago": {"t": "arm", "def": 18, "p": 500, "lv": 10, "cls": ["Mago"]}
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

ST_CL, ST_NM = range(2)

# ===== BANCO =====
def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS players (
                 id BIGINT PRIMARY KEY, nome TEXT, classe TEXT,
                 hp INTEGER, hp_max INTEGER,
                 mana INTEGER DEFAULT 0, mana_max INTEGER DEFAULT 0,
                 lv INTEGER, exp INTEGER, gold INTEGER,
                 energia INTEGER, energia_max INTEGER,
                 mapa INTEGER DEFAULT 1, local TEXT DEFAULT 'cap',
                 arma TEXT, arm TEXT,
                 atk_b INTEGER DEFAULT 0, def_b INTEGER DEFAULT 0,
                 crit INTEGER DEFAULT 0, double_atk INTEGER DEFAULT 0)''')
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

# ===== QUERY UNIFICADA - CORAÇÃO DO SISTEMA =====
def get_tudo(uid):
    """Busca player + combate + inventário em 1 única query. Núcleo da otimização."""
    if uid in player_cache:
        return player_cache[uid]
    
    conn = get_db_connection()
    c = conn.cursor(cursor_factory=RealDictCursor)
    c.execute("""
        SELECT 
            p.*,
            cb.inimigo, cb.i_hp, cb.i_hp_max, cb.i_atk, cb.i_def,
            cb.i_xp, cb.i_gold, cb.turno, cb.defendendo, cb.heroi,
            cb.tipo_monstro, cb.mapa_monstro,
            COALESCE(
                (SELECT json_object_agg(item, qtd) FROM inv WHERE pid = p.id),
                '{}'::json
            ) as inventario
        FROM players p
        LEFT JOIN combate cb ON cb.pid = p.id
        WHERE p.id = %s
    """, (uid,))
    row = c.fetchone()
    if row:
        player_cache[uid] = dict(row)
    return dict(row) if row else None

def get_p(uid):
    conn = get_db_connection()
    c = conn.cursor(cursor_factory=RealDictCursor)
    c.execute("SELECT * FROM players WHERE id = %s", (uid,))
    return c.fetchone()

def get_inv(uid):
    conn = get_db_connection()
    c = conn.cursor(cursor_factory=RealDictCursor)
    c.execute("SELECT * FROM inv WHERE pid = %s", (uid,))
    return {i['item']: i['qtd'] for i in c.fetchall()}

def add_inv(uid, item, qtd=1):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""INSERT INTO inv (pid, item, qtd) VALUES (%s, %s, %s)
                 ON CONFLICT (pid, item) DO UPDATE SET qtd = inv.qtd + %s""",
              (uid, item, qtd, qtd))
    conn.commit()

def use_inv(uid, item):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE inv SET qtd = qtd - 1 WHERE pid = %s AND item = %s", (uid, item))
    c.execute("DELETE FROM inv WHERE qtd <= 0")
    conn.commit()

def del_p(uid):
    invalidate_cache(uid)
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM heroi_oferta WHERE pid = %s", (uid,))
    c.execute("DELETE FROM combate WHERE pid = %s", (uid,))
    c.execute("DELETE FROM dung WHERE pid = %s", (uid,))
    c.execute("DELETE FROM inv WHERE pid = %s", (uid,))
    c.execute("DELETE FROM players WHERE id = %s", (uid,))
    conn.commit()

def img_c(cl):
    return IMAGENS["classes"].get(cl, IMG)

def calc_atk(dados):
    return CLASSE_STATS[dados['classe']]['atk'] + (dados['lv'] * 8) + dados['atk_b']  # 3 → 8

def calc_def(dados):
    return CLASSE_STATS[dados['classe']]['def'] + (dados['lv'] * 5) + dados['def_b']  # 2 → 5

# ===== MONTA TELA DE COMBATE (sem queries) =====
def montar_cap_combate(dados):
    inv_data = dados.get('inventario') or {}
    if isinstance(inv_data, str):
        import json
        inv_data = json.loads(inv_data)

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

    cons_hp = []
    if inv_data.get("Poção de Vida", 0) > 0:
        cons_hp.append(InlineKeyboardButton(f"💊 Poção HP ({inv_data['Poção de Vida']})", callback_data="bat_pot_hp"))
    if inv_data.get("Poção Grande de Vida", 0) > 0:
        cons_hp.append(InlineKeyboardButton(f"💊+ Grande ({inv_data['Poção Grande de Vida']})", callback_data="bat_pot_hp2"))
    if cons_hp:
        kb.append(cons_hp)

    if dados['mana_max'] > 0:
        cons_mp = []
        if inv_data.get("Poção de Mana", 0) > 0:
            cons_mp.append(InlineKeyboardButton(f"🔵 Mana ({inv_data['Poção de Mana']})", callback_data="bat_pot_mp"))
        if inv_data.get("Elixir de Mana", 0) > 0:
            cons_mp.append(InlineKeyboardButton(f"🔵+ Elixir ({inv_data['Elixir de Mana']})", callback_data="bat_pot_mp2"))
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
    """Exibe tela de combate com dados já em memória - ZERO queries extras."""
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

    # Já tem combate ativo?
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

    # 5% chance de herói
    if random.random() < 0.05:
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

    # Monta dados em memória sem nova query
    dados.update({
        'inimigo': inm, 'i_hp': ini['hp'], 'i_hp_max': ini['hp'],
        'i_atk': ini['atk'], 'i_def': ini['def'], 'i_xp': ini['xp'],
        'i_gold': ini['gold'], 'turno': 1, 'defendendo': 0, 'heroi': None,
        'tipo_monstro': ini['tipo'], 'mapa_monstro': dados['mapa'],
        'energia': dados['energia'] - 2, 'inventario': dados.get('inventario', {})
    })
    await exibir_combate(upd, ctx, dados)

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
    await q.answer("⚔️!")  # Responde imediatamente ao Telegram

    conn = get_db_connection()
    c = conn.cursor(cursor_factory=RealDictCursor)

    # 1 QUERY: lê tudo junto
    c.execute("""
        SELECT p.*, cb.inimigo, cb.i_hp, cb.i_hp_max, cb.i_atk, cb.i_def,
               cb.i_xp, cb.i_gold, cb.turno, cb.defendendo, cb.heroi,
               cb.tipo_monstro, cb.mapa_monstro,
               COALESCE((SELECT json_object_agg(item, qtd) FROM inv WHERE pid = p.id), '{}'::json) as inventario
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
        dano = max(1, p_atk - dados['i_def'] + random.randint(-2, 2))
        if is_crit:
            dano = int(dano * 1.5)
        i_hp -= dano
        log.append(f"{'💥 CRÍTICO' if is_crit else '⚔️ Você'}! -{dano} HP")
        if i_hp <= 0:
            break

    resultado = None

    if i_hp <= 0:
        p_hp = max(1, p_hp)
        c.execute("UPDATE players SET hp=%s, gold=gold+%s, exp=exp+%s WHERE id=%s",
                  (p_hp, dados['i_gold'], dados['i_xp'], uid))
        c.execute("DELETE FROM combate WHERE pid=%s", (uid,))
        resultado = "vitoria"
    else:
        def_bonus = 0.5 if dados['defendendo'] else 0
        dano_ini = max(1, int((dados['i_atk'] - p_def) * (1 - def_bonus) + random.randint(-2, 2)))
        p_hp -= dano_ini
        log.append(f"🐺 {dados['inimigo']} atacou! -{dano_ini} HP")

        if p_hp <= 0:
            c.execute("UPDATE players SET hp=1 WHERE id=%s", (uid,))
            c.execute("DELETE FROM combate WHERE pid=%s", (uid,))
            resultado = "derrota"
        else:
            c.execute("UPDATE combate SET i_hp=%s, turno=turno+1, defendendo=0 WHERE pid=%s", (i_hp, uid))
            c.execute("UPDATE players SET hp=%s WHERE id=%s", (p_hp, uid))
            resultado = "continua"

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
               cb.tipo_monstro, cb.mapa_monstro,
               COALESCE((SELECT json_object_agg(item, qtd) FROM inv WHERE pid = p.id), '{}'::json) as inventario
        FROM players p
        JOIN combate cb ON cb.pid = p.id
        WHERE p.id = %s
    """, (uid,))
    dados = c.fetchone()
    if not dados:
        return
    dados = dict(dados)

    c.execute("UPDATE combate SET defendendo=1, turno=turno+1 WHERE pid=%s", (uid,))
    conn.commit()
    invalidate_cache(uid)

    dados['defendendo'] = 1
    dados['turno'] = dados['turno'] + 1
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
               cb.tipo_monstro, cb.mapa_monstro,
               COALESCE((SELECT json_object_agg(item, qtd) FROM inv WHERE pid = p.id), '{}'::json) as inventario
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
    i_hp = dados['i_hp']

    if esp == "maldição" and dados['mana'] >= 20:
        dano = int(p_atk * 1.3)
        i_hp -= dano
        c.execute("""UPDATE combate SET i_hp=%s,
                     i_def=GREATEST(i_def-3,0), turno=turno+1, defendendo=0
                     WHERE pid=%s""", (i_hp, uid))
        c.execute("UPDATE players SET mana=mana-20 WHERE id=%s", (uid,))
        await q.answer(f"🔮 Maldição! -{dano} HP")
        dados['mana'] -= 20

    elif esp == "explosão" and dados['mana'] >= 30:
        dano_max = int(dados['i_hp_max'] * 0.25)
        dano = min(dano_max, int(p_atk * 1.5))
        i_hp -= dano
        c.execute("UPDATE combate SET i_hp=%s, turno=turno+1, defendendo=0 WHERE pid=%s", (i_hp, uid))
        c.execute("UPDATE players SET mana=mana-30 WHERE id=%s", (uid,))
        await q.answer(f"🔥 Explosão! -{dano} HP (25% máx)")
        dados['mana'] -= 30
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
               cb.tipo_monstro, cb.mapa_monstro,
               COALESCE((SELECT json_object_agg(item, qtd) FROM inv WHERE pid = p.id), '{}'::json) as inventario
        FROM players p
        JOIN combate cb ON cb.pid = p.id
        WHERE p.id = %s
    """, (uid,))
    dados = c.fetchone()
    if not dados:
        return
    dados = dict(dados)

    import json
    inv_data = dados.get('inventario') or {}
    if isinstance(inv_data, str):
        inv_data = json.loads(inv_data)

    if inv_data.get(item, 0) <= 0:
        await q.answer("Sem item!", show_alert=True)
        return

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

    # Consome item e inimigo contra-ataca
    c.execute("UPDATE inv SET qtd=qtd-1 WHERE pid=%s AND item=%s", (uid, item))
    c.execute("DELETE FROM inv WHERE qtd<=0")

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
    # Atualiza inventário em memória
    inv_data[item] = inv_data.get(item, 1) - 1
    dados['inventario'] = inv_data
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
        c.execute("""SELECT p.hp, p.hp_max, p.classe, p.lv, p.def_b,
                            cb.i_atk, cb.i_hp, cb.i_hp_max, cb.inimigo,
                            cb.i_def, cb.i_xp, cb.i_gold, cb.turno, cb.defendendo,
                            cb.heroi, cb.tipo_monstro, cb.mapa_monstro,
                            p.mana, p.mana_max, p.crit, p.double_atk, p.atk_b,
                            COALESCE((SELECT json_object_agg(item,qtd) FROM inv WHERE pid=p.id),'{}'::json) as inventario
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
        cap += f"🏠 {loc['nome']}{at}{lj}\n"
        kb.append([InlineKeyboardButton(f"📍 {loc['nome']}", callback_data=f"iloc_{lid}")])
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
    cap += f"{'━'*20}"
    kb = [[InlineKeyboardButton("🔙 Menu", callback_data="voltar")]]
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
           f"🏴‍☠️ **Mercado Negro**\n└ 💰 -30% preços\n└ ⚠️ 5% chance de roubo\n{'━'*20}")
    kb = [
        [InlineKeyboardButton("🏪 Loja Normal", callback_data="loja_normal")],
        [InlineKeyboardButton("🏴‍☠️ Mercado Negro", callback_data="loja_contra")],
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
    cap = f"🏪 **LOJA - {loc['nome']}**\n{'━'*20}\n💰 {dados['gold']}\n\n**⚔️ EQUIPAMENTOS:**\n"
    kb = []

    for n, eq in EQUIPS.items():
        if dados['classe'] not in eq['cls']:
            continue
        pf = eq['p']
        st = "✅" if dados['lv'] >= eq['lv'] else f"🔒 Lv.{eq['lv']}"
        em = "⚔️" if eq['t'] == "arma" else "🛡️"
        stat = f"+{eq.get('atk', eq.get('def'))}"
        cap += f"{st} {em} {n} {stat}\n└ 💰 {pf}\n"
        if dados['lv'] >= eq['lv'] and dados['gold'] >= pf:
            kb.append([InlineKeyboardButton(f"💰 {n}", callback_data=f"comp_normal_{n}")])

    cap += "\n**💊 CONSUMÍVEIS:**\n"
    for n, cs in CONSUMIVEIS.items():
        if cs['tipo'] == 'mana' and dados['mana_max'] == 0:
            continue
        pf = cs['preco']
        cap += f"💊 {n} ({cs['tipo'].upper()} +{cs['valor']})\n└ 💰 {pf}\n"
        if dados['gold'] >= pf:
            kb.append([InlineKeyboardButton(f"💊 {n}", callback_data=f"comp_normal_{n}")])

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

    for n, eq in EQUIPS.items():
        if dados['classe'] not in eq['cls']:
            continue
        pf = int(eq['p'] * 0.7)
        st = "✅" if dados['lv'] >= eq['lv'] else f"🔒 Lv.{eq['lv']}"
        em = "⚔️" if eq['t'] == "arma" else "🛡️"
        stat = f"+{eq.get('atk', eq.get('def'))}"
        cap += f"{st} {em} {n} {stat}\n└ 💰 ~~{eq['p']}~~ {pf}\n"
        if dados['lv'] >= eq['lv'] and dados['gold'] >= pf:
            kb.append([InlineKeyboardButton(f"💰 {n}", callback_data=f"comp_contra_{n}")])

    cap += "\n**💊 CONSUMÍVEIS:**\n"
    for n, cs in CONSUMIVEIS.items():
        if cs['tipo'] == 'mana' and dados['mana_max'] == 0:
            continue
        pf = int(cs['preco'] * 0.7)
        cap += f"💊 {n} ({cs['tipo'].upper()} +{cs['valor']})\n└ 💰 ~~{cs['preco']}~~ {pf}\n"
        if dados['gold'] >= pf:
            kb.append([InlineKeyboardButton(f"💊 {n}", callback_data=f"comp_contra_{n}")])

    kb.append([InlineKeyboardButton("🔙 Voltar", callback_data="loja")])
    cap += f"{'━'*20}"

    img_contra = IMAGENS["contrabandistas"].get(dados['mapa'], IMAGENS["classes"]["Guerreiro"])
    try:
        await q.message.delete()
    except:
        pass
    await ctx.bot.send_photo(upd.effective_chat.id, img_contra, caption=cap,
                             reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def comprar(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    dados = get_tudo(uid)

    parts = q.data.split('_')
    tipo_loja = parts[1]
    item = '_'.join(parts[2:])
    desconto = 0.7 if tipo_loja == "contra" else 1.0

    if item in EQUIPS:
        eq = EQUIPS[item]
        preco = int(eq['p'] * desconto)
        if dados['gold'] < preco:
            await q.answer("💸 Sem gold!", show_alert=True)
            return
        if tipo_loja == "contra" and random.random() < 0.05:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("UPDATE players SET gold=gold-%s WHERE id=%s", (preco, uid))
            conn.commit()
            invalidate_cache(uid)
            await q.answer("🏴‍☠️ Roubado!", show_alert=True)
            await loja(upd, ctx)
            return
        conn = get_db_connection()
        c = conn.cursor()
        if eq['t'] == "arma":
            c.execute("UPDATE players SET gold=gold-%s, arma=%s, atk_b=%s WHERE id=%s",
                      (preco, item, eq['atk'], uid))
        else:
            c.execute("UPDATE players SET gold=gold-%s, arm=%s, def_b=%s WHERE id=%s",
                      (preco, item, eq['def'], uid))
        conn.commit()
        invalidate_cache(uid)
        await q.answer(f"✅ {item}!", show_alert=True)
        await menu(upd, ctx, uid, f"✅ **{item}!**")

    elif item in CONSUMIVEIS:
        cons = CONSUMIVEIS[item]
        preco = int(cons['preco'] * desconto)
        img_pocao = IMAGENS["elixir"].get(item, IMAGENS["elixir"]["Poção de Vida"])
        cap = (f"💊 **{item}**\n{'━'*20}\n🔮 {cons['tipo'].upper()} +{cons['valor']}\n💰 {preco} Gold\n"
               + (f"\n⚠️ Contrabandista\n└ 5% chance de roubo\n" if tipo_loja == "contra" else "")
               + f"\n**Confirmar compra?**\n{'━'*20}")
        kb = [
            [InlineKeyboardButton("✅ Comprar", callback_data=f"conf_{tipo_loja}_{item}")],
            [InlineKeyboardButton("❌ Cancelar", callback_data=f"loja_{tipo_loja}")]
        ]
        try:
            await q.message.delete()
        except:
            pass
        await ctx.bot.send_photo(upd.effective_chat.id, img_pocao, caption=cap,
                                 reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def confirmar_compra(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    dados = get_tudo(uid)

    parts = q.data.split('_')
    tipo_loja = parts[1]
    item = '_'.join(parts[2:])
    cons = CONSUMIVEIS[item]
    desconto = 0.7 if tipo_loja == "contra" else 1.0
    preco = int(cons['preco'] * desconto)

    if dados['gold'] < preco:
        await q.answer("💸 Sem gold!", show_alert=True)
        return

    if tipo_loja == "contra" and random.random() < 0.05:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("UPDATE players SET gold=gold-%s WHERE id=%s", (preco, uid))
        conn.commit()
        invalidate_cache(uid)
        await q.answer("🏴‍☠️ Roubado!", show_alert=True)
        await loja(upd, ctx)
        return

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE players SET gold=gold-%s WHERE id=%s", (preco, uid))
    conn.commit()
    add_inv(uid, item, 1)
    invalidate_cache(uid)
    await q.answer(f"✅ {item}!", show_alert=True)

    if tipo_loja == "normal":
        await loja_normal(upd, ctx)
    else:
        await loja_contra(upd, ctx)

# ===== INVENTÁRIO =====
async def inv(upd, ctx):
    q = upd.callback_query
    uid = upd.effective_user.id
    dados = get_tudo(uid)
    await q.answer()

    import json
    inv_data = dados.get('inventario') or {}
    if isinstance(inv_data, str):
        inv_data = json.loads(inv_data)

    cap = f"🎒 **INVENTÁRIO**\n{'━'*20}\n"
    if not inv_data:
        cap += "Vazio\n"
    else:
        for item, qtd in inv_data.items():
            cap += f"💊 {item} x{qtd}\n"
    cap += f"{'━'*20}"

    kb = [[InlineKeyboardButton("🔙 Voltar", callback_data="voltar")]]
    try:
        await q.message.delete()
    except:
        pass
    await ctx.bot.send_photo(upd.effective_chat.id, img_c(dados['classe']), caption=cap,
                             reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

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
    cap += f"{'━'*20}"
    if dados['arma']:
        cap += f"\n⚔️ {dados['arma']}"
    if dados['arm']:
        cap += f"\n🛡️ {dados['arm']}"

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
           f"🛡️ **Guerreiro**\n└ HP Alto | Defesa Máxima\n└ ❤️ 250 HP | 🛡️ 18 DEF\n\n"
           f"🏹 **Arqueiro**\n└ Crítico | Ataque Duplo\n└ ❤️ 120 HP | 💥 25% CRIT\n\n"
           f"🔮 **Bruxa**\n└ Maldição | Dano Mágico\n└ ❤️ 150 HP | 💙 100 MANA\n\n"
           f"🔥 **Mago**\n└ Explosão | Poder Máximo\n└ ❤️ 130 HP | 💙 120 MANA\n{'━'*20}")
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
    uid = upd.effective_user.id
    p = get_p(uid)
    if p:
        invalidate_cache(uid)
        await menu(upd, ctx, uid)
        return ConversationHandler.END

    ctx.user_data.clear()
    agora = datetime.datetime.now().strftime("%H:%M:%S")
    cap = (f"✨ **AVENTURA RABISCADA** ✨\n{'━'*20}\n"
           f"Versão: `{VERSAO} - {agora}`\n\n"
           f"🎮 **NOVIDADES:**\n⚔️ Combate Manual\n🎭 Classes Únicas\n"
           f"💊 Sistema de Consumíveis\n🔮 Habilidades Especiais\n💙 Sistema de Mana\n{'━'*20}")
    kb = [[InlineKeyboardButton("🎮 Começar", callback_data="ir_cls")]]
    await upd.message.reply_photo(IMAGENS["logo"], caption=cap,
                                  reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    return ST_CL

async def menu_cls(upd, ctx):
    q = upd.callback_query
    await q.answer()
    cap = (f"🎭 **ESCOLHA SUA CLASSE**\n{'━'*20}\n\n"
           f"🛡️ **Guerreiro**\n└ HP Alto | Defesa Máxima\n└ ❤️ 250 HP | 🛡️ 18 DEF\n\n"
           f"🏹 **Arqueiro**\n└ Crítico | Ataque Duplo\n└ ❤️ 120 HP | 💥 25% CRIT\n\n"
           f"🔮 **Bruxa**\n└ Maldição | Dano Mágico\n└ ❤️ 150 HP | 💙 100 MANA\n\n"
           f"🔥 **Mago**\n└ Explosão | Poder Máximo\n└ ❤️ 130 HP | 💙 120 MANA\n{'━'*20}")
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
    if stats['especial']:
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
    nome = upd.message.text
    classe = ctx.user_data.get('classe', 'Guerreiro')
    stats = CLASSE_STATS[classe]

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""INSERT INTO players
                (id, nome, classe, hp, hp_max, mana, mana_max, lv, exp, gold,
                 energia, energia_max, mapa, local, arma, arm, atk_b, def_b, crit, double_atk)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (id) DO UPDATE SET
                nome=EXCLUDED.nome, classe=EXCLUDED.classe, hp=EXCLUDED.hp, hp_max=EXCLUDED.hp_max,
                mana=EXCLUDED.mana, mana_max=EXCLUDED.mana_max, lv=EXCLUDED.lv, exp=EXCLUDED.exp,
                gold=EXCLUDED.gold, energia=EXCLUDED.energia, energia_max=EXCLUDED.energia_max,
                mapa=EXCLUDED.mapa, local=EXCLUDED.local, arma=EXCLUDED.arma, arm=EXCLUDED.arm,
                atk_b=EXCLUDED.atk_b, def_b=EXCLUDED.def_b, crit=EXCLUDED.crit, double_atk=EXCLUDED.double_atk""",
              (uid, nome, classe, stats['hp'], stats['hp'], stats['mana'], stats['mana'],
               1, 0, 100, 20, 20, 1, 'cap', None, None, 0, 0,
               stats['crit'], 1 if stats['double'] else 0))
    conn.commit()
    invalidate_cache(uid)

    await upd.message.reply_text(f"✨ **{nome}!**\nBem-vindo, {classe}!", parse_mode='Markdown')
    await menu(upd, ctx, uid)
    return ConversationHandler.END

def main():
    init_db()
    token = os.getenv("TELEGRAM_TOKEN")

    try:
        requests.get(f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true", timeout=5)
    except:
        pass

    import threading
    t = threading.Thread(target=run_fake_server, daemon=True)
    t.start()

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

    logging.info(f"Bot {VERSAO} iniciado!")
    app.run_polling(drop_pending_updates=True, poll_interval=0.5, timeout=10)

if __name__ == '__main__':
    main()
