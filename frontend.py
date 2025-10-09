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

# Additional production detection - check if we're not on localhost
try:
    import socket
    hostname = socket.gethostname()
    # If hostname doesn't contain common local identifiers, assume production
    if not any(local in hostname.lower() for local in ["localhost", "127.0.0.1", "local", "desktop", "macbook", "laptop"]):
        os.environ["PRODUCTION"] = "true"
except:
    pass


st.set_page_config(page_title="MommyShops", page_icon="🌿", layout="wide")


def _normalize_url(value: str) -> str:
    return value.rstrip("/")


def resolve_api_base() -> Optional[str]:
    # Check if we're in production (Railway environment)
    is_production = os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("PRODUCTION")
    
    # Try to detect production by testing if localhost is not available
    local = "http://127.0.0.1:8000"
    local_available = False
    try:
        response = requests.get(f"{local}/health", timeout=10)
        if response.status_code == 200:
            local_available = True
    except requests.RequestException:
        pass
    
    # If local is not available and we're not explicitly in development, assume production
    if not local_available and not os.getenv("DEVELOPMENT"):
        is_production = True
    
    if is_production:
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
    
    # Development environment - use local
    if local_available:
        return local
    
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
    st.write(f"**DEVELOPMENT:** {os.getenv('DEVELOPMENT', 'Not set')}")
    st.write(f"**API_URL (env):** {os.getenv('API_URL', 'Not set')}")
    
    # Check localhost availability
    local = "http://127.0.0.1:8000"
    local_available = False
    try:
        response = requests.get(f"{local}/health", timeout=10)
        if response.status_code == 200:
            local_available = True
    except requests.RequestException:
        pass
    st.write(f"**Localhost Available:** {local_available}")
    
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
            response = requests.get(f"{resolved_url}/health", timeout=10)
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


def create_interactive_questionnaire():
    """Create an interactive step-by-step questionnaire"""
    
    # Initialize questionnaire state
    if "questionnaire_step" not in st.session_state:
        st.session_state.questionnaire_step = 0
    if "questionnaire_answers" not in st.session_state:
        st.session_state.questionnaire_answers = {}
    if "questionnaire_completed" not in st.session_state:
        st.session_state.questionnaire_completed = False
    
    # Questionnaire steps
    steps = [
        {
            "title": "Tipo de piel facial",
            "question": "¿Cuál es tu tipo de piel facial?",
            "options": ["Seca", "Grasa", "Mixta", "Sensible", "Normal"],
            "key": "skin_face"
        },
        {
            "title": "Tipo de cabello",
            "question": "¿Cuál es tu tipo de cabello?",
            "options": ["Liso", "Ondulado", "Rizado", "Afro"],
            "key": "hair_type"
        },
        {
            "title": "Objetivos faciales",
            "question": "¿Cuáles son tus objetivos principales para el cuidado facial?",
            "options": ["Hidratar", "Controlar brillo", "Tratar manchas", "Prevenir arrugas", "Reducir sensibilidad"],
            "key": "goals_face",
            "multiple": True
        },
        {
            "title": "Clima",
            "question": "¿En qué tipo de clima vives?",
            "options": ["Húmedo", "Seco", "Templado", "Cambiante"],
            "key": "climate"
        },
        {
            "title": "Piel corporal",
            "question": "¿Cuál es tu tipo de piel corporal?",
            "options": ["Seca", "Grasa", "Mixta", "Sensible", "Normal"],
            "key": "skin_body",
            "multiple": True
        },
        {
            "title": "Objetivos corporales",
            "question": "¿Cuáles son tus objetivos para el cuidado corporal?",
            "options": ["Hidratar", "Mejorar firmeza", "Reducir manchas", "Atenuar estrías o cicatrices", "Reducir sensibilidad"],
            "key": "goals_body",
            "multiple": True
        },
        {
            "title": "Porosidad del cabello",
            "question": "¿Cuál es la porosidad de tu cabello?",
            "options": ["Baja", "Media", "Alta"],
            "key": "hair_porosity"
        },
        {
            "title": "Objetivos del cabello",
            "question": "¿Cuáles son tus objetivos para el cuidado del cabello?",
            "options": ["Hidratar", "Definir", "Aumentar volumen", "Reducir frizz", "Fortalecer"],
            "key": "goals_hair",
            "multiple": True
        },
        {
            "title": "Condiciones especiales",
            "question": "¿Tienes alguna condición especial de la piel?",
            "options": ["Acné", "Rosácea", "Dermatitis", "Psoriasis", "Ninguna"],
            "key": "conditions",
            "multiple": True
        }
    ]
    
    # Progress bar
    progress = (st.session_state.questionnaire_step + 1) / len(steps)
    st.progress(progress)
    st.caption(f"Paso {st.session_state.questionnaire_step + 1} de {len(steps)}")
    
    # Current step
    current_step = steps[st.session_state.questionnaire_step]
    
    st.markdown(f"### {current_step['title']}")
    st.markdown(f"**{current_step['question']}**")
    
    # Question input
    if current_step.get('multiple', False):
        answer = st.multiselect(
            "Selecciona todas las opciones que apliquen:",
            current_step['options'],
            default=st.session_state.questionnaire_answers.get(current_step['key'], [])
        )
    else:
        answer = st.selectbox(
            "Selecciona una opción:",
            current_step['options'],
            index=current_step['options'].index(st.session_state.questionnaire_answers.get(current_step['key'], current_step['options'][0]))
        )
    
    # Navigation buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("⬅️ Anterior", disabled=st.session_state.questionnaire_step == 0):
            st.session_state.questionnaire_step -= 1
            st.rerun()
    
    with col2:
        if st.button("💾 Guardar respuesta"):
            st.session_state.questionnaire_answers[current_step['key']] = answer
            st.success("¡Respuesta guardada!")
    
    with col3:
        if st.button("Siguiente ➡️", disabled=st.session_state.questionnaire_step == len(steps) - 1):
            if answer:  # Check if answer is not empty
                st.session_state.questionnaire_answers[current_step['key']] = answer
                if st.session_state.questionnaire_step < len(steps) - 1:
                    st.session_state.questionnaire_step += 1
                    st.rerun()
                else:
                    # Complete questionnaire
                    st.session_state.questionnaire_completed = True
                    st.success("¡Cuestionario completado! 🎉")
                    st.rerun()
            else:
                st.warning("Por favor selecciona una respuesta antes de continuar.")
    
    # Show completion button if on last step
    if st.session_state.questionnaire_step == len(steps) - 1 and st.session_state.questionnaire_answers.get(current_step['key']):
        if st.button("✅ Completar cuestionario", type="primary", use_container_width=True):
            st.session_state.questionnaire_answers[current_step['key']] = answer
            st.session_state.questionnaire_completed = True
            st.success("¡Cuestionario completado! 🎉")
            st.rerun()
    
    return st.session_state.questionnaire_answers

