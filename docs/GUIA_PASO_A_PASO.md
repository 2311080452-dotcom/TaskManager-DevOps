# Guía paso a paso para el equipo (3 integrantes)

El código ya está terminado y probado. Esta guía explica cómo subirlo a GitHub **repartiendo el trabajo entre los 3 integrantes**, de modo que queden como evidencia ramas, commits, Pull Requests, ejecuciones de GitHub Actions, el Release y el despliegue.

> Sustituyan `USUARIO` por la cuenta de GitHub del integrante dueño del repositorio.

## Reparto de roles

| Integrante | Rol | Rama que sube | Archivos |
|---|---|---|---|
| **1** | Product Owner + Backend | `feature/registro-tareas` | `app.py`, `requirements.txt`, `Procfile`, `render.yaml` |
| **2** | Frontend + Release | `feature/interfaz` | `templates/`, `static/` |
| **3** | DevOps / QA | `feature/pruebas-ci` | `tests/`, `.github/`, `scripts/` |

Cada rama toca archivos distintos, así que **no habrá conflictos**.

---

## Fase 1 · Plan (Integrante 1)

1. En GitHub → **New repository**
   - Nombre: `TaskManager-DevOps`
   - Descripción: `Sistema web para la gestión de tareas.`
   - Public, ✅ *Add a README file* → **Create repository**.
