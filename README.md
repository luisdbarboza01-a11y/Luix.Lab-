# Luix° AI Network

Infraestructura experimental para coordinar tareas de investigación asistida por IA con trazabilidad, revisión independiente y control de permisos.

## Estado verificado

- GitHub conectado con acceso de lectura/escritura.
- Motor interno v1 implementado: registro, transiciones, cola de despacho, recepción de entregas y revisión independiente.
- Pruebas unitarias e integrales: **33/33 aprobadas** en la última ejecución de Deepnote.
- Auditoría del historial: disponible mediante `python -m engine.coordinator`.
- Integración continua: workflow añadido en `.github/workflows/ci.yml` para ejecutar pruebas y auditoría en cada push a `main` y en pull requests.
- Comunicación autónoma entre agentes: **no verificada**.
- Sincronización automática GitHub–Deepnote: **no implementada**.
- Integración de mensajería con agentes externos: **pendiente de un canal/API compatible**.

## Principios

1. No afirmar que una tarea fue recibida o ejecutada sin evidencia.
2. Toda tarea tiene un identificador único y criterios de aceptación.
3. Separar propuesta, ejecución, resultado y auditoría.
4. Mantener datos originales sin modificaciones no autorizadas.
5. No incluir claves API, contraseñas ni secretos en el repositorio.
6. No incurrir en gastos ni activar servicios de pago sin autorización explícita.

## Estructura

- `docs/`: arquitectura y protocolos.
- `tasks/inbox/`: tareas pendientes de asignación.
- `tasks/results/`: entregas de agentes.
- `tasks/reviews/`: auditorías independientes.
- `agents/`: perfiles y responsabilidades.
- `logs/`: registros verificables de eventos y pruebas.
- `engine/`: motor de coordinación y validación.
- `tests/`: pruebas unitarias e integrales.

## Flujo interno implementado

Creación → cola → paquete de despacho preparado → registro de envío/recepción → ejecución declarada → entrega estructurada → revisión independiente → aceptación/rechazo.

**Importante:** el paquete de despacho se prepara, pero el motor todavía no envía mensajes a un agente externo. Los estados de envío, recepción y ejecución requieren evidencia externa válida.

## Pruebas

```bash
python -m unittest discover -s tests -v
python -m engine.coordinator
```

La suite cubre estructura, unicidad, transiciones, evidencia, cola, entregas, revisión independiente y ciclo integral. La aprobación de pruebas de software no certifica por sí sola la validez científica de los resultados entregados por agentes.
