# Updated: Fixed eco_friendly KeyError - v2.1
import streamlit as st
import requests
from PIL import Image
import io
import validators  # Para validar URLs

# Configuración de la página
st.set_page_config(
    page_title="Mommyshops - Analiza tus Productos", 
    page_icon="🌿", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado con los colores de tu página web
st.markdown("""
<style>
    /* Colores principales de MommyShops */
    :root {
        --primary-pink: #b3368f;
        --primary-yellow: #fcc63c;
        --dark-pink: #8b2a6f;
        --light-pink: #f8e8f4;
        --light-yellow: #fef7d6;
        --background-gray: #F9FAFB;
        --text-dark: #111827;
        --white: #FFFFFF;
        --border-gray: #E5E7EB;
        --success-green: #10B981;
        --warning-orange: #F59E0B;
        --danger-red: #EF4444;
    }
    
    /* Estilo general */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
        background: var(--dark-pink);
    }
    
    /* Fondo de la página */
    .stApp {
        background: var(--dark-pink);
    }
    
    /* Fondo del contenido principal */
    .main {
        background: var(--dark-pink);
    }
    
    /* Header personalizado */
    .main-header {
        background: linear-gradient(135deg, var(--primary-pink) 0%, var(--primary-yellow) 100%);
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .main-header h1 {
        color: white !important;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .main-header p {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.1rem;
        margin-bottom: 0;
    }
    
    /* Cards con estilo */
    .stContainer {
        background: var(--white);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        border: 1px solid var(--border-gray);
        color: var(--text-dark);
    }
    
    /* Texto en contenedores */
    .stContainer h1, .stContainer h2, .stContainer h3, .stContainer h4, .stContainer h5, .stContainer h6 {
        color: var(--text-dark) !important;
    }
    
    .stContainer p, .stContainer li, .stContainer span, .stContainer strong {
        color: var(--text-dark) !important;
    }
    
    /* Asegurar que las listas se vean correctamente */
    .stContainer ul {
        color: var(--text-dark) !important;
        margin-left: 1rem;
    }
    
    .stContainer li {
        color: var(--text-dark) !important;
        margin-bottom: 0.5rem;
    }
    
    /* Botones personalizados */
    .stButton > button {
        background: var(--primary-pink);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.2s;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    }
    
    .stButton > button:hover {
        background: var(--dark-pink);
        transform: translateY(-1px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* Formularios */
    .stSelectbox > div > div {
        border-radius: 8px;
        border: 1px solid var(--border-gray);
    }
    
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 1px solid var(--border-gray);
    }
    
    /* File uploader */
    .stFileUploader > div {
        border-radius: 8px;
        border: 2px dashed var(--primary-pink);
        background: var(--light-pink);
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: var(--dark-pink);
    }
    
    /* Elementos del sidebar */
    .css-1d391kg .stSelectbox, .css-1d391kg .stTextInput {
        background: var(--white);
        color: var(--text-dark);
    }
    
    /* Métricas */
    .metric-card {
        background: var(--white);
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid var(--primary-pink);
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
    }
    
    /* Badges de ingredientes */
    .ingredient-badge {
        display: inline-block;
        background: var(--light-pink);
        color: var(--dark-pink);
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.875rem;
        font-weight: 500;
        margin: 0.25rem;
    }
    
    .ingredient-badge.safe {
        background: var(--light-yellow);
        color: #92400E;
    }
    
    .ingredient-badge.warning {
        background: #FEF3C7;
        color: #92400E;
    }
    
    .ingredient-badge.danger {
        background: #FEE2E2;
        color: #991B1B;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar session_state para persistir resultados
if 'result' not in st.session_state:
    st.session_state.result = None
if 'error' not in st.session_state:
    st.session_state.error = None

# Header principal con estilo personalizado
st.markdown("""
<div class="main-header">
    <h1>🌿 MommyShops</h1>
    <p>Analiza Productos Seguros y Eco-Friendly para tu Familia</p>
</div>
""", unsafe_allow_html=True)

# Descripción mejorada
st.markdown("### 🔍 ¿Cómo funciona?")
st.markdown("Sube una imagen de la etiqueta de un producto (JPEG/PNG, máximo 5MB) o ingresa la URL de la página del producto para analizar sus ingredientes.")
st.markdown("### 🆕 Nuevas capacidades:")
st.markdown("""
- 📸 **Reconocimiento de productos**: Ahora puedes subir fotos del producto completo, no solo la etiqueta
- 🏷️ **Identificación de marcas**: Detecta automáticamente la marca y nombre del producto  
- 🔍 **Búsqueda inteligente**: Busca ingredientes en bases de datos especializadas
- 🤖 **IA de respaldo**: Usa inteligencia artificial cuando no encuentra ingredientes
""")

# Checkbox para elegir tipo de análisis
analysis_type = st.checkbox("📱 URL Analysis", value=False)
if not analysis_type:
    st.checkbox("📸 Image Analysis", value=True)

# Formulario único basado en la selección
if analysis_type:
    # Análisis por URL
    with st.form(key="analysis_form"):
        url = st.text_input("URL del producto", placeholder="https://www.isdin.com/...")
        submit_button = st.form_submit_button("🔍 Analizar")
        
        if submit_button and url:
            user_need = "general safety"  # Valor por defecto
else:
    # Análisis por imagen
    with st.form(key="analysis_form"):
        image_file = st.file_uploader("Sube la imagen del producto o etiqueta (máx. 5MB)", type=["jpg", "jpeg", "png"], help="Puedes subir una foto del producto completo o solo de la etiqueta con ingredientes")
        submit_button = st.form_submit_button("🔍 Analizar")
        
        if submit_button and image_file:
            user_need = "general safety"  # Valor por defecto


# Función para mostrar resultados
def display_results(result):
    st.markdown('<div class="stContainer">', unsafe_allow_html=True)
    st.markdown("### 📊 Resultados del Análisis")
    
    # Mostrar información del producto si está disponible
    if 'product_name' in result and result['product_name']:
        st.subheader("🏷️ Información del Producto")
        st.info(f"**Producto:** {result['product_name']}")
    
    # Métricas principales con estilo mejorado
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h4>🌱 Puntaje Eco</h4>
            <h2 style="color: var(--primary-pink); margin: 0;">{result['avg_eco_score']}/100</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        suitability_color = {"Sí": "var(--success-green)", "Evaluar": "var(--warning-orange)", "No": "var(--danger-red)"}
        st.markdown(f"""
        <div class="metric-card">
            <h4>👤 Adecuado para tu piel</h4>
            <h2 style="color: {suitability_color.get(result['suitability'], 'var(--text-dark)')}; margin: 0;">{result['suitability']}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h4>🔬 Ingredientes</h4>
            <h2 style="color: var(--primary-yellow); margin: 0;">{len(result['ingredients_details'])}</h2>
        </div>
        """, unsafe_allow_html=True)

    # Ingredientes con badges de colores
    st.markdown('<div class="stContainer">', unsafe_allow_html=True)
    st.markdown("### 📋 Ingredientes Detectados")
    
    # Mostrar ingredientes como badges
    ingredients_html = "<div style='margin: 1rem 0;'>"
    for ing in result["ingredients_details"]:
        risk_level = ing.get("risk_level", "desconocido")
        eco_score = ing.get("eco_score", 50)
        
        # Determinar clase CSS basada en el nivel de riesgo
        if risk_level == "seguro":
            badge_class = "ingredient-badge safe"
        elif risk_level in ["riesgo bajo", "riesgo medio"]:
            badge_class = "ingredient-badge warning"
        else:
            badge_class = "ingredient-badge danger"
        
        ingredients_html += f"""
        <span class="{badge_class}">
            {ing.get("name", "Unknown")} - {eco_score}/100
        </span>
        """
    ingredients_html += "</div>"
    
    st.markdown(ingredients_html, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Tabla detallada
    st.markdown('<div class="stContainer">', unsafe_allow_html=True)
    st.markdown("#### 📊 Análisis Detallado")
    
    
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
    st.markdown('</div>', unsafe_allow_html=True)
    
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
    
    st.markdown('</div>', unsafe_allow_html=True)


# Procesar solicitud basada en el tipo de análisis
if 'submit_button' in locals() and submit_button:
    if analysis_type and 'url' in locals() and url:
        # Análisis por URL
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
    
    elif not analysis_type and 'image_file' in locals() and image_file:
        # Análisis por imagen
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
                form_data = {"user_need": user_need}
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