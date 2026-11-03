# Luix° Lab Autónomo v1

Laboratorio reproducible, local y sin dependencias externas. Su alcance se limita deliberadamente a operaciones que pueden ejecutarse y verificarse con Python estándar.

## Qué hace
- Importa CSV locales sin modificar el original.
- Calcula SHA-256 del archivo de entrada.
- Valida encabezados, filas, valores numéricos y ausencias.
- Produce un perfil descriptivo reproducible en JSON.
- Conserva explícitamente valores ausentes; nunca los convierte en cero.
- Genera un informe con límites y advertencias.
- Ejecuta pruebas automáticas sin red, API, agente externo ni plataforma de notebooks.

## Qué no pretende hacer
- No envía tareas a otros agentes.
- No sincroniza plataformas.
- No descarga datos de Internet.
- No afirma causalidad ni descubrimientos científicos.
- No sustituye una revisión científica independiente.

## Requisitos
Python 3.10 o superior. Solo biblioteca estándar.

## Ejecutar
Desde la raíz del repositorio:

```bash
python laboratorio-autonomo/run_lab.py laboratorio-autonomo/examples/sample.csv --output laboratorio-autonomo/output
python -m unittest discover -s laboratorio-autonomo/tests -v
```

## Salidas
- `profile.json`: hash, dimensiones, encabezados, conteos de ausencias y estadísticas descriptivas.
- `report.md`: resumen legible, método y limitaciones.

## Criterio de finalización v1
El laboratorio v1 se considera completo cuando:
1. La suite de pruebas pasa íntegramente.
2. El ejemplo produce salidas válidas.
3. El hash del original se calcula sin alterar el archivo.
4. Los datos ausentes se mantienen como ausentes.
5. Las salidas identifican el archivo y el método usados.

La finalización se refiere a este alcance cerrado, no a capacidades externas que deliberadamente no forman parte del diseño.
