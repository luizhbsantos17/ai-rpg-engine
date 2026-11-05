"""Teste real de uma jogada: 1ª jogada (preparação da ficha) + "outra versão" + uma ação. Banco separado em .tmp/.

Uso (na pasta backend): .venv/Scripts/python.exe scripts/real_turn_check.py [provedor] [modelo]
  provedor: ollama (padrão; precisa do Ollama aberto), gemini, groq ou openrouter (chave lida do .env).
  modelo vazio = escolha automática.
"""

import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app  # noqa: E402
from app.config import PROJECT_ROOT, load_settings  # noqa: E402
from app.persistence.migrations import upgrade_to_head  # noqa: E402

provider_name = sys.argv[1] if len(sys.argv) > 1 else "ollama"
model = sys.argv[2] if len(sys.argv) > 2 else ""
data_dir = PROJECT_ROOT / ".tmp" / f"real-{uuid.uuid4().hex[:6]}"
data_dir.mkdir(parents=True)
url = "sqlite:///" + (data_dir / "rpg.db").as_posix()
upgrade_to_head(url)
settings = load_settings(environ={"APP_ENV": "development", "DATA_DIR": str(data_dir), "DATABASE_URL": url,
                                  "AI_PROVIDER": provider_name, "AI_MODEL": model, "AI_SUMMARY_EVERY": "0",
                                  "AUTO_SNAPSHOT_EVERY": "0"})  # chaves vêm do .env
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
        if name == "TurnFailed":
            print("FALHA:", e.message)
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
start = time.monotonic()
action = "Uso minha magia para iluminar o corredor e procuro alguém por perto."
text3, notices, last = run(services.turns.run(services.turns.prepare(user, campaign["id"], str(uuid.uuid4()), action)))
print(f"== 2ª jogada: {action} ({time.monotonic() - start:.0f} s, {type(last).__name__})")
print("\n".join(notices))
print(text3)
