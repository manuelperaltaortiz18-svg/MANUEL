# Los Carpinteros de Albacete — demo especulativa

Web completa y funcional, lista para subir. Preparada **sin encargo**, como
pieza de venta. Método: `web-factory/comercial/PROSPECCION.md`.

---

## 🔴 Verificar ANTES de enviar nada

**No está confirmado a quién pertenecen estas reseñas.** Hay dos sociedades
parecidas en Albacete:

| Empresa | Datos |
|---|---|
| **Los Carpinteros de Albacete, S.L.** | CNAE 3109, trabajos de carpintería y ebanistería en general, compra y venta de muebles y maderas |
| **Los Carpinteros de Campollano, S.L.** | Calle F (Campollano) 10, Albacete, constituida en 2002 |

Las 12 reseñas de 4,1/5 son de una de las dos. **Una reseña dice literalmente
«un 10 para los Carpinteros de Campollano»**, lo que apunta a la segunda — pero
también encaja con que la primera tenga el taller en el polígono Campollano.

**Cómo salir de dudas en 2 minutos:** busca cada nombre en Google Maps y compara
el número de reseñas (12) y la nota (4,1). La ficha que coincida es la buena.

Mandar la demo a la empresa equivocada mata la venta en el primer segundo, así
que esto se resuelve antes de escribir a nadie. Si resulta ser Campollano, en
esta carpeta hay que cambiar el nombre en `index.html` y en los tres archivos
legales — nada más.

---

## Qué hay en la carpeta

```
index.html          Web completa: hero, servicios, reseñas, proceso, contacto
aviso-legal.html    LSSI-CE — NIF y domicilio pendientes
privacidad.html     RGPD — responsable pendiente
cookies.html        Sin cookies no esenciales → sin banner (correcto)
assets/base.css     Sistema de diseño
robots.txt          Disallow: / — la demo NO se indexa
img/                Vacía: aquí van las fotos del cliente
ENTREGA.md          Checklist de calidad antes de publicar de verdad
```

Se abre haciendo doble clic en `index.html`. No necesita servidor ni build.

---

## Qué datos lleva y de dónde salen

**Públicos y verificables** — nombre y forma jurídica (Iberinform / El
Economista), actividad CNAE 3109, las 6 reseñas positivas **literales** con su
autor y puntuación, y la nota global real (4,1 sobre 12) a la vista.

**Marcados en naranja como pendientes, nunca inventados** — teléfono, email,
dirección del taller, horarios, NIF y las seis fotos de trabajos.

Las tres reseñas negativas no se publican (ningún negocio publica las malas en
su propia web), pero **la nota global sí está a la vista**, así que la página no
engaña a nadie.

---

## Por qué esta web les sirve

Sus tres reseñas negativas dicen todas lo mismo: **plazos que no se cumplen,
trabajos pequeños que se aparcan y falta de respuesta.** Eso es lo primero que
lee quien los busca en Google, y hoy no tienen dónde contar su versión.

La sección «Cómo trabajamos» responde a esas tres quejas una por una, antes de
que el visitante llegue a leerlas. Ese es el argumento de venta, y es honesto.

⚠️ Los cuatro compromisos de esa sección **solo deben publicarse si van a
cumplirlos**. Prometer "contestamos siempre" y seguir dando largas hace más daño
que no tener web. Hay que decírselo en la reunión, sin rodeos.

---

## Reglas de la demo mientras no contraten

1. **El banner negro de arriba se queda.** Dice que no es su web oficial.
2. **`robots.txt` con `Disallow: /` y `noindex,nofollow`** en el HTML. Google no
   la ve.
3. **URL de vista previa neutra**: `demo-carpinteria-1.pages.dev`. Nunca algo
   parecido a su marca, y no registres un dominio con su nombre ni para
   enseñárselo.
4. **Si dicen que no, se borra en 24 h.** Sin discutir.

---

## Publicar la vista previa

```bash
cd clientes/carpinteros-albacete
wrangler pages project create demo-carpinteria-1 --production-branch main
wrangler pages deploy . --project-name=demo-carpinteria-1
```

Devuelve la URL que se manda por WhatsApp. Detalle en
`web-factory/deploy/DEPLOY.md`.

---

## Mensaje para enviarles

> Buenos días.
>
> Me llamo [TU NOMBRE], hago webs para negocios de Albacete.
>
> Vi que tienen 12 reseñas en Google pero no encontré su web, así que les he
> montado una de ejemplo con su nombre y sus propias reseñas, para que vean cómo
> quedaría. Sin compromiso ninguno:
>
> [ENLACE]
>
> Las fotos que faltan son las suyas: si me mandan unas cuantas del taller, se
> las dejo puestas. Y si no les interesa, la borro hoy mismo y no les molesto
> más.

Objeciones y seguimiento: `web-factory/comercial/PROSPECCION.md`.

---

## Si contratan

1. Borrar el `<div class="demo-bar">` y su bloque `.demo-bar` del CSS.
2. Quitar `noindex,nofollow` y cambiar `robots.txt` a `Allow: /`.
3. Rellenar teléfono, email, dirección, horarios, NIF y razón social exacta
   (aparecen 4 veces en `index.html` y en los tres archivos legales).
4. Sustituir las 7 zonas rayadas por fotos reales en WebP, bajo 300 KB.
5. Conectar el formulario a Web3Forms con **su** email
   (`web-factory/deploy/DEPLOY.md`).
6. Sustituir las reseñas por el widget oficial de Google, que se actualiza solo.
7. Recorrer `ENTREGA.md` entero.
8. Conectar su dominio — **a nombre de ellos**, nunca del estudio.

Paquete que le corresponde: **Exprés, 490 € + IVA**
(`web-factory/comercial/PRECIOS.md`).
