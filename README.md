# Luix° AI Network

Infraestructura experimental para coordinar tareas de investigación asistida por IA con trazabilidad, revisión independiente y control de permisos.

## Estado actual

- GitHub conectado con acceso de lectura/escritura verificado.
- Proyecto Deepnote `Luix° AI Network` existente.
- Arquitectura v1 documentada en Deepnote.
- Protocolo de tareas en preparación.
- Comunicación autónoma entre agentes: **no verificada**.
- Integraciones de proyecto Deepnote: ninguna confirmada.

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

## Flujo previsto

Coordinación → tarea identificada → recepción confirmada → ejecución autorizada → entrega → auditoría → registro.

Este flujo es el diseño objetivo. Cada transición debe probarse antes de considerarse operativa.
