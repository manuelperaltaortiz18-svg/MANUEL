# Checklist de entrega

> **Ninguna web se enseña al cliente sin pasar esta lista entera.**
> Un fallo tonto en la vista previa (un teléfono que no marca, la web rota en
> el móvil) cuesta el proyecto. Recorrerla entera son 15 minutos.

---

## A. Antes de mandar el enlace de vista previa

### Contenido
- [ ] **Cero tokens `[[...]]` en el HTML** → `grep -rn "\[\[" .`
- [ ] Cero "Lorem ipsum" y cero texto de plantilla sin sustituir
- [ ] Nombre del negocio escrito igual en todas partes (mayúsculas, tildes)
- [ ] Teléfono, email y dirección **verificados con el cliente**, no copiados de Google
- [ ] Horarios correctos, incluidos festivos y cierres
- [ ] Precios revisados por el cliente *(un precio mal puesto es un problema legal)*
- [ ] Sin datos inventados: nada de reseñas, logos de clientes, cifras ni premios falsos
- [ ] Ortografía revisada — el corrector no pilla "haber/a ver" ni "hay/ahí"

### Funcionamiento
- [ ] Cada enlace del menú lleva a algún sitio real. **Cero `href="#"`**
- [ ] `tel:` marca en móvil (probar en un teléfono real, no en el simulador)
- [ ] `mailto:` abre el cliente de correo
- [ ] El formulario **envía de verdad** y llega al email del cliente (prueba real)
- [ ] El formulario muestra confirmación tras enviar
- [ ] Enlace de Google Maps abre en la ubicación correcta
- [ ] Enlaces externos con `target="_blank" rel="noopener"`
- [ ] Cero errores en la consola del navegador (F12)

### Dispositivos
- [ ] iPhone (Safari) — **el 70 % del tráfico local**
- [ ] Android (Chrome)
- [ ] Escritorio 1440 px
- [ ] Ventana estrecha 320 px: **sin scroll horizontal**
- [ ] Modo oscuro del sistema: legible, sin texto invisible
- [ ] Botones con al menos 44 px de alto

### Imágenes
- [ ] Ninguna imagen pesa más de 300 KB (convertir a WebP)
- [ ] Todas con `alt` descriptivo (no "imagen1.jpg")
- [ ] `loading="lazy"` en todas menos la del hero
- [ ] Sin deformar: `object-fit: cover` y proporción correcta
- [ ] Nada descargado de Google Imágenes. **Licencia comprobada.**

### Velocidad y SEO
- [ ] PageSpeed móvil > 85 (`pagespeed.web.dev`)
- [ ] `<title>` único, ~60 caracteres, con ciudad si es negocio local
- [ ] `meta description` ~155 caracteres, escrita para que la cliqueen
- [ ] Un solo `<h1>` por página
- [ ] Open Graph con imagen — probar cómo se ve al pegar el enlace en WhatsApp
- [ ] Favicon puesto
- [ ] Datos estructurados válidos (`search.google.com/test/rich-results`)
- [ ] `sitemap.xml` y `robots.txt` creados

### Accesibilidad
- [ ] Contraste de texto ≥ 4.5:1 en claro y en oscuro
- [ ] Navegable con Tab, con foco visible
- [ ] Todos los campos del formulario con su `<label>`
- [ ] `lang="es"` en `<html>`

### Legal (España — LSSI-CE y RGPD)
- [ ] Aviso legal con **razón social, NIF y domicilio reales del cliente**
- [ ] Política de privacidad con responsable, finalidad y derechos
- [ ] Política de cookies **coherente con lo que la web usa de verdad**
- [ ] Casilla de consentimiento en el formulario, **sin premarcar**
- [ ] Enlace a la política de privacidad junto a la casilla
- [ ] Si hay Analytics u otras cookies no esenciales → banner que **bloquea
      hasta aceptar**. Si no hay cookies, no poner banner: molesta y no hace falta.

---

## B. Enviar la vista previa

- [ ] Desplegada en una URL de vista previa (ver `deploy/DEPLOY.md`)
- [ ] Vista previa **con `noindex`** para que Google no la indexe antes de tiempo
- [ ] Email al cliente con: el enlace, qué mirar, y **fecha límite para los
      cambios** ("mándame todo junto antes del viernes")
- [ ] Recordar que la ronda de cambios incluida es **una lista, no un goteo**

---

## C. Antes de publicar con el dominio del cliente

- [ ] Cambios de la ronda aplicados y confirmados por escrito
- [ ] **100 % de la factura cobrado** ✅
- [ ] `noindex` **quitado**
- [ ] Dominio apuntando y HTTPS activo (candado en el navegador)
- [ ] Redirección de `www` al dominio principal (o al revés), no las dos vivas
- [ ] URLs absolutas del `canonical` y del Open Graph con el dominio final
- [ ] Google Search Console verificado y sitemap enviado
- [ ] Analytics recibiendo datos

---

## D. Entrega al cliente

Enviar en un solo email:

- [ ] URL final
- [ ] Accesos: panel del dominio, panel de alojamiento, email del formulario
- [ ] Copia del proyecto (ZIP o repositorio) — **la web es suya**
- [ ] Documento de una página: cómo cambiar horarios, precios y fotos
- [ ] Factura final
- [ ] **Oferta del plan de mantenimiento** *(hoy es cuando más contento está)*
- [ ] Petición de reseña en Google **y** de una foto/captura para tu portfolio
- [ ] Petición de referidos: *"¿conoces a alguien más que lo necesite?"*

---

## E. Seguimiento

- [ ] Día +7: "¿todo bien? ¿ha entrado alguna llamada?"
- [ ] Día +30: enviar el dato de visitas. Es la mejor venta del mantenimiento.
- [ ] Día +90: proponer mejora concreta *(blog, más fotos, segunda página)*
