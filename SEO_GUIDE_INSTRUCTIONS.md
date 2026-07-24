# Guía SEO Completa 2026 — CUPERINOX.ES (WooCommerce)

## Objetivo

Instrucciones de SEO para posicionar www.cuperinox.es en el top de Google, ChatGPT Search y buscadores de IA (Perplexity, Gemini, Claude). Adaptado específicamente a una tienda WooCommerce de cuchillería, navajas, tijeras, jamoneros y menaje profesional de Albacete.

**CONTEXTO DE LA WEB:**
- Dominio: www.cuperinox.es
- Plataforma: WooCommerce (WordPress)
- Sector: Cuchillería y menaje profesional
- Sede: Albacete, España (75 años de tradición cuchillera)
- Categorías principales: Navajas, Cuchillos, Tijeras (Couture Series), Soportes Jamoneros, Menaje
- Venta también en: Amazon.es, Leroy Merlin, Makro, distribuidores
- Público: España, B2C + hostelería

---

# PARTE 1: PROBLEMAS SEO DETECTADOS EN CUPERINOX.ES

## 1.1 Problemas Críticos a Resolver

### 1. Títulos de producto demasiado largos y no optimizados
Los títulos actuales son tipo catálogo de Amazon, no SEO:
```
MALO: "CUPERINOX Navaja 5 en1 multiusos | Incluye Afilador Navaja| Funcion Abrebotella, rompecristales y corta cuerdas| Navaja Filo Liso y Sierra|"
BIEN: "Navaja Multiusos 5 en 1 con Afilador | Cuperinox"
```

**Regla**: Title tag < 60 caracteres, keyword principal al inicio, marca al final.

### 2. URLs de producto no optimizadas
Algunas URLs usan IDs numéricos (`/producto/1874/`) en vez de slugs descriptivos.
```
MALO: /producto/1874/
BIEN: /producto/navaja-multiusos-5-en-1-afilador/
```

### 3. Competencia con Amazon por tus propias keywords
Amazon rankea por "cuperinox navaja", "cuperinox jamonero", etc. Tu web propia debería ganar esas búsquedas de marca.

**Solución**: Optimizar fichas de producto con contenido único y superior al de Amazon (descripciones más largas, más fotos, más schema, reviews propias).

### 4. Categorías con poco contenido
Las páginas de categoría (`/categoria-producto/navajas/`) probablemente solo listan productos sin texto. Google necesita contenido propio en las categorías para rankearlas.

### 5. Firewall bloqueando bots
La web devuelve 403 a peticiones de bots. Verificar que no se esté bloqueando a Googlebot ni a los bots de IA.

---

# PARTE 2: SEO GOOGLE PARA WOOCOMMERCE

## 2.1 Core Web Vitals

WooCommerce es notoriamente lento. Las tres métricas obligatorias:

- **LCP (Largest Contentful Paint)**: < 2.5 segundos
- **CLS (Cumulative Layout Shift)**: < 0.1
- **INP (Interaction to Next Paint)**: < 200ms

### Optimizaciones específicas WooCommerce:

**Velocidad:**
- Instalar plugin de caché: WP Rocket, LiteSpeed Cache o W3 Total Cache
- CDN para imágenes y assets (Cloudflare, BunnyCDN)
- Imágenes en WebP con lazy loading (usar Imagify o ShortPixel)
- Limitar plugins a los esenciales (cada plugin añade JS/CSS)
- Desactivar scripts de WooCommerce en páginas que no son tienda
- Usar Object Cache (Redis o Memcached) para las queries de WooCommerce
- Optimizar base de datos: limpiar revisiones, transients, logs de WooCommerce

**CLS en WooCommerce:**
- Definir width/height en todas las imágenes de producto
- Reservar espacio para banners, sliders y botones de "añadir al carrito"
- No cargar pop-ups que empujen el contenido

**INP en WooCommerce:**
- Minimizar JS: desactivar jQuery migrate si no es necesario
- Defer scripts no críticos
- Evitar sliders pesados en home

