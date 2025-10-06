"""
MommyShops - Clean and Optimized Frontend
Streamlined Streamlit interface for cosmetic ingredient analysis
"""

import streamlit as st
import requests
from PIL import Image
import io
import os
import validators

# Page configuration
st.set_page_config(
    page_title="MommyShops - Analiza tus Productos", 
    page_icon="🌿", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
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
    
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
        background: var(--dark-pink);
    }
    
    .stApp {
        background: var(--dark-pink);
    }
    
    .main {
        background: var(--dark-pink);
    }
    
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
    
    .stContainer {
        background: var(--white);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        border: 1px solid var(--border-gray);
        color: var(--text-dark);
    }
    
    .stContainer h1, .stContainer h2, .stContainer h3, .stContainer h4, .stContainer h5, .stContainer h6 {
        color: var(--text-dark) !important;
    }
    
    .stContainer p, .stContainer li, .stContainer span, .stContainer strong {
        color: var(--text-dark) !important;
    }
    
    .stContainer ul {
        color: var(--text-dark) !important;
        margin-left: 1rem;
    }
    
    .stContainer li {
        color: var(--text-dark) !important;
        margin-bottom: 0.5rem;
    }
    
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
    
    .metric-card {
        background: var(--white);
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid var(--primary-pink);
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
    }
    
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

# Initialize session state
if 'result' not in st.session_state:
    st.session_state.result = None
if 'error' not in st.session_state:
    st.session_state.error = None

def get_api_url():
    """Get API URL from Streamlit secrets or environment variables."""
    try:
        if hasattr(st, 'secrets') and 'API_URL' in st.secrets:
            return st.secrets["API_URL"]
        elif hasattr(st, 'secrets') and hasattr(st.secrets, 'secrets') and 'API_URL' in st.secrets.secrets:
            return st.secrets.secrets["API_URL"]
    except Exception as e:
        st.sidebar.warning(f"Error reading secrets: {e}")
    
    api_url = os.getenv("API_URL")
    if api_url:
        return api_url
    
    return "http://127.0.0.1:8001"

# Get and display API URL
api_url = get_api_url()
st.sidebar.info(f"🔗 Backend: {api_url}")

# Header
st.markdown("""
<div class="main-header">
    <h1>🌿 MommyShops</h1>
    <p>Analiza Productos Seguros y Eco-Friendly para tu Familia</p>
</div>
""", unsafe_allow_html=True)

# Description
st.markdown("### 🔍 ¿Cómo funciona?")
st.markdown("Sube una imagen de la etiqueta de un producto (JPEG/PNG, máximo 5MB) o ingresa el texto de ingredientes para analizar su seguridad.")

# Analysis options
col1, col2 = st.columns(2)
with col1:
    url_analysis = st.checkbox("📱 URL Analysis", value=False)
with col2:
    image_analysis = st.checkbox("📸 Image Analysis", value=True)

# URL Analysis Form
if url_analysis:
    with st.form(key="url_form"):
        url = st.text_input("URL del producto", placeholder="https://www.isdin.com/...")
        submit_url = st.form_submit_button("🔍 Analizar URL")
        
        if submit_url and url:
            if not validators.url(url):
                st.session_state.error = "Por favor, ingresa una URL válida"
            else:
                try:
                    response = requests.post(
                        f"{api_url}/analyze-url",
                        json={"url": url, "user_need": "general safety"}
                    )
                    response.raise_for_status()
                    st.session_state.result = response.json()
                    st.success("✅ Análisis de URL completado")
                except requests.exceptions.RequestException as e:
                    st.session_state.error = f"Error al analizar la URL: {str(e)}"

