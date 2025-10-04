# Updated: Fixed eco_friendly KeyError - v2.1
import streamlit as st
import requests
from PIL import Image
import io
import validators  # Para validar URLs

# Configuración de la página
st.set_page_config(page_title="Mommyshops - Analiza tus Productos", page_icon="🌿", layout="wide")

# Inicializar session_state para persistir resultados
if 'result' not in st.session_state:
    st.session_state.result = None
if 'error' not in st.session_state:
    st.session_state.error = None

# Título y descripción
st.title("🌿 Mommyshops - Analiza Productos Seguros y Eco-Friendly")
st.markdown("""
Sube una imagen de la etiqueta de un producto (JPEG/PNG, máximo 5MB) o ingresa la URL de la página del producto para analizar sus ingredientes.
Selecciona la necesidad de tu piel para obtener recomendaciones personalizadas.

**🆕 Nuevas capacidades:**
- 📸 **Reconocimiento de productos**: Ahora puedes subir fotos del producto completo, no solo la etiqueta
- 🏷️ **Identificación de marcas**: Detecta automáticamente la marca y nombre del producto
- 🔍 **Búsqueda inteligente**: Busca ingredientes en bases de datos especializadas
- 🤖 **IA de respaldo**: Usa inteligencia artificial cuando no encuentra ingredientes
""")

# Sección "Cómo Funciona" se moverá después de los resultados

# Formulario para URL y selección de necesidad
st.header("📱 Analizar desde URL")
with st.form(key="url_form"):
    url = st.text_input("URL del producto", placeholder="https://www.isdin.com/...")
    user_need = st.selectbox("Necesidad de la piel", ["sensible skin", "general safety"])
    submit_url = st.form_submit_button("🔍 Analizar URL")

# Formulario para imagen y selección de necesidad
st.header("📸 Analizar desde Imagen")
with st.form(key="image_form"):
    image_file = st.file_uploader("Sube la imagen del producto o etiqueta (máx. 5MB)", type=["jpg", "jpeg", "png"], help="Puedes subir una foto del producto completo o solo de la etiqueta con ingredientes")
    user_need_image = st.selectbox("Necesidad de la piel (imagen)", ["sensible skin", "general safety"])
    submit_image = st.form_submit_button("🔍 Analizar Imagen")


# Función para mostrar resultados
def display_results(result):
    st.header("📊 Resultados del Análisis")
    
    # Mostrar información del producto si está disponible
    if 'product_name' in result and result['product_name']:
        st.subheader("🏷️ Información del Producto")
        st.info(f"**Producto:** {result['product_name']}")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        st.metric("Puntaje Eco Promedio", f"{result['avg_eco_score']}/100")
    with col2:
        suitability_color = {"Sí": "green", "Evaluar": "orange"}
        st.write(
            f"**Adecuación para tu piel**: <span style='color:{suitability_color.get(result['suitability'], 'gray')}'>{result['suitability']}</span>",
            unsafe_allow_html=True)

    # Tabla de ingredientes con colores para risk_level
    st.subheader("📋 Detalles de Ingredientes")
    
    
    rows = []
    for ing in result["ingredients_details"]:
        risk_color = {
            "seguro": "green",
            "riesgo bajo": "blue",
            "riesgo medio": "orange",
            "riesgo alto": "red",
            "cancerígeno": "darkred",
            "desconocido": "gray"
        }.get(ing["risk_level"], "gray")
        
        # Determine eco-friendly status based on eco_score (robust error handling)
        eco_score = ing.get("eco_score", 50)
        eco_friendly = eco_score >= 70
        eco_icon = "✅" if eco_friendly else "❌"
        
        # Ensure all required fields exist with defaults
        ingredient_name = ing.get("name", "Unknown")
        benefits = ing.get("benefits", "No disponible")
        risks = ing.get("risks_detailed", "No disponible")
        sources = ing.get("sources", "Unknown")
        
        # Clean sources - remove "Local Database" and keep only organization names
        clean_sources = sources.replace("Local Database + ", "").replace("Local Database", "").replace(" + ", ", ")
        if clean_sources.startswith(", "):
            clean_sources = clean_sources[2:]
        if clean_sources == "":
            clean_sources = "Enhanced Analysis"
        
        # Generate explanations
        eco_explanation = ""
        if eco_friendly:
            eco_explanation = "✅ Ingrediente natural/biodegradable con bajo impacto ambiental"
        else:
            if eco_score < 40:
                eco_explanation = "❌ Derivado del petróleo, no biodegradable, tóxico para corales"
            elif eco_score < 60:
                eco_explanation = "⚠️ Puede ser irritante o disruptor endocrino"
            else:
                eco_explanation = "⚠️ Impacto ambiental moderado"
        
        risk_explanation = ""
        risk_level = ing.get("risk_level", "desconocido")
        if risk_level == "seguro":
            risk_explanation = "✅ Sin efectos adversos conocidos, ingrediente natural"
        elif risk_level == "riesgo bajo":
            risk_explanation = "🔵 Puede causar irritación leve en piel sensible"
        elif risk_level == "riesgo medio":
            risk_explanation = "🟠 Irritante potencial, disruptor endocrino, o tóxico en altas dosis"
        elif risk_level == "riesgo alto":
            risk_explanation = "🔴 Alto riesgo de irritación, alergias, o toxicidad"
        elif risk_level == "cancerígeno":
            risk_explanation = "🚫 Clasificado como carcinógeno por IARC"
        else:
            risk_explanation = "❓ Datos insuficientes, recomendamos precaución"
        
        rows.append({
            "Ingrediente": ingredient_name,
            "Eco-Score": f"{eco_score}/100",
            "Eco-Friendly": f"{eco_icon} {'Sí' if eco_friendly else 'No'}",
            "¿Por qué no es eco-friendly?": eco_explanation,
            "Beneficios": benefits,
            "Riesgos": risks,
            "Nivel de Riesgo": risk_level,
            "¿Por qué este nivel de riesgo?": risk_explanation,
            "Fuentes": clean_sources
        })

    # Mostrar tabla con scroll si es larga
    st.dataframe(rows, width='stretch', hide_index=True)
    
    # Sección "Cómo Funciona" después de los resultados
    st.markdown("---")
    with st.expander("🔍 ¿Cómo funciona el análisis?"):
        st.markdown("""
        ### Eco-Friendly (🌿)
        Un ingrediente es **eco-friendly** si su `eco_score` es > 70/100. Este puntaje se calcula priorizando:
        - **Biodegradabilidad**: ¿Se descompone naturalmente sin dañar el medio ambiente?
        - **Toxicidad**: Impacto en la vida marina, suelo, y ecosistemas (basado en EWG Skin Deep).
        - **Sostenibilidad**: Origen natural, producción ética, y bajo uso de recursos.

        **Fuentes**: EWG (Environmental Working Group) para scores eco, combinado con COSING (EU) para restricciones.

        ### Nivel de Riesgo (⚠️)
        Clasificamos el riesgo en niveles basados en evidencia científica:
        - **Seguro**: Bajo riesgo para la mayoría de usuarios (sin irritación ni disruptores endocrinos).
        - **Riesgo Bajo**: Posible irritación leve, pero seguro en dosis bajas.
        - **Riesgo Medio**: Irritante potencial, disruptores endocrinos, o tóxico en altas dosis.
        - **Riesgo Alto**: Alto riesgo de irritación, alergias, o toxicidad.
        - **Cancerígeno**: Clasificado como carcinógeno por IARC (Agencia Internacional para la Investigación del Cáncer).
        - **Desconocido**: Datos insuficientes; recomendamos precaución.

        **Priorización**: IARC > FDA > INVIMA (Colombia) > EWG. Si "sensible skin", evaluamos estrictamente.

        ### Base de Datos Contrastada (📊)
        Nuestro análisis se basa en fuentes verificadas y contrastadas:
        - **APIs Externas**: FDA (EE.UU.), PubChem (química), EWG (eco-scores), IARC (cáncer), INVIMA (Colombia), COSING (UE).
        - **LLM Enriquecimiento**: NVIDIA Llama 3.1 para analizar datos faltantes y generar resúmenes empáticos.
        - **Actualización**: Datos actualizados continuamente (sin cutoff de conocimiento). **Disclaimer**: Consulta a un profesional para consejos médicos personalizados.
        """)