### Plugins recomendados para velocidad:
```
- WP Rocket o LiteSpeed Cache (caché)
- Imagify o ShortPixel (compresión imágenes WebP)
- Perfmatters (desactivar scripts innecesarios por página)
- Asset CleanUp (controlar qué CSS/JS carga en cada página)
```

## 2.2 E-E-A-T para Cuperinox

### Experience (Experiencia):
- Fotos propias del taller/fábrica en Albacete
- Videos del proceso de fabricación
- Contenido tipo "cómo se hace una navaja artesanal"
- Testimonios de clientes profesionales (hostelería, carnicerías)

### Expertise (Expertise):
- Página "Quiénes somos" ampliada: 75 años de historia, evolución desde Cuchillería Peralta
- Blog con guías especializadas: "Cómo elegir cuchillo jamonero", "Tipos de acero inoxidable"
- Fichas de producto con información técnica detallada (tipo de acero, dureza Rockwell, ángulo de filo)

### Authoritativeness (Autoridad):
- Conseguir enlaces desde: asociaciones de cuchillería de Albacete, ADECA, cámaras de comercio
- Presencia en directorios del sector: QDQ, Empresite, Axesor (ya están)
- Artículos en medios locales/sectoriales

### Trustworthiness (Confianza):
- HTTPS (verificar que esté activo en todo el sitio)
- Política de devoluciones visible
- Datos de contacto completos (dirección del Polígono Campollano)
- Certificaciones y sellos de calidad si los hay
- Reviews verificadas en fichas de producto

## 2.3 Optimización de Fichas de Producto WooCommerce

### Estructura ideal de ficha de producto:

```
TITLE TAG: Keyword Principal | Cuperinox (< 60 chars)
META DESC: Descripción compelling con keyword + beneficio + CTA (150-160 chars)
URL: /producto/keyword-principal/

H1: Nombre del producto con keyword natural
  Precio visible
  Botón "Añadir al carrito" above the fold
  
  Galería de imágenes (mín. 5 fotos):
    - Producto completo sobre fondo blanco
    - Producto en uso
    - Detalle del filo/material
    - Packaging
    - Comparativa de tamaño
  
  Descripción corta (extracto WooCommerce):
    2-3 frases con el beneficio principal y keyword
  
  H2: Características técnicas
    Tabla con: Material, Longitud hoja, Longitud total, Peso, Tipo de filo, Dureza
  
  H2: Descripción detallada
    3-4 párrafos: para qué sirve, por qué es mejor, cómo usarlo
    Claims autocontenidos (cada párrafo funciona solo para GEO)
  
  H2: ¿Para quién es este producto?
    Casos de uso específicos
  
  H2: Preguntas frecuentes
    H3: ¿Qué tipo de acero usa?
    H3: ¿Cómo se afila?
    H3: ¿Incluye funda/estuche?
    H3: ¿Tiene garantía?
  
  Reviews de clientes
  Productos relacionados (cross-selling)
  Breadcrumbs: Inicio > Categoría > Producto
```

### Ejemplo real para Cuperinox:

```html
<title>Navaja Multiusos 5 en 1 con Afilador | Cuperinox</title>
<meta name="description" content="Navaja plegable 5 en 1 de acero inoxidable con afilador integrado, abrebotella y cortacuerdas. Fabricada en Albacete. Envío 24-48h. Garantía Cuperinox.">

<h1>Navaja Multiusos 5 en 1 con Afilador Integrado</h1>

<p>La navaja multiusos Cuperinox 5 en 1 combina cinco herramientas en un 
diseño compacto de acero inoxidable: hoja de filo liso, sierra, abrebotella, 
rompecristales y cortacuerdas. Incluye afilador integrado en la funda.</p>

<h2>Características técnicas</h2>
<table>
  <tr><td>Material</td><td>Acero inoxidable AISI 420</td></tr>
  <tr><td>Longitud hoja</td><td>8,5 cm</td></tr>
  <tr><td>Longitud total</td><td>21 cm (abierta) / 12 cm (cerrada)</td></tr>
  <tr><td>Peso</td><td>185 g</td></tr>
  <tr><td>Bloqueo</td><td>Liner lock</td></tr>
  <tr><td>Fabricación</td><td>Albacete, España</td></tr>
</table>
```

