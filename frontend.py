"""
Streamlit app integrating MommyShops onboarding with backend APIs.
"""

import os
from typing import Any, Dict, List, Optional

import requests
import streamlit as st
from firebase_config import create_user, verify_user_credentials, update_user_profile, save_analysis_result, get_user_analysis_history

# Force production mode if running on Railway or in production
if not os.getenv("RAILWAY_ENVIRONMENT") and not os.getenv("PRODUCTION"):
    # Check if we're running on a production domain
    import socket
    try:
        hostname = socket.gethostname()
        if "railway" in hostname.lower() or "production" in hostname.lower():
            os.environ["PRODUCTION"] = "true"
    except:
        pass


st.set_page_config(page_title="MommyShops", page_icon="🌿", layout="wide")


def _normalize_url(value: str) -> str:
    return value.rstrip("/")


def resolve_api_base() -> Optional[str]:
    # Check if we're in production (Railway environment)
    if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("PRODUCTION"):
        # Production environment - use production URL
        secret_url = None
        try:
            secret_url = getattr(st.secrets, "API_URL", None)
        except Exception:
            secret_url = None
        if secret_url:
            return _normalize_url(str(secret_url).strip())

        # Check environment variable
        env_url = os.getenv("API_URL")
        if env_url:
            return _normalize_url(env_url.strip())
        
        # Default production URL
        return "https://web-production-f23a5.up.railway.app"
    
    # Development environment - try local first
    local = "http://127.0.0.1:8000"
    try:
        response = requests.get(f"{local}/health", timeout=2)
        if response.status_code == 200:
            return local
    except requests.RequestException:
        pass
    
    # If local not available, check secrets
    secret_url = None
    try:
        secret_url = getattr(st.secrets, "API_URL", None)
    except Exception:
        secret_url = None
    if secret_url:
        return _normalize_url(str(secret_url).strip())

    # Check environment variable
    env_url = os.getenv("API_URL")
    if env_url:
        return _normalize_url(env_url.strip())

    # Default fallback to local (even if not responding)
    return local


def debug_api_connection():
    """Debug function to help troubleshoot API connection issues"""
    st.write("🔍 **API Connection Debug Info:**")
    
    # Check environment variables
    st.write(f"**RAILWAY_ENVIRONMENT:** {os.getenv('RAILWAY_ENVIRONMENT', 'Not set')}")
    st.write(f"**PRODUCTION:** {os.getenv('PRODUCTION', 'Not set')}")
    st.write(f"**API_URL (env):** {os.getenv('API_URL', 'Not set')}")
    
    # Check secrets
    try:
        secret_url = getattr(st.secrets, "API_URL", None)
        st.write(f"**API_URL (secrets):** {secret_url}")
    except Exception as e:
        st.write(f"**API_URL (secrets):** Error accessing secrets: {e}")
    
    # Test resolved URL
    resolved_url = resolve_api_base()
    st.write(f"**Resolved API URL:** {resolved_url}")
    
    # Test connection
    if resolved_url:
        try:
            response = requests.get(f"{resolved_url}/health", timeout=5)
            st.write(f"**Health Check Status:** {response.status_code}")
            if response.status_code == 200:
                st.write("✅ **API is accessible!**")
            else:
                st.write("❌ **API returned error status**")
        except Exception as e:
            st.write(f"❌ **API Connection Error:** {e}")
    else:
        st.write("❌ **No API URL resolved**")


def parse_error(response: requests.Response) -> str:
    try:
        payload = response.json()
        detail = payload.get("detail") if isinstance(payload, dict) else None
        if isinstance(detail, list) and detail:
            if isinstance(detail[0], dict):
                return detail[0].get("msg", response.text)
            return str(detail[0])
        if detail:
            return str(detail)
    except ValueError:
        pass
    return response.text


