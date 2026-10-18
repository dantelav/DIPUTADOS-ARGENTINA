#!/usr/bin/env python3
"""Genera el sitio estático, los QR y las planchas de calcos.

Uso:
    pip install segno reportlab
    python3 build.py

Salida:
    site/            sitio listo para publicar (GitHub Pages, Netlify, Cloudflare Pages)
    qr/<slug>.svg    QR vectorial de cada calle (para la imprenta)
    qr/<slug>.png    QR en PNG
    imprimir/calcos-<slug>.pdf   plancha A4 con 16 calcos de esa calle
    imprimir/calcos-todas.pdf    todas las planchas juntas
"""

import html
import json
import shutil
from pathlib import Path

import segno
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

ROOT = Path(__file__).parent
DOMINIO = "nombresdecallesargentinas.com"
BASE_URL = f"https://{DOMINIO}"
SITE = ROOT / "site"
QR_DIR = ROOT / "qr"
PRINT_DIR = ROOT / "imprimir"


def url_calle(slug):
    # URL corta y estable: lo que va en el QR NO se puede cambiar después de imprimir.
    return f"{BASE_URL}/c/{slug}"


def e(texto):
    return html.escape(texto or "")


def cargar():
    calles = json.loads((ROOT / "data" / "calles.json").read_text(encoding="utf-8"))
    barrios = json.loads((ROOT / "data" / "barrios.json").read_text(encoding="utf-8"))
    return calles, barrios


# ---------------------------------------------------------------- HTML

def pagina(titulo, cuerpo, descripcion="", profundidad=0, og_imagen=None):
    pre = "../" * profundidad
    og = f'<meta property="og:image" content="{e(og_imagen)}">' if og_imagen else ""
    return f"""<!doctype html>
<html lang="es-AR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(titulo)}</title>
<meta name="description" content="{e(descripcion)}">
<meta property="og:title" content="{e(titulo)}">
<meta property="og:description" content="{e(descripcion)}">
{og}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{pre}static/style.css">
</head>
<body>
<header class="top"><a href="{pre}./" class="marca">Nombres de calles <span>argentinas</span></a></header>
<main>
{cuerpo}
</main>
<footer class="pie">
<p>Proyecto ciudadano para que cada cartel de calle cuente su historia.</p>
<p>Imágenes reales de Wikimedia Commons, con su autor y licencia en cada página. ¿Encontraste un error? Escribinos.</p>
</footer>
</body>
</html>
"""


def figura(img, alt, pre):
    if not img or not img.get("archivo"):
        return ""
    credito = " · ".join(x for x in [img.get("autor"), img.get("licencia")] if x)
    fuente = f' <a href="{e(img["pagina"])}">Fuente</a>' if img.get("pagina") else ""
    return f"""<figure class="foto">
<img src="{pre}{e(img['archivo'])}" alt="{e(alt)}" loading="eager">
<figcaption>{e(img.get('descripcion', ''))}<span class="credito">{e(credito)}{fuente}</span></figcaption>
</figure>"""


def fuentes(lista):
    if not lista:
        return ""
    items = "".join(f'<li><a href="{e(f["url"])}">{e(f["titulo"])}</a></li>' for f in lista)
    return f'<section class="fuentes"><h2>Fuentes</h2><ul>{items}</ul></section>'


def html_calle(calle, barrios):
    pre = "../../"
    chips = []
    for b in calle["barrios"]:
        nombre = barrios.get(b, {}).get("nombre", b)
        chips.append(f'<a class="chip" href="{pre}b/{b}/">{e(nombre)}</a>')
    tramo = f'<p class="tramo">{e(calle["tramo"])}</p>' if calle.get("tramo") else ""
    parrafos = "".join(f"<p>{e(p)}</p>" for p in calle["texto"])
    cuerpo = f"""<div class="cartel">
<div class="cartel-nombre">{e(calle['nombre_cartel'])}</div>
<div class="cartel-barrio">{e(barrios.get(calle['barrios'][0], {}).get('nombre', ''))}</div>
</div>
<article class="ficha">
<p class="tipo">{e(calle['tipo'])}</p>
<h1>{e(calle['titulo'])}</h1>
<p class="fechas">{e(calle.get('fechas', ''))}</p>
{figura(calle.get('imagen'), calle['titulo'], pre)}
<div class="texto">{parrafos}</div>
<section class="barrios"><h2>Esta calle pasa por</h2>{''.join(chips)}{tramo}</section>
{fuentes(calle.get('fuentes'))}
</article>"""
    og = f"{BASE_URL}/{calle['imagen']['archivo']}" if calle.get("imagen", {}).get("archivo") else None
    return pagina(f"{calle['nombre_cartel']} — ¿quién fue?", cuerpo, calle["texto"][0][:160], 2, og)