## 2.4 Optimización de Categorías WooCommerce

Las categorías son las páginas que más potencial SEO tienen en WooCommerce. Por defecto solo muestran un grid de productos — necesitan contenido propio.

### Estructura ideal de página de categoría:

```
URL: /categoria-producto/navajas/
TITLE: Navajas de Acero Inoxidable | Comprar Online | Cuperinox
META DESC: Navajas profesionales fabricadas en Albacete. Acero inoxidable, bloqueo de seguridad, multiusos. Desde 12,95€. Envío 24-48h. Garantía Cuperinox.

H1: Navajas de Acero Inoxidable Cuperinox

[Texto introductorio ANTES del grid de productos — 150-300 palabras]
  Párrafo 1: Qué ofrece la categoría, keyword principal
  Párrafo 2: Por qué elegir Cuperinox (E-E-A-T, fabricación Albacete)
  Párrafo 3: Tipos disponibles (enlace a subcategorías si hay)

[Grid de productos]

[Texto adicional DESPUÉS del grid — 200-400 palabras]
  H2: ¿Cómo elegir la mejor navaja?
    Guía breve de compra
  
  H2: Preguntas frecuentes sobre navajas
    H3: ¿Qué tipo de acero es mejor?
    H3: ¿Son legales las navajas en España?
    H3: ¿Cómo se mantiene una navaja?
  
  Internal links a: blog posts relacionados, otras categorías
```

### Categorías principales a optimizar:

| Categoría | Keyword principal | Long tail keywords |
|-----------|------------------|--------------------|
| Navajas | navajas acero inoxidable | navaja multiusos, navaja camping, navaja albacete |
| Cuchillos | cuchillos profesionales | cuchillo jamonero, cuchillo cocina, set cuchillos |
| Tijeras | tijeras profesionales | tijeras costura, tijeras cocina, tijeras peluquería |
| Jamoneros | soporte jamonero | jamonero profesional, jamonero madera, set jamonero cuchillo |
| Menaje | menaje cocina profesional | utensilios cocina, menaje hostelería |

## 2.5 Schema Markup para WooCommerce

### Schema Product (CRÍTICO — cada ficha de producto):

```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "Navaja Multiusos 5 en 1 con Afilador",
  "image": [
    "https://www.cuperinox.es/wp-content/uploads/navaja-5en1-1.webp",
    "https://www.cuperinox.es/wp-content/uploads/navaja-5en1-2.webp"
  ],
  "description": "Navaja plegable 5 en 1 de acero inoxidable con afilador integrado, fabricada en Albacete.",
  "brand": {
    "@type": "Brand",
    "name": "Cuperinox"
  },
  "manufacturer": {
    "@type": "Organization",
    "name": "Cuperinox, S.L.",
    "address": {
      "@type": "PostalAddress",
      "streetAddress": "Calle D, 44, Polígono Industrial Campollano",
      "addressLocality": "Albacete",
      "postalCode": "02007",
      "addressCountry": "ES"
    }
  },
  "material": "Acero inoxidable AISI 420",
  "countryOfOrigin": {
    "@type": "Country",
    "name": "España"
  },
  "offers": {
    "@type": "Offer",
    "url": "https://www.cuperinox.es/producto/navaja-multiusos-5-en-1/",
    "priceCurrency": "EUR",
    "price": "24.95",
    "availability": "https://schema.org/InStock",
    "seller": {
      "@type": "Organization",
      "name": "Cuperinox"
    },
    "shippingDetails": {
      "@type": "OfferShippingDetails",
      "shippingDestination": {
        "@type": "DefinedRegion",
        "addressCountry": "ES"
      },
      "deliveryTime": {
        "@type": "ShippingDeliveryTime",
        "handlingTime": {
          "@type": "QuantitativeValue",
          "minValue": 1,
          "maxValue": 2,
          "unitCode": "d"
        },
        "transitTime": {
          "@type": "QuantitativeValue",
          "minValue": 1,
          "maxValue": 3,
          "unitCode": "d"
        }
      }
    },
    "hasMerchantReturnPolicy": {
      "@type": "MerchantReturnPolicy",
      "returnPolicyCategory": "https://schema.org/MerchantReturnFiniteReturnWindow",
      "merchantReturnDays": 14,
      "returnMethod": "https://schema.org/ReturnByMail",
      "returnFees": "https://schema.org/FreeReturn"
    }
  },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.7",
    "reviewCount": "23"
  },
  "review": [
    {
      "@type": "Review",
      "author": {"@type": "Person", "name": "Cliente verificado"},
      "datePublished": "2026-03-15",
      "reviewRating": {
        "@type": "Rating",
        "ratingValue": "5"
      },
      "reviewBody": "Excelente navaja, muy robusta y el afilador integrado es muy práctico."
    }
  ]
}
```