# Image Analysis Form
if image_analysis:
    with st.form(key="image_form"):
        image_file = st.file_uploader(
            "Sube la imagen del producto o etiqueta (máx. 5MB)", 
            type=["jpg", "jpeg", "png"], 
            help="Puedes subir una foto del producto completo o solo de la etiqueta con ingredientes"
        )
        submit_image = st.form_submit_button("🔍 Analizar Imagen")
        
        if submit_image and image_file:
            try:
                # Validate file size
                image_data = image_file.read()
                if len(image_data) > 5 * 1024 * 1024:
                    st.session_state.error = "La imagen es demasiado grande (máximo 5MB)"
                else:
                    # Show image preview
                    image = Image.open(io.BytesIO(image_data))
                    st.image(image, caption="Imagen subida", width='stretch')

                    # Progress bar
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Upload image
                    status_text.text("📤 Subiendo imagen...")
                    progress_bar.progress(20)
                    
                    # Process image
                    form_data = {"user_need": "general safety"}
                    files = {"file": (image_file.name, image_data, image_file.type)}
                    
                    status_text.text("🔄 Procesando imagen (OCR)...")
                    progress_bar.progress(40)
                    
                    response = requests.post(
                        f"{api_url}/analyze-image",
                        data=form_data,
                        files=files,
                        timeout=60
                    )
                    
                    status_text.text("🧪 Analizando ingredientes...")
                    progress_bar.progress(80)
                    
                    response.raise_for_status()
                    st.session_state.result = response.json()
                    
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

# Text Analysis Form
st.markdown("### 📝 O Análisis por Texto")
with st.form(key="text_form"):
    text_input = st.text_area(
        "Ingresa los ingredientes del producto", 
        placeholder="Aqua, Glycerin, Phenoxyethanol, Parfum...",
        height=100
    )
    submit_text = st.form_submit_button("🔍 Analizar Texto")
    
    if submit_text and text_input:
        try:
            response = requests.post(
                f"{api_url}/analyze-text",
                json={"text": text_input, "user_need": "general safety"}
            )
            response.raise_for_status()
            st.session_state.result = response.json()
            st.success("✅ Análisis de texto completado")
        except requests.exceptions.RequestException as e:
            st.session_state.error = f"Error al analizar el texto: {str(e)}"

# Display results
def display_results(result):
    st.markdown('<div class="stContainer">', unsafe_allow_html=True)
    st.markdown("### 📊 Resultados del Análisis")
    
    # Product info
    if 'product_name' in result and result['product_name']:
        st.subheader("🏷️ Información del Producto")
        st.info(f"**Producto:** {result['product_name']}")
    
    # Metrics
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

    # Ingredients with badges
    st.markdown('<div class="stContainer">', unsafe_allow_html=True)
    st.markdown("### 📋 Ingredientes Detectados")
    
    ingredients_html = "<div style='margin: 1rem 0;'>"
    for ing in result["ingredients_details"]:
        risk_level = ing.get("risk_level", "desconocido")
        eco_score = ing.get("eco_score", 50)
        
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
    
    # Detailed table
    st.markdown('<div class="stContainer">', unsafe_allow_html=True)
    st.markdown("#### 📊 Análisis Detallado")
    
    rows = []
    for ing in result["ingredients_details"]:
        eco_score = ing.get("eco_score", 50)
        eco_friendly = eco_score >= 70
        eco_icon = "✅" if eco_friendly else "❌"
        
        rows.append({
            "Ingrediente": ing.get("name", "Unknown"),
            "Eco-Score": f"{eco_score}/100",
            "Eco-Friendly": f"{eco_icon} {'Sí' if eco_friendly else 'No'}",
            "Nivel de Riesgo": ing.get("risk_level", "desconocido"),
            "Beneficios": ing.get("benefits", "No disponible"),
            "Riesgos": ing.get("risks_detailed", "No disponible"),
            "Fuentes": ing.get("sources", "Unknown")
        })

    st.dataframe(rows, width='stretch', hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Recommendations
    st.markdown('<div class="stContainer">', unsafe_allow_html=True)
    st.markdown("#### 💡 Recomendaciones")
    st.markdown(result.get("recommendations", "No hay recomendaciones disponibles"))
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Show results or errors
if st.session_state.error:
    st.error(st.session_state.error)
if st.session_state.result:
    display_results(st.session_state.result)

# Footer
st.markdown("---")
st.markdown("Desarrollado por Mommyshops | Consulta a un profesional para consejos médicos.")