# Actualizar Backend en Ngrok

## Pasos para actualizar el backend con el endpoint de leads

### 1. Verificar que el código esté actualizado
```bash
cd /Users/arielsanroj/PycharmProjects/mommyshops
git pull origin main
```

### 2. Detener el servidor backend actual
```bash
# Buscar el proceso
ps aux | grep uvicorn

# Detener el proceso (reemplaza PID con el número del proceso)
kill <PID>
```

### 3. Iniciar el servidor backend con el código actualizado
```bash
cd backend-python
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

O si tienes un entorno virtual:
```bash
cd backend-python
source .venv/bin/activate  # o el nombre de tu venv
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Verificar que el endpoint esté disponible
En otra terminal:
```bash
curl -X POST http://localhost:8000/leads \
  -H "Content-Type: application/json" \
  -d '{"first_name":"Test","last_name":"User","email":"test@test.com","country":"mx"}'
```

Deberías recibir una respuesta JSON con los datos del lead creado.

### 5. Verificar que ngrok esté apuntando al puerto 8000
```bash
# Verificar que ngrok esté corriendo
ps aux | grep ngrok

# Si ngrok está corriendo, debería estar apuntando a localhost:8000
# Si no está corriendo, inícialo:
ngrok http 8000
```

### 6. Actualizar vercel.json si la URL de ngrok cambió
Si ngrok te da una nueva URL, actualiza `vercel.json`:
```json
{
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "https://TU-NUEVA-URL-NGROK.ngrok-free.dev/$1"
    }
  ]
}
```

### 7. Verificar en producción
Después de hacer push de los cambios a Vercel, prueba el formulario en:
https://mommyshopslabs.vercel.app/

## Troubleshooting

### El endpoint no responde
- Verifica que el servidor esté corriendo: `curl http://localhost:8000/health`
- Verifica los logs del servidor para ver errores
- Asegúrate de que el archivo `backend-python/app/routers/leads.py` exista

### Ngrok no funciona
- Verifica que ngrok esté corriendo: `ps aux | grep ngrok`
- Verifica que ngrok esté apuntando al puerto correcto (8000)
- Reinicia ngrok si es necesario

### Error de CORS
- El backend ya tiene CORS configurado para permitir el dominio de Vercel
- Si persiste, verifica la configuración en `backend-python/app/middleware/cors.py`