# Procesar solicitud de URL
if submit_url and url:
    with st.spinner("🔄 Analizando URL..."):
        st.session_state.error = None
        if not validators.url(url):
            st.session_state.error = "Por favor, ingresa una URL válida (por ejemplo, https://www.isdin.com/...)"
        else:
            try:
                response = requests.post(
                    "http://127.0.0.1:8001/analyze-url",
                    json={"url": url, "user_need": user_need}
                )
                response.raise_for_status()
                st.session_state.result = response.json()
                st.success("✅ Análisis de URL completado con éxito")
            except requests.exceptions.RequestException as e:
                st.session_state.error = f"Error al analizar la URL: {str(e)}"

# Procesar solicitud de imagen
if submit_image and image_file:
    st.session_state.error = None
    try:
        # Validar tamaño de la imagen
        image_data = image_file.read()
        if len(image_data) > 5 * 1024 * 1024:
            st.session_state.error = "La imagen es demasiado grande (máximo 5MB)"
        else:
            # Mostrar vista previa de la imagen
            image = Image.open(io.BytesIO(image_data))
            st.image(image, caption="Imagen subida", width='stretch')

            # Progress bar for image analysis
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Step 1: Uploading image
            status_text.text("📤 Subiendo imagen...")
            progress_bar.progress(20)
            
            # Enviar imagen al backend
            form_data = {"user_need": user_need_image}
            files = {"file": (image_file.name, image_data, image_file.type)}
            
            # Step 2: Processing image
            status_text.text("🔄 Procesando imagen (OCR)...")
            progress_bar.progress(40)
            
            response = requests.post(
                "http://127.0.0.1:8001/analyze-image",
                data=form_data,
                files=files,
                timeout=60  # 60 second timeout for optimized processing
            )
            
            # Step 3: Analyzing ingredients
            status_text.text("🧪 Analizando ingredientes...")
            progress_bar.progress(80)
            
            response.raise_for_status()
            st.session_state.result = response.json()
            
            # Step 4: Complete
            progress_bar.progress(100)
            status_text.text("✅ Análisis completado")
            st.success("✅ Análisis de imagen completado con éxito")
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
    except requests.exceptions.Timeout:
        st.session_state.error = "⏰ El análisis tardó demasiado tiempo. Intenta con una imagen más pequeña o clara."
    except requests.exceptions.RequestException as e:
        st.session_state.error = f"Error al analizar la imagen: {str(e)}"

# Mostrar resultados o errores
if st.session_state.error:
    st.error(st.session_state.error)
if st.session_state.result:
    display_results(st.session_state.result)

# Pie de página
st.markdown("---")
st.markdown("Desarrollado por Mommyshops | Consulta a un profesional para consejos médicos.")