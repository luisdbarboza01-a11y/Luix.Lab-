# Protocolo de tareas v1

## 1. Identidad

Cada tarea debe tener un identificador único e inmutable, por ejemplo `EXP-001`.

## 2. Campos obligatorios

- `task_id`
- `title`
- `objective`
- `context`
- `inputs`
- `permissions`
- `constraints`
- `deliverables`
- `acceptance_criteria`
- `owner`
- `status`
- `created_at`
- `protocol_version`

## 3. Estados permitidos

- `draft`: en preparación.
- `queued`: lista para asignar.
- `sent`: enviada por un canal comprobado.
- `received`: recepción confirmada por evidencia.
- `in_progress`: ejecución confirmada.
- `blocked`: existe un impedimento documentado.
- `submitted`: entrega recibida.
- `under_review`: auditoría en curso.
- `accepted`: criterios de aceptación satisfechos.
- `rejected`: criterios no satisfechos.
- `cancelled`: cancelada con motivo.

No usar `sent`, `received` o `in_progress` por inferencia. Deben existir evidencias.

## 4. Entrega del agente

Toda entrega debe incluir:

1. task_id exacto.
2. estado y alcance realmente completado.
3. acciones realizadas.
4. fuentes, archivos o datos utilizados.
5. método y pasos reproducibles.
6. resultados y limitaciones.
7. errores o bloqueos.
8. evidencia verificable.
9. cambios realizados, si fueron autorizados.

## 5. Auditoría

El auditor debe evaluar los criterios de aceptación de forma independiente, señalar discrepancias y no asumir que una ejecución exitosa equivale a un resultado correcto.

## 6. Seguridad

- Permisos mínimos necesarios.
- No exponer secretos.
- No ejecutar acciones externas no autorizadas.
- No modificar datos originales sin autorización explícita.
- No realizar compras, despliegues ni acciones con coste sin autorización explícita.

## 7. Regla de comunicación

Un archivo compartido no demuestra que un agente lo haya leído. La recepción requiere respuesta identificable con el mismo task_id a través de un canal observado.
