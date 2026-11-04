"""Teste real com o Ollama local: 1ª jogada (preparação da ficha) + "outra versão". Banco separado em .tmp/.

Uso (na pasta backend, com o Ollama aberto): .venv/Scripts/python.exe scripts/real_turn_check.py [modelo]
"""

import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app  # noqa: E402
from app.config import PROJECT_ROOT, load_settings  # noqa: E402
from app.persistence.migrations import upgrade_to_head  # noqa: E402

model = sys.argv[1] if len(sys.argv) > 1 else "qwen2.5:1.5b"
data_dir = PROJECT_ROOT / ".tmp" / f"real-{uuid.uuid4().hex[:6]}"
data_dir.mkdir(parents=True)
url = "sqlite:///" + (data_dir / "rpg.db").as_posix()
upgrade_to_head(url)
settings = load_settings(environ={"APP_ENV": "development", "DATA_DIR": str(data_dir), "DATABASE_URL": url,
                                  "AI_PROVIDER": "ollama", "AI_MODEL": model, "AI_SUMMARY_EVERY": "0",
                                  "AUTO_SNAPSHOT_EVERY": "0"}, env_file=None)
services = create_app(settings).extensions["rpg_engine"]
user = services.local_user_id
campaign = services.campaigns.create(user, "A Torre de Vidro",
                                     "Uma aprendiz de maga acorda numa torre que flutua sobre um mar de nuvens.",
                                     ["fantasia", "isekai"])


def run(events):
    text, notices, last = "", [], None
    for e in events:
        name = type(e).__name__
        if name == "NarrationDelta":
            text += e.text
        elif name == "MechanicsApplied":
            notices += [m["content"] for m in e.messages]
        last = e
    return text, notices, last


start = time.monotonic()
turn_id = str(uuid.uuid4())
text1, notices, last = run(services.turns.run(services.turns.prepare(user, campaign["id"], turn_id, "Comece a história.")))
print(f"== 1ª jogada ({time.monotonic() - start:.0f} s, {type(last).__name__})")
print("\n".join(notices))
print(text1)
sheet = services.sheets.sheet(user, campaign["id"])["character"] if hasattr(services, "sheets") else None
if sheet:
    print("== ficha:", [(a["name"], a.get("value")) for a in sheet["attributes"]])
    print("   habilidades:", [s["name"] for s in sheet["skills"]], "itens:",
          [(i["name"], i.get("equipped_slot")) for i in sheet["items"]])
start = time.monotonic()
text2, _, last = run(services.turns.run(services.turns.prepare_regeneration(user, campaign["id"], turn_id)))
print(f"== outra versão ({time.monotonic() - start:.0f} s, {type(last).__name__})")
print(text2)
print("== textos diferentes:", text1.strip() != text2.strip())
