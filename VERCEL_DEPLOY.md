# 🚀 Vercel Deployment Guide

## Configuración para Deploy en Vercel

### 1. Conectar Repositorio a Vercel

1. Ve a [vercel.com](https://vercel.com) e inicia sesión
2. Haz clic en "Add New Project"
3. Conecta tu repositorio de GitHub `ArielSanroj/mommyshops`
4. Vercel detectará automáticamente la configuración desde `vercel.json`

### 2. Configuración del Proyecto

**Framework Preset:** Otro (Static HTML)

**Root Directory:** `/` (raíz del proyecto)

**Build Command:** (dejar vacío - no se necesita build)

**Output Directory:** (dejar vacío - Vercel servirá `frontend.html` directamente)

### 3. Variables de Entorno

En el dashboard de Vercel, ve a **Settings > Environment Variables** y agrega:

```
API_URL=https://tu-backend-api.com
```

O si tu backend está en otro servicio (Railway, Render, etc.):

```
API_URL=https://mommyshops-backend.railway.app
```

**Nota:** El frontend detectará automáticamente si está en localhost y usará `http://localhost:8000` para desarrollo local.

### 4. Deploy

Una vez configurado:

1. Vercel hará deploy automáticamente en cada push a `main`
2. O puedes hacer deploy manual desde el dashboard
3. Vercel te dará una URL como: `https://mommyshops.vercel.app`

### 5. Configuración de Dominio Personalizado (Opcional)

1. Ve a **Settings > Domains**
2. Agrega tu dominio personalizado
3. Sigue las instrucciones de DNS que Vercel te proporciona

### 6. Verificación Post-Deploy

Después del deploy, verifica:

- ✅ El frontend carga correctamente
- ✅ Las llamadas a la API funcionan (verifica la consola del navegador)
- ✅ Si hay errores CORS, configura CORS en tu backend para permitir el dominio de Vercel

### 7. Troubleshooting

**Error: API no responde**
- Verifica que `API_URL` esté configurada correctamente en Vercel
- Verifica que tu backend esté corriendo y accesible
- Verifica CORS en el backend

**Error: 404 en rutas**
- El `vercel.json` está configurado para servir `frontend.html` en todas las rutas
- Si persiste, verifica la configuración de routing en Vercel

**Error: Variables de entorno no funcionan**
- Las variables de entorno en Vercel están disponibles en tiempo de build
- Para variables en runtime, usa `window.API_URL` o configura un script de inyección

### 8. Estructura de Archivos

```
/
├── frontend.html          # Frontend principal
├── vercel.json            # Configuración de Vercel
├── .vercelignore          # Archivos excluidos del deploy
└── ...
```

### 9. Próximos Pasos

- [ ] Configurar backend en producción (Railway, Render, etc.)
- [ ] Agregar dominio personalizado
- [ ] Configurar SSL/HTTPS (automático en Vercel)
- [ ] Configurar monitoreo y analytics

