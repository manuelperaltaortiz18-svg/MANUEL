# Publicación: enlace de vista previa → dominio del cliente

Dos fases, siempre en este orden:

1. **Vista previa** — una URL provisional que el cliente abre desde el móvil.
   Se enseña con el 50 % pagado.
2. **Producción** — su dominio, con HTTPS. Solo cuando está cobrado el 100 %.

---

## Canal por defecto: Cloudflare Pages

Gratis, ilimitado en tráfico, dominio propio incluido, HTTPS automático y el
más rápido en España. Es el que usamos salvo motivo concreto.

### Primera vez (una sola vez en la vida)

```bash
npm install -g wrangler
wrangler login
```

### Vista previa (30 segundos)

```bash
cd clientes/<cliente>
wrangler pages project create <cliente> --production-branch main
wrangler pages deploy . --project-name=<cliente>
```

Devuelve `https://<hash>.<cliente>.pages.dev` → **ese es el enlace que se
manda al cliente**.

⚠️ Antes de desplegar la vista previa, añadir al `<head>`:

```html
<meta name="robots" content="noindex,nofollow">
```

y **quitarlo** antes de producción. Si Google indexa la vista previa, el
cliente acaba con dos versiones de su web compitiendo.

### Producción con el dominio del cliente

1. En el panel de Cloudflare → Pages → el proyecto → **Custom domains** →
   añadir `sudominio.es` y `www.sudominio.es`.
2. Cloudflare da los registros DNS. En el registrador **del cliente**:
   - `CNAME  www   <cliente>.pages.dev`
   - Raíz del dominio: `CNAME @ <cliente>.pages.dev` (si el registrador
     soporta CNAME flattening) o los registros `A` que indique Cloudflare.
3. Esperar la propagación: normalmente minutos, hasta 24 h en el peor caso.
4. Comprobar el candado HTTPS y que `www` redirige al dominio principal.

> **El dominio se queda a nombre del cliente.** Tú pides acceso temporal al
> panel DNS o le mandas los dos registros por WhatsApp para que los pegue.
> Registrar el dominio a tu nombre "para simplificar" es la forma más rápida
> de tener un problema legal dentro de dos años.

### Actualizar una web ya publicada

```bash
wrangler pages deploy . --project-name=<cliente>
```

Se publica en segundos y Cloudflare guarda todas las versiones anteriores por
si hay que volver atrás.

---

## Alternativa: Netlify

Equivalente en prestaciones y con **formularios incluidos** en el plan
gratuito (100 envíos/mes), lo que ahorra montar un servicio aparte.

```bash
npm install -g netlify-cli
netlify login
netlify deploy --dir=. --site=<cliente>            # vista previa
netlify deploy --dir=. --site=<cliente> --prod     # producción
```

Dominio propio: panel → Domain settings → Add custom domain → mismos
registros DNS. Para el formulario basta con añadir `data-netlify="true"` al
`<form>`.

**Cuándo elegir Netlify sobre Cloudflare:** cuando el cliente vaya a recibir
pocos envíos de formulario y quieras cero servicios externos.

---

## Alternativa: hosting propio del cliente (FTP / cPanel)

Cuando el cliente ya paga un hosting español y no lo quiere soltar.

1. Subir el contenido de la carpeta a `public_html/` por FTP (FileZilla).
2. Activar el certificado SSL gratuito (Let's Encrypt) desde cPanel.
3. Forzar HTTPS con un `.htaccess`:

```apache
RewriteEngine On
RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
```

Sin acceso a línea de comandos aquí: el despliegue es manual y no hay
versiones anteriores. Cobrar el mantenimiento más caro o convencerle de migrar.

---

## Atajo para maquetas: Higgsfield

Este entorno tiene herramientas de Higgsfield (`create_website`,
`deploy_website`) que levantan un sitio en un subdominio suyo en minutos.

**Sirve para:** enseñar una maqueta en una primera llamada, validar una idea
de diseño rápido.

**No sirve para entregar al cliente:** la URL vive en un subdominio de
Higgsfield y no se puede apuntar al dominio del cliente. Una web vendida
termina siempre en Cloudflare Pages, Netlify o el hosting del cliente.

---

## Formularios (webs estáticas, sin servidor)

| Servicio | Gratis | Notas |
|---|---|---|
| **Web3Forms** | 250/mes | Solo una clave en el `action`. Sin registro del cliente. |
| **Formspree** | 50/mes | El más conocido; el plan gratis pone su marca. |
| **Netlify Forms** | 100/mes | Solo si alojas en Netlify. Cero configuración. |

Con Web3Forms:

```html
<form action="https://api.web3forms.com/submit" method="POST">
  <input type="hidden" name="access_key" value="TU-CLAVE">
  <input type="hidden" name="subject" value="Nuevo contacto desde la web">
  <input type="hidden" name="redirect" value="https://sudominio.es/gracias.html">
  <!-- campos -->
</form>
```

Crear una clave **por cliente** con **su** email de destino, nunca el tuyo.
Y probar el envío de verdad antes de entregar: el formulario que no llega es
el fallo más caro de todos, porque el cliente pierde clientes sin saberlo.

---

## Estructura de carpetas de la fábrica

```
clientes/
  restaurante-la-plaza/
    index.html
    aviso-legal.html  privacidad.html  cookies.html
    img/
    BRIEF.md          ← copia rellena del brief
    ENTREGA.md        ← copia de la checklist marcada
```

Un cliente, una carpeta, autónoma. Nada compartido entre clientes salvo
`web-factory/assets/base.css`, que se **copia** dentro de cada proyecto antes
de desplegar (la ruta relativa `../../assets/` no existe una vez desplegado):

```bash
mkdir -p clientes/<cliente>/assets && cp web-factory/assets/base.css clientes/<cliente>/assets/
# y en el HTML: <link rel="stylesheet" href="assets/base.css">
```
