# Guía Completa SEO 2026 — Instrucciones para Claude Code

## Objetivo

Este documento contiene todas las instrucciones de SEO actualizadas a 2026 para posicionamiento en Google, ChatGPT Search y buscadores de IA (Perplexity, Gemini, Claude). Debe usarse como referencia al construir o modificar cualquier sitio web, landing page, blog o contenido digital.

---

# PARTE 1: SEO CLÁSICO — POSICIONAMIENTO EN GOOGLE

## 1.1 Core Web Vitals (Factores de Ranking Confirmados)

Las tres métricas obligatorias son:

- **LCP (Largest Contentful Paint)**: < 2.5 segundos. Es el tiempo que tarda en renderizarse el elemento visible más grande.
- **CLS (Cumulative Layout Shift)**: < 0.1. Mide la estabilidad visual (que nada "salte" mientras carga).
- **INP (Interaction to Next Paint)**: < 200ms. Reemplazó a FID en marzo 2024. Mide la latencia de interacción real del usuario.

### Cómo optimizar Core Web Vitals:

**Para LCP:**
- Comprimir y servir imágenes en formato WebP/AVIF
- Usar lazy loading en imágenes below-the-fold
- Precargar recursos críticos con `<link rel="preload">`
- Minimizar CSS y JS que bloqueen el renderizado
- Usar CDN para servir assets estáticos

**Para CLS:**
- Definir dimensiones explícitas (width/height) en todas las imágenes y videos
- Reservar espacio para ads y embeds con CSS `aspect-ratio` o contenedores de tamaño fijo
- Evitar inserción dinámica de contenido sobre contenido ya visible
- Usar `font-display: swap` para fuentes web

**Para INP:**
- Dividir tareas JavaScript largas con `requestIdleCallback` o `scheduler.yield()`
- Minimizar el trabajo del hilo principal
- Usar `content-visibility: auto` para elementos fuera de pantalla
- Debounce/throttle en event listeners pesados

### Implementación técnica:

```html
<!-- Preload del LCP element -->
<link rel="preload" as="image" href="/hero-image.webp" fetchpriority="high">

<!-- Imágenes con dimensiones explícitas -->
<img src="foto.webp" width="800" height="600" loading="lazy" alt="Descripción relevante">

<!-- Font display swap -->
@font-face {
  font-family: 'MiFuente';
  src: url('/fonts/mifuente.woff2') format('woff2');
  font-display: swap;
}
```

---

## 1.2 E-E-A-T (Experience, Expertise, Authoritativeness, Trustworthiness)

Google evalúa ecosistemas completos, no páginas aisladas. Cruza señales de contenido, comportamiento del usuario, reputación de marca, experiencia del autor y consistencia temática.

### Implementar E-E-A-T:

**Experience (Experiencia):**
- Incluir evidencia de experiencia directa: fotos propias, capturas, datos de primera mano
- Testimonios reales con nombre y contexto
- Casos de estudio basados en trabajo propio

**Expertise (Expertise):**
- Biografías de autores con credenciales verificables
- Enlazar a perfiles profesionales (LinkedIn, publicaciones académicas)
- Demostrar conocimiento profundo, no superficial

**Authoritativeness (Autoridad):**
- Conseguir menciones y backlinks de sitios reputados del sector
- Internal linking sólido entre contenidos relacionados
- Mantener consistencia temática (no escribir de todo)

**Trustworthiness (Confianza):**
- HTTPS obligatorio
- Política de privacidad, aviso legal, datos de contacto visibles
- Citar fuentes cuando se usan datos o estadísticas
- Reviews y valoraciones verificables

### Schema markup para E-E-A-T:

```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "author": {
    "@type": "Person",
    "name": "Nombre del Autor",
    "url": "https://linkedin.com/in/autor",
    "jobTitle": "Especialista en [tema]",
    "description": "15 años de experiencia en [campo]"
  },
  "publisher": {
    "@type": "Organization",
    "name": "Nombre de la Empresa",
    "logo": {
      "@type": "ImageObject",
      "url": "https://ejemplo.com/logo.png"
    }
  },
  "datePublished": "2026-01-15",
  "dateModified": "2026-07-20"
}
```

