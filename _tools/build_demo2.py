"""Construye una demo completa a partir de un spec JSON (ver specs/*.json).

Pasos: bot + agente de IA (Landbot Success) -> flujo -> publicar -> v4 + Back -> CSS de marca + script lbx
-> captura de su web -> página -> commit. Deja el estado en .build/<slug>.json para poder reanudar.
Uso: python3 _tools/build_demo.py specs/<empresa>.json
"""
import json, os, pathlib, re, secrets, subprocess, sys, time, uuid

ROOT = pathlib.Path(__file__).resolve().parent.parent
SK = pathlib.Path("/Users/raul/.claude/plugins/cache/landbot-skills/landbot/0.4.6/skills/landbot-flows/scripts")
LB, CHANNEL, HANDOFF = str(SK / "lb"), str(SK / "channel"), str(SK / "handoff")
PWCORE = subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip() + "/@playwright/cli/node_modules/playwright-core"
TXT = {
    "en": {"q": "I have a question", "step": "Step {n} of {total}", "done": "Your summary", "back": "Back", "ph": ""},
    "es": {"q": "Tengo una pregunta", "step": "Paso {n} de {total}", "done": "Tu resumen", "back": "Atrás", "ph": "Escribe tu respuesta aquí…"},
}


def run(args, body=None, check=True):
    cmd = args + ([body] if body is not None else [])
    r = subprocess.run(cmd, capture_output=True, text=True)
    code = re.search(r"HTTP (\d+)", r.stderr)
    if check and (r.returncode != 0):
        raise SystemExit(f"FAILED {' '.join(args[:3])}: {r.stderr[-400:]}")
    return r.stdout, (int(code.group(1)) if code else None)


def lbj(method, path, body=None):
    out, _ = run([LB, method, path], json.dumps(body, ensure_ascii=False) if body is not None else None)
    return json.loads(out) if out.strip().startswith("{") else {}


def _lum(hexs):
    def c(v):
        v /= 255; return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    h = hexs.lstrip("#"); r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * c(r) + 0.7152 * c(g) + 0.0722 * c(b)


def readable_on_white(hexs, target=4.5):
    """Oscurece el color (mismo tono) hasta que el texto blanco encima tenga contraste >= target."""
    h = hexs.lstrip("#"); r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    while 1.05 / (_lum("#%02x%02x%02x" % (r, g, b)) + 0.05) < target and (r + g + b) > 0:
        r, g, b = int(r * 0.95), int(g * 0.95), int(b * 0.95)
    return "#%02x%02x%02x" % (r, g, b)


def rgb(hexs):
    h = hexs.lstrip("#"); return ",".join(str(int(h[i:i + 2], 16)) for i in (0, 2, 4))


