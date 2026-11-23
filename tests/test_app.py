"""Pruebas unitarias de TaskManager (Pytest).

Cada prueba usa una base de datos SQLite temporal, por lo que no
afectan los datos reales. Los IDs de prueba (CPxx) coinciden con la
matriz de casos de prueba de la Fase 4.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app, validar_tarea  # noqa: E402


@pytest.fixture
def client(tmp_path):
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.db")})
    with app.test_client() as c:
        yield c


def crear(client, **kwargs):
    datos = {"nombre": "Elaborar documentación", "descripcion": "Manual de usuario",
             "prioridad": "Alta"}
    datos.update(kwargs)
    return client.post("/api/tareas", json=datos)


# ---------------------------------------------------------- Ejemplo del PDF
def test_registro_tarea():
    tarea = {"nombre": "Realizar actividad DevOps", "estado": "Pendiente"}
    assert tarea["nombre"] == "Realizar actividad DevOps"
    assert tarea["estado"] == "Pendiente"


# ----------------------------------------------------- Validación (unitarias)
def test_validar_tarea_correcta():
    datos, errores = validar_tarea({"nombre": "  Tarea  ", "prioridad": "Baja"})
    assert errores == []
    assert datos["nombre"] == "Tarea"
    assert datos["estado"] == "Pendiente"


def test_validar_tarea_sin_nombre():
    _, errores = validar_tarea({"nombre": "   "})
    assert "El nombre de la tarea es obligatorio." in errores


def test_validar_cuerpo_no_json():
    _, errores = validar_tarea(None)
    assert errores


# --------------------------------------------------------------- CP01 / RF01
def test_cp01_registrar_tarea(client):
    resp = crear(client)
    assert resp.status_code == 201
    cuerpo = resp.get_json()
    assert cuerpo["mensaje"] == "Tarea registrada correctamente."
    assert cuerpo["tarea"]["nombre"] == "Elaborar documentación"
    assert cuerpo["tarea"]["estado"] == "Pendiente"


def test_registrar_tarea_sin_descripcion(client):
    """Regresión del Issue 'Error al guardar tareas sin descripción'."""
    resp = client.post("/api/tareas", json={"nombre": "Sin descripción"})
    assert resp.status_code == 201
    assert resp.get_json()["tarea"]["descripcion"] == ""


# --------------------------------------------------------------------- CP02
def test_cp02_registrar_tarea_sin_nombre(client):
    resp = crear(client, nombre="")
    assert resp.status_code == 400
    assert "El nombre de la tarea es obligatorio." in resp.get_json()["errores"]


def test_registrar_nombre_demasiado_largo(client):
    resp = crear(client, nombre="x" * 101)
    assert resp.status_code == 400


def test_registrar_sin_cuerpo_json(client):
    resp = client.post("/api/tareas", data="texto", content_type="text/plain")
    assert resp.status_code == 400


# --------------------------------------------------------------- CP03 / RF02
def test_cp03_consultar_tareas(client):
    crear(client, nombre="Tarea 1")
    crear(client, nombre="Tarea 2")
    resp = client.get("/api/tareas")
    assert resp.status_code == 200
    nombres = [t["nombre"] for t in resp.get_json()]
    assert set(nombres) == {"Tarea 1", "Tarea 2"}


def test_consultar_lista_vacia(client):
    assert client.get("/api/tareas").get_json() == []


def test_consultar_tarea_por_id(client):
    tid = crear(client).get_json()["tarea"]["id"]
    resp = client.get(f"/api/tareas/{tid}")
    assert resp.status_code == 200
    assert resp.get_json()["id"] == tid


def test_consultar_tarea_inexistente(client):
    assert client.get("/api/tareas/999").status_code == 404


def test_filtrar_por_estado_y_prioridad(client):
    crear(client, nombre="A", prioridad="Alta")
    crear(client, nombre="B", prioridad="Baja", estado="Terminada")
    altas = client.get("/api/tareas?prioridad=Alta").get_json()
    terminadas = client.get("/api/tareas?estado=Terminada").get_json()
    assert [t["nombre"] for t in altas] == ["A"]
    assert [t["nombre"] for t in terminadas] == ["B"]


def test_orden_por_prioridad(client):
    crear(client, nombre="Baja", prioridad="Baja")
    crear(client, nombre="Alta", prioridad="Alta")
    crear(client, nombre="Media", prioridad="Media")
    nombres = [t["nombre"] for t in client.get("/api/tareas").get_json()]
    assert nombres == ["Alta", "Media", "Baja"]


# --------------------------------------------------------------- CP04 / RF03
def test_cp04_editar_tarea(client):
    tid = crear(client).get_json()["tarea"]["id"]
    resp = client.put(f"/api/tareas/{tid}",
                      json={"nombre": "Documentación final", "prioridad": "Baja"})
    assert resp.status_code == 200
    tarea = resp.get_json()["tarea"]
    assert tarea["nombre"] == "Documentación final"
    assert tarea["prioridad"] == "Baja"
    assert tarea["descripcion"] == "Manual de usuario"  # no se pierde


def test_editar_con_nombre_vacio(client):
    tid = crear(client).get_json()["tarea"]["id"]
    assert client.put(f"/api/tareas/{tid}", json={"nombre": ""}).status_code == 400


def test_editar_tarea_inexistente(client):
    assert client.put("/api/tareas/999", json={"nombre": "X"}).status_code == 404


def test_editar_sin_campos(client):
    tid = crear(client).get_json()["tarea"]["id"]
    assert client.put(f"/api/tareas/{tid}", json={}).status_code == 400


# --------------------------------------------------------------- CP05 / RF04
def test_cp05_eliminar_tarea(client):
    tid = crear(client).get_json()["tarea"]["id"]
    resp = client.delete(f"/api/tareas/{tid}")
    assert resp.status_code == 200
    assert client.get(f"/api/tareas/{tid}").status_code == 404
    assert client.get("/api/tareas").get_json() == []


def test_eliminar_tarea_inexistente(client):
    assert client.delete("/api/tareas/999").status_code == 404


# --------------------------------------------------------------- CP06 / RF05
@pytest.mark.parametrize("estado", ["Pendiente", "En proceso", "Terminada"])
def test_cp06_cambiar_estado(client, estado):
    tid = crear(client).get_json()["tarea"]["id"]
    resp = client.patch(f"/api/tareas/{tid}/estado", json={"estado": estado})
    assert resp.status_code == 200
    # El cambio debe reflejarse en el listado
    listado = client.get("/api/tareas").get_json()
    assert listado[0]["estado"] == estado


def test_cambiar_estado_invalido(client):
    tid = crear(client).get_json()["tarea"]["id"]
    resp = client.patch(f"/api/tareas/{tid}/estado", json={"estado": "Cancelada"})
    assert resp.status_code == 400


def test_cambiar_estado_tarea_inexistente(client):
    resp = client.patch("/api/tareas/999/estado", json={"estado": "Terminada"})
    assert resp.status_code == 404


# --------------------------------------------------------------- CP07 / RF06
@pytest.mark.parametrize("prioridad", ["Alta", "Media", "Baja"])
def test_cp07_seleccionar_prioridad(client, prioridad):
    resp = crear(client, prioridad=prioridad)
    assert resp.get_json()["tarea"]["prioridad"] == prioridad


def test_prioridad_invalida(client):
    assert crear(client, prioridad="Urgente").status_code == 400


def test_prioridad_por_defecto_media(client):
    resp = client.post("/api/tareas", json={"nombre": "Sin prioridad"})
    assert resp.get_json()["tarea"]["prioridad"] == "Media"


# --------------------------------------------------- Interfaz y monitoreo
def test_pagina_principal(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "TaskManager" in resp.get_data(as_text=True)


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    datos = resp.get_json()
    assert datos["status"] == "ok"
    assert datos["base_de_datos"] == "ok"


def test_cabecera_tiempo_respuesta(client):
    resp = client.get("/api/tareas")
    assert "X-Response-Time-ms" in resp.headers
