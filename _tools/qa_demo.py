"""QA de una demo construida: recorre el flujo dentro del widget de la página (local) y monta una hoja de capturas.
Uso: python3 _tools/qa_demo.py <key> [ancho alto]"""
import json, os, pathlib, subprocess, sys
from PIL import Image
ROOT = pathlib.Path(__file__).resolve().parent.parent
key = sys.argv[1]; w, h = (sys.argv[2], sys.argv[3]) if len(sys.argv) > 3 else ("1000", "560")
spec = json.loads((ROOT / "specs" / f"{key}.json").read_text()); st = json.loads((ROOT / ".build" / f"{key}.json").read_text())
answers = [spec["cta"]] + [q["options"][1 if len(q["options"]) > 1 else 0] if q["type"] == "buttons" else "test@example.com" for q in spec["questions"]]
out = pathlib.Path("/private/tmp/claude-501/-Users-raul-Desktop-CSM/6eb14f4e-6252-51cf-80a3-216345a9ff98/scratchpad/qa") / key
out.mkdir(parents=True, exist_ok=True)
for f in out.glob("walk-*.png"): f.unlink()
pw = subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip() + "/@playwright/cli/node_modules/playwright-core"
r = subprocess.run(["node", str(ROOT / "_tools/qa-walk.cjs"), f"http://127.0.0.1:8765/public/{st['slug']}/", str(out), w, h, "|".join(answers)],
                   env={**os.environ, "PWCORE": pw}, capture_output=True, text=True)
print(r.stdout.strip()[-300:], r.stderr.strip()[-300:])
shots = sorted(out.glob(f"walk-{w}-*.png"), key=lambda p: int(p.stem.split("-")[-1]))
W = int(w); crop = (max(0, W - 440), 0, W, int(h)) if W > 500 else (0, 0, W, int(h))
sel = [shots[1], shots[min(3, len(shots) - 1)], shots[-1]] if len(shots) >= 3 else shots
ims = [Image.open(p).crop(crop).resize((330, int(330 * (crop[3] - crop[1]) / (crop[2] - crop[0])))) for p in sel]
cw, ch = ims[0].size; cols = 3; rows = (len(ims) + cols - 1) // cols
sheet = Image.new("RGB", (cols * (cw + 16), rows * (ch + 16)), "white")
for i, im in enumerate(ims): sheet.paste(im, ((i % cols) * (cw + 16), (i // cols) * (ch + 16)))
sheet.save(out / f"sheet-{w}.png"); print(out / f"sheet-{w}.png")