---

## 1.3 Contenido Optimizado para Google

### Reglas fundamentales:

1. **Contenido evergreen** que mantenga relevancia a largo plazo + actualización periódica con datos recientes
2. **Una keyword principal por página** + keywords secundarias semánticamente relacionadas
3. **Longitud adecuada**: no hay mínimo, pero el contenido debe cubrir el tema en profundidad
4. **Title tag**: keyword principal al inicio, < 60 caracteres, compelling
5. **Meta description**: 150-160 caracteres, incluir keyword, call-to-action
6. **URL limpia**: corta, descriptiva, con keyword, sin parámetros innecesarios
7. **Headings jerárquicos**: un solo H1, múltiples H2/H3 organizando subtemas
8. **Imágenes**: alt text descriptivo en TODAS las imágenes, compresión WebP/AVIF
9. **Internal linking**: enlazar contenido relacionado con anchor text descriptivo
10. **No duplicar contenido**: canonical tags cuando sea necesario

### Estructura de página ideal:

```
H1: Keyword principal — Título atractivo
  Párrafo introductorio (respuesta directa en las primeras 2 frases)
  
  H2: Subtema 1
    Contenido + datos + ejemplos
    H3: Detalle del subtema
    
  H2: Subtema 2
    Contenido + datos + ejemplos
    
  H2: Preguntas frecuentes (FAQ)
    H3: ¿Pregunta 1?
    Respuesta directa.
    H3: ¿Pregunta 2?
    Respuesta directa.
```

### Template HTML SEO-optimizado:

```html
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Keyword Principal — Complemento Atractivo | Marca</title>
  <meta name="description" content="Descripción compelling de 150-160 chars con keyword principal y CTA.">
  <link rel="canonical" href="https://ejemplo.com/url-limpia">
  
  <!-- Open Graph -->
  <meta property="og:title" content="Título para redes sociales">
  <meta property="og:description" content="Descripción para compartir en redes">
  <meta property="og:image" content="https://ejemplo.com/imagen-social.jpg">
  <meta property="og:url" content="https://ejemplo.com/url-limpia">
  <meta property="og:type" content="article">
  
  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="Título para Twitter">
  <meta name="twitter:description" content="Descripción para Twitter">
  
  <!-- Schema JSON-LD (ver sección Schema) -->
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "WebPage",
    "name": "Título de la página",
    "description": "Descripción",
    "url": "https://ejemplo.com/url-limpia"
  }
  </script>
</head>
<body>
  <header>
    <nav aria-label="Navegación principal">
      <!-- Breadcrumbs con schema -->
    </nav>
  </header>
  <main>
    <article>
      <h1>Keyword Principal — Título Atractivo</h1>
      <!-- Contenido estructurado -->
    </article>
  </main>
  <footer>
    <!-- Datos de contacto, legal, privacidad -->
  </footer>
</body>
</html>
```

---

## 1.4 SEO Técnico

### Checklist obligatorio:

- [ ] **HTTPS** en todo el sitio
- [ ] **Mobile-first**: diseño responsive, touch-friendly
- [ ] **Sitemap XML** enviado a Google Search Console
- [ ] **robots.txt** correcto (no bloquear recursos necesarios)
- [ ] **Canonical tags** en páginas con contenido similar
- [ ] **Hreflang** si hay versiones en varios idiomas
- [ ] **404 personalizada** que guíe al usuario
- [ ] **Redirecciones 301** para URLs cambiadas (nunca cadenas de redirecciones)
- [ ] **Sin contenido duplicado** (www vs no-www, http vs https)
- [ ] **Structured data** validada con Rich Results Test
- [ ] **Velocidad de carga** < 3 segundos en móvil

### robots.txt recomendado:

