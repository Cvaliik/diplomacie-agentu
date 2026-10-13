"""tools/test_odmitnuti.py

Jedno volani hrace primo na PLAYER_MODEL bez zalozniho modelu, se stejnymi parametry jako ostry tah
(schema, thinking, effort, max_tokens, cachovany prefix). Vstup je debug soubor z run_turn.py --dry-model
nebo tools/vstup_kola.py. Vypise model, stop_reason, kategorii odmitnuti, tokeny a cenu. Nic nezapisuje do hry.

    python tools/test_odmitnuti.py debug/vstup_kolo_007_B.md B
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import anthropic  # noqa: E402
import config  # noqa: E402
import run_turn  # noqa: E402


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    path, pid = Path(sys.argv[1]), sys.argv[2]
    text = path.read_text(encoding="utf-8")
    system = text.split("\n## system\n\n", 1)[1].split("\n\n## user\n\n", 1)[0]
    user = text.split("\n\n## user\n\n", 1)[1].rstrip("\n")
    prefix = run_turn.player_cache_prefix()
    blocks = [{"type": "text", "text": system}]
    if system.startswith(prefix):
        blocks = [{"type": "text", "text": prefix, "cache_control": {"type": "ephemeral"}},
                  {"type": "text", "text": system[len(prefix):]}]
    c = anthropic.Anthropic(api_key=os.environ["ARDAN_API_KEY"])
    r = c.messages.create(model=config.PLAYER_MODEL, max_tokens=run_turn.PLAYER_MAX_TOKENS, system=blocks,
                          messages=[{"role": "user", "content": user}], thinking=run_turn.PLAYER_THINKING,
                          output_config={**({"effort": run_turn.PLAYER_EFFORT} if run_turn.PLAYER_EFFORT else {}),
                                         "format": {"type": "json_schema", "schema": run_turn.player_schema(pid)}})
    u = {"model": r.model, "input_tokens": r.usage.input_tokens, "output_tokens": r.usage.output_tokens,
         "cache_creation_input_tokens": getattr(r.usage, "cache_creation_input_tokens", 0) or 0,
         "cache_read_input_tokens": getattr(r.usage, "cache_read_input_tokens", 0) or 0}
    d = getattr(r, "stop_details", None)
    print("model:", r.model, "| stop_reason:", r.stop_reason,
          "| kategorie:", getattr(d, "category", None) if r.stop_reason == "refusal" else "-")
    print("tokeny: vstup %d, zapis cache %d, cteni cache %d, vystup %d | %.4f USD" % (
        u["input_tokens"], u["cache_creation_input_tokens"], u["cache_read_input_tokens"], u["output_tokens"],
        run_turn.call_cost(u)))
    txt = "".join(b.text for b in r.content if b.type == "text")
    if txt:
        try:
            m = json.loads(txt)
            print("akce:", json.dumps(m.get("actions"), ensure_ascii=False), "| domaci:", m.get("domestic_action"))
        except ValueError as err:
            print("odpoved neni uplny JSON (%s), %d znaku" % (err, len(txt)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