2. **Settings → Collaborators → Add people**: invitar a los integrantes 2 y 3 (deben aceptar el correo).
3. Instalar [GitHub CLI](https://cli.github.com) y [jq](https://jqlang.github.io/jq/download/), luego:
   ```bash
   gh auth login
   gh auth refresh -s project
   ```
4. Clonar el repo y copiar dentro **solo** la carpeta `scripts/` del zip. Ejecutar:
   ```bash
   bash scripts/configurar_github.sh USUARIO usuario1 usuario2 usuario3
   ```
   Esto crea: etiquetas, milestone v1.0.0, 6 historias de usuario (HU01–HU06), 12 issues de actividades y el **GitHub Project** con los campos Prioridad, Estimación, Fase DevOps y Fecha límite, y las columnas Backlog / To Do / In Progress / Review / Done.
   *(No hagan commit de `scripts/` todavía; lo sube el integrante 3.)*
5. Abrir el Project → **New view → Board** → agrupar por *Status*. Si el script avisó que no pudo crear las columnas, editarlas a mano en el campo *Status*.

📸 **Evidencias:** repositorio, tablero, lista de issues, una historia de usuario abierta.

---

## Fase 2 · Code (los 3)

Cada integrante, en su computadora:

```bash
git clone https://github.com/2311080452-dotcom/TaskManager-DevOps.git
cd TaskManager-DevOps
git config user.name "Tu Nombre"
git config user.email "tu-correo-de-github@ejemplo.com"
```

**Integrante 1**
```bash
git checkout -b feature/registro-tareas
# copiar del zip: app.py, requirements.txt, Procfile, render.yaml, .gitignore, README.md
git add .
git commit -m "Agregar backend Flask con registro, consulta, edición y eliminación de tareas"
git push origin feature/registro-tareas
```

**Integrante 2**
```bash
git checkout -b feature/interfaz
# copiar del zip: templates/ y static/
git add .
git commit -m "Agregar interfaz web de gestión de tareas"
git push origin feature/interfaz
```

**Integrante 3**
```bash
git checkout -b feature/pruebas-ci
# copiar del zip: tests/, .github/, scripts/, docs/
git add .
git commit -m "Agregar pruebas unitarias y workflows de GitHub Actions"
git push origin feature/pruebas-ci
```

> Recomendación: hagan **varios commits pequeños** (por ejemplo, un commit por archivo o funcionalidad) en lugar de uno solo; el historial se ve mejor en la evaluación.

### Pull Requests (en este orden)
1. `feature/registro-tareas` → `main` (revisa el Integrante 3)
2. `feature/interfaz` → `main` (revisa el Integrante 1)
3. `feature/pruebas-ci` → `main` (revisa el Integrante 2) ← aquí ya corre la CI

En cada PR: **Pull requests → New pull request** → elegir la rama → escribir qué cambia y `Closes #N` (número del issue) → **Reviewers** → el revisor da **Approve** → **Merge pull request**.

Mientras trabajan, muevan las tarjetas del tablero: To Do → In Progress → Review → Done.

📸 **Evidencias:** pestaña *Branches*, *Commits*, los 3 PRs con su aprobación, *Insights → Network*.

---

## Fase 3 · Integración continua (Integrante 3)

1. Pestaña **Actions** → workflow **Integracion Continua** → abrir la ejecución → verificar ✅ en *Ejecutar pruebas* (34 pruebas aprobadas).
2. Descargar el artefacto `reporte-pruebas` como evidencia.

### Registro de errores detectados y corregidos (práctica del ciclo)
Para practicar el ciclo de detección y corrección:
1. Crear rama `test/error-ejemplo`, cambiar en `app.py` la línea
   `MAX_NOMBRE = 100` por `MAX_NOMBRE = 10`, commit y push, abrir PR.
2. La CI marcará ❌ (fallan CP01 y otras pruebas). Captura del error.
3. Crear un **Issue** con la plantilla de bug (ver Fase 4) y regresar el valor a `100` en la misma rama → push → la CI pasa ✅ → cerrar el PR **sin** merge o hacer merge una vez corregido.

📸 **Evidencias:** ejecución exitosa, ejecución fallida, ejecución corregida.

---

## Fase 4 · Test (Integrante 1 con apoyo de 3)

1. Ejecutar la matriz CP01–CP07 manualmente en la app (ver documento de resultados). En `docs/capturas/` hay capturas de referencia de cada caso.
2. Por cada error encontrado, crear un Issue:
   ```
   Título: Error al ...
   - Funcionalidad afectada:
   - Pasos para reproducir:
   - Resultado obtenido:
   - Resultado esperado:
   - Prioridad:
   ```
   Etiquetas `bug` + prioridad. Corregir en rama `fix/...` con PR que diga `Closes #N`.

---

## Fase 5 · Release (Integrante 2)

1. Verificar: todo en `main`, CI en verde, README completo.
2. **Releases → Create a new release**
   - Tag: `v1.0.0` (Create new tag on publish)
   - Título: `Primera versión estable de TaskManager`
   - Notas: copiar las del documento de resultados (o usar *Generate release notes*).
   - **Publish release**.
3. En **Actions** se ejecuta **Entrega Continua** y genera el artefacto `TaskManager-v1.0.0`.

📸 **Evidencias:** release publicado, ejecución de *Entrega Continua*, artefacto descargable.

---

## Fase 6 · Deploy (Integrante 3)

1. Entrar a https://render.com → *Sign in with GitHub*.
2. **New → Web Service** → elegir `TaskManager-DevOps`.
3. Configurar:
   - Runtime: **Python 3**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
   - Instance type: **Free**
   - Environment → `PYTHON_VERSION` = `3.12.7`
   - Advanced → Health Check Path: `/health`
4. **Create Web Service** y esperar a *Live*. Copiar la URL (ej. `https://taskmanager-devops.onrender.com`).
5. **Despliegue continuo con GitHub Actions:**
   - Render → servicio → **Settings → Deploy Hook** → copiar URL.
   - Render → **Settings → Auto-Deploy: Off** (así solo se despliega si pasan las pruebas).
   - GitHub → **Settings → Secrets and variables → Actions → New repository secret**: `RENDER_DEPLOY_HOOK_URL` = la URL copiada.
   - En la misma pantalla, pestaña **Variables** → `APP_URL` = URL pública de la app.
6. Hacer cualquier cambio pequeño (por ejemplo, poner la URL real en el README) por PR → al hacer merge, **Despliegue Continuo** corre pruebas y luego despliega.
7. Verificar en la URL: carga, registrar, editar, eliminar, cambiar estado.

> ⚠️ En el plan gratuito de Render el servicio "se duerme" tras 15 min sin uso (la primera carga tarda ~1 min) y **los datos de SQLite se reinician en cada despliegue**. Menciónenlo como incidencia/mejora (ver Fase 7).

📸 **Evidencias:** panel de Render en *Live*, logs del deploy, la app funcionando con la URL visible.

---

## Fase 7 · Operate & Monitor (Integrante 1)

1. Abrir `https://SU-URL/health` → debe responder `"status": "ok"`.
2. **Actions → Monitoreo → Run workflow** (además corre solo cada 6 h). Captura del resultado con código HTTP y tiempo.
3. Render → **Logs** y **Metrics**: cada petición se registra con su tiempo en ms.
4. Crear los Issues de incidencias y de mejoras (etiquetas `incidencia` y `mejora`) que vienen en el documento de resultados.
5. Crear un milestone **v1.1.0** y asignarle los issues de mejora (planeación de la nueva versión).

---

## Entrega del 25 de noviembre (checklist)

- [ ] URL del repositorio
- [ ] Captura/enlace del tablero de GitHub Projects
- [ ] Historias de usuario (issues HU01–HU06)
- [ ] Issues creados y cerrados
- [ ] Código fuente completo en `main`
- [ ] Ramas y Pull Requests
- [ ] `ci.yml`
- [ ] Pruebas unitarias (`tests/`) y funcionales (matriz)
- [ ] Capturas de GitHub Actions
- [ ] Release v1.0.0
- [ ] Evidencia de despliegue
- [ ] URL pública
- [ ] Documento de resultados y conclusiones (exportado a PDF/Word)