```
User-agent: *
Allow: /
Disallow: /admin/
Disallow: /api/
Disallow: /private/

# IMPORTANTE: Permitir bots de IA para GEO
User-agent: GPTBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: Google-Extended
Allow: /

Sitemap: https://ejemplo.com/sitemap.xml
```

---

## 1.5 Schema Markup (Structured Data)

### Schemas prioritarios por tipo de contenido:

**Para todas las webs:**
- `Organization` — identidad de la empresa/marca
- `WebSite` — con SearchAction para sitelinks
- `BreadcrumbList` — navegación jerárquica

**Para blogs/artículos:**
- `Article` o `BlogPosting` — con author, datePublished, dateModified
- `FAQPage` — preguntas frecuentes (muy efectivo para AI Overviews)

**Para negocios locales:**
- `LocalBusiness` — dirección, horario, teléfono
- `Review` / `AggregateRating`

**Para e-commerce:**
- `Product` — precio, disponibilidad, reviews
- `Offer` — condiciones de venta
- `ItemList` — listados de productos

**Para servicios:**
- `Service` — descripción, área, precio
- `HowTo` — guías paso a paso

### Ejemplo completo — Organization + WebSite:

```json
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": "https://ejemplo.com/#organization",
      "name": "Nombre de la Empresa",
      "url": "https://ejemplo.com",
      "logo": {
        "@type": "ImageObject",
        "url": "https://ejemplo.com/logo.png",
        "width": 600,
        "height": 60
      },
      "sameAs": [
        "https://twitter.com/empresa",
        "https://linkedin.com/company/empresa",
        "https://www.instagram.com/empresa"
      ],
      "contactPoint": {
        "@type": "ContactPoint",
        "telephone": "+34-XXX-XXX-XXX",
        "contactType": "customer service",
        "availableLanguage": ["Spanish", "English"]
      }
    },
    {
      "@type": "WebSite",
      "@id": "https://ejemplo.com/#website",
      "url": "https://ejemplo.com",
      "name": "Nombre del Sitio",
      "publisher": {"@id": "https://ejemplo.com/#organization"},
      "potentialAction": {
        "@type": "SearchAction",
        "target": "https://ejemplo.com/buscar?q={search_term_string}",
        "query-input": "required name=search_term_string"
      }
    }
  ]
}
```

