#!/usr/bin/env bash
# =====================================================================
#  Configuración automática de la Fase 1 (Plan) en GitHub
#  - Etiquetas (prioridad y fase DevOps)
#  - Milestone v1.0.0
#  - Issues de historias de usuario y actividades
#  - Tablero de GitHub Projects con los campos que pide la práctica
#
#  Requisitos:
#    1. GitHub CLI instalado: https://cli.github.com
#    2. Sesión iniciada con permiso de proyectos:
#         gh auth login
#         gh auth refresh -s project
#    3. jq instalado (https://jqlang.github.io/jq/)
#    4. Ejecutar desde la carpeta del repositorio ya subido a GitHub.
#
#  Uso:
#    bash scripts/configurar_github.sh USUARIO_DUEÑO INTEGRANTE1 INTEGRANTE2 INTEGRANTE3
#  Ejemplo:
#    bash scripts/configurar_github.sh juanperez juanperez anagomez luisruiz
#  (los integrantes deben haber aceptado la invitación como colaboradores)
# =====================================================================
set -uo pipefail

if [ $# -lt 4 ]; then
  echo "Uso: $0 USUARIO_DUEÑO INTEGRANTE1 INTEGRANTE2 INTEGRANTE3"
  exit 1
fi

OWNER="$1"; I1="$2"; I2="$3"; I3="$4"
REPO="$OWNER/TaskManager-DevOps"

command -v gh >/dev/null || { echo "Falta GitHub CLI (gh)"; exit 1; }
command -v jq >/dev/null || { echo "Falta jq"; exit 1; }

echo "==> Repositorio: $REPO"

# ------------------------------------------------------------ Etiquetas
echo "==> Creando etiquetas"
crear_label() { gh label create "$1" --repo "$REPO" --color "$2" --description "$3" --force >/dev/null; }
crear_label "prioridad: crítica" "7f1d1d" "Prioridad crítica"
crear_label "prioridad: alta"    "dc2626" "Prioridad alta"
crear_label "prioridad: media"   "d97706" "Prioridad media"
crear_label "prioridad: baja"    "16a34a" "Prioridad baja"
for f in Plan Code Build Test Release Deploy Operate Monitor; do
  crear_label "fase: $f" "2563eb" "Fase DevOps: $f"
done
crear_label "historia de usuario" "7c3aed" "Historia de usuario"
crear_label "bug"        "b91c1c" "Error detectado"
crear_label "incidencia" "ea580c" "Incidencia en producción"
crear_label "mejora"     "0891b2" "Propuesta de mejora"

# ------------------------------------------------------------ Milestone
echo "==> Creando milestone v1.0.0"
gh api "repos/$REPO/milestones" -f title="v1.0.0" \
  -f description="Primera versión estable de TaskManager" \
  -f due_on="2026-11-25T23:59:59Z" >/dev/null 2>&1 || true

# ------------------------------------------------------------ Proyecto
echo "==> Creando GitHub Project"
PROJ_JSON=$(gh project create --owner "$OWNER" --title "TaskManager-DevOps" --format json)
PNUM=$(echo "$PROJ_JSON" | jq -r '.number')
PID=$(echo "$PROJ_JSON" | jq -r '.id')
echo "    Proyecto #$PNUM"
gh project link "$PNUM" --owner "$OWNER" --repo "$REPO" >/dev/null 2>&1 || true

gh project field-create "$PNUM" --owner "$OWNER" --name "Prioridad" \
  --data-type SINGLE_SELECT --single-select-options "Crítica,Alta,Media,Baja" >/dev/null
gh project field-create "$PNUM" --owner "$OWNER" --name "Estimación" --data-type NUMBER >/dev/null
gh project field-create "$PNUM" --owner "$OWNER" --name "Fase DevOps" \
  --data-type SINGLE_SELECT \
  --single-select-options "Plan,Code,Build,Test,Release,Deploy,Operate,Monitor" >/dev/null
gh project field-create "$PNUM" --owner "$OWNER" --name "Fecha límite" --data-type DATE >/dev/null

FIELDS=$(gh project field-list "$PNUM" --owner "$OWNER" --format json --limit 50)
fid()  { echo "$FIELDS" | jq -r --arg n "$1" '.fields[] | select(.name==$n) | .id'; }
oid()  { echo "$FIELDS" | jq -r --arg n "$1" --arg o "$2" \
           '.fields[] | select(.name==$n) | .options[]? | select(.name==$o) | .id'; }

# Columnas del tablero: Backlog, To Do, In Progress, Review, Done
STATUS_ID=$(fid "Status")
echo "==> Configurando columnas de Status"
if gh api graphql -f query='
  mutation($f:ID!){
    updateProjectV2Field(input:{fieldId:$f, singleSelectOptions:[
      {name:"Backlog",     color:GRAY,   description:"Actividades pendientes de realizar"},
      {name:"To Do",       color:BLUE,   description:"Actividades que se realizarán"},
      {name:"In Progress", color:YELLOW, description:"Actividades en desarrollo"},
      {name:"Review",      color:PURPLE, description:"Actividades en revisión"},
      {name:"Done",        color:GREEN,  description:"Actividades terminadas"}
    ]}){ projectV2Field{ ... on ProjectV2SingleSelectField { id } } }
  }' -f f="$STATUS_ID" >/dev/null 2>&1; then
  echo "    Columnas creadas."
  FIELDS=$(gh project field-list "$PNUM" --owner "$OWNER" --format json --limit 50)
else
  echo "    AVISO: no se pudieron crear las columnas automáticamente."
  echo "    Créalas a mano en el tablero: Backlog, To Do, In Progress, Review, Done."
fi

F_PRI=$(fid "Prioridad"); F_EST=$(fid "Estimación"); F_FASE=$(fid "Fase DevOps"); F_FECHA=$(fid "Fecha límite")

# ------------------------------------------------------------ Issues
# crear_issue "Título" "Cuerpo" responsable prioridad fase horas fecha estado
crear_issue() {
  local titulo="$1" cuerpo="$2" resp="$3" pri="$4" fase="$5" horas="$6" fecha="$7" estado="$8"
  local pri_label; pri_label="prioridad: $(echo "$pri" | tr '[:upper:]' '[:lower:]')"
  local labels=(--label "$pri_label" --label "fase: $fase")
  [[ "$titulo" == HU* ]] && labels+=(--label "historia de usuario")
  local url
  # Si el responsable aún no acepta la invitación, se crea sin asignar.
  url=$(gh issue create --repo "$REPO" --title "$titulo" --body "$cuerpo" \
        --assignee "$resp" "${labels[@]}" --milestone "v1.0.0" 2>/dev/null \
        || gh issue create --repo "$REPO" --title "$titulo" --body "$cuerpo" "${labels[@]}")
  echo "    $url"
  local item
  item=$(gh project item-add "$PNUM" --owner "$OWNER" --url "$url" --format json | jq -r '.id')
  gh project item-edit --project-id "$PID" --id "$item" --field-id "$F_PRI" \
     --single-select-option-id "$(oid Prioridad "$pri")" >/dev/null
  gh project item-edit --project-id "$PID" --id "$item" --field-id "$F_FASE" \
     --single-select-option-id "$(oid 'Fase DevOps' "$fase")" >/dev/null
  gh project item-edit --project-id "$PID" --id "$item" --field-id "$F_EST" --number "$horas" >/dev/null
  gh project item-edit --project-id "$PID" --id "$item" --field-id "$F_FECHA" --date "$fecha" >/dev/null
  local sid; sid=$(oid Status "$estado")
  [ -n "$sid" ] && gh project item-edit --project-id "$PID" --id "$item" \
     --field-id "$STATUS_ID" --single-select-option-id "$sid" >/dev/null
}

echo "==> Creando historias de usuario"
crear_issue "HU01: Registrar tareas" \
"**Como** usuario del sistema, **quiero** registrar nuevas tareas **para** organizar mis actividades.

**Criterios de aceptación**
- [ ] Permite ingresar el nombre de la tarea (obligatorio).
- [ ] Permite agregar una descripción.
- [ ] Permite seleccionar una prioridad.
- [ ] La tarea se guarda en la base de datos.
- [ ] Se muestra un mensaje de confirmación.

Requerimiento: RF01" "$I1" "Alta" "Plan" 1 2026-11-23 "Backlog"

crear_issue "HU02: Consultar tareas" \
"**Como** usuario, **quiero** ver todas las tareas registradas **para** identificar las pendientes y terminadas.

**Criterios de aceptación**
- [ ] Se muestra el listado de tareas con nombre, descripción, prioridad, estado y responsable.
- [ ] Las tareas se ordenan por prioridad.
- [ ] Se puede filtrar por estado y por prioridad.
- [ ] Si no hay tareas se muestra un mensaje.

Requerimiento: RF02" "$I1" "Alta" "Plan" 1 2026-11-23 "Backlog"

crear_issue "HU03: Editar tareas" \
"**Como** usuario, **quiero** modificar la información de una tarea **para** corregir o actualizar sus datos.

**Criterios de aceptación**
- [ ] Se puede abrir una tarea existente en el formulario.
- [ ] Se pueden cambiar nombre, descripción, responsable, prioridad y estado.
- [ ] No se permite dejar el nombre vacío.
- [ ] Los cambios se reflejan en el listado y se muestra confirmación.

Requerimiento: RF03" "$I2" "Alta" "Plan" 1 2026-11-23 "Backlog"

crear_issue "HU04: Eliminar tareas" \
"**Como** usuario, **quiero** eliminar tareas existentes **para** evitar duplicados e información obsoleta.

**Criterios de aceptación**
- [ ] Se pide confirmación antes de eliminar.
- [ ] La tarea desaparece del listado.
- [ ] Se muestra un mensaje de confirmación.

Requerimiento: RF04" "$I3" "Media" "Plan" 1 2026-11-23 "Backlog"

crear_issue "HU05: Cambiar estado de tareas" \
"**Como** usuario, **quiero** cambiar el estado de una tarea **para** conocer su progreso.

**Criterios de aceptación**
- [ ] Permite seleccionar Pendiente.
- [ ] Permite seleccionar En proceso.
- [ ] Permite seleccionar Terminada.
- [ ] El cambio se refleja en el listado de tareas.

Requerimiento: RF05" "$I2" "Alta" "Plan" 1 2026-11-23 "Backlog"

crear_issue "HU06: Asignar prioridad" \
"**Como** responsable de área, **quiero** clasificar las tareas como Alta, Media o Baja **para** atender primero lo más importante.

**Criterios de aceptación**
- [ ] Al registrar o editar se puede elegir Alta, Media o Baja.
- [ ] Si no se elige, la prioridad es Media.
- [ ] La prioridad se distingue visualmente en el listado.
- [ ] No se aceptan valores distintos.

Requerimiento: RF06" "$I3" "Media" "Plan" 1 2026-11-23 "Backlog"

echo "==> Creando actividades"
crear_issue "Crear la estructura inicial del proyecto" \
"Crear app.py, requirements.txt, templates/, static/ y tests/ según la estructura de la práctica." \
"$I1" "Crítica" "Code" 2 2026-11-23 "To Do"
crear_issue "Diseñar la interfaz del sistema" \
"Formulario de tareas, listado, filtros y estilos (index.html, style.css)." \
"$I2" "Alta" "Code" 3 2026-11-23 "To Do"
crear_issue "Implementar el registro y la consulta de tareas" \
"RF01 y RF02: endpoints POST/GET /api/tareas y su conexión con el frontend. Rama: feature/registro-tareas" \
"$I1" "Alta" "Code" 3 2026-11-24 "To Do"
crear_issue "Implementar la edición de tareas y el cambio de estado" \
"RF03 y RF05: endpoints PUT /api/tareas/<id> y PATCH /api/tareas/<id>/estado. Rama: feature/editar-tareas" \
"$I2" "Alta" "Code" 3 2026-11-24 "To Do"
crear_issue "Implementar la eliminación de tareas y las prioridades" \
"RF04 y RF06: endpoint DELETE y validación de prioridad. Rama: feature/eliminar-tareas" \
"$I3" "Alta" "Code" 2 2026-11-24 "To Do"
crear_issue "Configurar la integración continua (ci.yml)" \
"Workflow de GitHub Actions que ejecuta pytest en cada push y pull request a main." \
"$I3" "Alta" "Build" 1 2026-11-24 "To Do"
crear_issue "Implementar las pruebas unitarias" \
"Pruebas con Pytest para CP01–CP07 en tests/test_app.py." \
"$I3" "Alta" "Test" 3 2026-11-24 "To Do"
crear_issue "Ejecutar las pruebas funcionales (matriz CP01–CP07)" \
"Ejecutar manualmente cada caso de prueba y registrar resultados con capturas." \
"$I1" "Media" "Test" 2 2026-11-24 "Backlog"
crear_issue "Publicar el Release v1.0.0 y el workflow de entrega" \
"Crear la etiqueta v1.0.0, notas de versión y verificar el artefacto generado por entrega.yml." \
"$I2" "Media" "Release" 1 2026-11-25 "Backlog"
crear_issue "Desplegar la aplicación en Render" \
"Conectar el repositorio, configurar build/start, deploy hook y verificar la URL pública." \
"$I3" "Alta" "Deploy" 2 2026-11-25 "Backlog"
crear_issue "Monitorear la aplicación publicada" \
"Revisar /health, tiempos de respuesta, logs de Render y el workflow monitoreo.yml. Documentar incidencias." \
"$I1" "Media" "Monitor" 1 2026-11-25 "Backlog"
crear_issue "Elaborar documentación y conclusiones" \
"README, documento de resultados y respuestas a las preguntas de análisis." \
"$I2" "Media" "Operate" 2 2026-11-25 "Backlog"

echo
echo "Listo. Abre el proyecto en: https://github.com/users/$OWNER/projects/$PNUM"
echo "En el proyecto cambia la vista a 'Board' agrupada por Status."
