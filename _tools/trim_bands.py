"""Quita de una captura las franjas lisas (secciones que solo se pintan con animación al hacer scroll).
Uso: python3 trim_bands.py <img> [min_alto_px] [alto_que_queda_px]"""
import sys
from PIL import Image, ImageStat
path = sys.argv[1]; min_h = int(sys.argv[2]) if len(sys.argv) > 2 else 120; keep = int(sys.argv[3]) if len(sys.argv) > 3 else 48
im = Image.open(path).convert("RGB"); w, h = im.size
flat = []
for y in range(h):
    row = im.crop((0, y, w, y + 1)); st = ImageStat.Stat(row)
    flat.append(max(st.stddev) < 3.0)
keep_rows, y = [], 0
while y < h:
    if flat[y]:
        z = y
        while z < h and flat[z]: z += 1
        if z - y >= min_h:
            keep_rows.append((y, y + keep)); y = z; continue
        keep_rows.append((y, z)); y = z
    else:
        z = y
        while z < h and not flat[z]: z += 1
        keep_rows.append((y, z)); y = z
out_h = sum(b - a for a, b in keep_rows); out = Image.new("RGB", (w, out_h)); oy = 0
for a, b in keep_rows: out.paste(im.crop((0, a, w, b)), (0, oy)); oy += b - a
out.save(path, quality=80); print(f"{path}: {h}px -> {out_h}px")
