// TaskManager - lógica del frontend
const API = "/api/tareas";

const form = document.getElementById("form-tarea");
const campos = {
  id: document.getElementById("tarea-id"),
  nombre: document.getElementById("nombre"),
  descripcion: document.getElementById("descripcion"),
  responsable: document.getElementById("responsable"),
  prioridad: document.getElementById("prioridad"),
  estado: document.getElementById("estado"),
};
const errorNombre = document.getElementById("error-nombre");
const tituloForm = document.getElementById("titulo-form");
const btnGuardar = document.getElementById("btn-guardar");
const btnCancelar = document.getElementById("btn-cancelar");
const lista = document.getElementById("lista-tareas");
const vacio = document.getElementById("vacio");
const filtroEstado = document.getElementById("filtro-estado");
const filtroPrioridad = document.getElementById("filtro-prioridad");
const toast = document.getElementById("toast");

let tareasCache = [];

function mostrarMensaje(texto, esError = false) {
  toast.textContent = texto;
  toast.classList.toggle("error", esError);
  toast.classList.add("visible");
  clearTimeout(mostrarMensaje._t);
  mostrarMensaje._t = setTimeout(() => toast.classList.remove("visible"), 2800);
}

async function peticion(url, opciones = {}) {
  const resp = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...opciones,
  });
  const datos = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    const msg = (datos.errores && datos.errores.join(" ")) || datos.error || "Ocurrió un error.";
    throw new Error(msg);
  }
  return datos;
}

// El servidor guarda las fechas en UTC; se muestran en la hora local del usuario.
function fechaLocal(utc) {
  const d = new Date(String(utc).replace(" ", "T") + "Z");
  return isNaN(d) ? utc : d.toLocaleString("es-MX", { dateStyle: "short", timeStyle: "short" });
}

function escapar(texto) {
  const div = document.createElement("div");
  div.textContent = texto ?? "";
  return div.innerHTML;
}

// RF02 - Consultar tareas
async function cargarTareas() {
  const params = new URLSearchParams();
  if (filtroEstado.value) params.set("estado", filtroEstado.value);
  if (filtroPrioridad.value) params.set("prioridad", filtroPrioridad.value);
  try {
    tareasCache = await peticion(`${API}?${params}`);
    pintarTareas();
    actualizarResumen();
  } catch (e) {
    mostrarMensaje(e.message, true);
  }
}

function pintarTareas() {
  lista.innerHTML = "";
  vacio.classList.toggle("oculto", tareasCache.length > 0);
  for (const t of tareasCache) {
    const li = document.createElement("li");
    li.className = `tarea ${t.prioridad} ${t.estado === "Terminada" ? "terminada" : ""}`;
    li.dataset.id = t.id;
    const opciones = window.ESTADOS.map(
      (e) => `<option value="${e}" ${e === t.estado ? "selected" : ""}>${e}</option>`
    ).join("");
    li.innerHTML = `
      <h3>${escapar(t.nombre)}</h3>
      ${t.descripcion ? `<p>${escapar(t.descripcion)}</p>` : ""}
      <div class="meta">
        <span class="etiqueta ${t.prioridad}">${t.prioridad}</span>
        ${t.responsable ? `<span>👤 ${escapar(t.responsable)}</span>` : ""}
        <span>Actualizada: ${fechaLocal(t.fecha_actualizacion)}</span>
      </div>
      <div class="tarea-acciones">
        <select class="sel-estado" aria-label="Cambiar estado">${opciones}</select>
        <button class="btn secundario pequeno btn-editar">Editar</button>
        <button class="btn peligro pequeno btn-eliminar">Eliminar</button>
      </div>`;
    lista.appendChild(li);
  }
}

async function actualizarResumen() {
  try {
    const todas = await peticion(API);
    const conteo = { "Pendiente": 0, "En proceso": 0, "Terminada": 0 };
    todas.forEach((t) => (conteo[t.estado] = (conteo[t.estado] || 0) + 1));
    const textos = { "Pendiente": "pendientes", "En proceso": "en proceso", "Terminada": "terminadas" };
    document.querySelectorAll("[data-resumen]").forEach((el) => {
      const e = el.dataset.resumen;
      el.textContent = `${conteo[e]} ${textos[e]}`;
    });
  } catch (_) { /* el resumen no es crítico */ }
}

function limpiarFormulario() {
  form.reset();
  campos.id.value = "";
  campos.prioridad.value = "Media";
  campos.estado.value = "Pendiente";
  errorNombre.textContent = "";
  campos.nombre.classList.remove("invalido");
  tituloForm.textContent = "Nueva tarea";
  btnGuardar.textContent = "Guardar tarea";
  btnCancelar.classList.add("oculto");
}

// RF01 - Registrar  /  RF03 - Editar
form.addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const nombre = campos.nombre.value.trim();
  if (!nombre) {
    errorNombre.textContent = "El nombre de la tarea es obligatorio.";
    campos.nombre.classList.add("invalido");
    campos.nombre.focus();
    return;
  }
  errorNombre.textContent = "";
  campos.nombre.classList.remove("invalido");

  const cuerpo = {
    nombre,
    descripcion: campos.descripcion.value.trim(),
    responsable: campos.responsable.value.trim(),
    prioridad: campos.prioridad.value,
    estado: campos.estado.value,
  };
  const id = campos.id.value;
  try {
    const datos = id
      ? await peticion(`${API}/${id}`, { method: "PUT", body: JSON.stringify(cuerpo) })
      : await peticion(API, { method: "POST", body: JSON.stringify(cuerpo) });
    mostrarMensaje(datos.mensaje);
    limpiarFormulario();
    cargarTareas();
  } catch (e) {
    mostrarMensaje(e.message, true);
  }
});

btnCancelar.addEventListener("click", limpiarFormulario);

lista.addEventListener("click", async (ev) => {
  const li = ev.target.closest(".tarea");
  if (!li) return;
  const id = li.dataset.id;
  const tarea = tareasCache.find((t) => String(t.id) === id);

  if (ev.target.classList.contains("btn-editar") && tarea) {
    campos.id.value = tarea.id;
    campos.nombre.value = tarea.nombre;
    campos.descripcion.value = tarea.descripcion;
    campos.responsable.value = tarea.responsable;
    campos.prioridad.value = tarea.prioridad;
    campos.estado.value = tarea.estado;
    tituloForm.textContent = "Editar tarea";
    btnGuardar.textContent = "Actualizar tarea";
    btnCancelar.classList.remove("oculto");
    campos.nombre.focus();
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  // RF04 - Eliminar
  if (ev.target.classList.contains("btn-eliminar")) {
    if (!confirm("¿Deseas eliminar esta tarea?")) return;
    try {
      const datos = await peticion(`${API}/${id}`, { method: "DELETE" });
      mostrarMensaje(datos.mensaje);
      if (campos.id.value === id) limpiarFormulario();
      cargarTareas();
    } catch (e) {
      mostrarMensaje(e.message, true);
    }
  }
});

// RF05 - Cambiar estado
lista.addEventListener("change", async (ev) => {
  if (!ev.target.classList.contains("sel-estado")) return;
  const id = ev.target.closest(".tarea").dataset.id;
  try {
    const datos = await peticion(`${API}/${id}/estado`, {
      method: "PATCH",
      body: JSON.stringify({ estado: ev.target.value }),
    });
    mostrarMensaje(datos.mensaje);
    cargarTareas();
  } catch (e) {
    mostrarMensaje(e.message, true);
  }
});

filtroEstado.addEventListener("change", cargarTareas);
filtroPrioridad.addEventListener("change", cargarTareas);

cargarTareas();