def handle_google_callback(code: str) -> Optional[Dict[str, Any]]:
    """Handle Google OAuth callback and get user info"""
    try:
        api_base = st.session_state.get("api_base")
        if not api_base:
            st.error("Backend no configurado")
            return None
        
        # Call the backend to handle the OAuth callback
        response = requests.get(f"{api_base}/auth/google/callback", params={"code": code}, timeout=30)
        
        if response.status_code == 200:
            auth_data = response.json()
            st.success("¡Inicio de sesión exitoso!")
            return auth_data
        else:
            st.error(f"Error en la autenticación: {response.text}")
            return None
            
    except Exception as e:
        st.error(f"Error al procesar la autenticación: {e}")
        return None

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
    """Submit profile using unified data service (both SQLite and Firebase)"""
    try:
        # Get current user ID from session state
        user_id = st.session_state.auth.get("user_id") if st.session_state.auth else None
        
        if not user_id:
            st.error("No hay usuario autenticado.")
            return None
        
        # Get Firebase UID if available
        firebase_uid = st.session_state.auth.get("firebase_uid") if st.session_state.auth else None
        
        # Update user profile using unified data service
        from unified_data_service import update_user_profile_unified
        success = update_user_profile_unified(user_id, payload, firebase_uid)
        
        if success:
            st.success("Perfil guardado correctamente en ambos sistemas.")
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

    # Check for Google OAuth callback
    if "code" in st.query_params and not st.session_state.get("auth"):
        code = st.query_params["code"]
        auth_result = handle_google_callback(code)
        if auth_result:
            st.session_state.auth = auth_result
            st.rerun()


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
        response = requests.get(f"{current_base}/health", timeout=10)
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

# User info in sidebar when authenticated
if st.session_state.get("auth"):
    user = st.session_state.auth.get("user", {})
    user_name = user.get("name", "Usuario")
    user_email = user.get("email", "")
    user_picture = user.get("picture", "")
    
    st.sidebar.markdown("### 👋 ¡Bienvenida!")
    
    # User info display
    col1, col2 = st.sidebar.columns([1, 3])
    if user_picture:
        col1.image(user_picture, width=50)
    col2.markdown(f"**{user_name}**")
    col2.caption(user_email)
    
    st.sidebar.success("✅ Sesión activa")
    
    # Logout button
    if st.sidebar.button("🚪 Cerrar sesión", type="secondary", use_container_width=True):
        st.session_state.auth = None
        st.session_state.analysis = None
        st.session_state.stored_recommendations = None
        st.rerun()


