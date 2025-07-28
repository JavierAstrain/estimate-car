import streamlit as st
import google.generativeai as genai
import pandas as pd
import time
from PIL import Image
import io # Importamos el módulo 'io' para manejar los bytes de la imagen

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
# IMPORTANTE: st.secrets es la forma segura de acceder a tus claves.
# Para desarrollo local, asegúrate de que el archivo .streamlit/secrets.toml exista.
# Para Streamlit Cloud, el archivo debe estar en tu repositorio de GitHub.
try:
    # Intenta obtener la API Key de los secretos de Streamlit
    gemini_api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=gemini_api_key)
except KeyError:
    # Si la clave no se encuentra en secrets, muestra un error y detiene la aplicación.
    st.error("""
        Error: La API Key de Gemini no ha sido configurada.
        Por favor, crea un archivo `.streamlit/secrets.toml` en la raíz de tu proyecto
        y añade tu clave de la siguiente manera:

        ```toml
        GEMINI_API_KEY="tu_clave_aqui"
        ```
        Para más detalles, consulta la documentación de Streamlit sobre secretos.
    """)
    st.stop() # Detiene la ejecución de la aplicación si no hay API Key

# Inicializa el modelo de Gemini para visión (ej. gemini-pro-vision o gemini-1.5-pro)
# Asegúrate de usar un modelo que soporte entrada de imagen.
# Gemini 1.5 Pro es más potente para esto.
model = genai.GenerativeModel('gemini-1.5-pro')


# --- Funciones de Asistencia con Gemini ---

@st.cache_data # Mantén el caché para que el análisis de la imagen no se repita innecesariamente
def analyze_image_with_gemini(image_bytes_content):
    """
    Usa Gemini para analizar una imagen de vehículo y extraer información.
    """
    try:
        # Envuelve los bytes de la imagen en un objeto BytesIO
        # Esto permite que Image.open() lo trate como un archivo en memoria.
        img_file = io.BytesIO(image_bytes_content)
        img = Image.open(img_file)

        # Puedes darle un prompt más específico para guiar la respuesta de Gemini
        prompt = """
        Analiza esta imagen de un vehículo.
        Identifica la marca y el modelo. Si puedes inferir un año aproximado o tipo de carrocería (ej. Sedan, SUV, Camioneta), menciónalo.
        Proporciona la información de forma concisa.
        Ejemplo de salida deseada:
        Marca: Toyota
        Modelo: Corolla
        Tipo/Año: Sedan, posible 2020-2023
        """
        response = model.generate_content([prompt, img])
        return response.text
    except Exception as e:
        # Captura cualquier error durante el análisis de Gemini o la apertura de la imagen
        st.error(f"Error al conectar con Gemini para análisis de imagen o al procesar la imagen: {e}")
        return "No se pudo analizar la imagen con Gemini. Inténtalo de nuevo."

# --- SIMULACIÓN DE MODELO DE REGRESIÓN DE PRECIOS ---
# ESTO NECESITARÍA SER UN MODELO REAL ENTRENADO CON TUS DATOS DE MERCADO CHILENO
# NO ES ALGO QUE GEMINI PUEDA HACER DIRECTAMENTE CON PRECISION NUMERICA.
# DEBERÍAS REEMPLAZAR ESTA FUNCIÓN CON LA CARGA Y USO DE TU MODELO ENTRENADO REAL.
def estimate_value(marca, modelo, ano, kilometraje, version):
    """
    Simula la estimación del valor de mercado y toma.
    En un proyecto real, cargarías un modelo de ML entrenado (ej., un modelo Scikit-learn, XGBoost)
    y lo usarías para predecir los valores.
    """
    # Valores base (ej. en CLP)
    # Consideramos el año actual para los cálculos de depreciación.
    current_year = pd.to_datetime('today').year
    base_market_value = 8_000_000 # Un valor base en pesos chilenos

    # Ajustes simulados (deberían basarse en tu modelo real y datos chilenos)
    # Depreciación por año (ej. 500.000 CLP por año desde el actual)
    year_factor = (current_year - ano) * 500_000
    if year_factor < 0: # Para autos nuevos o futuros (si el año fuera mayor al actual)
        year_factor = 0

    # Depreciación por kilometraje (ej. 100.000 CLP cada 10.000 km)
    km_factor = (kilometraje / 10_000) * 100_000

    # Ajustes por marca/modelo (ejemplo simplificado)
    # Estas serían características importantes en tu modelo de ML real
    market_adjustment = 0
    if "Toyota" in marca and "Corolla" in modelo:
        market_adjustment = 1_000_000 # Más valor por popularidad/fiabilidad
    elif "Hyundai" in marca and "Elantra" in modelo:
        market_adjustment = 500_000
    elif "Chevrolet" in marca:
        market_adjustment = -200_000 # Ejemplo, si ciertas marcas tienen menor valor residual

    # Ajuste por versión (ejemplo simplificado)
    version_adjustment = 0
    if "Full Equipo" in version:
        version_adjustment = 800_000
    elif "Sport" in version:
        version_adjustment = 1_200_000
    elif "Limited" in version or "Luxury" in version:
        version_adjustment = 1_500_000

    # Cálculo del valor de mercado estimado
    estimated_market_value = base_market_value - year_factor - km_factor + market_adjustment + version_adjustment

    # Asegurarse de que el valor no sea negativo y tenga un mínimo lógico
    estimated_market_value = max(1_000_000, estimated_market_value)

    # Valor de toma para concesionaria (generalmente un porcentaje menor del valor de mercado)
    # Podría ser un modelo separado, pero aquí usamos un % y un ajuste adicional.
    estimated_trade_in_value = (estimated_market_value * 0.80) - 200_000 # 80% del mercado, con un pequeño descuento adicional
    estimated_trade_in_value = max(500_000, estimated_trade_in_value) # Mínimo para el valor de toma

    return int(estimated_market_value), int(estimated_trade_in_value)


