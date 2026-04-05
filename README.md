# BC5 — Spotify Analytics Assistant

##Objetivo

El objetivo de este proyecto es analizar el historial de reproducción de Spotify de forma interactiva, permitiendo al usuario hacer preguntas en lenguaje natural y obtener visualizaciones claras sobre sus hábitos de escucha.

Pasos realizados

Primero, se carga y limpia el dataset exportado de Spotify, eliminando datos irrelevantes como podcasts y corrigiendo formatos de fecha.
Después, se crean nuevas columnas (como mes, hora o tipo de día) para facilitar el análisis.
Se construye una aplicación web con Streamlit donde el usuario puede escribir preguntas.
Un modelo de lenguaje interpreta la pregunta y genera automáticamente el código necesario para crear un gráfico.
Ese código se ejecuta en tiempo real y muestra el resultado junto con una explicación.

Conclusión

La solución permite explorar datos personales de Spotify de forma sencilla, sin necesidad de conocimientos técnicos.
El usuario puede descubrir patrones de escucha, artistas favoritos o hábitos temporales de manera intuitiva y visual, convirtiendo datos complejos en información útil.


Business Case 5 del programa MDA13 de la escuela de negocios ISDI.

Este repositorio es un ejercicio docente. Los datos son sintéticos y no corresponden a ningún usuario real de Spotify. La estructura del dataset está inspirada en el formato de exportación de datos de Spotify, pero ha sido generada específicamente para este caso.

Ante cualquier duda: mtaboada@isdi.education

## Puesta en marcha

1. Clona el repositorio o descarga los archivos
2. Crea un entorno virtual y actívalo
3. Instala dependencias: `pip install -r requirements.txt`
4. Copia `.streamlit/secrets.toml.example` como `.streamlit/secrets.toml` y rellena la API key y tu contraseña
5. Ejecuta: `streamlit run app.py`

## Archivos

| Archivo | Descripción |
|---|---|
| `app.py` | Esqueleto de la aplicación. Tu trabajo está aquí. |
| `streaming_history.json` | Dataset del caso (~15.000 registros) |
| `requirements.txt` | Dependencias fijadas. No modificar. |
| `.gitignore` | Excluye secrets del repositorio |
| `.streamlit/secrets.toml.example` | Plantilla para API key y contraseña. Copiar como `secrets.toml`. |

