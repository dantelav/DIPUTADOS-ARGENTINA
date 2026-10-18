# nombresdecallesargentinas.com

Cada cartel de calle con un QR que lleva a una página que cuenta quién fue (o qué fue) ese nombre.
Alcance inicial: **Parque Chas**, las cuadras cercanas a **Altolaguirre y Av. de los Incas**.

## Cómo está armado

Sitio estático, sin base de datos ni servidor: el contenido vive en dos archivos JSON y un script genera todo.

```
data/calles.json     una entrada por calle (texto, barrios, imagen, fuentes)
data/barrios.json    una entrada por barrio (por qué se llama así, curiosidades)
img/                 imágenes reales (Wikimedia Commons), con autor y licencia en el JSON
static/style.css     estilos
build.py             genera site/, qr/ e imprimir/
```

```
pip install segno reportlab
python3 build.py
```

Genera:

- `site/` — el sitio listo para subir. Cada calle queda en `/c/<slug>/` y cada barrio en `/b/<slug>/`.
- `qr/<slug>.svg` y `.png` — el QR suelto de cada calle (para la imprenta o para otro diseño).
- `imprimir/calcos-<slug>.pdf` — hoja A4 con 16 calcos de esa calle (46 × 64 mm, línea de corte punteada).
- `imprimir/calcos-todas.pdf` — todas las hojas juntas.

## Agregar una calle

1. Copiar una entrada de `data/calles.json` y cambiar los datos. El `slug` va en minúsculas, sin tildes, con guiones.
2. Bajar la imagen a `img/` y completar autor, licencia y página de origen.
3. `python3 build.py` y volver a publicar.

## Reglas que no hay que romper

- **El QR apunta a `https://nombresdecallesargentinas.com/c/<slug>`.** Una vez impreso, ese slug no se cambia nunca.
  Si una calle cambia de nombre, se agrega una página nueva y la vieja se mantiene (o redirige).
- **Comprar el dominio antes de imprimir.** Si el dominio no es tuyo, los QR quedan apuntando a algo que no controlás.
- Corrección de errores del QR en nivel H (30 %): sigue funcionando aunque el calco se raye.

## Publicar (gratis)

- **GitHub Pages**: subir el contenido de `site/` a un repo, activar Pages y apuntar el dominio (el archivo `CNAME` ya está generado).
- **Netlify / Cloudflare Pages**: arrastrar la carpeta `site/` en el panel; después configurar el dominio.

## Imprimir

- Vinilo blanco autoadhesivo **para exterior**, con **laminado UV** (sin laminado el sol lo borra en meses).
- Imprimir al 100 % (sin "ajustar a página") para que el QR mida 4 cm.
- Probar un calco escaneándolo con 2 o 3 celulares distintos antes de mandar la tirada.
- Antes de pegar en carteles públicos, conviene pedir autorización a la Comuna (Parque Chas es Comuna 15):
  pegar en señalización pública sin permiso puede considerarse contravención.
