"""Rellena la plantilla de página para una demo. Uso: python3 render.py <slug> <Company> <domain> <share_token>"""
import sys, pathlib
slug, company, domain, token = sys.argv[1:5]
t = pathlib.Path(__file__).with_name("page-template.html").read_text(encoding="utf-8")
out = (t.replace("{{COMPANY}}", company).replace("{{DOMAIN}}", domain)
         .replace("{{CONFIG_URL}}", f"https://storage.googleapis.com/landbot.pro/v3/{token}/index.json")
         .replace("{{OPEN_DELAY_MS}}", "2500"))
p = pathlib.Path(__file__).parent.parent / slug / "index.html"
p.write_text(out, encoding="utf-8"); print(p)
