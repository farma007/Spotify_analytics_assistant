    # ============================================================
    # CABECERA
    # ============================================================
    # Alumno: Juan Becedas
    # URL Streamlit Cloud: https://...streamlit.app
    # URL GitHub: https:/https://github.com/jbecedasisdi/Spotify_analytics_assistant

    # ============================================================
    # IMPORTS
    # ============================================================
    # Streamlit: framework para crear la interfaz web
    # pandas: manipulación de datos tabulares
    # plotly: generación de gráficos interactivos
    # openai: cliente para comunicarse con la API de OpenAI
    # json: para parsear la respuesta del LLM (que llega como texto JSON)
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from openai import OpenAI
import json

    # ============================================================
    # CONSTANTES
    # ============================================================
    # Modelo de OpenAI. No lo cambies.
MODEL = "gpt-4.1-mini"

    # -------------------------------------------------------
    # >>> SYSTEM PROMPT — TU TRABAJO PRINCIPAL ESTÁ AQUÍ <<<
    # -------------------------------------------------------
    # El system prompt es el conjunto de instrucciones que recibe el LLM
    # ANTES de la pregunta del usuario. Define cómo se comporta el modelo:
    # qué sabe, qué formato debe usar, y qué hacer con preguntas inesperadas.
    #
    # Puedes usar estos placeholders entre llaves — se rellenan automáticamente
    # con información real del dataset cuando la app arranca:
    #   {fecha_min}             → primera fecha del dataset
    #   {fecha_max}             → última fecha del dataset
    #   {plataformas}           → lista de plataformas (Android, iOS, etc.)
    #   {reason_start_values}   → valores posibles de reason_start
    #   {reason_end_values}     → valores posibles de reason_end
    #
    # IMPORTANTE: como el prompt usa llaves para los placeholders,
    # si necesitas escribir llaves literales en el texto (por ejemplo para
    # mostrar un JSON de ejemplo), usa doble llave: {{ y }}
    #
