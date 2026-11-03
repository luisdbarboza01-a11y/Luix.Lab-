# Motor de coordinación v1

## Alcance
Valida la estructura del registro, la unicidad de identificadores, el historial de eventos, las transiciones permitidas, la evidencia mínima y la coherencia entre el estado actual y la reproducción del historial.

## Ejecutar auditoría
Desde la raíz del repositorio:

```bash
python -m engine.coordinator
```

Con rutas explícitas:

```bash
python -m engine.coordinator --registry tasks/registry.json --events logs/events.jsonl
```

Códigos de salida:
- `0`: auditoría sin inconsistencias detectadas.
- `1`: inconsistencias de protocolo o trazabilidad.
- `2`: error de lectura o formato.

## Ejecutar pruebas
```bash
python -m unittest discover -s tests -v
```

## Limitaciones
Esta versión es un auditor/validador de registros. No despacha tareas, no se conecta a chats de agentes, no sincroniza plataformas y no demuestra que una persona o agente haya ejecutado acciones. Las referencias de evidencia deben revisarse; la mera existencia de un texto de referencia no certifica su contenido.
