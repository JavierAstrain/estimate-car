import streamlit as st
import google.generativeai as genai
import pandas as pd
import time
from PIL import Image

# --- Configuración de la Página Streamlit ---
st.set_page_config(
    page_title="Estimador de Valor de Vehículos - Gemini IA",
    page_icon="🚗",
    layout="centered"
)

st.title("🚗 Estimador de Valor de Vehículos con IA de Gemini")
st.markdown("""
    Sube una foto de tu vehículo. La IA de Gemini analizará la imagen
    para identificar la marca y modelo, y luego te pedirá más detalles
    para una estimación de su valor de mercado y valor de toma.
""")

st.write("---")

# --- Configuración de la API de Gemini ---
# IMPORTANTE: Reemplaza "TU_API_KEY_DE_GEMINI" con tu clave real.
# st.secrets es una forma segura de guardar tus claves en Streamlit Cloud.
# Para desarrollo local, puedes ponerla directamente o en una variable de entorno.
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except KeyError:
    st.error("Error: API Key de Gemini no encontrada. Por favor, configura st.secrets['GEMINI_API_KEY'] o define tu clave directamente.")
    st.stop() # Detiene la ejecución si no hay API Key

# Inicializa el modelo de Gemini para visión (ej. gemini-pro-vision o gemini-1.5-pro)
# Asegúrate de usar un modelo que soporte entrada de imagen.
model = genai.GenerativeModel('gemini-1.5-pro') # O 'gemini-pro-vision' si 1.5-pro no está disponible o es overkill


# --- Funciones de Asistencia con Gemini ---

@st.cache_data
def analyze_image_with_gemini(image_bytes):
    """
    Usa Gemini para analizar una imagen de vehículo y extraer información.
    """
    # Convertir bytes a un formato que Gemini pueda procesar (ej. bytes de imagen)
    # Gemini 1.5 Pro acepta objetos PIL Image directamente, o puedes usar bytes.
    img = Image.open(image_bytes)

    # Puedes darle un prompt más específico para guiar la respuesta de Gemini
    prompt = """
    Analiza esta imagen de un vehículo.
    Identifica la marca y el modelo. Si puedes inferir un año aproximado o tipo de carrocería (ej. Sedan, SUV), menciónalo.
    Proporciona la información de forma concisa.
    Ejemplo de salida deseada:
    Marca: Toyota
    Modelo: Corolla
    Tipo/Año: Sedan, posible 2020-2023
    """
    try:
        response = model.generate_content([prompt, img])
        return response.text
    except Exception as e:
        st.error(f"Error al conectar con Gemini para análisis de imagen: {e}")
        return "No se pudo analizar la imagen con Gemini."

# --- SIMULACIÓN DE MODELO DE REGRESIÓN DE PRECIOS ---
# ESTO NECESITARÍA SER UN MODELO REAL ENTRENADO CON TUS DATOS DE MERCADO CHILENO
# NO ES ALGO QUE GEMINI PUEDA HACER DIRECTAMENTE CON PRECISION NUMERICA.
def estimate_value(marca, modelo, ano, kilometraje, version):
    """
    Simula la estimación del valor de mercado y toma.
    En un proyecto real, cargarías un modelo de ML entrenado (ej., un modelo Scikit-learn, XGBoost)
    y lo usarías para predecir los valores.
    """
    # Valores base (ej. CLP)
    base_market_value = 8_000_000
    base_trade_in_value = 6_000_000

    # Ajustes simulados (deberían basarse en tu modelo real)
    # Estos ajustes son solo para la demo
    year_factor = (pd.to_datetime('today').year - ano) * 500_000
    km_factor = (kilometraje / 10_000) * 100_000 # Cada 10k km resta 100k

    # Ajustes por marca/modelo/versión (muy simplificado, debería venir del modelo real)
    if "Toyota" in marca and "Corolla" in modelo:
        market_adjustment = 1_000_000
    elif "Hyundai" in marca and "Elantra" in modelo:
        market_adjustment = 500_000
    else:
        market_adjustment = 0

    if "Full Equipo" in version:
        version_adjustment = 800_000
    else:
        version_adjustment = 0

    estimated_market_value = base_market_value - year_factor - km_factor + market_adjustment + version_adjustment
    estimated_trade_in_value = (estimated_market_value * 0.8) - 200_000 # Un 80% del mercado menos un poco más

    # Asegurarse de que los valores no sean negativos
    estimated_market_value = max(1_000_000, estimated_market_value)
    estimated_trade_in_value = max(500_000, estimated_trade_in_value)

    return int(estimated_market_value), int(estimated_trade_in_value)


# --- Flujo de la Aplicación Streamlit ---

