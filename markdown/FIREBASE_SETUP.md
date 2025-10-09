# Firebase Setup para MommyShops

## Configuración de Firebase

### 1. Crear un proyecto en Firebase

1. Ve a [Firebase Console](https://console.firebase.google.com/)
2. Crea un nuevo proyecto o selecciona uno existente
3. Habilita Authentication y Firestore Database

### 2. Configurar Authentication

1. En Firebase Console, ve a Authentication > Sign-in method
2. Habilita "Email/Password" como método de autenticación
3. Opcionalmente, habilita otros métodos como Google, Facebook, etc.

### 3. Configurar Firestore Database

1. En Firebase Console, ve a Firestore Database
2. Crea una base de datos en modo de producción
3. Configura las reglas de seguridad:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Users can read/write their own data
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    
    // Analysis results are private to each user
    match /analysis_results/{document} {
      allow read, write: if request.auth != null && request.auth.uid == resource.data.user_id;
    }
  }
}
```

### 4. Generar credenciales de servicio

1. En Firebase Console, ve a Project Settings > Service Accounts
2. Haz clic en "Generate new private key"
3. Descarga el archivo JSON
4. Renómbralo a `firebase-service-account.json`
5. Colócalo en la raíz del proyecto

### 5. Configurar variables de entorno

Crea un archivo `.env` basado en `.env.example`:

```bash
# Firebase Configuration
FIREBASE_SERVICE_ACCOUNT_PATH="firebase-service-account.json"
```

O alternativamente, puedes usar la variable de entorno `FIREBASE_CREDENTIALS` con el contenido JSON del archivo de credenciales.

### 6. Estructura de datos en Firestore

#### Colección: `users`
```json
{
  "uid": "user_id_from_firebase_auth",
  "username": "usuario123",
  "email": "usuario@ejemplo.com",
  "created_at": "timestamp",
  "updated_at": "timestamp",
  "profile": {
    "skin_face": "Seca",
    "hair_type": "Liso",
    "goals_face": ["Hidratar", "Prevenir arrugas"],
    "climate": "Húmedo",
    "skin_body": ["Seca"],
    "goals_body": ["Hidratar"],
    "hair_porosity": ["Media porosidad"],
    "goals_hair": {
      "Reducir frizz": 4,
      "Dar volumen": 3
    },
    "hair_thickness_scalp": {
      "thickness": ["Medio"],
      "scalp": ["Normal"]
    },
    "conditions": ["Ninguna"],
    "other_condition": "",
    "products": ["La Roche-Posay Anthelios"]
  }
}
```

#### Colección: `analysis_results`
```json
{
  "user_id": "user_id_from_firebase_auth",
  "analysis": {
    "routine_id": "generated_id",
    "analysis": {
      "recommendations": "...",
      "products": [...],
      "substitutes": [...]
    }
  },
  "created_at": "timestamp"
}
```

### 7. Verificar la configuración

1. Ejecuta la aplicación: `streamlit run frontend.py --server.port 8507`
2. Intenta registrar un nuevo usuario
3. Verifica en Firebase Console que el usuario aparece en Authentication
4. Verifica en Firestore que se creó el documento del usuario

### 8. Solución de problemas

#### Error: "Firebase Admin SDK not initialized"
- Verifica que el archivo `firebase-service-account.json` existe y es válido
- Verifica que las credenciales son correctas

#### Error: "Permission denied"
- Verifica las reglas de seguridad de Firestore
- Asegúrate de que el usuario está autenticado

#### Error: "User not found"
- Verifica que el usuario existe en Firebase Authentication
- Verifica que el email es correcto

### 9. Características implementadas

- ✅ Registro de usuarios con Firebase Auth
- ✅ Inicio de sesión con Firebase Auth
- ✅ Almacenamiento de perfiles en Firestore
- ✅ Actualización de perfiles
- ✅ Almacenamiento de resultados de análisis
- ✅ Historial de análisis por usuario
- ✅ Integración con OCR mejorado
- ✅ Detección automática de backend local vs Railway

### 10. Próximos pasos

- [ ] Implementar autenticación con Google/Facebook
- [ ] Agregar recuperación de contraseña
- [ ] Implementar notificaciones push
- [ ] Agregar roles de usuario (admin, premium, etc.)
- [ ] Implementar analytics de uso