### Ejemplo FAQPage (crucial para AI Overviews):

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "¿Pregunta frecuente 1?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Respuesta directa y completa a la pregunta 1."
      }
    },
    {
      "@type": "Question",
      "name": "¿Pregunta frecuente 2?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Respuesta directa y completa a la pregunta 2."
      }
    }
  ]
}
```

---

## 1.6 Google AI Overviews (SGE)

Google genera respuestas con IA directamente en los resultados. Las webs citadas como fuente obtienen visibilidad privilegiada.

### Cómo ser citado en AI Overviews:

1. **Secciones FAQ** con schema `FAQPage` — el formato más efectivo
2. **Respuestas directas** en las primeras 2 frases de cada sección
3. **Datos y estadísticas propias** con fuente
4. **Listas y tablas** — los AI Overviews extraen muy bien estos formatos
5. **Contenido que demuestre E-E-A-T** — Google prioriza fuentes autoritativas
6. **Headings como preguntas** — facilita la extracción

---

# PARTE 2: SEO PARA CHATGPT SEARCH

## 2.1 Concepto Fundamental

En ChatGPT Search NO "rankeas" como en Google. El objetivo es **ser citado o referenciado** en la respuesta que la IA genera. ChatGPT usa RAG (Retrieval-Augmented Generation): indexa, embebe como vectores y recupera pasajes relevantes de fuentes externas.

### Diferencias clave con Google SEO:

| Aspecto | Google SEO | ChatGPT SEO |
|---------|-----------|-------------|
| Objetivo | Rankear en posición 1-10 | Ser citado en la respuesta |
| Unidad | La página completa | El pasaje/párrafo |
| Keywords | Keywords específicas | Preguntas conversacionales |
| Métrica | Posición, CTR | Citation Rate |
| Clic | El usuario hace clic | Puede no haber clic |
| Queries | Fragmentadas ("mejor hotel madrid") | Conversacionales ("¿cuál es el mejor hotel para familias en Madrid centro?") |

### Dato crítico:
65-85% de los prompts de ChatGPT **no coinciden con ninguna keyword tradicional**. La keyword research clásica sola deja un gap enorme.

## 2.2 Estrategias de Optimización para ChatGPT

### 2.2.1 Claridad de Entidad

La IA debe poder entender fácilmente:
- **Quién eres** (persona/empresa)
- **Qué haces** (producto/servicio)
- **A quién sirves** (audiencia/mercado)

Implementar con:
- Schema `Organization` completo
- Página "Sobre nosotros" clara y detallada
- Presencia consistente en directorios, Wikipedia (si aplica), redes sociales

### 2.2.2 Estructura del Contenido

```
[Heading como pregunta]
[Respuesta directa en 1-2 frases — esto es lo que la IA extrae]
[Desarrollo con datos, ejemplos, contexto]
[Estadística o dato que respalde la afirmación]
```

### 2.2.3 Contenido Optimizado para Extracción

- **Front-load**: la respuesta va PRIMERO, luego el desarrollo
- **Claims autocontenidos**: cada párrafo debe tener sentido por sí solo
- **Datos con fuente**: "Según [estudio/fuente], el 73% de..."
- **Listas y tablas**: formatos fácilmente extraíbles
- **Definiciones claras**: "X es Y que hace Z" — formato que la IA cita directamente

### 2.2.4 Autoridad y Menciones

ChatGPT pondera:
- Menciones en sitios que indexa frecuentemente (medios, Wikipedia, directorios de industria)
- Backlinks de sitios autoritativos
- Consistencia de información entre fuentes (NAP para negocios locales)
- Reviews en plataformas reconocidas

### 2.2.5 Accesibilidad Técnica

```
# En robots.txt — PERMITIR los bots de ChatGPT:
User-agent: GPTBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: OAI-SearchBot
Allow: /
```

- Sitio rápido y crawleable
- Sin contenido detrás de paywalls/login para lo que quieras que cite
- Structured data completa

## 2.3 Métrica: Citation Rate

**Citation Rate** = con qué frecuencia tu sitio/marca aparece en respuestas de IA.

- Benchmark actual: **25%** se considera buen nivel de visibilidad
- Monitorizar tráfico referral desde `chatgpt.com` en analytics
- Herramientas emergentes: se están desarrollando dashboards específicos para tracking

---

# PARTE 3: GEO — GENERATIVE ENGINE OPTIMIZATION

## 3.1 Qué es GEO

Generative Engine Optimization es la práctica de estructurar contenido y presencia online para que los motores de IA — **ChatGPT, Perplexity, Google AI Overviews, Gemini y Claude** — citen, recomienden o incluyan tu contenido en sus respuestas.

### Escala actual (Q1 2026):
Los buscadores IA manejan un **12-18% de las consultas informacionales** en inglés, vs menos del 2% un año antes. Crecimiento exponencial.

## 3.2 Diferencia Fundamental con SEO

- **SEO** optimiza para **rankear una página**
- **GEO** optimiza para **ser citado en una respuesta** (a menudo sin clic)

### Mecanismo: RAG (Retrieval-Augmented Generation)
1. El contenido se trocea en pasajes
2. Se embebe como vectores semánticos
3. Se recupera por relevancia semántica al query del usuario
4. La IA sintetiza una respuesta y cita los pasajes que usó

**La unidad de optimización pasa de la PÁGINA al PASAJE/PÁRRAFO.**

Esto significa que:
- Claridad > keywords
- Estructura > longitud
- Claims autocontenidos > narrativa fluida
- Datos verificables > opiniones

## 3.3 Tácticas Prácticas de GEO

### 3.3.1 Optimización a Nivel de Pasaje

```html
<!-- MALO para GEO -->
<p>Hay muchas formas de invertir y cada una tiene sus ventajas 
e inconvenientes que dependen de muchos factores como el plazo, 
el riesgo y la situación personal del inversor...</p>

