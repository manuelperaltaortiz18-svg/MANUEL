# Web Factory

Sistema de producción para vender y entregar webs a pymes y autónomos en
España. El objetivo es que **una web se venda, se construya y se publique en
días, no en semanas**, sin que la calidad dependa de cuántas horas le eches.

La ventaja competitiva no es el precio: es el plazo y la ausencia de fricción.
Todo lo que hay aquí existe para eliminar decisiones repetidas.

---

## Contenido

| Ruta | Qué es |
|---|---|
| `assets/base.css` | Sistema de diseño: tokens, reset, layout, componentes, modo oscuro. **No se edita por proyecto.** |
| `templates/local-negocio/` | Bar, peluquería, taller, gimnasio → objetivo: que llamen |
| `templates/servicios-profesionales/` | Asesoría, clínica, despacho → objetivo: pedir cita |
| `templates/portfolio/` | Fotógrafo, diseñador, arquitecto → objetivo: que escriban |
| `templates/producto-landing/` | SaaS, curso, app → objetivo: registro o compra |
| `templates/_legal/` | Aviso legal, privacidad y cookies (LSSI-CE + RGPD) |
| `brief/BRIEF.md` | Formulario de entrada. Sin esto no se arranca. |
| `checklists/ENTREGA.md` | Control de calidad. Obligatorio antes de enseñar nada. |
| `comercial/PRECIOS.md` | Tres paquetes, extras, mantenimiento, cómo poner precio |
| `comercial/PROPUESTA.md` | Plantilla de propuesta + respuestas a objeciones |
| `deploy/DEPLOY.md` | Vista previa → dominio del cliente. Formularios. |
| `nuevo-cliente.sh` | Crea `clientes/<slug>/` a partir de una plantilla |

El agente `.claude/agents/web-creator.md` orquesta todo esto. En Claude Code:

```
> usa el agente web-creator: web para un restaurante en Granada, el brief está
  en clientes/la-plaza/BRIEF.md
```

---

## El ciclo, de principio a fin

```
Llamada (20 min)
   └─ BRIEF.md relleno, campos 🔴 obligatorios
        └─ PROPUESTA.md enviada en 24 h
             └─ 50 % cobrado ← no se escribe código antes de esto
                  └─ ./web-factory/nuevo-cliente.sh <slug> <plantilla>
                       └─ personalización: tokens, copy, tema, imágenes, legales
                            └─ ENTREGA.md bloque A ← control de calidad
                                 └─ vista previa con noindex → enlace al cliente
                                      └─ 1 ronda de cambios (lista única, con fecha)
                                           └─ 100 % cobrado
                                                └─ dominio del cliente + HTTPS
                                                     └─ entrega + venta del mantenimiento
```

**Los dos puntos donde se pierde dinero** son siempre los mismos:

1. Empezar sin anticipo → el cliente desaparece y has trabajado gratis.
2. Rondas de cambios infinitas → un proyecto de 4 h se convierte en 20 h.
   Por eso las rondas van numeradas, por escrito y con fecha límite.

---

## Empezar un cliente

```bash
./web-factory/nuevo-cliente.sh restaurante-la-plaza local-negocio
```

Crea:

```
clientes/restaurante-la-plaza/
  index.html                          ← plantilla, con los tokens [[...]] por sustituir
  aviso-legal.html privacidad.html cookies.html
  assets/base.css                     ← copia local (rutas ya corregidas)
  img/                                ← aquí van las fotos en WebP
  robots.txt
  BRIEF.md   ENTREGA.md               ← copias de trabajo del proyecto
```

Comprobación de que no queda nada sin personalizar:

```bash
grep -rn "\[\[" clientes/restaurante-la-plaza/     # tiene que salir vacío
```

---

## Las cuatro plantillas

Se eligen por **objetivo de conversión**, no por sector. Un fisioterapeuta
puede necesitar `local-negocio` (que le llamen) o `servicios-profesionales`
(que pidan cita online); lo decide qué le trae más dinero, no su epígrafe.

Todas comparten `assets/base.css` y se diferencian en el bloque `<style>` de
su `index.html`: paleta, tipografía y densidad. **Ese bloque se reescribe en
cada proyecto** — es lo que evita que cuatro clientes tengan la misma web con
otro logo.

---

## Economía

| Concepto | Importe |
|---|---|
| Paquete Exprés | 490 € |
| Paquete Profesional ⭐ | 990 € |
| Coste real por proyecto | ~12 €/año de dominio; alojamiento 0 € |
| Tiempo con la fábrica montada | 3–6 h (Exprés) |
| **Mantenimiento** | 25–120 €/mes ← **el negocio real está aquí** |

Detalle completo, extras y guion de la conversación de precio en
`comercial/PRECIOS.md`.

---

## Límites — decir que no también es parte del sistema

- **No** se promete posicionamiento en Google.
- **No** se inventan reseñas, testimonios, logos de clientes ni cifras.
- **No** se registra el dominio a nombre del estudio: es del cliente.
- **No** se usan imágenes sin licencia comprobada.
- **No** se entrega una web sin páginas legales con NIF real.
- **No** se empieza sin anticipo.

Cada uno de estos puntos existe porque saltárselo cuesta más dinero (o más
disgustos) del que ahorra.
