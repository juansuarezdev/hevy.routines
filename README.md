# hevy.routines

Script para crear rutinas de entrenamiento en [Hevy](https://hevy.com) mediante su API REST.

## Stack

- **Python 3.11+** con `httpx`, `pydantic` v2, `python-dotenv`, `PyYAML`
- Sin SDK: la API es REST con autenticación por header `api-key`

| Paquete        | Uso                                      |
| -------------- | ---------------------------------------- |
| `httpx`        | Cliente HTTP                             |
| `pydantic` v2  | Modelar y validar rutinas antes de enviar |
| `python-dotenv`| API key desde `.env`                     |
| `PyYAML`       | Definir rutinas en YAML                  |

## API key

Necesitas **Hevy Pro**. La clave se genera en [Ajustes → Developer](https://hevy.com/settings?developer).

En `.env`:

```env
HEVY_API_KEY=sk_live_...
```

## Estructura del proyecto

```
hevy-routines/
├── .env
├── routines/
│   ├── push_day.yaml
│   ├── pull_day.yaml
│   └── leg_day.yaml
├── hevy_client.py
├── models.py
├── create_routines.py
└── requirements.txt
```

## API (resumen)

- **Base:** `https://api.hevyapp.com/v1`
- **Auth:** en cada request, header `api-key: {HEVY_API_KEY}`

| Método | Endpoint               | Descripción              |
| ------ | ---------------------- | ------------------------ |
| `GET`  | `/exercise_templates`  | Ejercicios e IDs reales  |
| `POST` | `/routines`            | Crear rutina             |
| `GET`  | `/routines`            | Listar rutinas           |

Documentación: [api.hevyapp.com/docs](https://api.hevyapp.com/docs/)

## Flujo del script

1. Cargar rutinas desde YAML en `routines/`.
2. `GET /exercise_templates` (paginado) para mapear **nombre → `exercise_template_id`**.
3. Resolver los nombres del YAML a los IDs de Hevy (paso crítico).
4. `POST /routines` por cada rutina.
5. Mostrar un resumen de resultados.

Las rutinas en YAML usan nombres de ejercicio legibles; el script debe resolverlos a los IDs internos de Hevy antes de enviar el payload.

## Más detalle

La guía con stack, ejemplo de YAML, `requirements.txt` y prompt para Cursor está en [`hevy-api-script-guide.md`](hevy-api-script-guide.md).

## Referencias

- [Documentación API Hevy](https://api.hevyapp.com/docs/)
- [API key (Hevy Pro)](https://hevy.com/settings?developer)
