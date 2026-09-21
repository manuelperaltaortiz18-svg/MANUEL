# Cómo mover esto a su propio repositorio

Este directorio vive temporalmente dentro del repo `manuel` porque la
integración de GitHub de la sesión no tenía permiso para crear repositorios
(`403 Resource not accessible by integration`). El código **no depende de nada
de `manuel`**: es autocontenido.

Para extraerlo:

```bash
# 1. Crea el repo vacío en GitHub (a mano, desde la web):
#    manuelperaltaortiz18-svg/cuperinox-social-agent  (privado)

# 2. Desde un clon de `manuel`:
cd social-agent
git init
git add -A
git commit -m "Agente de publicacion semanal para cuperinox.es"
git branch -M main
git remote add origin git@github.com:manuelperaltaortiz18-svg/cuperinox-social-agent.git
git push -u origin main

# 3. Ya en el repo `manuel`, borra el directorio:
cd .. && git rm -r social-agent && git commit -m "Mover el agente social a su propio repo"
```

Después, en el repo nuevo: Settings -> Secrets -> Actions -> añadir
`ANTHROPIC_API_KEY`.
