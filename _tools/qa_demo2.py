"""QA v2: recorre las tres rutas (caliente, nurturing, no encaja) de una demo dentro del widget de su página
y monta una hoja con el último fotograma de cada ruta. Uso: python3 _tools/qa_demo2.py <key> [ancho alto]"""
import json, os, pathlib, subprocess, sys
from PIL import Image
ROOT = pathlib.Path(__file__).resolve().parent.parent
key = sys.argv[1]; w, h = (sys.argv[2], sys.argv[3]) if len(sys.argv) > 3 else ("1000", "560")
spec = json.loads((ROOT / "specs" / f"{key}.json").read_text(encoding="utf-8"))
st = json.loads((ROOT / ".build" / f"v2-{key}.json").read_text())
qs = spec["questions"]


def ok_option(q, want_hot=None):
    bad = set(q.get("disqualify", []))
    for i, o in enumerate(q["options"]):
        if i in bad: continue
        if want_hot is None or (i in q.get("hot", [])) == want_hot: return o
    return q["options"][0]


routes = {}
routes["hot"] = [spec["cta"]] + [ok_option(q) for q in qs[:-1]] + [ok_option(qs[-1], True), "Test Visitor", "5550100199"]
routes["warm"] = [spec["cta"]] + [ok_option(q) for q in qs[:-1]] + [ok_option(qs[-1], False), "test@example.com"]
di = next(i for i, q in enumerate(qs) if q.get("disqualify"))
routes["cold"] = [spec["cta"]] + [ok_option(q) for q in qs[:di]] + [qs[di]["options"][qs[di]["disqualify"][0]]]
out = pathlib.Path("/private/tmp/claude-501/-Users-raul-Desktop-CSM/6eb14f4e-6252-51cf-80a3-216345a9ff98/scratchpad/qa2") / key
pw = subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip() + "/@playwright/cli/node_modules/playwright-core"
lasts = []
for name, answers in routes.items():
    d = out / name; d.mkdir(parents=True, exist_ok=True)
    for f in d.glob("*.png"): f.unlink()
    r = subprocess.run(["node", str(ROOT / "_tools/qa-walk.cjs"), f"http://127.0.0.1:8765/public/{st['slug']}/", str(d), w, h, "|".join(answers)],
                       env={**os.environ, "PWCORE": pw}, capture_output=True, text=True)
    miss = [l for l in r.stdout.splitlines() if "could not" in l]
    print(name, "ok" if not miss else miss)
    shots = sorted(d.glob(f"walk-{w}-*.png"), key=lambda p: int(p.stem.split("-")[-1]))
    lasts.append(shots[-1])
W = int(w); crop = (max(0, W - 440), 0, W, int(h))
ims = [Image.open(p).crop(crop).resize((330, int(330 * int(h) / 440))) for p in lasts]
sheet = Image.new("RGB", (3 * 340, ims[0].height), "white")
for i, im in enumerate(ims): sheet.paste(im, (i * 340, 0))
sheet.save(out / "ends.png"); print(out / "ends.png")
