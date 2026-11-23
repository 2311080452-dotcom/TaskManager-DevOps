"""TaskManager - Sistema web para la gestión de tareas (TechSolutions).

Backend en Flask con base de datos SQLite.
Requerimientos cubiertos:
    RF01 Registrar tareas        -> POST   /api/tareas
    RF02 Consultar tareas        -> GET    /api/tareas  y  GET /api/tareas/<id>
    RF03 Editar tareas           -> PUT    /api/tareas/<id>
    RF04 Eliminar tareas         -> DELETE /api/tareas/<id>
    RF05 Cambiar estado          -> PATCH  /api/tareas/<id>/estado
    RF06 Asignar prioridad       -> campo "prioridad" (Alta, Media, Baja)
Monitoreo (Fase 7):
    GET /health -> disponibilidad, estado de la base de datos y tiempo de actividad
"""

import logging
import os
import sqlite3
import time
from datetime import datetime, timezone

from flask import Flask, g, jsonify, render_template, request

ESTADOS = ("Pendiente", "En proceso", "Terminada")
PRIORIDADES = ("Alta", "Media", "Baja")
MAX_NOMBRE = 100
MAX_DESCRIPCION = 500

SCHEMA = """
CREATE TABLE IF NOT EXISTS tareas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    descripcion TEXT NOT NULL DEFAULT '',
    prioridad TEXT NOT NULL DEFAULT 'Media',
    estado TEXT NOT NULL DEFAULT 'Pendiente',
    responsable TEXT NOT NULL DEFAULT '',
    fecha_creacion TEXT NOT NULL,
    fecha_actualizacion TEXT NOT NULL
);
"""


