# Maestros del Corte — tema y grabado

Tema de bloques a medida para **Maestros del Corte by Cuperinox** sobre WordPress + WooCommerce, más un plugin para el grabado personalizado.

Colores de marca: **azul y negro**.

## Qué hay aquí

```
theme/                    Tema de bloques "Maestros del Corte"
  theme.json              Colores, tipografía y espaciados (el diseño vive aquí)
  functions.php           Soportes de Woo, columnas del catálogo, sellos de confianza
  templates/              Portada, catálogo, ficha de producto, página, blog, 404
  parts/                  Cabecera y pie
  patterns/               Secciones editables de la portada
  assets/css/             Acabado de las páginas de WooCommerce

plugin-grabado/           Plugin "Grabado personalizado"
```

## Instalación

**1. Subir el tema**

Comprime la carpeta `theme/` como `maestros-del-corte.zip` y súbela en *Apariencia → Temas → Añadir nuevo → Subir tema*. Actívalo.

> Al comprimir, la carpeta dentro del zip debe llamarse `maestros-del-corte`, no `theme`.

**2. Subir el plugin**

Comprime `plugin-grabado/` como `maestros-del-corte-grabado.zip` y súbelo en *Plugins → Añadir nuevo → Subir plugin*. Actívalo.

**3. Tipografías**

El tema pide *Cormorant Garamond* (titulares) e *Inter* (texto), con alternativas del sistema si no están. Para instalarlas: *Apariencia → Editor → Estilos → Tipografía → Gestionar fuentes → Instalar fuentes*. Búscalas en la biblioteca de Google Fonts y actívalas.

Instalarlas desde ahí las **autoaloja** — no hay llamadas a los servidores de Google, que es lo correcto para el RGPD.

**4. Páginas de WooCommerce**

En *WooCommerce → Ajustes → Avanzado*, comprueba que están asignadas Carrito, Finalizar compra y Mi cuenta. Crea la página **Regalo de empresa** con un formulario de contacto (no lleva carrito: es petición de presupuesto).

**5. Portada**

*Ajustes → Lectura → Tu portada muestra → Una página estática*. La plantilla `front-page.html` ya monta las cinco secciones; edítalas en *Apariencia → Editor → Plantillas → Portada*.

**6. Zonas de envío**

En *WooCommerce → Ajustes → Envío* hacen falta **tres zonas**:

| Zona | Regiones | Método |
|---|---|---|
| Península | España, **excluyendo** Baleares, Las Palmas, Santa Cruz de Tenerife, Ceuta y Melilla | Envío gratuito (sin mínimo) |
| Baleares | Provincia de Baleares | Precio fijo o por peso |
| Canarias, Ceuta y Melilla | Las Palmas, Santa Cruz de Tenerife, Ceuta, Melilla | Precio fijo o por peso |

WooCommerce permite seleccionar provincias españolas concretas dentro de la zona, así que la exclusión de la península se hace añadiendo provincia a provincia en las otras dos zonas y dejando "España" en la primera. **El orden importa**: WooCommerce aplica la primera zona que coincide, así que Baleares y Canarias deben ir *por encima* de la de península en la lista.

Sin ninguna tarifa configurada, el checkout se queda sin métodos disponibles y bloquea la compra.

**7. Páginas de contenido**

Crea estas páginas e insértale a cada una su patrón desde el editor (botón `+` → pestaña *Patrones* → categoría **Maestros del Corte**):

| Página | URL |
|---|---|
| Envíos y plazos | `/envios/` |
| Devoluciones y garantía | `/devoluciones/` |
| Cuidado y mantenimiento | `/cuidado/` |
| Aviso legal | `/aviso-legal/` |
| Condiciones generales de venta | `/terminos/` |

Los textos legales llevan **huecos entre corchetes** (`[CIF]`, `[RAZÓN SOCIAL]`…) que hay que rellenar con los datos fiscales reales. Busca `[` en la página para localizarlos todos.

> Estos textos son una base bien fundamentada, con las referencias legales correctas, pero **no sustituyen a un asesor**. Que los revise alguien antes de publicar.

Faltan aún **Política de Privacidad** (`/privacidad/`) y **Política de Cookies** (`/cookies/`), que dependen de qué herramientas de analítica y marketing acabéis instalando.

**8. Imágenes**

El patrón de portada y el de grabado traen los huecos de imagen vacíos a propósito. Añade las tuyas desde el editor. Formato recomendado: **4:5 vertical** para producto de catálogo, para que la rejilla quede pareja.

## Activar el grabado en un producto

Edita el producto → *Datos del producto → General*:

- **Admite grabado** — márcalo solo en cuchillos y estuches. Las bases de madera no lo admiten.
- **Recargo por grabado** — el importe que se suma. Vacío o 0 = grabado sin coste.

En la ficha aparece un campo de texto (máximo 20 caracteres). El texto viaja al carrito, al checkout, al email y a la línea del pedido en el admin, para que el taller lo vea sin preguntar.

Dos unidades del mismo cuchillo con grabados distintos se mantienen como líneas separadas.

## Decisiones de diseño que conviene conocer

**No hay botón de "añadir al carrito" en la rejilla del catálogo.** En ticket alto empuja a comprar sin leer la ficha, y la ficha es donde se cierra la venta. En su lugar hay un enlace discreto.

**Los sellos de confianza van justo debajo del botón de compra** (envío, devolución, garantía). Es el punto exacto de la duda. Se editan en `functions.php`, función `mdc_trust_badges`.

**El aviso de "no admite devolución" aparece junto al campo de grabado.** Un producto personalizado está excluido del derecho de desistimiento, pero solo si el cliente lo sabe **antes** de comprar.

**Catálogo a 3 columnas y 24 productos por página.** Con catálogo corto cabe todo sin paginar; cada clic de paginación es una fuga.

## Condiciones comerciales implementadas

| | |
|---|---|
| Envío península | Gratuito, sin importe mínimo |
| Baleares, Canarias, Ceuta y Melilla | Tarifa aparte, calculada en el carrito |
| Plazo | 24–48 h laborables (+2–3 días si lleva grabado) |
| Devolución | 14 días naturales, porte de vuelta a cargo del cliente |
| Defecto de fábrica | Recogida y sustitución sin coste |
| Garantía legal | 3 años por falta de conformidad |
| Piezas grabadas | Excluidas del desistimiento (avisado antes de comprar) |

El aviso de devolución aparece en tres sitios: sello bajo el botón de compra, nota junto al botón de pagar del checkout, y página de devoluciones. No es redundancia — el coste del porte solo se puede repercutir al cliente si se le informó **antes** de comprar, y esto lo deja acreditado.

## Pendiente antes de lanzar

- [ ] Rellenar los datos fiscales `[entre corchetes]` en aviso legal y condiciones de venta
- [ ] Política de privacidad y de cookies
- [ ] Las tres zonas de envío configuradas (si falta alguna, el checkout se bloquea en ese destino)
- [ ] Cerrar tarifas reales con el transportista para Baleares y Canarias antes de fijar los importes
- [ ] Pasarela de pago en producción y una compra real de prueba de principio a fin
- [ ] Redirecciones 301 desde las URLs de la línea en cuperinox.es
- [ ] Analítica y consentimiento de cookies
- [ ] Emails de pedido con la identidad de Maestros del Corte, no la de Cuperinox
