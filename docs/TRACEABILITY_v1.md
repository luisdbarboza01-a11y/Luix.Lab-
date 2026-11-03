# Sincronización y trazabilidad v1

## Propósito
Mantener un registro verificable del ciclo de vida de cada tarea, sin confundir almacenamiento compartido con comunicación real entre agentes.

## Fuentes de verdad
- GitHub: registro documental versionado y evidencia persistente.
- Deepnote: entorno de análisis y ejecución; su estado debe registrarse por separado.
- Agentes: solo se consideran actores que hayan respondido mediante un canal verificable.
- Registro de eventos: historial append-only; no editar eventos antiguos para ocultar cambios.

## Identificadores
- `task_id`: identifica la tarea de forma permanente.
- `event_id`: identifica cada evento.
- `agent_id`: identifica al actor lógico; no implica que exista una integración funcional.
- `artifact_id`: identifica entregas, revisiones, archivos o snapshots.

## Estados y evidencia mínima
| Estado | Evidencia necesaria |
|---|---|
| draft | Especificación guardada |
| queued | Criterios y permisos completos |
| sent | Registro del envío por un canal probado |
| received | Respuesta del destinatario con task_id coincidente |
| in_progress | Confirmación explícita de inicio |
| blocked | Bloqueo descrito y evidencia |
| submitted | Entrega persistida y asociada a task_id |
| under_review | Auditor asignado y revisión iniciada |
| accepted | Revisión que demuestra todos los criterios |
| rejected | Revisión con criterios incumplidos |
| cancelled | Motivo y actor que cancela |

No se permiten saltos de estado sin evento y evidencia. Un archivo en GitHub no prueba que un agente lo haya leído.

## Formato de evento
Cada evento registra:
- event_id
- timestamp_utc
- task_id
- event_type
- from_status
- to_status
- actor_id
- channel
- evidence_refs
- details

## Sincronización
1. Escribir primero la especificación de tarea.
2. Registrar el evento de creación.
3. Enviar por un canal realmente disponible.
4. Registrar el envío solo después de la acción y respuesta del canal.
5. Registrar recepción solo al recibir confirmación con task_id.
6. Guardar entrega y registrar su referencia.
7. Abrir revisión independiente.
8. Registrar veredicto y cerrar tarea.

## Resolución de conflictos
- No sobrescribir entregas originales.
- Si dos eventos incompatibles aparecen, conservar ambos y marcar conflicto.
- La cronología se determina por timestamp UTC y referencia de origen; el orden de commits por sí solo no demuestra el orden real de ejecución.
- Cambios manuales deben identificar actor y motivo.

## Límites actuales
GitHub ofrece almacenamiento versionado y commits. No existe todavía sincronización automática demostrada entre GitHub, Deepnote y agentes. El registro manual o asistido por herramientas no debe presentarse como automatización.
