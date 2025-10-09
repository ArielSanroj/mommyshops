# 🔧 Configuración de Google OAuth en Railway

## Problema
La API está devolviendo "Not Found" para `/auth/google` porque las variables de entorno de Google OAuth no están configuradas en Railway.

## Solución

### 1. Configurar Variables de Entorno en Railway

1. Ve a tu dashboard de Railway: https://railway.app/dashboard
2. Selecciona tu proyecto "mommyshops"
3. Ve a la pestaña "Variables"
4. Agrega las siguientes variables de entorno:

```
GOOGLE_CLIENT_ID=tu-google-client-id-aqui
GOOGLE_CLIENT_SECRET=tu-google-client-secret-aqui
GOOGLE_REDIRECT_URI=https://web-production-f23a5.up.railway.app/auth/google/callback
RAILWAY_ENVIRONMENT=true
```

### 2. Obtener las Credenciales de Google

Si no tienes las credenciales de Google OAuth:

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Selecciona tu proyecto
3. Ve a **APIs & Services** > **Credentials**
4. Crea un nuevo **OAuth 2.0 Client ID** si no tienes uno
5. Configura los **Authorized redirect URIs**:
   - `http://localhost:8000/auth/google/callback` (para desarrollo)
   - `https://web-production-f23a5.up.railway.app/auth/google/callback` (para producción)

### 3. Verificar la Configuración

Después de configurar las variables de entorno:

1. Railway desplegará automáticamente los cambios
2. Verifica que la API esté funcionando:
   ```bash
   curl https://web-production-f23a5.up.railway.app/auth/google
   ```
3. Debería devolver una respuesta JSON con `auth_url`

### 4. Probar el Flujo Completo

1. Ve a tu aplicación frontend
2. Haz clic en "🔐 Iniciar con Gmail"
3. Debería redirigirte a Google para autenticación
4. Después de autenticarte, debería regresar a tu aplicación

## Variables de Entorno Requeridas

```
GOOGLE_CLIENT_ID=tu-client-id
GOOGLE_CLIENT_SECRET=tu-client-secret
GOOGLE_REDIRECT_URI=https://web-production-f23a5.up.railway.app/auth/google/callback
RAILWAY_ENVIRONMENT=true
```

## Troubleshooting

Si sigues teniendo problemas:

1. **Verifica las variables de entorno** en Railway dashboard
2. **Revisa los logs** de Railway para errores
3. **Prueba la API directamente** con curl
4. **Verifica que las credenciales de Google** estén correctas

## Notas Importantes

- Las credenciales de Google OAuth son sensibles, no las compartas
- Asegúrate de que el redirect URI en Google Console coincida exactamente con el de Railway
- Railway puede tardar unos minutos en aplicar los cambios de variables de entorno