def html_barrio(slug, barrio, calles):
    pre = "../../"
    propias = [c for c in calles if slug in c["barrios"]]
    lista = "".join(
        f'<li><a href="{pre}c/{c["slug"]}/"><strong>{e(c["nombre_cartel"])}</strong>'
        f'<span>{e(c["titulo"])}</span></a></li>'
        for c in sorted(propias, key=lambda c: c["nombre_cartel"])
    )
    if barrio.get("texto"):
        texto = "".join(f"<p>{e(p)}</p>" for p in barrio["texto"])
        curiosidades = "".join(f"<li>{e(x)}</li>" for x in barrio.get("curiosidades", []))
        extra = f'<section class="curiosidades"><h2>Curiosidades</h2><ul>{curiosidades}</ul></section>' if curiosidades else ""
    else:
        texto = "<p>Estamos preparando la historia de este barrio.</p>"
        extra = ""
    cuerpo = f"""<article class="ficha">
<p class="tipo">Barrio</p>
<h1>{e(barrio['nombre'])}</h1>
<p class="fechas">{e(barrio.get('comuna', ''))}</p>
{figura(barrio.get('imagen'), barrio['nombre'], pre)}
<div class="texto">{texto}</div>
{extra}
<section class="lista-calles"><h2>Calles con historia</h2><ul class="calles">{lista or '<li>Próximamente.</li>'}</ul></section>
{fuentes(barrio.get('fuentes'))}
</article>"""
    return pagina(f"Barrio {barrio['nombre']}", cuerpo, (barrio.get("texto") or [""])[0][:160], 2)


def html_inicio(calles, barrios):
    con_calles = [s for s in barrios if any(s in c["barrios"] for c in calles) and barrios[s].get("texto")]
    tarjetas = "".join(
        f'<a class="tarjeta" href="b/{s}/"><strong>{e(barrios[s]["nombre"])}</strong>'
        f'<span>{e(barrios[s].get("bajada", ""))}</span></a>'
        for s in con_calles
    )
    lista = "".join(
        f'<li data-q="{e((c["nombre_cartel"] + " " + c["titulo"]).lower())}"><a href="c/{c["slug"]}/">'
        f'<strong>{e(c["nombre_cartel"])}</strong><span>{e(c["titulo"])}</span></a></li>'
        for c in sorted(calles, key=lambda c: c["nombre_cartel"])
    )
    cuerpo = f"""<section class="hero">
<h1>Cada calle tiene<br>una historia.</h1>
<p>Escaneá el QR del cartel de tu esquina y conocé quién fue, qué pasó o qué lugar recuerda ese nombre.</p>
</section>
<section><h2>Barrios</h2><div class="tarjetas">{tarjetas}</div></section>
<section><h2>Calles</h2>
<input id="buscar" type="search" placeholder="Buscar una calle…" aria-label="Buscar una calle">
<ul class="calles" id="lista">{lista}</ul>
</section>
<script>
document.getElementById('buscar').addEventListener('input', function () {{
  var q = this.value.toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g, '');
  document.querySelectorAll('#lista li').forEach(function (li) {{
    var t = li.dataset.q.normalize('NFD').replace(/[\\u0300-\\u036f]/g, '');
    li.hidden = q && t.indexOf(q) === -1;
  }});
}});
</script>"""
    return pagina("Nombres de calles argentinas", cuerpo, "Quién fue cada nombre de calle de la Argentina. Escaneá el QR del cartel.")


def escribir(ruta, texto):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto, encoding="utf-8")


def construir_sitio(calles, barrios):
    if SITE.exists():
        shutil.rmtree(SITE)
    shutil.copytree(ROOT / "static", SITE / "static")
    shutil.copytree(ROOT / "img", SITE / "img")
    escribir(SITE / "index.html", html_inicio(calles, barrios))
    for c in calles:
        escribir(SITE / "c" / c["slug"] / "index.html", html_calle(c, barrios))
    for slug, b in barrios.items():
        escribir(SITE / "b" / slug / "index.html", html_barrio(slug, b, calles))
    escribir(SITE / "404.html", pagina("Página no encontrada", '<article class="ficha"><h1>No encontramos esa página</h1><p><a href="/">Volver al inicio</a></p></article>'))
    escribir(SITE / "CNAME", DOMINIO + "\n")  # para GitHub Pages con dominio propio


# ---------------------------------------------------------------- QR

