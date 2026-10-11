"""Valida un spec v2. Uso: python3 _tools/check_spec2.py specs/<key>.json  -> imprime OK o la lista de problemas."""
import json, sys
s = json.load(open(sys.argv[1], encoding="utf-8")); errs = []
qs = s.get("questions", []); R = s.get("routing", {})
if not 3 <= len(qs) <= 5: errs.append("3-5 preguntas")
emojis = set()
for i, q in enumerate(qs):
    if q.get("type") != "buttons": errs.append(f"{q.get('id')}: todas deben ser buttons (el contacto lo piden las rutas)")
    if not 2 <= len(q.get("options", [])) <= 4: errs.append(f"{q.get('id')}: 2-4 opciones")
    if any(len(o) > 22 for o in q.get("options", [])): errs.append(f"{q.get('id')}: opción > 22 caracteres")
    for k in ("id", "text", "field", "emoji", "label"):
        if not q.get(k): errs.append(f"q{i}: falta {k}")
    if q.get("emoji") in emojis: errs.append(f"{q.get('id')}: emoji repetido")
    emojis.add(q.get("emoji"))
    for d in q.get("disqualify", []):
        if d >= len(q.get("options", [])): errs.append(f"{q.get('id')}: disqualify fuera de rango")
if "hot" not in qs[-1]: errs.append("la ÚLTIMA pregunta debe llevar 'hot' (índices que van a lead caliente)")
if any("hot" in q for q in qs[:-1]): errs.append("solo la última pregunta lleva 'hot'")
if not any(q.get("disqualify") for q in qs): errs.append("al menos una opción 'disqualify' basada en un requisito real")
need = ["file_title", "file_done", "route_label", "name_label", "phone_label", "hot_text", "name_q", "phone_q", "warm_text", "email_q",
        "cold_text", "hot_label", "warm_label", "cold_label", "hot_closing", "warm_closing", "cold_closing"]
errs += [f"routing.{k} falta" for k in need if not R.get(k)]
for k in ("hot_label", "warm_label", "cold_label"):
    if "·" in R.get(k, ""): errs.append(f"{k}: sin '·' (separa campos en la tarjeta)")
    if "." not in R.get(k, ""): errs.append(f"{k}: formato 'Etiqueta. Siguiente paso' (con punto)")
for k in ("greeting", "summary_intro"):
    if any(ord(c) > 0x2600 for c in s.get(k, "")): errs.append(f"{k}: sin emoji")
print("OK" if not errs else "\n".join(errs))