<!-- BUENO para GEO -->
<h2>¿Cuáles son las mejores formas de invertir a largo plazo?</h2>
<p>Las mejores formas de invertir a largo plazo son los fondos indexados 
globales, los ETFs diversificados y la inversión inmobiliaria. 
Según datos de Morningstar (2025), los fondos indexados al MSCI World 
han generado un retorno anualizado del 8.2% en los últimos 30 años.</p>
```

### 3.3.2 Checklist GEO para Cada Página

- [ ] **Heading como pregunta** que la gente haría a una IA
- [ ] **Respuesta directa** en las primeras 1-2 frases bajo cada heading
- [ ] **Al menos 1 estadística o dato** por sección con fuente citada
- [ ] **Schema markup** relevante (FAQ, Article, HowTo, Product)
- [ ] **Datos originales** cuando sea posible (estudios propios, encuestas, benchmarks)
- [ ] **Claims verificables** — evitar opiniones sin respaldo
- [ ] **Formato extraíble**: listas, tablas, definiciones claras
- [ ] **robots.txt** permite GPTBot, PerplexityBot, ClaudeBot
- [ ] **Menciones externas** en sitios que las IAs indexan
- [ ] **Actualización reciente** — las IAs priorizan contenido fresco

### 3.3.3 Bots de IA — Configuración de robots.txt

```
# Bots de IA para permitir (GEO)
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

User-agent: Bytespider
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: Applebot-Extended
Allow: /

User-agent: anthropic-ai
Allow: /

User-agent: cohere-ai
Allow: /
```

### 3.3.4 Tipos de Contenido que las IAs Citan Más

1. **Definiciones claras**: "X es Y" — las IAs las citan directamente
2. **Estadísticas con fuente**: "El 73% de los usuarios..." 
3. **Listas comparativas**: "Los 5 mejores X para Y"
4. **Tablas de datos**: comparaciones estructuradas
5. **Paso a paso**: guías con instrucciones numeradas
6. **FAQs**: pregunta + respuesta directa
7. **Datos originales**: estudios, encuestas, benchmarks propios

### 3.3.5 Métricas GEO

| Métrica | Qué mide | Herramienta |
|---------|----------|-------------|
| Citation Rate | Veces que apareces en respuestas IA | Manual / herramientas GEO emergentes |
| Tráfico referral IA | Visitas desde chatgpt.com, perplexity.ai | Google Analytics 4 |
| Brand mentions | Menciones de marca en respuestas IA | Monitorización manual |
| Benchmark | 25% citation rate = buena visibilidad | - |

---

# PARTE 4: ESTRATEGIA INTEGRADA (Google + ChatGPT + GEO)

## 4.1 Las Tres Capas Son Complementarias

No hay que elegir entre SEO clásico y GEO. Son capas que se refuerzan:

| Capa | Objetivo | Acción principal |
|------|----------|-----------------|
| SEO Google | Rankear en SERPs | Keywords, backlinks, Core Web Vitals, E-E-A-T |
| SEO ChatGPT | Ser citado en respuestas | Claridad de entidad, estructura extraíble |
| GEO | Ser fuente de la IA | Datos originales, claims verificables, schema |

## 4.2 Workflow de Creación de Contenido SEO+GEO

1. **Investigar**: keywords tradicionales + preguntas conversacionales que la gente haría a una IA
2. **Estructurar**: headings como preguntas, respuestas front-loaded
3. **Escribir**: claims autocontenidos, datos con fuente, formato extraíble
4. **Marcar**: schema markup (Article, FAQ, Organization, Product según aplique)
5. **Optimizar**: Core Web Vitals, mobile-first, velocidad
6. **E-E-A-T**: autor con bio, experiencia demostrada, fuentes citadas
7. **Distribuir**: conseguir menciones en sitios que las IAs indexan
8. **Monitorizar**: posiciones Google + citation rate en IAs + tráfico referral

## 4.3 Errores Comunes a Evitar

1. **Bloquear bots de IA en robots.txt** — verificar siempre
2. **Contenido tras paywall** que quieres que la IA cite
3. **Keyword stuffing** — las IAs detectan contenido de baja calidad
4. **No actualizar contenido** — las IAs priorizan contenido reciente
5. **Ignorar schema markup** — es el puente entre tu contenido y las IAs
6. **No tener datos originales** — las IAs prefieren fuentes primarias
7. **Contenido genérico** sin experiencia real (falla en E-E-A-T)
8. **No monitorizar tráfico de IAs** — configurar GA4 para tracking referral

---

# PARTE 5: TEMPLATES RÁPIDOS

## 5.1 Template de Artículo SEO+GEO

```html
<!-- Schema Article + FAQ -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Título con keyword principal",
  "author": {"@type": "Person", "name": "Autor", "url": "URL perfil"},
  "datePublished": "2026-XX-XX",
  "dateModified": "2026-XX-XX",
  "publisher": {"@type": "Organization", "name": "Marca"}
}
</script>