### Schema Organization (una vez, en toda la web):

```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "@id": "https://www.cuperinox.es/#organization",
  "name": "Cuperinox, S.L.",
  "alternateName": "Cuperinox",
  "url": "https://www.cuperinox.es",
  "logo": "https://www.cuperinox.es/wp-content/uploads/logo-cuperinox.png",
  "description": "Fabricante de cuchillería y menaje profesional de Albacete con 75 años de tradición. Cuchillos, navajas, tijeras y jamoneros de acero inoxidable.",
  "foundingDate": "2004",
  "founder": {
    "@type": "Person",
    "name": "Familia Peralta"
  },
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "Calle D, 44, Polígono Industrial Campollano",
    "addressLocality": "Albacete",
    "addressRegion": "Castilla-La Mancha",
    "postalCode": "02007",
    "addressCountry": "ES"
  },
  "sameAs": [
    "https://www.amazon.es/stores/CUPERINOX/page/XXXXX",
    "https://www.leroymerlin.es/vendedor/cuperinox.html",
    "https://www.makro.es/marketplace/b/cuperinox",
    "https://www.instagram.com/cuperinox/",
    "https://www.facebook.com/cuperinox/"
  ],
  "contactPoint": {
    "@type": "ContactPoint",
    "contactType": "customer service",
    "availableLanguage": ["Spanish"]
  },
  "knowsAbout": [
    "Cuchillería",
    "Navajas",
    "Cuchillos profesionales",
    "Jamoneros",
    "Menaje de cocina",
    "Acero inoxidable",
    "Tradición cuchillera de Albacete"
  ]
}
```

### Schema BreadcrumbList:

```json
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {"@type": "ListItem", "position": 1, "name": "Inicio", "item": "https://www.cuperinox.es/"},
    {"@type": "ListItem", "position": 2, "name": "Navajas", "item": "https://www.cuperinox.es/categoria-producto/navajas/"},
    {"@type": "ListItem", "position": 3, "name": "Navaja Multiusos 5 en 1"}
  ]
}
```