SYSTEM_PROMPT = """
    Eres un analista de datos experto en Spotify. Tu trabajo es responder preguntas del usuario generando código Python que use pandas y plotly para analizar un DataFrame llamado `df`.

    ========================
    📊 DATASET DISPONIBLE
    ========================
    El DataFrame `df` contiene datos de escucha de Spotify con estas columnas:

    - ts: timestamp (datetime)
    - anio: año
    - mes: mes (nombre)
    - mes: mes en español (Enero, Febrero, etc.)
    - mes_num: número del mes (1-12, usado para ordenar cronológicamente)
    - estacion: estación del año (invierno, primavera, verano, otoño)
    - dia_semana: día de la semana
    - hora: hora del día (0-23)
    - cancion: nombre de la canción
    - artista: artista principal
    - album: álbum
    - track_id: identificador único
    - segundos_played: duración reproducida en segundos
    - inicio: motivo de inicio ({reason_start_values})
    - fin: motivo de fin ({reason_end_values})
    - aleatorio: booleano (shuffle activado)
    - saltada: booleano (si se saltó la canción)
    - plataforma: dispositivo ({plataformas})
    - estacion: estación del año (verano, invierno)
    - tipo_dia: tipo de día (entre semana, fin de semana)
    - semestre: primer semestre o segundo semestre


    Rango temporal del dataset:
    - Desde: {fecha_min}
    - Hasta: {fecha_max}

    ========================
    🎯 OBJETIVO
    ========================
    Responder preguntas del usuario generando un JSON con este formato EXACTO:

    {{
    "tipo": "grafico",
    "codigo": "CODIGO PYTHON",
    "interpretacion": "Explicación clara del resultado"
    }}

    O si la pregunta está fuera de alcance:

    {{
    "tipo": "fuera_de_alcance",
    "codigo": "",
    "interpretacion": "Explica por qué no puedes responder"
    }}

    ========================
    📈 REGLAS PARA EL CÓDIGO
    ========================
    - Usa SIEMPRE el DataFrame `df`
    - Usa pandas para transformar datos
    - Usa plotly.express (px) o plotly.graph_objects (go)
    - El resultado debe guardarse en una variable llamada `fig`
    - NO uses print()
    - NO generes texto fuera del JSON
    - NO inventes columnas que no existen
    - El código debe ser limpio, funcional y reproducible
    - Para evolución temporal por mes, SIEMPRE ordenar por `mes_num`, no por el nombre del mes
    - Nunca ordenar meses alfabéticamente

    ========================
    📊 VISUALIZACIÓN
    ========================

    - Comparaciones → usar gráficos de barras (px.bar)
    - Rankings → barras ordenadas descendente
    - Evolución → líneas (px.line)

    Cuando compares categorías (ej: verano vs invierno), usa colores diferentes.




    ========================
    📊 TIPOS DE PREGUNTAS (ejemplos)
    ========================

    - Top artistas o canciones → usar groupby sobre `artista` o `cancion`
    - Evolución temporal → Agrupar por `mes`, `anio`, `dia_semana`
    - Comparaciones → Usar columnas derivadas como `estacion`, `tipo_dia`, `semestre`

    Ejemplos de preguntas válidas que el LLM debe poder atender:
    - "Top 5 artistas"
    - "Evolución de reproducciones por mes"
    - "Verano vs invierno: ¿qué artista escucho más?"
    - "Top 5 artistas en verano vs invierno"
    - "¿Escucho más entre semana o fin de semana?"
    - "Compara artistas de verano y de invierno"

    IMPORTANTE:
    - Para comparar verano vs invierno → usar columna `estacion`
    - Para comparar entre semana vs fin de semana → usar columna `tipo_dia`
    - Para rankings → ordenar por número de reproducciones o segundos_played


    NOTA: si añades columnas nuevas en `load_data()` actualiza `build_prompt()` y `SYSTEM_PROMPT` para que el LLM conozca sus valores posibles.
    """


    # ============================================================
    # CARGA Y PREPARACIÓN DE DATOS
    # ============================================================
    # Esta función se ejecuta UNA SOLA VEZ gracias a @st.cache_data.
    # Lee el fichero JSON y prepara el DataFrame para que el código
    # que genere el LLM sea lo más simple posible.

@st.cache_data
def load_data():
        df = pd.read_json("streaming_history.json")

        df["ts"] = pd.to_datetime(df["ts"], errors="coerce", utc=True)
    # eliminar filas donde ts no se pudo convertir
        df = df.dropna(subset=["ts"])
        df.loc[:, "hora"] = df["ts"].dt.hour
        df.loc[:, "dia_semana"] = df["ts"].dt.day_name()
        # Mes numérico (para ordenar correctamente)
        df.loc[:, "mes_num"] = df["ts"].dt.month

    # Mes en español (para mostrar)
        meses_es = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
        }
        df.loc[:, "mes"] = df["mes_num"].map(meses_es)
    # 🔥 AQUÍ VA ESTACION
        df.loc[:, "estacion"] = df["mes"].map({
        "Diciembre": "invierno", "Enero": "invierno", "Febrero": "invierno",
        "Marzo": "primavera", "Abril": "primavera", "Mayo": "primavera",
        "Junio": "verano", "Julio": "verano", "Agosto": "verano",
        "Septiembre": "otoño", "Octubre": "otoño", "Noviembre": "otoño"
        })



        df.loc[:, "anio"] = df["ts"].dt.year

        df.loc[:, "segundos_played"] = df["ms_played"] / 1000

        df = df.rename(columns={
            "master_metadata_track_name": "cancion",
            "master_metadata_album_artist_name": "artista",
            "master_metadata_album_album_name": "album",
            "spotify_track_uri": "track_id",
            "reason_start": "inicio",
            "reason_end": "fin",
            "shuffle": "aleatorio",
            "skipped": "saltada",
            "platform": "plataforma"
        })

        df = df[~df["album"].str.contains("Podcast", case=False, na=False)]

        # NUEVAS COLUMNAS CLAVE 🔥
        
        # Tipo de día
        df.loc[:, "tipo_dia"] = df["dia_semana"].apply(
            lambda x: "fin de semana" if x in ["Saturday", "Sunday"] else "entre semana"
        )

        # Semestre
        df.loc[:, "semestre"] = df["ts"].dt.month.apply(
            lambda x: "primer semestre" if x <= 6 else "segundo semestre"
        )

        return df


