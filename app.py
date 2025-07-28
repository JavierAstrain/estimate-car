import streamlit as st
import google.generativeai as genai
import pandas as pd
import time
# Ya no necesitamos PIL ni io si no vamos a subir imágenes
# from PIL import Image
# import io

# --- Configuración de la Página Streamlit ---
st.set_page_config(
    page_title="Estimador de Valor de Vehículos - Manual",
    page_icon="📝", # Cambiamos el ícono para reflejar que es manual
    layout="centered"
)

st.title("📝 Estimador de Valor de Vehículos")
st.markdown("""
    Ingresa los detalles de tu vehículo para obtener una estimación
    de su valor de mercado y valor de toma para concesionarias.
""")

st.write("---")

# --- Configuración de la API de Gemini (solo para la explicación final) ---
try:
    gemini_api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=gemini_api_key)
except KeyError:
    st.error("""
        Error: La API Key de Gemini no ha sido configurada.
        Por favor, crea un un archivo `.streamlit/secrets.toml` en la raíz de tu proyecto
        y añade tu clave de la siguiente manera:

        ```toml
        GEMINI_API_KEY="tu_clave_aqui"
        ```
        Para más detalles, consulta la documentación de Streamlit sobre secretos.
    """)
    st.stop()

# Inicializa el modelo de Gemini (ya no necesitamos el modelo de visión, solo texto)
# Puedes usar 'gemini-pro' para texto, o 'gemini-1.5-pro' si prefieres.
model = genai.GenerativeModel('gemini-pro')


# --- SIMULACIÓN DE MODELO DE REGRESIÓN DE PRECIOS ---
# ESTO NECESITARÍA SER UN MODELO REAL ENTRENADO CON TUS DATOS DE MERCADO CHILENO
# DEBERÍAS REEMPLAZAR ESTA FUNCIÓN CON LA CARGA Y USO DE TU MODELO ENTRENADO REAL.
def estimate_value(marca, modelo, ano, kilometraje, version):
    """
    Simula la estimación del valor de mercado y toma.
    En un proyecto real, cargarías un modelo de ML entrenado (ej., un modelo Scikit-learn, XGBoost)
    y lo usarías para predecir los valores.
    """
    current_year = pd.to_datetime('today').year
    base_market_value = 8_000_000 # Un valor base en pesos chilenos

    year_factor = (current_year - ano) * 500_000
    if year_factor < 0:
        year_factor = 0

    km_factor = (kilometraje / 10_000) * 100_000

    market_adjustment = 0
    if "Toyota" in marca and "Corolla" in modelo:
        market_adjustment = 1_000_000
    elif "Hyundai" in marca and "Elantra" in modelo:
        market_adjustment = 500_000
    elif "Chevrolet" in marca:
        market_adjustment = -200_000

    version_adjustment = 0
    if "Full Equipo" in version:
        version_adjustment = 800_000
    elif "Sport" in version:
        version_adjustment = 1_200_000
    elif "Limited" in version or "Luxury" in version:
        version_adjustment = 1_500_000

    estimated_market_value = base_market_value - year_factor - km_factor + market_adjustment + version_adjustment
    estimated_market_value = max(1_000_000, estimated_market_value)

    estimated_trade_in_value = (estimated_market_value * 0.80) - 200_000
    estimated_trade_in_value = max(500_000, estimated_trade_in_value)

    return int(estimated_market_value), int(estimated_trade_in_value)


# --- Flujo de la Aplicación Streamlit (Solo entrada de datos) ---

st.subheader("Paso 1: Ingresa los detalles de tu vehículo")

# Campos de entrada de texto para Marca y Modelo
marca_final = st.text_input("Marca del Vehículo", placeholder="Ej: Toyota")
modelo_final = st.text_input("Modelo del Vehículo", placeholder="Ej: Corolla")

col1, col2 = st.columns(2)
with col1:
    current_year = pd.to_datetime('today').year
    ano = st.number_input("Año del Vehículo", min_value=1990, max_value=current_year + 1, value=current_year)
with col2:
    kilometraje = st.number_input("Kilometraje (km)", min_value=0, value=50000, step=1000)

versiones_comunes = ["Básico", "Estándar", "Full Equipo", "Sport", "Limited", "Luxury", "Otra"]
version_especifica = st.selectbox("Versión Específica (ej. Full Equipo, Sport)", versiones_comunes)
if version_especifica == "Otra":
    version_especifica = st.text_input("Ingresa la versión específica:")

st.write("---")
st.subheader("Paso 2: Obtén tu Estimación")

if st.button("Estimar Valor del Vehículo"):
    # Validar que los campos de texto no estén vacíos y los numéricos tengan valor
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
        # Generar texto explicativo con Gemini
        prompt_explicacion = f"""
        Genera una explicación concisa y profesional para un cliente de una concesionaria sobre la estimación de valor de un vehículo.
        El vehículo es un {ano} {marca_final} {modelo_final}, versión {version_especifica}, con {kilometraje} km.
        El valor de mercado estimado es de ${valor_mercado:,.0f} CLP.
        El valor de toma para la concesionaria es de ${valor_toma:,.0f} CLP.
        Incluye una nota importante sobre la naturaleza **referencial y estimativa** de estos valores.
        Menciona claramente que el valor final siempre requerirá una **revisión física exhaustiva** del vehículo
        (estado de carrocería, motor, neumáticos, interiores, accesorios),
        y que las **condiciones actuales del mercado** de vehículos usados en Chile también pueden influir.
        El tono debe ser informativo y transparente.
        """
        with st.spinner("Preparando el reporte detallado con Gemini..."):
            try:
                explanation_response = model.generate_content(prompt_explicacion)
                st.write(explanation_response.text)
            except Exception as e:
                st.error(f"Error al generar explicación con Gemini: {e}")
                st.write("No se pudo generar una explicación detallada en este momento.")


    else:
        st.error("Por favor, completa todos los detalles del vehículo para obtener una estimación.")

st.write("---")
st.markdown("Herramienta desarrollada para optimizar el proceso de compra-venta de autos en pequeñas concesionarias.")
st.markdown("---")
st.caption("Aviso: Esta aplicación utiliza IA para proveer estimaciones. Los valores son referenciales y no constituyen una tasación oficial.")
