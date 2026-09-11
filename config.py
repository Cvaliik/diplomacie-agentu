"""config.py

Jedno misto pro modely, cesty a prepinace. Zadna logika.
Zmena modelu = zmena tady a commit (BUILD.md cast 3).
"""

from pathlib import Path

# --- modely ---------------------------------------------------------------
# Hraci a kronikar nejsilnejsi dostupny model, rozhodci levnejsi.
# Pokud Opus dochazi, prepni PLAYER_MODEL na Sonnet; kronikar zustava Opus.
PLAYER_MODEL = "claude-opus-5"
REFEREE_MODEL = "claude-sonnet-5"
CHRONICLER_MODEL = "claude-opus-5"

# --- cesty ----------------------------------------------------------------
ROOT = Path(__file__).parent
STATE_PATH = ROOT / "state.json"
NPC_PATH = ROOT / "npc.json"
DOCS_DIR = ROOT / "docs"
PROMPTS_DIR = ROOT / "prompts"
SECRETS_DIR = ROOT / "secrets"
VIEWS_DIR = ROOT / "views"
HISTORY_DIR = ROOT / "history"
CHRONICLE_DIR = ROOT / "chronicle"
WEB_DIR = ROOT / "web"

RULES_PATH = DOCS_DIR / "pravidla.md"
RULINGS_PATH = DOCS_DIR / "rulings.md"
TURN_FORMAT_PATH = DOCS_DIR / "format_tahu.md"

# --- casy a rozsah hry ----------------------------------------------------
TIMEZONE = "Europe/Prague"
SLOT_TIMES = {1: "07:00", 2: "13:00", 3: "20:00"}
TOTAL_TURNS = 90
TURNS_PER_DAY = 3

# --- prepinace ------------------------------------------------------------
# Kolikrat zopakovat volani hrace, nez se bere jako mlceni (pravidla 10.6).
PLAYER_RETRIES = 2
# Kolik tahu drzi state.json v logu; plny log je v history/ (pravidla 10.9).
LOG_WINDOW = 9
# Kolik tahu verejneho logu dostava hrac v promptu (BUILD.md cast 3).
PUBLIC_LOG_TURNS = 9