# Authentication Section - Moved to top
st.markdown("---")
if not st.session_state.get("auth"):
    st.markdown("### 🔐 Registrarme o Iniciar sesión")
    
    if st.button("🚀 Iniciar con Gmail", type="primary", use_container_width=True):
        try:
            # Get Google auth URL
            api_base = st.session_state.get("api_base")
            if not api_base:
                st.error("Backend no configurado")
            else:
                response = requests.get(f"{api_base}/auth/google", timeout=30)
                if response.status_code == 200:
                    auth_data = response.json()
                    auth_url = auth_data.get("auth_url")
                    if auth_url:
                        st.markdown(f"[🔗 Iniciar sesión con Google]({auth_url})")
                        st.info("Se abrirá una nueva ventana para autenticarte con Google")
                    else:
                        st.error("No se pudo obtener la URL de autenticación")
                else:
                    st.error("Error al conectar con el servidor")
        except Exception as e:
            st.error(f"Error: {e}")
    
    st.markdown("---")
    st.markdown("**¿No tienes cuenta?** El registro es automático al iniciar sesión con Gmail")

# Personalized title based on authentication status
if st.session_state.get("auth"):
    user = st.session_state.auth.get("user", {})
    user_name = user.get("name", "Usuario")
    st.title(f"👋 ¡Hola {user_name}!")
    st.markdown("Completa tu perfil y recibe recomendaciones personalizadas para ti.")
else:
    st.title("MommyShops · Personalización de rutina")
    st.markdown("Inicia sesión con Gmail para recibir recomendaciones adaptadas a tu perfil.")



# Interactive Questionnaire - Only for authenticated users
if st.session_state.get("auth"):
    st.markdown("---")
    st.markdown("### 📋 Cuestionario Personalizado")
    
    if not st.session_state.get("questionnaire_completed", False):
        st.info("Completa este cuestionario para recibir recomendaciones personalizadas.")
        questionnaire_answers = create_interactive_questionnaire()
    else:
        st.success("✅ Cuestionario completado")
        
        # Show summary of answers
        with st.expander("Ver respuestas del cuestionario", expanded=False):
            for key, value in st.session_state.questionnaire_answers.items():
                if isinstance(value, list):
                    st.write(f"**{key.replace('_', ' ').title()}:** {', '.join(value)}")
                else:
                    st.write(f"**{key.replace('_', ' ').title()}:** {value}")
        
        # Option to restart questionnaire
        if st.button("🔄 Reiniciar cuestionario"):
            st.session_state.questionnaire_step = 0
            st.session_state.questionnaire_answers = {}
            st.session_state.questionnaire_completed = False
            st.rerun()
        
        # Submit profile to backend
        if st.button("💾 Guardar perfil en el sistema", type="primary"):
            # Convert answers to API format
            profile_data = {}
            for key, value in st.session_state.questionnaire_answers.items():
                if key in ["goals_face", "skin_body", "goals_body", "hair_porosity", "goals_hair", "conditions"]:
                    if isinstance(value, list):
                        profile_data[key] = {item.lower().replace(" ", "_"): True for item in value}
                    else:
                        profile_data[key] = {value.lower().replace(" ", "_"): True}
                else:
                    profile_data[key] = value.lower() if isinstance(value, str) else value
            
            # Submit profile
            result = submit_profile(profile_data)
            if result:
                st.success("¡Perfil guardado exitosamente en el sistema!")
                st.session_state.profile_saved = True
            else:
                st.error("Error al guardar el perfil. Inténtalo de nuevo.")
        
        # Show analysis section after profile is saved
        if st.session_state.get("profile_saved", False):
            st.markdown("---")
            st.markdown("### 📸 Análisis de Productos")
            st.info("Ahora puedes analizar productos subiendo una foto de la etiqueta para recibir recomendaciones personalizadas.")
            
            uploaded_file = st.file_uploader(
                "Sube foto de etiqueta para análisis",
                type=["jpg", "jpeg", "png"],
                help="Utiliza nuestro sistema OCR avanzado para máxima precisión"
            )
            
            if uploaded_file:
                st.success("¡Archivo cargado! Haz clic en 'Analizar' para procesar la imagen.")
                if st.button("🔍 Analizar producto", type="primary"):
                    # Process the uploaded file
                    user_id = st.session_state.auth.get("user", {}).get("id")
                    if user_id:
                        file_bytes = uploaded_file.getvalue()
                        
                        # Show OCR processing status
                        st.info("🔧 Procesando imagen...")
                        with st.spinner("Aplicando análisis OCR avanzado..."):
                            analysis = analyze_routine(user_id, None, file_bytes, uploaded_file.name)
                        
                        if analysis:
                            st.session_state.analysis = analysis
                            rec_items = fetch_recommendations(user_id, None)
                            st.session_state.stored_recommendations = rec_items
                            st.success("✅ Análisis completado con alta precisión")
else:
    st.markdown("---")
    st.info("🔐 Inicia sesión con Gmail para acceder al cuestionario personalizado y recibir recomendaciones adaptadas a tu perfil.")



analysis_result = st.session_state.analysis
if analysis_result:
    render_analysis(analysis_result)

stored_recs = st.session_state.stored_recommendations or []
render_recommendations(stored_recs)



st.markdown("---")
st.caption("MommyShops ©")