def main(spec_path):
    spec = json.loads(pathlib.Path(spec_path).read_text(encoding="utf-8"))
    t = TXT[spec["lang"]]
    state_path = ROOT / ".build" / f"v2-{spec['key']}.json"
    v1 = ROOT / ".build" / f"{spec['key']}.json"
    state_path.parent.mkdir(exist_ok=True)
    st = json.loads(state_path.read_text()) if state_path.exists() else {}
    save = lambda: state_path.write_text(json.dumps(st, indent=1))
    if "slug" not in st and v1.exists():
        st["slug"] = json.loads(v1.read_text()).get("slug") or spec.get("slug")
    if "slug" not in st and spec.get("slug"):
        st["slug"] = spec["slug"]

    # 1. bot
    if "bot" not in st:
        name = f"Demo v2 {spec['company']} {time.strftime('%m-%d')}"[:50]
        d = lbj("POST", "/bots", {"name": name, "channel_family": "landbot"})
        st["bot"] = (d.get("data") or {}).get("id")
        if not st["bot"]:
            time.sleep(6)
            st["bot"] = next(b["id"] for b in lbj("GET", "/bots")["data"] if b["name"] == name)
        save()
    bot = st["bot"]
    for _ in range(10):
        if lbj("GET", f"/bots/{bot}").get("data", {}).get("channels"):
            break
        time.sleep(4)

    # 2. agent
    if "agent" not in st:
        st["exit"] = str(uuid.uuid4())
        d = lbj("POST", "/ai-agents", {"channel": "web", "flow": {"id": bot}, "is_builder_block": True,
                                       "instructions": spec["agent_instructions"][:9000],
                                       "exit_conditions": [{"id": st["exit"], "name": spec["cta"][:100], "type": "output", "args": {},
                                                            "criteria": spec["agent_exit"][:1000]}]})
        (ROOT / ".build" / f"{spec['key']}-agent.json").write_text(json.dumps(d))
        st["agent"] = (d.get("data") or d).get("id")
        save()

    # 3. flow: qualifiers -> (disqualify | hot | warm) -> route-specific summary
    if "flow" not in st:
        def btns(opts): return [{"text": o, "payload": f"${i}"} for i, o in enumerate(opts)]
        def msg(text, mid="#0"): return [{"entity": "text", "text": text, "id": mid}]
        R = spec["routing"]; qs = spec["questions"]
        blocks = [
            {"id": "welcome", "type": "buttons", "name": "Greeting", "top": 200, "left": 500,
             "params": {"version": 3, "messages": msg(spec["greeting"]), "buttons": btns([spec["cta"], t["q"]]),
                        "destination": "entry_choice", "buttonsAlignment": "vertical"}},
            {"id": "agent", "type": "ai_agent", "name": "Questions", "top": 450, "left": 850,
             "params": {"assistantId": st["agent"], "name": "Questions", "outputs": [{"id": st["exit"], "name": spec["cta"][:100]}],
                        "errorMessage": spec.get("agent_error", "Sorry, I didn't catch that.")}},
        ]
        conns = [("welcome", qs[0]["id"], "$0"), ("welcome", "agent", "$1"), ("agent", qs[0]["id"], "$" + st["exit"])]
        left = 1200
        for i, q in enumerate(qs):
            nxt = qs[i + 1]["id"] if i + 1 < len(qs) else "warm_intro"
            blocks.append({"id": q["id"], "type": "buttons", "name": q["id"], "top": 200, "left": left,
                           "params": {"messages": msg(q["text"]), "buttons": btns(q["options"]), "destination": q["field"], "buttonsAlignment": "vertical"}})
            for k in range(len(q["options"])):
                if k in q.get("disqualify", []): tgt = "cold_text"
                elif "hot" in q: tgt = "hot_intro" if k in q["hot"] else "warm_intro"
                else: tgt = nxt
                conns.append((q["id"], tgt, f"${k}"))
            left += 350
        line = lambda extra: "  ·  ".join(["🚦 @lead_route"] + [f"{q['emoji']} @{q['field']}" for q in qs] + extra)
        def tail(tier, top, steps, extra):
            x = left; prev = None
            for bid, btype, params in steps + [
                (f"{tier}_set", "set_a_field", {"action": "SET", "field": "lead_route", "type": "STRING", "value": R[tier + "_label"]}),
                (f"{tier}_sum", "send_text", {"messages": [{"entity": "text", "text": spec["summary_intro"], "id": "$0"},
                                                           {"entity": "text", "text": line(extra), "id": "$1"}], "buttons": []}),
                (f"{tier}_end", "send_text", {"messages": msg(R[tier + "_closing"], "$0"), "buttons": []})]:
                blocks.append({"id": bid, "type": btype, "name": bid, "top": top, "left": x, "params": params})
                if prev: conns.append((prev[0], bid, prev[1]))
                prev = (bid, "success" if btype == "set_a_field" else "$success"); x += 350
        tail("hot", 200, [("hot_intro", "send_text", {"messages": msg(R["hot_text"], "$0"), "buttons": []}),
                          ("hot_name", "ask_name", {"text": R["name_q"], "destination": "name"}),
                          ("hot_phone", "ask_phone", {"text": R["phone_q"], "destination": "phone", "errorText": spec.get("error_text", "Could you check that?")})],
             ["👤 @name", "📞 @phone"])
        tail("warm", 500, [("warm_intro", "send_text", {"messages": msg(R["warm_text"], "$0"), "buttons": []}),
                           ("warm_email", "ask_email", {"text": R["email_q"], "destination": "email", "errorText": spec.get("error_text", "Could you check that?")})],
             ["✉️ @email"])
        tail("cold", 800, [("cold_text", "send_text", {"messages": msg(R["cold_text"], "$0"), "buttons": []})], [])
        d = lbj("POST", f"/bots/{bot}/draft/blocks", {"blocks": blocks, "connections": [
            {"sourcePath": a, "targetPath": b, "type": ty} for a, b, ty in conns]})
        v = (d.get("data") or d).get("violations") or d.get("error", {}).get("violations")
        if v:
            raise SystemExit(f"violations: {v}")
        run([LB, "POST", f"/bots/{bot}/versions"])
        run([CHANNEL, "v4", "--bot", bot]); run([CHANNEL, "back", "on", "--bot", bot])
        st["flow"] = True; save()

    # 4. look + behaviour
    p = dict(spec["palette"]); p["accent"] = readable_on_white(p["accent"])
    css = (ROOT / "_tools" / "demo-style-v2.css").read_text(encoding="utf-8")
    for k, v in {"MARKER": f"demo-{spec['key']} {time.strftime('%Y-%m-%d')}", "FONT_URL": p["font"].replace(" ", "+"), "FONT": p["font"],
                 "DARK": p["dark"], "DARK_HOVER": p.get("dark_hover", p["dark"]), "ACCENT": p["accent"], "ACCENT_RGB": rgb(p["accent"]),
                 "ACCENT_SOFT": p["accent_soft"], "ACCENT_LINE": p.get("accent_line", p["accent_soft"]), "ACCENT_BRIGHT": p.get("accent_bright", p["accent"]),
                 "BG": p["bg"], "DARK_RGB": rgb(p["dark"]), "BACK": t["back"],
                 "INITIALS": "".join(w[0] for w in spec["company"].split()[:2]).upper()}.items():
        css = css.replace("{{" + k + "}}", v)
    css_path = ROOT / "styles" / f"v2-{spec['key']}.css"; css_path.write_text(css, encoding="utf-8")
    js = (ROOT / "_tools" / "lbx-file.js").read_text(encoding="utf-8")
    qs = spec["questions"]; R = spec["routing"]
    labels = {"🚦": R["route_label"], "👤": R["name_label"], "📞": R["phone_label"], "✉️": "Email"}
    labels.update({q["emoji"]: q["label"] for q in qs})
    cfg = {"fileTitle": R["file_title"], "fileDone": R["file_done"], "focus": spec["format"] == "experience",
           "slots": [{"q": q.get("match") or q["text"][:28], "label": q["label"]} for q in qs], "cardMarker": "🚦", "cardLabels": labels,
           "tiers": {"hot": R["hot_label"].split(".")[0], "warm": R["warm_label"].split(".")[0], "cold": R["cold_label"].split(".")[0]},
           "placeholder": t["ph"]}
    js = re.sub(r"var CONFIG = \{.*?\n  \};", "var CONFIG = " + json.dumps(cfg, ensure_ascii=False) + ";", js, count=1, flags=re.S)
    js_path = ROOT / ".build" / f"v2-{spec['key']}.js"; js_path.write_text(js, encoding="utf-8")
    run([CHANNEL, "css", str(css_path), "--bot", bot]); run([CHANNEL, "js", str(js_path), "--custom", "--bot", bot])

    # 5. page
    out, _ = run([HANDOFF, bot], check=False)
    token = re.search(r"share=https://[^/]+/v3/(H-[A-Z0-9-]+)/", out).group(1)
    if "slug" not in st:
        st["slug"] = f"{spec['key']}-{secrets.token_hex(4)}"; save()
    page_dir = ROOT / "public" / st["slug"]; page_dir.mkdir(parents=True, exist_ok=True)
    if not (page_dir / "site-desktop.jpg").exists():
        subprocess.run(["node", str(ROOT / "_tools" / "capture.cjs"), spec["url"], str(page_dir)], env={**os.environ, "PWCORE": PWCORE}, check=True)
        for f, a in (("site-desktop.jpg", ["120", "48"]), ("site-mobile.jpg", ["240", "96"])):
            subprocess.run(["python3", str(ROOT / "_tools" / "trim_bands.py"), str(page_dir / f)] + a, check=True)
    subprocess.run(["python3", str(ROOT / "_tools" / "render.py"), st["slug"], spec["company"], spec["domain"], token, p["page_bg"]], check=True)
    st["token"] = token; save()
    print(json.dumps({"key": spec["key"], "bot": bot, "slug": st["slug"], "share": f"https://landbot.pro/v3/{token}/index.html",
                      "page": f"https://demos.landbot-lab.dev/{st['slug']}/"}))


if __name__ == "__main__":
    main(sys.argv[1])