<article>
  <h1>¿Keyword principal como pregunta o afirmación directa?</h1>
  <p><strong>Respuesta directa en 1-2 frases.</strong> Desarrollo con dato 
  respaldado por fuente. Según [fuente], [estadística relevante].</p>
  
  <h2>¿Subtema como pregunta?</h2>
  <p>Respuesta directa. Desarrollo. Dato con fuente.</p>
  
  <h2>Preguntas frecuentes</h2>
  <h3>¿Pregunta 1?</h3>
  <p>Respuesta directa y completa.</p>
  
  <h3>¿Pregunta 2?</h3>
  <p>Respuesta directa y completa.</p>
</article>
```

## 5.2 Checklist Rápido Pre-Publicación

```
SEO GOOGLE:
[ ] Title tag < 60 chars con keyword al inicio
[ ] Meta description 150-160 chars con keyword + CTA
[ ] URL limpia y descriptiva
[ ] H1 único con keyword principal
[ ] Imágenes con alt text + compresión WebP
[ ] Internal links a contenido relacionado
[ ] Core Web Vitals OK (LCP < 2.5s, CLS < 0.1, INP < 200ms)
[ ] Mobile responsive
[ ] Schema markup validada
[ ] Canonical tag

GEO / IA:
[ ] Respuesta directa en primeras 2 frases de cada sección
[ ] Headings como preguntas conversacionales
[ ] Al menos 1 estadística con fuente por sección
[ ] FAQ section con schema FAQPage
[ ] Claims autocontenidos (cada párrafo funciona solo)
[ ] robots.txt permite GPTBot, PerplexityBot, ClaudeBot
[ ] Datos originales cuando sea posible
[ ] Contenido actualizado recientemente
```

---

# PARTE 6: REFERENCIA RÁPIDA DE BOTS DE IA

| Bot | Propietario | Qué hace |
|-----|------------|----------|
| GPTBot | OpenAI | Crawlea para entrenar modelos |
| ChatGPT-User | OpenAI | Browsing en tiempo real de ChatGPT |
| OAI-SearchBot | OpenAI | ChatGPT Search |
| PerplexityBot | Perplexity | Búsqueda y citación |
| ClaudeBot | Anthropic | Crawling de Claude |
| anthropic-ai | Anthropic | Entrenamiento Anthropic |
| Google-Extended | Google | Gemini / AI Overviews |
| Applebot-Extended | Apple | Apple Intelligence |
| Bytespider | ByteDance | Crawling para TikTok/Doubao |
| cohere-ai | Cohere | Modelos Cohere |

---

*Guía compilada en julio 2026. Actualizar periódicamente con cambios de algoritmo.*
