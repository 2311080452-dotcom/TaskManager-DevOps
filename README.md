# TaskManager-DevOps

Sistema web para la gestión de tareas de **TechSolutions**, desarrollado aplicando las fases del ciclo de vida DevOps con GitHub (Projects, Issues, Actions y Releases).

![CI](https://github.com/2311080452-dotcom/TaskManager-DevOps/actions/workflows/ci.yml/badge.svg)

**Aplicación publicada:** https://taskmanager-devops-fxl0.onrender.com

## Funcionalidades

| Código | Funcionalidad     | Cómo se usa |
|--------|-------------------|-------------|
| RF01   | Registrar tareas  | Formulario "Nueva tarea" → Guardar tarea |
| RF02   | Consultar tareas  | Listado "Tareas registradas" (con filtros por estado y prioridad) |
| RF03   | Editar tareas     | Botón **Editar** en cada tarea |
| RF04   | Eliminar tareas   | Botón **Eliminar** (pide confirmación) |
| RF05   | Cambiar estado    | Selector Pendiente / En proceso / Terminada en cada tarea |
| RF06   | Asignar prioridad | Alta, Media o Baja (color en el borde de la tarea) |

## Tecnologías

- **Frontend:** HTML, CSS y JavaScript
- **Backend:** Python 3.12 + Flask
- **Base de datos:** SQLite
- **Pruebas:** Pytest (34 pruebas)
- **CI/CD:** GitHub Actions
- **Despliegue:** Render (gunicorn)

## Estructura

```text
TaskManager-DevOps/
├── app.py                  # Backend Flask + API REST
├── requirements.txt
├── Procfile / render.yaml  # Configuración de despliegue
├── templates/index.html
├── static/css/style.css
├── static/js/app.js
├── tests/test_app.py       # Pruebas unitarias
├── scripts/configurar_github.sh   # Crea Issues, etiquetas y Project
├── docs/                   # Guía y capturas de pruebas
└── .github/workflows/
    ├── ci.yml              # Integración continua
    ├── entrega.yml         # Entrega continua (artefacto en cada Release)
    ├── despliegue.yml      # Despliegue continuo a Render
    └── monitoreo.yml       # Revisión periódica de /health
```

## Ejecutar en local

```bash
git clone https://github.com/2311080452-dotcom/TaskManager-DevOps.git
cd TaskManager-DevOps
python -m venv venv
# Windows: venv\Scripts\activate    |   Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Abrir http://localhost:5000

## Ejecutar pruebas

```bash
pytest -v
```

## API

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET    | `/api/tareas?estado=&prioridad=` | Listar tareas |
| GET    | `/api/tareas/<id>` | Ver una tarea |
| POST   | `/api/tareas` | Registrar (`nombre` obligatorio) |
| PUT    | `/api/tareas/<id>` | Editar |
| PATCH  | `/api/tareas/<id>/estado` | Cambiar estado |
| DELETE | `/api/tareas/<id>` | Eliminar |
| GET    | `/health` | Monitoreo: estado, BD, tiempo activo |

Cada respuesta incluye la cabecera `X-Response-Time-ms` con el tiempo de respuesta.

## Equipo

| Rol | Integrante |
|-----|-----------|
| Product Owner + Desarrollador backend | Integrante 1 |
| Desarrollador frontend + Releases | Integrante 2 |
| Ingeniero DevOps / QA | Integrante 3 |