# --- Flujo de la Aplicación Streamlit ---

st.subheader("Paso 1: Sube una foto de tu vehículo")
uploaded_file = st.file_uploader("Elige una imagen de tu auto...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    st.image(uploaded_file, caption='Imagen Subida.', use_column_width=True)

    # Convertir la imagen cargada a bytes para pasarla a Gemini
    # .getvalue() retorna los bytes de la imagen.
    img_bytes = uploaded_file.getvalue()

    with st.spinner("¡Gemini está analizando tu imagen! Esto puede tomar unos segundos..."):
        # Llamamos a la función que usa Gemini para analizar la imagen
        gemini_analysis_text = analyze_image_with_gemini(img_bytes)

    st.write("---")
    st.subheader("Análisis de Gemini:")
    st.info(gemini_analysis_text) # Muestra la respuesta directa de Gemini

    # Intentar parsear la respuesta de Gemini para extraer marca y modelo
    # Esto es un ejemplo y puede necesitar mejoras según el formato de salida de Gemini
    # Se busca "Marca:" y "Modelo:" en las líneas de la respuesta.
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

    # Campos para que el usuario ingrese detalles adicionales
    col1, col2 = st.columns(2)
    with col1:
        # El año máximo se ajusta al año actual + 1 para permitir autos nuevos/modelos futuros
        current_year = pd.to_datetime('today').year
        ano = st.number_input("Año del Vehículo", min_value=1990, max_value=current_year + 1, value=current_year)
    with col2:
        kilometraje = st.number_input("Kilometraje (km)", min_value=0, value=50000, step=1000)

    # Selectbox para la versión específica (esto es importante ya que la IA no lo puede inferir fácilmente)
    versiones_comunes = ["Básico", "Estándar", "Full Equipo", "Sport", "Limited", "Luxury", "Otra"]
    version_especifica = st.selectbox("Versión Específica (ej. Full Equipo, Sport)", versiones_comunes)
    if version_especifica == "Otra":
        version_especifica = st.text_input("Ingresa la versión específica:")


    st.write("---")
    st.subheader("Paso 3: Obtén tu Estimación")

    if st.button("Estimar Valor del Vehículo"):
        # Validar que todos los campos necesarios estén completos
        if marca_final and modelo_final and ano and kilometraje is not None and version_especifica:
            with st.spinner("Calculando valores de mercado y toma..."):
                # Llama a la función de estimación (actualmente simulada)
                valor_mercado, valor_toma = estimate_value(marca_final, modelo_final, ano, kilometraje, version_especifica)

            st.success("¡Estimación completada!")

            # Muestra los resultados de forma clara y formateada
            col_res1, col_res2 = st.columns(2)
            with col_res1:
                st.metric(
                    label="**Valor de Mercado Estimado**",
                    value=f"${valor_mercado:,.0f} CLP",
                    delta="Referencial" # Indica que es un valor de referencia
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
            # Aquí se le pide a Gemini que genere un texto profesional basado en los resultados numéricos.
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
            st.error("Por favor, asegúrate de haber subido una imagen y completado todos los detalles del vehículo.")

st.write("---")
st.markdown("Herramienta desarrollada para optimizar el proceso de compra-venta de autos en pequeñas concesionarias.")
st.markdown("---")
st.caption("Aviso: Esta aplicación utiliza IA para proveer estimaciones. Los valores son referenciales y no constituyen una tasación oficial.")