def build_prompt(df):
        """
        Inyecta información dinámica del dataset en el system prompt.
        Los valores que calcules aquí reemplazan a los placeholders
        {fecha_min}, {fecha_max}, etc. dentro de SYSTEM_PROMPT.
        """
        fecha_min = df["ts"].min() if "ts" in df.columns else ""
        fecha_max = df["ts"].max() if "ts" in df.columns else ""
        plataformas = df["plataforma"].unique().tolist() if "plataforma" in df.columns else []
        reason_start_values = df["inicio"].unique().tolist() if "inicio" in df.columns else []
        reason_end_values = df["fin"].unique().tolist() if "fin" in df.columns else []

        return SYSTEM_PROMPT.format(
            fecha_min=fecha_min,
            fecha_max=fecha_max,
            plataformas=plataformas,
            reason_start_values=reason_start_values,
            reason_end_values=reason_end_values,
        )


    # ============================================================
    # FUNCIÓN DE LLAMADA A LA API
    # ============================================================
    # Esta función envía DOS mensajes a la API de OpenAI:
    # 1. El system prompt (instrucciones generales para el LLM)
    # 2. La pregunta del usuario
    #
    # El LLM devuelve texto (que debería ser un JSON válido).
    # temperature=0.2 hace que las respuestas sean más predecibles.
    #
    # No modifiques esta función.
    #
def get_response(user_msg, system_prompt):
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content


    # ============================================================
    # PARSING DE LA RESPUESTA
    # ============================================================
    # El LLM devuelve un string que debería ser un JSON con esta forma:
    #
    #   {"tipo": "grafico",          "codigo": "...", "interpretacion": "..."}
    #   {"tipo": "fuera_de_alcance", "codigo": "",    "interpretacion": "..."}
    #
    # Esta función convierte ese string en un diccionario de Python.
    # Si el LLM envuelve el JSON en backticks de markdown (```json...```),
    # los limpia antes de parsear.
    #
    # No modifiques esta función.
    #
def parse_response(raw):
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

        return json.loads(cleaned)


    # ============================================================
    # EJECUCIÓN DEL CÓDIGO GENERADO
    # ============================================================
    # El LLM genera código Python como texto. Esta función lo ejecuta
    # usando exec() y busca la variable `fig` que el código debe crear.
    # `fig` debe ser una figura de Plotly (px o go).
    #
    # El código generado tiene acceso a: df, pd, px, go.
    #
    # No modifiques esta función.
    #
def execute_chart(code, df):
        local_vars = {"df": df, "pd": pd, "px": px, "go": go}
        exec(code, {}, local_vars)
        return local_vars.get("fig")


    # ============================================================
    # INTERFAZ STREAMLIT
    # ============================================================
    # Toda la interfaz de usuario. No modifiques esta sección.
    #

    # Configuración de la página
st.set_page_config(page_title="Spotify Analytics", layout="wide")

    # --- Control de acceso ---
    # Lee la contraseña de secrets.toml. Si no coincide, no muestra la app.
if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

if not st.session_state.authenticated:
        st.title("🔒 Acceso restringido")
        pwd = st.text_input("Contraseña:", type="password")
        if pwd:
            if pwd == st.secrets["PASSWORD"]:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta.")
        st.stop()

    # --- App principal ---
st.title("🎵 Spotify Analytics Assistant")
st.caption("Pregunta lo que quieras sobre tus hábitos de escucha")

    # Cargar datos y construir el prompt con información del dataset
df = load_data()
system_prompt = build_prompt(df)

    # Caja de texto para la pregunta del usuario
