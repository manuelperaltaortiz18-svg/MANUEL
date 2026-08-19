#!/usr/bin/env bash
# Crea la carpeta de un cliente nuevo a partir de una plantilla.
#
#   ./web-factory/nuevo-cliente.sh <slug-cliente> <plantilla>
#
#   plantillas: local-negocio | servicios-profesionales | portfolio | producto-landing
#
# Ejemplo:
#   ./web-factory/nuevo-cliente.sh restaurante-la-plaza local-negocio

set -euo pipefail

SLUG="${1:-}"
TPL="${2:-}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FACTORY="$ROOT/web-factory"

if [[ -z "$SLUG" || -z "$TPL" ]]; then
  echo "Uso: $0 <slug-cliente> <plantilla>"
  echo "Plantillas disponibles:"
  ls -1 "$FACTORY/templates" | grep -v '^_'
  exit 1
fi

if [[ ! -d "$FACTORY/templates/$TPL" ]]; then
  echo "❌ La plantilla '$TPL' no existe."
  ls -1 "$FACTORY/templates" | grep -v '^_'
  exit 1
fi

DEST="$ROOT/clientes/$SLUG"
if [[ -e "$DEST" ]]; then
  echo "❌ Ya existe $DEST — elige otro slug o bórralo primero."
  exit 1
fi

mkdir -p "$DEST/img" "$DEST/assets"

# Página principal + legales + sistema de diseño
cp "$FACTORY/templates/$TPL/index.html" "$DEST/index.html"
cp "$FACTORY/templates/_legal/"*.html   "$DEST/"
cp "$FACTORY/assets/base.css"           "$DEST/assets/base.css"

# La plantilla apunta a ../../assets; dentro del proyecto es assets/
sed -i.bak 's|\.\./\.\./assets/base\.css|assets/base.css|g' "$DEST/index.html"
rm -f "$DEST/index.html.bak"

# Documentación de trabajo del proyecto
cp "$FACTORY/brief/BRIEF.md"           "$DEST/BRIEF.md"
cp "$FACTORY/checklists/ENTREGA.md"    "$DEST/ENTREGA.md"

cat > "$DEST/robots.txt" <<EOF
User-agent: *
Allow: /

Sitemap: https://DOMINIO/sitemap.xml
EOF

cat > "$DEST/.gitignore" <<'EOF'
img/originales/
*.psd
*.ai
EOF

echo "✅ Cliente creado en clientes/$SLUG (plantilla: $TPL)"
echo
echo "Siguientes pasos:"
echo "  1. Rellenar clientes/$SLUG/BRIEF.md con el cliente"
echo "  2. Sustituir los tokens [[...]] en index.html y en las páginas legales"
echo "  3. Meter las imágenes en clientes/$SLUG/img/ (WebP, <300 KB)"
echo "  4. Recorrer clientes/$SLUG/ENTREGA.md antes de enseñar nada"
echo "  5. Publicar: ver web-factory/deploy/DEPLOY.md"
echo
echo "Tokens pendientes en este proyecto:"
grep -oh '\[\[[A-Z0-9_]*\]\]' "$DEST"/*.html | sort -u | sed 's/^/  /'