st.subheader("Paso 1: Sube una foto de tu vehículo")
uploaded_file = st.file_uploader("Elige una imagen de tu auto...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    st.image(uploaded_file, caption='Imagen Subida.', use_column_width=True)

    # Convertir la imagen a bytes para pasar a Gemini (aunque PIL Image también funciona con 1.5 Pro)
    img_bytes = uploaded_file.getvalue()

    with st.spinner("¡Gemini está analizando tu imagen! Esto puede tomar unos segundos..."):
        gemini_analysis_text = analyze_image_with_gemini(img_bytes)

    st.write("---")
    st.subheader("Análisis de Gemini:")
    st.info(gemini_analysis_text) # Muestra la respuesta directa de Gemini

    # Intentar parsear la respuesta de Gemini para extraer marca y modelo
    # Esto es un ejemplo y puede necesitar mejoras según el formato de salida de Gemini
    marca_gemini = "Desconocida"
    modelo_gemini = "Desconocido"
    lines = gemini_analysis_text.split('\n')
    for line in lines:
        if "Marca:" in line:
            marca_gemini = line.split("Marca:")[1].strip()
        if "Modelo:" in line:
            modelo_gemini = line.split("Modelo:")[1].strip()

    st.write("---")
    st.subheader("Paso 2: Confirma y Añade Más Detalles")

    st.write(f"Según Gemini, el vehículo es un **{marca_gemini} {modelo_gemini}**.")
    confirm_auto = st.checkbox("¿Es correcta la identificación?", value=True)

    if not confirm_auto:
        st.warning("Por favor, corrige la marca y modelo si es necesario.")
        marca_final = st.text_input("Marca Correcta", value=marca_gemini)
        modelo_final = st.text_input("Modelo Correcto", value=modelo_gemini)
    else:
        marca_final = marca_gemini
        modelo_final = modelo_gemini

    col1, col2 = st.columns(2)
    with col1:
        ano = st.number_input("Año del Vehículo", min_value=1990, max_value=pd.to_datetime('today').year + 1, value=2020)
    with col2:
        kilometraje = st.number_input("Kilometraje (km)", min_value=0, value=50000, step=1000)

    # Aquí podrías usar Gemini para sugerir versiones específicas si tuvieras una forma de consultarlo
    # o si Gemini puede inferir de la imagen un tipo de versión.
    # Por ahora, un selectbox manual es más robusto para versiones específicas.
    versiones_comunes = ["Básico", "Estándar", "Full Equipo", "Sport", "Limited", "Luxury"]
    version_especifica = st.selectbox("Versión Específica (ej. Full Equipo, Sport)", versiones_comunes)

    st.write("---")
    st.subheader("Paso 3: Obtén tu Estimación")

    if st.button("Estimar Valor del Vehículo"):
        if marca_final and modelo_final and ano and kilometraje is not None and version_especifica:
            with st.spinner("Calculando valores de mercado y toma..."):
                valor_mercado, valor_toma = estimate_value(marca_final, modelo_final, ano, kilometraje, version_especifica)

            st.success("¡Estimación completada!")

            col_res1, col_res2 = st.columns(2)
            with col_res1:
                st.metric(
                    label="**Valor de Mercado Estimado**",
                    value=f"${valor_mercado:,.0f} CLP",
                    delta="Referencial"
                )
            with col_res2:
                st.metric(
                    label="**Valor de Toma para Concesionaria**",
                    value=f"${valor_toma:,.0f} CLP",
                    delta="Referencial"
                )

            st.markdown("""
                ### Detalles de la Estimación (Generados con Gemini)
                ---
            """)
            # --- Generar texto explicativo con Gemini ---
            # Ahora que tenemos los números, podemos pedirle a Gemini que genere un texto "profesional".
            prompt_explicacion = f"""
            Genera una explicación concisa y profesional para un cliente de una concesionaria sobre la estimación de valor de un vehículo.
            El vehículo es un {ano} {marca_final} {modelo_final}, versión {version_especifica}, con {kilometraje} km.
            El valor de mercado estimado es de ${valor_mercado:,.0f} CLP.
            El valor de toma para la concesionaria es de ${valor_toma:,.0f} CLP.
            Incluye una nota importante sobre la naturaleza referencial de estos valores y la necesidad de una revisión física final.
            """
            with st.spinner("Preparando el reporte detallado con Gemini..."):
                try:
                    explanation_response = model.generate_content(prompt_explicacion)
                    st.write(explanation_response.text)
                except Exception as e:
                    st.error(f"Error al generar explicación con Gemini: {e}")
                    st.write("No se pudo generar una explicación detallada en este momento.")


        else:
            st.error("Por favor, asegúrate de haber subido una imagen y completado todos los detalles del vehículo.")

st.write("---")
st.markdown("Herramienta desarrollada para optimizar el proceso de compra-venta de autos.")