if prompt := st.chat_input("Ej: ¿Cuál es mi artista más escuchado?"):

        # Mostrar la pregunta en la interfaz
        with st.chat_message("user"):
            st.write(prompt)

        # Generar y mostrar la respuesta
        with st.chat_message("assistant"):
            with st.spinner("Analizando..."):
                try:
                    # 1. Enviar pregunta al LLM
                    raw = get_response(prompt, system_prompt)

                    # 2. Parsear la respuesta JSON
                    parsed = parse_response(raw)

                    if parsed["tipo"] == "fuera_de_alcance":
                        # Pregunta fuera de alcance: mostrar solo texto
                        st.write(parsed["interpretacion"])
                    else:
                        # Pregunta válida: ejecutar código y mostrar gráfico
                        fig = execute_chart(parsed["codigo"], df)
                        if fig:
                            st.plotly_chart(fig, use_container_width=True)
                            st.write(parsed["interpretacion"])
                            st.code(parsed["codigo"], language="python")
                        else:
                            st.warning("El código no produjo ninguna visualización. Intenta reformular la pregunta.")
                            st.code(parsed["codigo"], language="python")

                except json.JSONDecodeError:
                    st.error("No he podido interpretar la respuesta. Intenta reformular la pregunta.")
                except Exception as e:
                    st.error("Ha ocurrido un error al generar la visualización. Intenta reformular la pregunta.")


    # ============================================================
    # REFLEXIÓN TÉCNICA (máximo 30 líneas)
    # ============================================================
    #
    # Responde a estas tres preguntas con tus palabras. Sé concreto
    # y haz referencia a tu solución, no a generalidades.
    # No superes las 30 líneas en total entre las tres respuestas.
    #
    # 1. ARQUITECTURA TEXT-TO-CODE
    #    ¿Cómo funciona la arquitectura de tu aplicación? ¿Qué recibe
    #    el LLM? ¿Qué devuelve? ¿Dónde se ejecuta el código generado?
    #    ¿Por qué el LLM no recibe los datos directamente?
    #
    #    La app envía al LLM un system prompt con la estructura del dataset (df) y reglas de código.
    #    El LLM recibe la pregunta del usuario y devuelve un JSON con código Python (codigo) y una interpretación(interpretacion)
    #    El código se ejecuta localmente en Python usando exec() sobre el DataFrame df cargado, generando la variable fig.
    #.   No se envían los datos al LLM por privacidad y eficiencia: el modelo solo genera instrucciones, no necesita los datos brutos.
    #
    # 2. EL SYSTEM PROMPT COMO PIEZA CLAVE
    #    ¿Qué información le das al LLM y por qué? Pon un ejemplo
    #    concreto de una pregunta que funciona gracias a algo específico
    #    de tu prompt, y otro de una que falla o fallaría si quitases
    #    una instrucción.
    #
    #    El prompt informa al LLM de las columnas, tipos y reglas (pandas, plotly, fig, etc.)
    #    Por ejemplo, la pregunta “Evolución por mes” funciona porque le indicamos ordenar por mes_num para que los meses queden cronológicos.
    #    Si quitamos esa instrucción, el gráfico ordenaría meses alfabéticamente y no tendría sentido.
    #    Otra pregunta que fallaría sin el prompt: “Compara artistas de verano e invierno”, porque
    #    el LLM necesita saber que existe la columna estacion para hacer la comparación.
    #
    #
    # 3. EL FLUJO COMPLETO
    #    Describe paso a paso qué ocurre desde que el usuario escribe
    #    una pregunta hasta que ve el gráfico en pantalla.
    #
    #    El usuario escribe la pregunta en Streamlit.
    #    La app envía la pregunta y el system prompt al LLM.
    #    La app interpreta y convierte el JSON en un diccionario de Python usando parse_response().
    #    Si es un gráfico, execute_chart() ejecuta el código sobre df y crea fig.
    #    Streamlit muestra fig con st.plotly_chart() y la interpretación, junto con el código generado para transparencia.