### Schema FAQPage (en categorías y productos):

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "¿Qué tipo de acero usan las navajas Cuperinox?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Las navajas Cuperinox están fabricadas con acero inoxidable AISI 420, un acero de alta resistencia a la corrosión con excelente capacidad de afilado y retención del filo. Toda la producción se realiza en Albacete, España."
      }
    },
    {
      "@type": "Question",
      "name": "¿Son legales las navajas Cuperinox en España?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Sí. Las navajas con hoja inferior a 11 cm son legales para llevar en España. Las navajas Cuperinox cumplen con la normativa vigente. Para actividades de caza o campo, se permite portar navajas de mayor tamaño con justificación."
      }
    },
    {
      "@type": "Question",
      "name": "¿Cuperinox envía a toda España?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Sí, Cuperinox envía a toda España peninsular en 24-48 horas. También se realizan envíos a Baleares, Canarias y Europa con plazos y tarifas específicas."
      }
    }
  ]
}
```

### Plugin recomendado para Schema en WooCommerce:
```
- Rank Math SEO (incluye schema Product automático + FAQPage + Organization)
- O Yoast SEO Premium + WooCommerce SEO addon
- Evitar instalar ambos — elegir UNO
```

## 2.6 SEO Técnico WooCommerce — Checklist Cuperinox

### URLs y estructura:
- [ ] Cambiar URLs de producto con IDs numéricos a slugs descriptivos
- [ ] Estructura: `/producto/nombre-producto/` (no `/producto/1874/`)
- [ ] Categorías: `/categoria-producto/navajas/` (OK, mantener)
- [ ] Configurar permalinks en WP: Ajustes > Enlaces permanentes > Nombre de la entrada
- [ ] Redirección 301 de URLs viejas a nuevas

### Contenido duplicado (problema grave en WooCommerce):
- [ ] Canonical tags en todas las variaciones de producto
- [ ] Noindex en: tags de producto, páginas de filtros, resultados de búsqueda interna
- [ ] Noindex en páginas de paginación (?page=2, ?page=3...)
- [ ] No permitir que los filtros de precio/color/tamaño creen URLs indexables
- [ ] Un solo producto = una sola URL canónica

```php
// En functions.php — noindex para tags de WooCommerce
add_action('wp_head', function() {
    if (is_product_tag()) {
        echo '<meta name="robots" content="noindex, follow">';
    }
});
```

### Imágenes de producto:
- [ ] Todas en formato WebP (usar Imagify o ShortPixel)
- [ ] Alt text descriptivo: "Navaja multiusos 5 en 1 Cuperinox acero inoxidable"
- [ ] Nombre de archivo descriptivo: `navaja-multiusos-5en1-cuperinox.webp` (no `IMG_4532.jpg`)
- [ ] Mínimo 5 fotos por producto
- [ ] Dimensiones definidas (width/height) para evitar CLS

### Páginas innecesarias a noindex:
- [ ] Mi cuenta (`/mi-cuenta/`)
- [ ] Carrito (`/carrito/`)
- [ ] Finalizar compra (`/finalizar-compra/`)
- [ ] Tags de producto
- [ ] Resultados de búsqueda interna
- [ ] Páginas de archivo por fecha

### Internal linking:
- [ ] Productos relacionados configurados manualmente (no solo automáticos)
- [ ] Cross-selling y up-selling en cada ficha
- [ ] Breadcrumbs activos con schema
- [ ] Menú de navegación con categorías principales
- [ ] Blog posts que enlacen a fichas de producto

## 2.7 robots.txt para Cuperinox

```
User-agent: *
Allow: /
Disallow: /mi-cuenta/
Disallow: /carrito/
Disallow: /finalizar-compra/
Disallow: /wp-admin/
Disallow: /wp-login.php
Disallow: /*?add-to-cart=*
Disallow: /*?orderby=*
Disallow: /*?filter*
Allow: /wp-admin/admin-ajax.php

# BOTS DE IA — PERMITIR TODOS
User-agent: GPTBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: OAI-SearchBot
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: Applebot-Extended
Allow: /

User-agent: anthropic-ai
Allow: /

User-agent: Bytespider
Allow: /

User-agent: cohere-ai
Allow: /

Sitemap: https://www.cuperinox.es/sitemap.xml
```

### IMPORTANTE — Firewall/WAF:
Verificar en Cloudflare/Wordfence/Sucuri que NO se esté bloqueando a:
- Googlebot
- GPTBot
- OAI-SearchBot
- PerplexityBot
- ClaudeBot

Si usas Wordfence, ir a: Wordfence > Firewall > Blocking > verificar que estos user-agents no están bloqueados.

Si usas Cloudflare, ir a: Security > WAF > Custom Rules > crear regla para permitir estos bots.

## 2.8 Sitemap XML

Configurar con Rank Math o Yoast. Debe incluir:

```xml
<!-- Sitemaps separados: -->
sitemap-products.xml    <!-- Todas las fichas de producto -->
sitemap-categories.xml  <!-- Categorías de producto -->
sitemap-pages.xml       <!-- Páginas estáticas (quiénes somos, contacto) -->
sitemap-posts.xml       <!-- Posts del blog -->

<!-- NO incluir: -->
<!-- Tags de producto -->
<!-- Páginas de carrito/checkout/mi-cuenta -->
<!-- Páginas de filtros -->
```

---

# PARTE 3: SEO PARA CHATGPT SEARCH — CUPERINOX

## 3.1 Cómo ChatGPT Podría Citar a Cuperinox

Cuando alguien pregunte a ChatGPT:
- "¿Cuál es el mejor cuchillo jamonero español?"
- "¿Dónde comprar navajas de Albacete?"
- "¿Qué jamonero profesional comprar?"

ChatGPT debe encontrar y citar a cuperinox.es. Para eso:

### 3.1.1 Claridad de Entidad

ChatGPT debe entender QUÉ es Cuperinox. Necesita:

1. **Schema Organization completo** (ver sección 2.5)
2. **Página "Quiénes somos" optimizada** con:
   - Historia: 75 años, evolución desde Cuchillería Peralta
   - Ubicación: Albacete, capital de la cuchillería española
   - Qué fabrican: lista clara de categorías
   - Diferenciación: fabricación propia, acero inoxidable, tradición artesanal
3. **Presencia consistente** en directorios:
   - Wikipedia (artículo de cuchillería de Albacete que mencione a Cuperinox)
   - Google Business Profile actualizado
   - Directorios: QDQ, Empresite, Axesor, ADECA (ya están, mantener actualizados)

### 3.1.2 Contenido que ChatGPT Extraiga

Cada página debe tener **pasajes autocontenidos** que la IA pueda citar:

```
EJEMPLO — En la página de categoría "Jamoneros":

"Cuperinox fabrica jamoneros profesionales de madera y acero inoxidable 
en Albacete desde 2004. El jamonero góndola Cuperinox es el modelo más 
vendido para uso doméstico, con base antideslizante y pincho regulable. 
Precio desde 39,95€ con envío en 24-48h a toda España."
```

Ese párrafo puede ser citado tal cual por ChatGPT. Contiene: qué es, quién lo hace, dónde, modelo concreto, precio, envío.

### 3.1.3 Blog con Contenido de Autoridad

Crear artículos que respondan preguntas que la gente hace a ChatGPT:

| Pregunta conversacional | Artículo del blog |
|------------------------|-------------------|
| "¿Cuál es el mejor cuchillo jamonero?" | "Guía: Cómo Elegir el Mejor Cuchillo Jamonero en 2026" |
| "¿Qué navaja comprar para camping?" | "Las 5 Mejores Navajas para Camping y Outdoor" |
| "¿Cómo se afila un cuchillo correctamente?" | "Guía Completa: Cómo Afilar Cuchillos como un Profesional" |
| "¿Son legales las navajas en España?" | "Normativa sobre Navajas en España: Qué Puedes y Qué No" |
| "¿Qué tijeras de costura comprar?" | "Tijeras de Costura Profesionales: Guía de Compra 2026" |
| "¿Qué regalo para alguien que le gusta cocinar?" | "10 Regalos de Cocina para Foodies: Cuchillos y Menaje Premium" |
| "¿Diferencia entre acero inoxidable y acero al carbono?" | "Acero Inoxidable vs Acero al Carbono en Cuchillos: ¿Cuál Elegir?" |

Cada artículo debe:
- Responder la pregunta en las primeras 2 frases
- Incluir datos propios (de Cuperinox como fabricante)
- Mencionar productos Cuperinox con enlace interno
- Tener FAQ section con schema

## 3.2 Métricas ChatGPT para Cuperinox

- Monitorizar tráfico referral desde `chatgpt.com` en Google Analytics 4
- Buscar periódicamente en ChatGPT: "mejor cuchillo jamonero", "navajas Albacete", "comprar navajas online España" — verificar si Cuperinox aparece
- Citation Rate objetivo: aparecer en al menos 1 de cada 4 consultas relevantes

---

# PARTE 4: GEO — GENERATIVE ENGINE OPTIMIZATION PARA CUPERINOX

## 4.1 Por Qué GEO es Crucial para Cuperinox

Los buscadores IA manejan ya un 12-18% de las consultas informacionales (Q1 2026). Para un e-commerce de nicho como Cuperinox, esto significa:

- Cuando alguien pregunta a Perplexity "mejores navajas españolas", Cuperinox debe aparecer
- Cuando alguien pregunta a Gemini "jamonero profesional recomendado", Cuperinox debe ser citado
- La unidad de optimización es el PASAJE, no la página

## 4.2 Tácticas GEO Específicas para Cuperinox

### 4.2.1 Claims Verificables en Cada Página

```
BUENO (citable por IA):
"Cuperinox es un fabricante español de cuchillería fundado en Albacete en 2004, 
continuando 75 años de tradición de Cuchillería Peralta. Fabrica navajas, 
cuchillos, tijeras y jamoneros de acero inoxidable en el Polígono Industrial 
Campollano de Albacete."

MALO (no citable):
"Somos una empresa con mucha experiencia en el sector que fabrica productos 
de gran calidad para nuestros clientes."
```

### 4.2.2 Datos Originales que las IAs Prioricen

Como fabricante, Cuperinox tiene datos que nadie más tiene:
- "El 73% de nuestras navajas se venden para uso outdoor y camping"
- "Cada cuchillo jamonero Cuperinox se afila a mano con ángulo de 15°"
- "Producimos más de X.000 navajas al año en nuestra fábrica de Albacete"
- "El acero AISI 420 que usamos tiene una dureza de 54-56 HRC"

Estos datos originales son ORO para GEO — las IAs priorizan fuentes primarias.

### 4.2.3 Formato de Contenido para Extracción IA

**Definiciones claras:**
```
"Un jamonero góndola es un soporte para jamón con forma de barco que permite 
fijar la pieza de jamón en posición horizontal. Se diferencia del jamonero de 
pincho por su mayor estabilidad y facilidad de corte."
```

**Tablas comparativas:**
```html
<table>
  <caption>Comparativa de Jamoneros Cuperinox</caption>
  <thead>
    <tr><th>Modelo</th><th>Material</th><th>Uso</th><th>Precio</th></tr>
  </thead>
  <tbody>
    <tr><td>Góndola Profesional</td><td>Madera + acero</td><td>Hostelería</td><td>89,95€</td></tr>
    <tr><td>Góndola Doméstico</td><td>Madera</td><td>Hogar</td><td>49,95€</td></tr>
    <tr><td>Pincho Básico</td><td>Madera</td><td>Hogar</td><td>29,95€</td></tr>
  </tbody>
</table>
```

**Listas de recomendación:**
```
Las 3 mejores navajas Cuperinox para camping son:
1. Navaja Outdoor Series Camuflaje — acero inoxidable negro, mango antideslizante
2. Navaja Multiusos 5 en 1 — con afilador, abrebotella y cortacuerdas integrados
3. Navaja Bloqueo Seguridad — liner lock, hoja de 8.5cm, ideal para EDC
```

## 4.3 robots.txt para Bots IA

Ver sección 2.7 — verificar especialmente que:
- GPTBot NO está bloqueado
- OAI-SearchBot NO está bloqueado
- PerplexityBot NO está bloqueado
- El WAF/firewall no devuelve 403 a estos bots

---

# PARTE 5: PLAN DE ACCIÓN — PRIORIDADES

## Prioridad 1 — URGENTE (semana 1-2):
1. Verificar que el firewall no bloquea Googlebot ni bots de IA
2. Instalar/configurar Rank Math SEO (schema automático para productos)
3. Corregir URLs de productos con IDs numéricos → slugs descriptivos
4. Configurar robots.txt correcto (ver sección 2.7)
5. Verificar sitemap XML en Google Search Console

## Prioridad 2 — IMPORTANTE (semana 3-4):
6. Optimizar títulos y meta descriptions de TODOS los productos
7. Añadir contenido a páginas de categoría (texto intro + FAQ)
8. Ampliar descripciones de producto (mín. 300 palabras cada una)
9. Optimizar imágenes (WebP, alt text, nombres descriptivos)
10. Configurar Schema Organization completo

## Prioridad 3 — CRECIMIENTO (mes 2-3):
11. Crear blog con los artículos de la tabla de la sección 3.1.3
12. Implementar reviews de clientes con schema
13. Optimizar velocidad (caché, CDN, limpieza de plugins)
14. Construir internal linking entre productos, categorías y blog
15. Conseguir backlinks de asociaciones de Albacete, medios sectoriales

## Prioridad 4 — MANTENIMIENTO (continuo):
16. Actualizar contenido existente cada 3-6 meses
17. Monitorizar Citation Rate en ChatGPT, Perplexity, Gemini
18. Monitorizar tráfico referral de IAs en GA4
19. Publicar 2-4 artículos de blog al mes
20. Responder reviews de clientes

---

# PARTE 6: PLUGINS WOOCOMMERCE RECOMENDADOS PARA SEO

```
SEO General:
  - Rank Math SEO (FREE/PRO) — schema, titles, sitemap, redirects, todo en uno
  
Velocidad:
  - WP Rocket — caché (de pago, el mejor)
  - LiteSpeed Cache — alternativa gratuita si el hosting es LiteSpeed
  - Imagify — compresión y conversión a WebP
  - Perfmatters — desactivar scripts por página
  
Schema adicional:
  - Rank Math lo cubre todo. Si usas Yoast, añadir Schema Pro.
  
Reviews:
  - Site Reviews — reviews con schema automático
  - O activar reviews nativas de WooCommerce + schema de Rank Math
  
Analytics:
  - Google Site Kit — conectar Analytics + Search Console desde WP
  - Rank Math Analytics — métricas SEO dentro del dashboard
  
Seguridad (sin bloquear bots):
  - Wordfence — pero configurar whitelist para bots de IA
  - Cloudflare — crear regla Allow para user-agents de bots IA
```

---

# PARTE 7: REFERENCIA RÁPIDA

## Bots de IA — User Agents

| Bot | Propietario | Función |
|-----|------------|---------|
| GPTBot | OpenAI | Crawling para entrenamiento |
| ChatGPT-User | OpenAI | Browsing en tiempo real |
| OAI-SearchBot | OpenAI | ChatGPT Search |
| PerplexityBot | Perplexity | Búsqueda y citación |
| ClaudeBot | Anthropic | Crawling de Claude |
| Google-Extended | Google | Gemini / AI Overviews |
| Applebot-Extended | Apple | Apple Intelligence |
| Bytespider | ByteDance | TikTok/Doubao |

## Checklist Pre-Publicación de Producto

```
SEO GOOGLE:
[ ] Title < 60 chars, keyword al inicio, "| Cuperinox" al final
[ ] Meta description 150-160 chars con keyword + precio + CTA
[ ] URL slug descriptiva (no IDs numéricos)
[ ] H1 con keyword natural
[ ] Mín. 5 imágenes WebP con alt text descriptivo
[ ] Descripción > 300 palabras
[ ] Tabla de características técnicas
[ ] FAQ con schema FAQPage
[ ] Schema Product completo (precio, stock, reviews, envío)
[ ] Breadcrumbs con schema
[ ] Productos relacionados configurados
[ ] Internal links a categoría y blog

GEO / IA:
[ ] Respuesta directa en primeras 2 frases de la descripción
[ ] Claims autocontenidos (cada párrafo funciona solo)
[ ] Al menos 1 dato propio (como fabricante)
[ ] Formato extraíble: tablas, listas, definiciones
[ ] Contenido que responda preguntas conversacionales
```

---

*Guía creada para www.cuperinox.es — Julio 2026*
*Actualizar con cada cambio de algoritmo de Google o evolución de los buscadores IA*
