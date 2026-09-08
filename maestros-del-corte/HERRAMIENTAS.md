# Stack de herramientas recomendado

Selección para Maestros del Corte. El criterio: **lo mínimo que hace falta para vender, medir y no tener un problema legal.** Cada plugin instalado es peso en la web y una superficie más de fallo, así que la lista es corta a propósito.

Las políticas de privacidad y cookies del tema ya están redactadas **para este stack concreto**. Si cambias de herramienta, hay que tocarlas.

---

## Esencial — antes de lanzar

### 1. Complianz — consentimiento de cookies
**Gratis** (versión Premium ~55 €/año, no necesaria de inicio)

El más ajustado a lo que exige la AEPD. Lo importante: **bloquea los scripts de Google y Meta hasta que el usuario acepta**, en lugar de limitarse a enseñar un banner mientras las cookies ya se han instalado — que es el error que acaba en sanción.

Configúralo con: rechazar tan visible como aceptar, y sin casillas premarcadas.

### 2. Rank Math SEO
**Gratis**

Mejor que Yoast en su versión gratuita: schema de producto, breadcrumbs, sitemaps y redirecciones incluidas. El **schema de producto** es lo que hace que en Google salga tu precio y disponibilidad bajo el resultado, y eso sube el clic notablemente.

Aquí también configuras las **redirecciones 301** desde las URLs viejas de cuperinox.es.

### 3. UpdraftPlus — copias de seguridad
**Gratis**

Copia diaria a Google Drive o Dropbox. Con la campaña de Navidad encima, perder la tienda sin copia es un riesgo que no merece la pena correr. Configúralo **el primer día**, no el último.

### 4. ShortPixel — optimización de imágenes
**Gratis hasta 100 imágenes/mes**, luego ~10 €/año

Convierte a WebP y comprime. Tus fotos de producto van a ser grandes y pesadas, y en móvil eso es abandono directo del carrito.

### 5. Caché
**Gratis o ~60 €/año**

Si el hosting es LiteSpeed (Webempresa, Raiola, SiteGround), usa **LiteSpeed Cache**: es gratis y va mejor que cualquier alternativa de pago. Si no, **WP Rocket** (~60 €/año).

**Importante:** excluye del caché las páginas de carrito, checkout y mi cuenta, o los clientes verán el carrito de otro.

### 6. Wordfence — seguridad
**Gratis**

Cortafuegos y control de accesos. Si el hosting ya trae protección propia, puedes saltártelo para no duplicar carga.

---

## En cuanto empieces a vender

### 7. Brevo — email y carritos abandonados
**Gratis hasta 300 emails/día**, planes desde ~9 €/mes

Elegido sobre Mailchimp por dos razones: es **empresa francesa** (sin el problema de transferencias a EE. UU.) y en el plan gratuito ya incluye automatizaciones.

Lo que de verdad importa aquí: **recuperación de carritos abandonados**. En ticket alto, entre el 10 % y el 30 % de los carritos abandonados se recuperan con una secuencia de dos o tres emails. Es la automatización con mejor retorno que puedes montar.

Configura también los **emails transaccionales** (confirmación de pedido, envío) desde Brevo, no desde WordPress: los correos que manda WordPress por su cuenta acaban en spam con mucha frecuencia.

### 8. Google Analytics 4 + Google Search Console
**Gratis**

GA4 con **Consent Mode v2** activado desde Complianz. Search Console es igual de importante y se olvida siempre: te dice por qué búsquedas te encuentran y qué páginas se están indexando mal.

Activa el **seguimiento de comercio electrónico** para ver qué producto vende y cuál solo recibe visitas.

### 9. Google Merchant Center
**Gratis** (la publicidad ya no)

Sube tu catálogo para que los productos aparezcan en la pestaña Shopping. Hay **fichas gratuitas** además de las de pago, así que merece la pena aunque no vayas a invertir todavía. Plugin: *Product Feed PRO* (gratis).

---

## Para la campaña de Navidad

### 10. Meta Pixel + catálogo
**Gratis** (la publicidad no)

Instálalo **ya**, aunque no vayas a anunciarte hasta octubre. El píxel necesita tiempo acumulando datos para que las campañas funcionen: si lo pones el día que lanzas la campaña, empiezas a ciegas.

Con el catálogo subido puedes hacer **retargeting dinámico** — enseñarle a quien vio un jamonero exactamente ese jamonero. Es lo más rentable que existe en producto regalo.

### 11. Google Ads
Presupuesto aparte

Para Navidad, campañas de Shopping y de marca. No lo montes en septiembre: en octubre, con la web ya rodada y el píxel con datos.

---

## Lo que NO te recomiendo instalar

**Elementor o cualquier maquetador.** El tema ya es de bloques y editable desde el editor nativo. Un maquetador encima duplicaría el peso y ralentizaría la web sin aportarte nada.

**Plugins de reseñas de pago.** WooCommerce ya trae valoraciones. Cuando tengas volumen, valora Judge.me o Trustpilot.

**Chat en vivo.** Solo si vas a atenderlo de verdad. Un chat sin nadie detrás es peor que no tenerlo.

**Plugins "todo en uno" de optimización.** Se solapan entre sí y provocan fallos difíciles de diagnosticar.

---

## Coste anual del stack

| Concepto | Coste |
|---|---|
| Complianz, Rank Math, UpdraftPlus, Wordfence, GA4, Search Console, Merchant Center | **0 €** |
| ShortPixel | ~10 €/año |
| Caché (0 € si LiteSpeed, si no WP Rocket) | 0–60 €/año |
| Brevo (gratis al inicio) | 0–110 €/año |
| **Total software** | **10–180 €/año** |

Publicidad y hosting van aparte.

---

## Orden de instalación

1. Copias de seguridad (UpdraftPlus) — **antes que nada**
2. Caché + ShortPixel
3. Rank Math + Search Console
4. Complianz, configurado y probado
5. GA4 con Consent Mode
6. Meta Pixel
7. Brevo y la secuencia de carrito abandonado
8. Merchant Center

**No instales analítica ni píxeles antes que Complianz.** Si los scripts se cargan sin consentimiento previo, aunque sea unos días, estás incumpliendo — y es exactamente el tipo de cosa por la que llegan las reclamaciones.