def register_account(username: str, email: str, password: str) -> bool:
    """Register account using Firebase"""
    try:
        # Prepare user data for Firebase
        user_data = {
            'username': username.strip(),
            'email': email.strip(),
            'password': password
        }
        
        # Create user in Firebase
        result = create_user(user_data)
        
        if result:
            st.sidebar.success("Registro completado. Inicia sesión para continuar.")
            return True
        else:
            st.sidebar.error("Error al crear la cuenta. Verifica los datos e intenta nuevamente.")
            return False
            
    except Exception as e:
        st.sidebar.error(f"Error al registrar: {e}")
        return False


def login_account(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Login account using Firebase"""
    try:
        # For now, we'll use email as the identifier
        # In a real implementation, you might want to store username separately
        email = username.strip()  # Assuming username is email for now
        
        # Verify credentials with Firebase
        result = verify_user_credentials(email, password)
        
        if result:
            st.sidebar.success("Inicio de sesión exitoso.")
            return result
        else:
            st.sidebar.error("Credenciales incorrectas. Verifica tu usuario y contraseña.")
            return None
            
    except Exception as e:
        st.sidebar.error(f"Error al iniciar sesión: {e}")
        return None


def submit_profile(payload: Dict[str, Any], token: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Submit profile using Firebase"""
    try:
        # Get current user ID from session state
        user_id = st.session_state.auth.get("user_id") if st.session_state.auth else None
        
        if not user_id:
            st.error("No hay usuario autenticado.")
            return None
        
        # Update user profile in Firebase
        success = update_user_profile(user_id, payload)
        
        if success:
            st.success("Perfil guardado correctamente.")
            return {"user_id": user_id, "status": "success"}
        else:
            st.error("Error al guardar el perfil.")
            return None
            
    except Exception as e:
        st.error(f"Error al guardar el perfil: {e}")
        return None


def analyze_routine(user_id: int, token: Optional[str], file_bytes: Optional[bytes], filename: Optional[str]) -> Optional[Dict[str, Any]]:
    base = require_backend()
    if not base:
        return None
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request_kwargs: Dict[str, Any] = {"headers": headers, "timeout": 150, "data": {}}  # Increased timeout for improved OCR
    if file_bytes:
        request_kwargs["files"] = {
            "file": (filename or "etiqueta.png", file_bytes, "application/octet-stream")
        }
    try:
        response = requests.post(
            f"{base}/analyze_routine/{user_id}",
            **request_kwargs,
        )
        if response.status_code == 200:
            return response.json()
        st.error(f"Análisis fallido: {parse_error(response)}")
    except requests.RequestException as exc:
        st.error(f"Error durante el análisis: {exc}")
    return None


def analyze_url(url: str, user_need: str = "general safety") -> Optional[Dict[str, Any]]:
    base = require_backend()
    if not base:
        return None
    """Analyze product from URL."""
    try:
        response = requests.post(
            f"{base}/analyze-url",
            json={"url": url, "user_need": user_need},
            timeout=60
        )
        if response.status_code == 200:
            return response.json()
        if response.status_code == 404:
            st.error("El backend no tiene habilitado el endpoint /analyze-url. Actualiza el servidor para usar esta función.")
            return None
        st.error(f"Análisis de URL fallido: {parse_error(response)}")
    except requests.RequestException as exc:
        st.error(f"Error durante el análisis de URL: {exc}")
    return None


def fetch_recommendations(user_id: int, token: Optional[str]) -> Optional[List[Dict[str, Any]]]:
    base = require_backend()
    if not base:
        return None
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        response = requests.get(
            f"{base}/recommendations/{user_id}",
            headers=headers,
            timeout=30,
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("items", [])
        st.warning(f"No se pudo recuperar recomendaciones: {parse_error(response)}")
    except requests.RequestException as exc:
        st.warning(f"Error recuperando recomendaciones: {exc}")
    return None


def ensure_session_state() -> None:
    if "auth" not in st.session_state:
        st.session_state.auth = None
    if "analysis" not in st.session_state:
        st.session_state.analysis = None
    if "stored_recommendations" not in st.session_state:
        st.session_state.stored_recommendations = None
    if "url_analysis" not in st.session_state:
        st.session_state.url_analysis = None
    if "api_base" not in st.session_state:
        st.session_state.api_base = resolve_api_base()


def require_backend(target: str = "main") -> Optional[str]:
    base = st.session_state.get("api_base")
    if base:
        return base
    container = st.sidebar if target == "sidebar" else st
    container.error("Configura la URL del backend en la barra lateral.")
    return None


def render_analysis(result: Dict[str, Any]) -> None:
    st.subheader("Recomendaciones Personalizadas")
    st.caption(f"Rutina #{result.get('routine_id')}")

    analysis = result.get("analysis") or {}
    avg_eco = analysis.get("avg_eco_score", 0)
    suitability = analysis.get("suitability", "Sin datos")
    ingredient_count = len(analysis.get("ingredients_details", []))

    col1, col2, col3 = st.columns(3)
    col1.metric("Eco-score", f"{avg_eco:.1f}/100")
    col2.metric("Adecuación", suitability)
    col3.metric("Ingredientes Analizados", ingredient_count)

    extracted = result.get("extracted_ingredients") or []
    if extracted:
        st.write("**Ingredientes detectados via OCR:**")
        st.write(", ".join(extracted))

    alerts = result.get("alerts") or []
    if alerts:
        st.markdown("### Alertas")
        for alert in alerts:
            st.warning(alert)

    recommendations = result.get("recommendations") or []
    if recommendations:
        st.markdown("### Consejos y alternativas")
        for rec in recommendations:
            st.info(rec)

    substitutes = result.get("substitutes") or []
    if substitutes:
        st.markdown("### Sustitutos sugeridos")
        table = []
        for item in substitutes:
            table.append(
                {
                    "Producto": item.get("name"),
                    "Marca": item.get("brand") or "",
                    "Puntaje Eco": item.get("eco_score"),
                    "Riesgo": item.get("risk_level"),
                    "Similitud": round(item.get("similarity", 0.0), 2),
                    "Razón": item.get("reason", ""),
                }
            )
        st.dataframe(table, hide_index=True)

    products = result.get("products") or []
    if products:
        st.markdown("### Detalle por producto")
        for product in products:
            with st.expander(product.get("product_name", "Producto")):
                if product.get("alerts"):
                    st.write("- " + "\n- ".join(product["alerts"]))
                if product.get("substitutes"):
                    st.write("**Sustitutos:**")
                    for alt in product["substitutes"]:
                        st.write(f"• {alt.get('name')} ({alt.get('reason', 'Sin motivo')})")


def render_recommendations(items: List[Dict[str, Any]]) -> None:
    if not items:
        return
    st.markdown("### Recomendaciones guardadas")
    for entry in items:
        with st.expander(entry.get("reason", "Recomendación")):
            st.write(f"Estado: {entry.get('status', 'pendiente')}")
            original = entry.get("original_product_name")
            substitute = entry.get("substitute_product_name")
            if original:
                st.write(f"Producto analizado: {original}")
            if substitute:
                st.write(f"Sugerido: {substitute}")


ensure_session_state()


st.sidebar.markdown("### Configuración del backend")

# Show current backend status
current_base = st.session_state.get("api_base") or ""
if current_base == "http://127.0.0.1:8000":
    st.sidebar.success(f"🔗 Backend: Local ({current_base})")
    st.sidebar.caption("✅ Ejecutándose localmente con OCR mejorado")
elif current_base and "railway" in current_base:
    st.sidebar.info(f"🔗 Backend: Railway ({current_base})")
    st.sidebar.caption("☁️ Ejecutándose en la nube")
elif current_base:
    st.sidebar.info(f"🔗 Backend: Personalizado ({current_base})")
    st.sidebar.caption("⚙️ Configuración personalizada")
else:
    st.sidebar.warning("⚠️ No se detectó un backend disponible")

# Backend configuration
backend_input = st.sidebar.text_input(
    "URL del backend (opcional)",
    current_base if current_base != "http://127.0.0.1:8000" else "",
    placeholder="https://tu-mommyshops-api.com",
    help="Solo configura si quieres usar un backend diferente al detectado automáticamente",
)

if st.sidebar.button("Guardar backend"):
    cleaned = _normalize_url(backend_input.strip()) if backend_input else ""
    if cleaned:
        st.session_state.api_base = cleaned
        st.sidebar.success("Backend actualizado.")
    else:
        st.sidebar.error("Ingresa una URL válida.")

if st.sidebar.button("Probar conexión"):
    try:
        response = requests.get(f"{current_base}/health", timeout=5)
        if response.status_code == 200:
            st.sidebar.success("Conexión exitosa con el backend.")
        else:
            st.sidebar.warning(f"Backend respondió con estado {response.status_code}.")
    except requests.RequestException as exc:
        st.sidebar.error(f"No se pudo conectar: {exc}")

# Debug section
if st.sidebar.button("🔍 Debug API"):
    with st.sidebar.expander("Debug Info", expanded=True):
        debug_api_connection()

st.sidebar.markdown("### Autenticación")

sidebar_username = st.sidebar.text_input("Usuario")
sidebar_email = st.sidebar.text_input("Email")
sidebar_password = st.sidebar.text_input("Contraseña", type="password")

col_reg, col_login, col_logout = st.sidebar.columns(3)
if col_reg.button("Registrar"):
    if not sidebar_username or not sidebar_email or not sidebar_password:
        st.sidebar.error("Completa usuario, email y contraseña.")
    else:
        register_account(sidebar_username, sidebar_email, sidebar_password)

if col_login.button("Iniciar sesión"):
    if not sidebar_username or not sidebar_password:
        st.sidebar.error("Usuario y contraseña son obligatorios.")
    else:
        profile = login_account(sidebar_username, sidebar_password)
        if profile:
            st.session_state.auth = {
                "token": profile.get("access_token"),
                "user_id": profile.get("user_id"),
                "username": profile.get("username"),
                "email": profile.get("email"),
            }
            st.sidebar.success(f"Sesión iniciada como {profile.get('username')}")

# Google OAuth2 Login
st.sidebar.markdown("---")
st.sidebar.markdown("**O inicia sesión con:**")

if st.sidebar.button("🔐 Iniciar con Gmail", type="primary"):
    try:
        # Get Google auth URL
        api_base = st.session_state.get("api_base")
        if not api_base:
            st.sidebar.error("Backend no configurado")
        else:
            response = requests.get(f"{api_base}/auth/google", timeout=10)
            if response.status_code == 200:
                auth_data = response.json()
                auth_url = auth_data.get("auth_url")
                if auth_url:
                    st.sidebar.markdown(f"[Iniciar sesión con Google]({auth_url})")
                    st.sidebar.info("Se abrirá una nueva ventana para autenticarte con Google")
                else:
                    st.sidebar.error("No se pudo obtener la URL de autenticación")
            else:
                st.sidebar.error("Error al conectar con el servidor")
    except Exception as e:
        st.sidebar.error(f"Error: {e}")

if col_logout.button("Cerrar sesión"):
    st.session_state.auth = None
    st.session_state.analysis = None
    st.session_state.stored_recommendations = None

if st.session_state.auth:
    st.sidebar.success(f"Conectado como {st.session_state.auth.get('username')}")


st.title("MommyShops · Personalización de rutina")
st.markdown("Completa tu perfil y recibe recomendaciones adaptadas.")

# OCR Improvements info
st.info("🔧 **Nuevo**: Sistema OCR mejorado con Otsu binarization, corrección de inclinación y fuzzy matching para 90%+ de precisión en análisis de ingredientes.")


with st.form("Perfil Personalizado"):
    st.subheader("Características personales")
    skin_face = st.selectbox("Tipo de piel facial", ["Seca", "Grasa", "Mixta", "Sensible", "Normal"], index=0)
    hair_type = st.selectbox("Tipo de cabello", ["Liso", "Ondulado", "Rizado", "Afro"], index=0)
    goals_face = st.multiselect(
        "Objetivo principal para tu cara",
        ["Hidratar", "Controlar brillo", "Tratar manchas", "Prevenir arrugas", "Reducir sensibilidad"],
    )
    climate = st.selectbox("Clima donde vives", ["Húmedo", "Seco", "Templado", "Cambiante"], index=0)

    st.subheader("Cuidado corporal")
    skin_body = st.multiselect(
        "Tipo de piel corporal",
        ["Seca", "Grasa", "Mixta", "Sensible", "Normal"],
    )
    goals_body = st.multiselect(
        "Objetivos para el cuerpo",
        ["Hidratar", "Mejorar firmeza", "Reducir manchas", "Atenuar estrías o cicatrices", "Reducir sensibilidad"],
    )

    st.subheader("Cabello")
    hair_porosity = st.multiselect(
        "Porosidad",
        ["Baja porosidad", "Media porosidad", "Alta porosidad", "No estoy segura"],
    )
    st.markdown("Selecciona objetivos y asigna prioridad (1-5).")
    goals_hair_options = [
        "Reducir frizz",
        "Estimular crecimiento",
        "Dar volumen",
        "Reparar daño",
        "Mantener color",
        "Hidratación/más suavidad",
    ]
    goals_hair: Dict[str, int] = {}
    for goal in goals_hair_options:
        enabled = st.checkbox(goal, key=f"goal_{goal}")
        if enabled:
            goals_hair[goal] = st.slider(goal, 1, 5, 3, key=f"slider_{goal}")

    st.subheader("Grosor y cuero cabelludo")
    hair_thickness = st.multiselect("Grosor", ["Fino", "Medio", "Grueso"])
    scalp = st.multiselect("Condición del cuero cabelludo", ["Graso", "Seco", "Sensible", "Normal"])

    st.subheader("Condiciones o sensibilidades")
    conditions = st.multiselect(
        "Selecciona las que aplican",
        [
            "Alergias",
            "Acné severo",
            "Dermatitis",
            "Psoriasis",
            "Rosácea",
            "Queratosis",
            "Manchas o hiperpigmentación",
            "Cicatrices visibles",
            "Calvicie o pérdida de densidad",
            "Caspa o descamación",
            "Cuero cabelludo sensible",
            "Cabello muy fino o quebradizo",
            "Ninguna",
        ],
    )
    other_condition = st.text_input("Otra condición (opcional)")

    products_input = st.text_area(
        "Productos que usas habitualmente",
        "Ej: La Roche-Posay Anthelios, TRESemmé Shampoo",
    )
    product_list = [item.strip() for item in products_input.split(",") if item.strip()]

    uploaded_file = st.file_uploader(
        "Sube foto de etiqueta para análisis",
        type=["jpg", "jpeg", "png"],
        help="Utiliza nuestro sistema OCR avanzado con Otsu binarization, corrección de inclinación y fuzzy matching para máxima precisión"
    )

    submitted = st.form_submit_button("Analizar y recomendar")

if submitted:
    if not product_list:
        st.error("Agrega al menos un producto.")
    elif not goals_hair:
        st.error("Selecciona al menos un objetivo para el cabello.")
    else:
        payload = {
            "skin_face": skin_face,
            "hair_type": hair_type,
            "goals_face": goals_face,
            "climate": climate,
            "skin_body": skin_body,
            "goals_body": goals_body,
            "hair_porosity": hair_porosity,
            "goals_hair": goals_hair,
            "hair_thickness_scalp": {"thickness": hair_thickness, "scalp": scalp},
            "conditions": conditions,
            "other_condition": other_condition,
            "products": product_list,
            "accept_terms": True,
        }

        profile_response = submit_profile(payload)
        if profile_response:
            st.success("Perfil guardado correctamente.")
            user_id = profile_response.get("user_id")
            if user_id:
                # Store user_id in session state for anonymous users
                if not st.session_state.auth:
                    st.session_state.auth = {"user_id": user_id}
                else:
                    st.session_state.auth["user_id"] = user_id
                
                file_bytes = uploaded_file.getvalue() if uploaded_file else None
                
                # Show OCR processing status if file is uploaded
                if uploaded_file:
                    st.info("🔧 Procesando imagen...")
                    with st.spinner("Aplicando Otsu binarization, corrección de inclinación y fuzzy matching..."):
                        analysis = analyze_routine(user_id, None, file_bytes, uploaded_file.name if uploaded_file else None)
                else:
                    analysis = analyze_routine(user_id, None, file_bytes, uploaded_file.name if uploaded_file else None)
                
                if analysis:
                    st.session_state.analysis = analysis
                    rec_items = fetch_recommendations(user_id, None)
                    st.session_state.stored_recommendations = rec_items
                    
                    # Show OCR success message if file was processed
                    if uploaded_file:
                        st.success("✅ Análisis de imagen completado")


analysis_result = st.session_state.analysis
if analysis_result:
    render_analysis(analysis_result)

stored_recs = st.session_state.stored_recommendations or []
render_recommendations(stored_recs)

# Nueva sección para análisis de URL
st.markdown("---")
st.markdown("## 🌐 Análisis por URL")
st.markdown("Analiza un producto específico ingresando su URL")

with st.form("url_analysis_form"):
    col1, col2 = st.columns([3, 1])
    
    with col1:
        product_url = st.text_input(
            "URL del producto",
            placeholder="https://www.isdin.com/producto...",
            help="Ingresa la URL completa del producto"
        )
    
    with col2:
        user_need_url = st.selectbox(
            "Tipo de análisis",
            ["general safety", "skin sensitivity", "pregnancy safety", "eco-friendly", "acne-prone skin"],
            help="Selecciona tu necesidad específica"
        )
    
    url_submitted = st.form_submit_button("🔍 Analizar Producto", use_container_width=True)

if url_submitted and product_url:
    if not product_url.startswith(('http://', 'https://')):
        st.error("Por favor, ingresa una URL válida que comience con http:// o https://")
    else:
        with st.spinner("Analizando producto desde URL..."):
            url_analysis = analyze_url(product_url, user_need_url)
            if url_analysis:
                st.session_state.url_analysis = url_analysis
                st.success("✅ Análisis de URL completado")

# Mostrar resultados del análisis de URL
if hasattr(st.session_state, 'url_analysis') and st.session_state.url_analysis:
    st.markdown("### 📊 Resultados del Análisis de URL")
    
    result = st.session_state.url_analysis
    
    # Información del producto
    if 'product_name' in result and result['product_name']:
        st.info(f"**Producto:** {result['product_name']}")
    
    # Métricas principales
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("🌱 Puntaje Eco", f"{result.get('avg_eco_score', 0)}/100")
    
    with col2:
        suitability = result.get('suitability', 'No disponible')
        st.metric("👤 Adecuado para tu piel", suitability)
    
    with col3:
        ingredients_count = len(result.get('ingredients_details', []))
        st.metric("🔬 Ingredientes", ingredients_count)
    
    # Ingredientes detectados
    if 'ingredients_details' in result and result['ingredients_details']:
        st.markdown("#### 📋 Ingredientes Detectados")
        
        ingredients_data = []
        for ing in result['ingredients_details']:
            risk_level = ing.get('risk_level', 'desconocido')
            eco_score = ing.get('eco_score', 50)
            
            # Determinar color según nivel de riesgo
            if risk_level == "seguro":
                risk_color = "🟢"
            elif risk_level in ["riesgo bajo", "riesgo medio"]:
                risk_color = "🟡"
            else:
                risk_color = "🔴"
            
            ingredients_data.append({
                "Ingrediente": ing.get('name', 'Unknown'),
                "Eco-Score": f"{eco_score}/100",
                "Nivel de Riesgo": f"{risk_color} {risk_level}",
                "Beneficios": ing.get('benefits', 'No disponible'),
                "Riesgos": ing.get('risks_detailed', 'No disponible')
            })
        
        st.dataframe(ingredients_data, hide_index=True)
    
    # Recomendaciones
    if 'recommendations' in result and result['recommendations']:
        st.markdown("#### 💡 Recomendaciones")
        st.write(result['recommendations'])


st.markdown("---")
st.caption("MommyShops ©")