def ahora():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def validar_tarea(datos, parcial=False):
    """Valida los datos de una tarea. Devuelve (datos_limpios, errores)."""
    if not isinstance(datos, dict):
        return None, ["El cuerpo de la petición debe ser un objeto JSON."]

    errores = []
    limpio = {}

    if "nombre" in datos or not parcial:
        nombre = str(datos.get("nombre") or "").strip()
        if not nombre:
            errores.append("El nombre de la tarea es obligatorio.")
        elif len(nombre) > MAX_NOMBRE:
            errores.append(f"El nombre no puede superar {MAX_NOMBRE} caracteres.")
        limpio["nombre"] = nombre

    if "descripcion" in datos or not parcial:
        descripcion = str(datos.get("descripcion") or "").strip()
        if len(descripcion) > MAX_DESCRIPCION:
            errores.append(f"La descripción no puede superar {MAX_DESCRIPCION} caracteres.")
        limpio["descripcion"] = descripcion

    if "prioridad" in datos or not parcial:
        prioridad = datos.get("prioridad") or "Media"
        if prioridad not in PRIORIDADES:
            errores.append("La prioridad debe ser Alta, Media o Baja.")
        limpio["prioridad"] = prioridad

    if "estado" in datos or not parcial:
        estado = datos.get("estado") or "Pendiente"
        if estado not in ESTADOS:
            errores.append("El estado debe ser Pendiente, En proceso o Terminada.")
        limpio["estado"] = estado

    if "responsable" in datos or not parcial:
        limpio["responsable"] = str(datos.get("responsable") or "").strip()[:60]

    return limpio, errores


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(
        DATABASE=os.environ.get(
            "DATABASE_PATH", os.path.join(app.root_path, "taskmanager.db")
        ),
        JSON_AS_ASCII=False,
    )
    if config:
        app.config.update(config)
    app.json.ensure_ascii = False
    app.config["INICIO"] = time.time()

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )

    # ------------------------------------------------------------------ BD
    def get_db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"])
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close_db(_exc):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    def init_db():
        directorio = os.path.dirname(app.config["DATABASE"])
        if directorio:
            os.makedirs(directorio, exist_ok=True)
        con = sqlite3.connect(app.config["DATABASE"])
        con.executescript(SCHEMA)
        con.commit()
        con.close()

    init_db()

    def obtener(tarea_id):
        fila = get_db().execute(
            "SELECT * FROM tareas WHERE id = ?", (tarea_id,)
        ).fetchone()
        return dict(fila) if fila else None

    def no_encontrada():
        return jsonify({"error": "Tarea no encontrada."}), 404

    # ------------------------------------------- Monitoreo de peticiones
    @app.before_request
    def iniciar_cronometro():
        g.inicio = time.perf_counter()

    @app.after_request
    def registrar_peticion(respuesta):
        if hasattr(g, "inicio"):
            ms = (time.perf_counter() - g.inicio) * 1000
            respuesta.headers["X-Response-Time-ms"] = f"{ms:.2f}"
            app.logger.info(
                "%s %s -> %s (%.2f ms)",
                request.method, request.path, respuesta.status_code, ms,
            )
        return respuesta

    @app.errorhandler(500)
    def error_interno(_e):
        app.logger.exception("Error interno")
        return jsonify({"error": "Error interno del servidor."}), 500

    # ---------------------------------------------------------- Vistas
    @app.route("/")
    def index():
        return render_template(
            "index.html", estados=ESTADOS, prioridades=PRIORIDADES
        )

    @app.route("/health")
    def health():
        try:
            total = get_db().execute("SELECT COUNT(*) FROM tareas").fetchone()[0]
            bd = "ok"
        except sqlite3.Error:
            total, bd = None, "error"
        return jsonify({
            "status": "ok" if bd == "ok" else "degradado",
            "base_de_datos": bd,
            "tareas_registradas": total,
            "tiempo_activo_seg": round(time.time() - app.config["INICIO"], 1),
            "version": "1.0.0",
        }), (200 if bd == "ok" else 503)

    # ------------------------------------------------------------ API
    @app.route("/api/tareas", methods=["GET"])
    def listar_tareas():  # RF02
        sql = "SELECT * FROM tareas"
        filtros, params = [], []
        estado = request.args.get("estado")
        prioridad = request.args.get("prioridad")
        if estado:
            filtros.append("estado = ?")
            params.append(estado)
        if prioridad:
            filtros.append("prioridad = ?")
            params.append(prioridad)
        if filtros:
            sql += " WHERE " + " AND ".join(filtros)
        sql += (" ORDER BY CASE prioridad WHEN 'Alta' THEN 1 "
                "WHEN 'Media' THEN 2 ELSE 3 END, id DESC")
        filas = get_db().execute(sql, params).fetchall()
        return jsonify([dict(f) for f in filas])

    @app.route("/api/tareas/<int:tarea_id>", methods=["GET"])
    def ver_tarea(tarea_id):  # RF02
        tarea = obtener(tarea_id)
        return jsonify(tarea) if tarea else no_encontrada()

    @app.route("/api/tareas", methods=["POST"])
    def crear_tarea():  # RF01 + RF06
        datos, errores = validar_tarea(request.get_json(silent=True))
        if errores:
            return jsonify({"errores": errores}), 400
        fecha = ahora()
        db = get_db()
        cur = db.execute(
            "INSERT INTO tareas (nombre, descripcion, prioridad, estado, "
            "responsable, fecha_creacion, fecha_actualizacion) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (datos["nombre"], datos["descripcion"], datos["prioridad"],
             datos["estado"], datos["responsable"], fecha, fecha),
        )
        db.commit()
        return jsonify({
            "mensaje": "Tarea registrada correctamente.",
            "tarea": obtener(cur.lastrowid),
        }), 201

    @app.route("/api/tareas/<int:tarea_id>", methods=["PUT"])
    def editar_tarea(tarea_id):  # RF03
        if not obtener(tarea_id):
            return no_encontrada()
        datos, errores = validar_tarea(request.get_json(silent=True), parcial=True)
        if errores:
            return jsonify({"errores": errores}), 400
        if not datos:
            return jsonify({"errores": ["No se enviaron campos para actualizar."]}), 400
        campos = ", ".join(f"{k} = ?" for k in datos)
        db = get_db()
        db.execute(
            f"UPDATE tareas SET {campos}, fecha_actualizacion = ? WHERE id = ?",
            (*datos.values(), ahora(), tarea_id),
        )
        db.commit()
        return jsonify({
            "mensaje": "Tarea actualizada correctamente.",
            "tarea": obtener(tarea_id),
        })

    @app.route("/api/tareas/<int:tarea_id>/estado", methods=["PATCH"])
    def cambiar_estado(tarea_id):  # RF05
        if not obtener(tarea_id):
            return no_encontrada()
        estado = (request.get_json(silent=True) or {}).get("estado")
        if estado not in ESTADOS:
            return jsonify({"errores": [
                "El estado debe ser Pendiente, En proceso o Terminada."
            ]}), 400
        db = get_db()
        db.execute(
            "UPDATE tareas SET estado = ?, fecha_actualizacion = ? WHERE id = ?",
            (estado, ahora(), tarea_id),
        )
        db.commit()
        return jsonify({
            "mensaje": f"Estado cambiado a '{estado}'.",
            "tarea": obtener(tarea_id),
        })

    @app.route("/api/tareas/<int:tarea_id>", methods=["DELETE"])
    def eliminar_tarea(tarea_id):  # RF04
        if not obtener(tarea_id):
            return no_encontrada()
        db = get_db()
        db.execute("DELETE FROM tareas WHERE id = ?", (tarea_id,))
        db.commit()
        return jsonify({"mensaje": "Tarea eliminada correctamente."})

    return app


app = create_app()

if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=puerto, debug=os.environ.get("FLASK_DEBUG") == "1")
