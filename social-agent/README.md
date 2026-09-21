# Agente de contenido semanal — cuperinox.es

Genera publicaciones semanales para LinkedIn e Instagram, las deja en una cola
de revisión, y solo publica lo que un humano ha aprobado.

```
generate  ->  [pendiente]  --revisión humana-->  [aprobado]  ->  publish
```

Nada llega a una red social sin pasar por `approve`. El workflow semanal
**genera pero no publica**, a propósito.

---

## Antes de escribir una línea de configuración: los requisitos de acceso

Esta es la parte que bloquea el proyecto, no el código.

### Instagram

| Requisito | ¿Opcional? |
|---|---|
| Cuenta **Business** o **Creator** | No. Una cuenta personal no puede publicar por API. |
| Vinculada a una **Página de Facebook** | No. |
| App de Meta con `instagram_content_publish` | No. Requiere App Review. |
| Imagen en **URL pública** | No. Meta descarga el archivo; no se sube el binario. |

Límite: 50 publicaciones por cada 24 horas. No soporta Stories.

### LinkedIn

| Autor | Scope | Producto | Accesible |
|---|---|---|---|
| `urn:li:person:*` (perfil personal) | `w_member_social` | Share on LinkedIn | Sí, autoservicio |
| `urn:li:organization:*` (página de empresa) | `w_organization_social` | Community Management API | **Requiere aprobación de partner** |

Publicar en la **página de empresa** exige que LinkedIn apruebe tu acceso a la
Community Management API. No es autoservicio y se deniega con frecuencia a
proyectos individuales. Mientras tanto, el `LinkedInPublisher` acepta también
un URN de persona: cambias `LINKEDIN_AUTHOR_URN` y publicas desde el perfil
personal sin tocar código.

El token de LinkedIn **caduca a los 60 días** y el flujo estándar no da refresh
token: hay que reautorizar a mano. `LinkedInPublisher.verify_token()` lo
detecta antes de que reviente una publicación.

---

## Instalación

```bash
pip install -e ".[dev]"
cp .env.example .env   # y rellena las credenciales
```

Edita `brand.yaml`. **El borrador actual está inferido del nombre del dominio,
no verificado** — corrígelo antes del primer uso o el contenido saldrá mal.

## Uso

```bash
social generate                                  # borradores de la semana
social generate -p linkedin -b "Barandilla AISI 316 para un hotel en Cádiz"
social review                                    # ver lo pendiente, completo
social edit 3 "Texto corregido"
social image 4 https://cuperinox.es/media/foto.jpg   # Instagram exige imagen
social approve 3
social reject 4 --reason "la foto no vale"
social publish                                   # solo lo aprobado
social status
```

Con `DRY_RUN=true`, `publish` enseña lo que enviaría sin llamar a ninguna API.

## Cómo elige el tema

`brand.yaml` define **pilares de contenido**. El generador rota entre ellos por
número de semana ISO: cadencia predecible sin guardar estado entre ejecuciones,
y el mismo número de semana da siempre el mismo pilar. Con `--briefing` le pasas
el material real de esa semana (un proyecto terminado, una pieza concreta); sin
él escribe algo atemporal dentro del pilar.

El prompt prohíbe explícitamente inventar cifras, clientes, premios o plazos.

## Estructura

```
src/social_agent/
  settings.py        configuración desde .env
  models.py          Draft, Platform, límites por plataforma
  brand/             perfil de marca y rotación de pilares
  content/           prompts + generador (Claude API)
  store/             cola de revisión en SQLite
  publishers/        LinkedIn, Instagram, registro
  cli/               interfaz de línea de comandos
```

## Tests

```bash
python -m pytest tests/ -v
```

Las APIs se prueban con transportes simulados de `httpx`: no hay llamadas de
red reales en la suite.

## Automatización

`.github/workflows/weekly-content.yml` se ejecuta los lunes a las 07:00 UTC.
Genera los borradores y los sube como artefacto. **La publicación sigue siendo
manual**: es el control que evita que salga algo mal escrito con el nombre de
la empresa.

Secreto necesario en el repo: `ANTHROPIC_API_KEY`.