def construir_qr(calles):
    QR_DIR.mkdir(exist_ok=True)
    for c in calles:
        # Corrección de errores alta (H, ~30%): el calco sigue leyéndose aunque se raye o ensucie.
        qr = segno.make(url_calle(c["slug"]), error="h", micro=False)
        qr.save(QR_DIR / f"{c['slug']}.svg", scale=10, border=4)
        qr.save(QR_DIR / f"{c['slug']}.png", scale=20, border=4)


# ---------------------------------------------------------------- Calcos

CAL_W, CAL_H = 46 * mm, 64 * mm   # tamaño de cada calco
COLS, FILAS = 4, 4                # 16 por hoja A4, como la maqueta
QR_LADO = 40 * mm


def ajustar_fuente(pdf, texto, fuente, maximo, ancho):
    tam = maximo
    while tam > 6 and pdf.stringWidth(texto, fuente, tam) > ancho:
        tam -= 0.5
    return tam


def dibujar_calco(pdf, x, y, calle):
    # x, y = esquina inferior izquierda del calco
    pdf.setStrokeColorRGB(0.75, 0.75, 0.75)
    pdf.setLineWidth(0.3)
    pdf.setDash(2, 2)
    pdf.rect(x, y, CAL_W, CAL_H)  # línea de corte
    pdf.setDash()

    qr = segno.make(url_calle(calle["slug"]), error="h", micro=False)
    matriz = list(qr.matrix_iter(border=2))
    modulo = QR_LADO / len(matriz)
    qx = x + (CAL_W - QR_LADO) / 2
    qy = y + CAL_H - QR_LADO - 3 * mm
    pdf.setFillColorRGB(0, 0, 0)
    for fila, linea in enumerate(matriz):
        for col, oscuro in enumerate(linea):
            if oscuro:
                pdf.rect(qx + col * modulo, qy + (len(matriz) - 1 - fila) * modulo,
                         modulo + 0.01, modulo + 0.01, stroke=0, fill=1)

    # franja negra con el nombre, como los carteles porteños
    franja_h = 10 * mm
    fy = qy - franja_h - 2 * mm
    pdf.rect(x + 2 * mm, fy, CAL_W - 4 * mm, franja_h, stroke=0, fill=1)
    nombre = calle["nombre_cartel"].upper()
    tam = ajustar_fuente(pdf, nombre, "Helvetica-Bold", 13, CAL_W - 7 * mm)
    pdf.setFillColorRGB(1, 1, 1)
    pdf.setFont("Helvetica-Bold", tam)
    pdf.drawCentredString(x + CAL_W / 2, fy + (franja_h - tam * 0.7) / 2, nombre)

    pdf.setFillColorRGB(0, 0, 0)
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawCentredString(x + CAL_W / 2, fy - 4.5 * mm, "¿Quién fue? Escaneá")
    pdf.setFont("Helvetica", ajustar_fuente(pdf, DOMINIO, "Helvetica", 6.5, CAL_W - 4 * mm))
    pdf.drawCentredString(x + CAL_W / 2, fy - 8 * mm, DOMINIO)


def plancha(pdf, calles_hoja):
    ancho, alto = A4
    gap_x = (ancho - COLS * CAL_W) / (COLS + 1)
    gap_y = (alto - FILAS * CAL_H) / (FILAS + 1)
    for i, calle in enumerate(calles_hoja):
        col, fila = i % COLS, i // COLS
        x = gap_x + col * (CAL_W + gap_x)
        y = alto - (fila + 1) * (CAL_H + gap_y)
        dibujar_calco(pdf, x, y, calle)
    pdf.showPage()


def construir_calcos(calles):
    PRINT_DIR.mkdir(exist_ok=True)
    a_imprimir = [c for c in calles if c.get("imprimir", True)]
    todas = canvas.Canvas(str(PRINT_DIR / "calcos-todas.pdf"), pagesize=A4)
    todas.setTitle("Calcos QR — Nombres de calles argentinas")
    for c in a_imprimir:
        una = canvas.Canvas(str(PRINT_DIR / f"calcos-{c['slug']}.pdf"), pagesize=A4)
        una.setTitle(f"Calcos QR — {c['nombre_cartel']}")
        plancha(una, [c] * (COLS * FILAS))
        una.save()
        plancha(todas, [c] * (COLS * FILAS))
    todas.save()


if __name__ == "__main__":
    calles, barrios = cargar()
    construir_sitio(calles, barrios)
    construir_qr(calles)
    construir_calcos(calles)
    print(f"{len(calles)} calles, {len(barrios)} barrios -> site/, qr/, imprimir/")
