# Bugs Críticos Identificados y Corregidos

## 1. ✅ CORREGIDO: ddl-auto=create (Destruye datos en producción)

**Archivo**: `mommyshops-app/src/main/resources/application.properties`

**Antes**:
```properties
spring.jpa.hibernate.ddl-auto=create
```

**Después**:
```properties
spring.jpa.hibernate.ddl-auto=validate
```

**Impacto**: CRÍTICO - Evita pérdida de datos en producción

---

## 2. 🔴 PENDIENTE: Dual-write a PostgreSQL y Firebase

**Problema**: El código escribe simultáneamente a PostgreSQL y Firebase sin transacciones coordinadas, causando inconsistencias.

**Ubicación**: `main.py` líneas 2317-2605

**Solución Propuesta**:
```python
# Implementar patrón Saga o Event Sourcing
# Opción 1: Usar PostgreSQL como fuente de verdad, sincronizar a Firebase async
# Opción 2: Eliminar Firebase para datos transaccionales, usar solo para auth
```

**Archivos a modificar**:
- `main.py` - Eliminar dual-write
- `database.py` - Consolidar en PostgreSQL
- Crear `firebase_sync_service.py` para sincronización asíncrona

---

## 3. 🔴 PENDIENTE: Rate Limiting no implementado

**Problema**: No hay rate limiting en endpoints públicos, vulnerable a DDoS.

**Solución**:
```java
// En Java Spring Boot
@Configuration
public class RateLimitConfig {
    @Bean
    public RateLimiter rateLimiter() {
        return RateLimiter.create(100.0); // 100 requests/second
    }
}
```

```python
# En Python FastAPI
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/analyze-image")
@limiter.limit("10/minute")
async def analyze_image(...):
    pass
```

**Archivos a crear**:
- `mommyshops-app/src/main/java/com/mommyshops/config/RateLimitConfig.java`
- `backend/middleware/rate_limit.py`

---

## 4. 🔴 PENDIENTE: Secrets en logs

**Problema**: Variables sensibles se logean en `/debug/env`

**Ubicación**: `main.py` línea 3331

**Solución**:
```python
@app.get("/debug/env")
async def debug_environment():
    env_vars = {}
    SENSITIVE_KEYS = ['PASSWORD', 'SECRET', 'KEY', 'TOKEN', 'API_KEY']
    
    for key, value in os.environ.items():
        if any(sensitive in key.upper() for sensitive in SENSITIVE_KEYS):
            env_vars[key] = "***REDACTED***"
        else:
            env_vars[key] = value
    
    return {"environment": env_vars}
```

---

## 5. 🔴 PENDIENTE: SQL Injection en queries dinámicas

**Problema**: Uso de f-strings en queries SQL

**Ubicación**: `database.py` múltiples funciones

**Solución**:
```python
# MAL
query = f"SELECT * FROM ingredients WHERE name = '{ingredient_name}'"

# BIEN
query = "SELECT * FROM ingredients WHERE name = :name"
result = db.execute(query, {"name": ingredient_name})
```

---

## 6. 🔴 PENDIENTE: CORS configurado con allow_origins=["*"]

**Problema**: CORS demasiado permisivo en producción

**Ubicación**: `main.py` línea 476

**Solución**:
```python
# Usar variable de entorno
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

---

## 7. 🔴 PENDIENTE: Passwords no hasheadas correctamente

**Problema**: En algunos lugares se guarda password directamente

**Ubicación**: `main.py` línea 2140

**Solución**:
```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Al crear usuario
hashed_password = pwd_context.hash(password)
user.hashed_password = hashed_password

# Al verificar
if not pwd_context.verify(password, user.hashed_password):
    raise HTTPException(status_code=401, detail="Invalid credentials")
```

---

## Prioridad de Corrección

1. **CRÍTICO** (Corregir inmediatamente):
   - ✅ ddl-auto=create
   - 🔴 Passwords no hasheadas
   - 🔴 SQL Injection

2. **ALTO** (Corregir antes de producción):
   - 🔴 CORS permisivo
   - 🔴 Secrets en logs
   - 🔴 Rate limiting

3. **MEDIO** (Refactorización arquitectónica):
   - 🔴 Dual-write PostgreSQL/Firebase
