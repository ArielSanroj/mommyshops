# Firebase Integration for MommyShops

Esta documentación explica cómo usar la integración de Firebase en MommyShops, incluyendo Firebase Auth y Firestore para el manejo de usuarios.

## Configuración

### 1. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar Credenciales de Firebase

Tienes tres opciones para configurar las credenciales de Firebase:

#### Opción A: Archivo de Service Account
1. Descarga el archivo JSON de service account desde Firebase Console
2. Colócalo en la raíz del proyecto (ej: `firebase-service-account.json`)
3. Configura la variable de entorno:
```bash
export FIREBASE_SERVICE_ACCOUNT_PATH="firebase-service-account.json"
```

#### Opción B: Variable de Entorno JSON
```bash
export FIREBASE_CREDENTIALS='{"type":"service_account","project_id":"tu-proyecto",...}'
```

#### Opción C: Google Application Default Credentials
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/ruta/a/tu-service-account-key.json"
```

### 3. Configurar Variables de Entorno

Copia `.env.example` a `.env` y configura las variables necesarias:

```bash
cp .env.example .env
```

Edita `.env` con tus credenciales de Firebase.

## Endpoints de Firebase

### Registro de Usuario

**POST** `/firebase/register`

Registra un nuevo usuario en Firebase Auth y crea su perfil en Firestore.

```json
{
  "email": "usuario@ejemplo.com",
  "password": "password123",
  "name": "Nombre Usuario",
  "skin_face": "seca",
  "hair_type": "rizado",
  "goals_face": "[\"hidratar\", \"anti-edad\"]",
  "climate": "seco",
  "skin_body": "[\"normal\"]",
  "goals_body": "[\"hidratar\"]",
  "hair_porosity": "[\"baja\"]",
  "goals_hair": "{\"hidratar\": 5, \"definir\": 4}",
  "hair_thickness_scalp": "{\"thickness\": [\"fino\"], \"scalp\": [\"normal\"]}",
  "conditions": "[\"acné\"]"
}
```

**Respuesta:**
```json
{
  "uid": "firebase-user-uid",
  "email": "usuario@ejemplo.com",
  "message": "User registered successfully. Please check your email for verification."
}
```

### Login de Usuario

**POST** `/firebase/login`

Autentica un usuario y devuelve su perfil.

```json
{
  "email": "usuario@ejemplo.com",
  "password": "password123"
}
```

**Respuesta:**
```json
{
  "uid": "firebase-user-uid",
  "email": "usuario@ejemplo.com",
  "name": "Nombre Usuario",
  "custom_token": "custom-token-for-client-auth",
  "message": "Login successful"
}
```

### Obtener Perfil de Usuario

**GET** `/firebase/user/{uid}`

Obtiene el perfil completo de un usuario desde Firestore.

**Respuesta:**
```json
{
  "uid": "firebase-user-uid",
  "email": "usuario@ejemplo.com",
  "name": "Nombre Usuario",
  "skin_face": "seca",
  "hair_type": "rizado",
  "goals_face": {"hidratar": true, "anti-edad": true},
  "climate": "seco",
  "skin_body": {"normal": true},
  "goals_body": {"hidratar": true},
  "hair_porosity": {"baja": true},
  "goals_hair": {"hidratar": 5, "definir": 4},
  "hair_thickness_scalp": {"thickness": ["fino"], "scalp": ["normal"]},
  "conditions": {"acné": true},
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### Actualizar Perfil de Usuario

**PUT** `/firebase/user/{uid}`

Actualiza el perfil de un usuario en Firestore.

```json
{
  "name": "Nuevo Nombre",
  "skin_face": "mixta",
  "goals_face": "[\"hidratar\", \"anti-edad\", \"iluminar\"]"
}
```

### Eliminar Usuario

**DELETE** `/firebase/user/{uid}`

Elimina un usuario de Firebase Auth y Firestore.

**Respuesta:**
```json
{
  "message": "User deleted successfully"
}
```

## Migración desde SQLite

### Ejecutar Migración

```bash
# Migración completa
python migrate_to_firebase.py --sqlite-path dev_sqlite.db

# Dry run (solo mostrar qué se migraría)
python migrate_to_firebase.py --sqlite-path dev_sqlite.db --dry-run

# Con logging verbose
python migrate_to_firebase.py --sqlite-path dev_sqlite.db --verbose
```

### Parámetros del Script de Migración

- `--sqlite-path`: Ruta al archivo de base de datos SQLite (default: `dev_sqlite.db`)
- `--dry-run`: Ejecuta sin migrar datos reales
- `--verbose`: Habilita logging detallado

## Estructura de Datos en Firestore

### Colección: `users`

Cada documento representa un usuario con el siguiente esquema:

```json
{
  "uid": "string",           // UID de Firebase Auth
  "email": "string",         // Email del usuario
  "name": "string",          // Nombre del usuario
  "skin_face": "string",     // Tipo de piel facial
  "hair_type": "string",     // Tipo de cabello
  "goals_face": "object",    // Objetivos faciales (JSON)
  "climate": "string",       // Clima
  "skin_body": "object",     // Piel corporal (JSON)
  "goals_body": "object",    // Objetivos corporales (JSON)
  "hair_porosity": "object", // Porosidad del cabello (JSON)
  "goals_hair": "object",    // Objetivos del cabello (JSON)
  "hair_thickness_scalp": "object", // Grosor y cuero cabelludo (JSON)
  "conditions": "object",    // Condiciones médicas (JSON)
  "created_at": "timestamp", // Timestamp de creación
  "updated_at": "timestamp"  // Timestamp de última actualización
}
```

## Seguridad

### Reglas de Firestore

Configura las siguientes reglas de seguridad en Firebase Console:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Los usuarios solo pueden acceder a su propio documento
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
  }
}
```

### Autenticación

- Firebase Auth maneja la autenticación de usuarios
- Los tokens JWT se generan para autenticación del lado del servidor
- Los custom tokens se generan para autenticación del lado del cliente

## Manejo de Errores

### Códigos de Estado HTTP

- `200`: Operación exitosa
- `400`: Error en la solicitud (email ya registrado, datos inválidos)
- `401`: No autorizado (credenciales inválidas)
- `404`: Usuario no encontrado
- `500`: Error interno del servidor
- `503`: Firebase no disponible

### Logging

El sistema registra todos los eventos importantes:
- Creación de usuarios
- Errores de autenticación
- Fallos en Firestore
- Errores de migración

## Testing

### Probar la Integración

1. **Iniciar el servidor:**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

2. **Probar registro:**
```bash
curl -X POST "http://localhost:8000/firebase/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@ejemplo.com",
    "password": "password123",
    "name": "Usuario Test"
  }'
```

3. **Probar login:**
```bash
curl -X POST "http://localhost:8000/firebase/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@ejemplo.com",
    "password": "password123"
  }'
```

4. **Verificar en Firebase Console:**
   - Ve a Authentication > Users para ver usuarios creados
   - Ve a Firestore > Data > users para ver perfiles

## Troubleshooting

### Problemas Comunes

1. **Error 503 - Firebase not available**
   - Verifica que las credenciales estén configuradas correctamente
   - Asegúrate de que el archivo de service account existe y es válido

2. **Error 400 - Email already registered**
   - El email ya existe en Firebase Auth
   - Usa un email diferente o elimina el usuario existente

3. **Error de migración**
   - Verifica que la base de datos SQLite existe y es accesible
   - Revisa los logs para errores específicos

4. **Error de Firestore**
   - Verifica que las reglas de seguridad permiten la operación
   - Asegúrate de que el proyecto de Firebase esté configurado correctamente

### Logs

Los logs se muestran en la consola con el formato:
```
2024-01-01 12:00:00 - firebase_config - INFO - Firebase Admin SDK initialized successfully
```

Para debugging, habilita logging verbose:
```bash
export LOG_LEVEL=DEBUG
```