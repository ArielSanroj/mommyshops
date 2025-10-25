# MommyShops Frontend

Frontend de la aplicación MommyShops para análisis de productos cosméticos usando Vaadin.

## Características

- **Cuestionario de Personalización**: 9 pasos interactivos para personalizar las recomendaciones
- **Carga de Imágenes**: Soporte para subir imágenes o proporcionar URLs
- **Análisis de Ingredientes**: Visualización detallada de ingredientes y sus riesgos
- **Recomendaciones Personalizadas**: Sugerencias basadas en el perfil del usuario
- **Interfaz Intuitiva**: Diseño moderno y fácil de usar

## Tecnologías

- **Vaadin 24.7.13**: Framework de UI para Java
- **Spring Boot**: Framework de aplicación
- **REST API**: Comunicación con el backend
- **Jackson**: Procesamiento de JSON

## Estructura del Proyecto

```
src/main/java/com/mommyshops/frontend/
├── config/
│   └── RestTemplateConfig.java          # Configuración de REST
├── service/
│   └── UserProfileService.java          # Servicio para comunicación con backend
├── view/
│   ├── MainView.java                    # Vista principal
│   ├── QuestionnaireView.java           # Cuestionario de personalización
│   ├── ImageUploadView.java             # Carga de imágenes
│   ├── ResultsView.java                 # Resultados del análisis
│   └── AboutView.java                   # Página "Acerca de"
└── MommyShopsFrontendApplication.java   # Clase principal
```

## Flujo de la Aplicación

1. **Página Principal**: Presentación y opciones de inicio
2. **Cuestionario**: 9 pasos para personalizar el perfil del usuario
3. **Carga de Imagen**: Subir imagen o proporcionar URL del producto
4. **Análisis**: Procesamiento y análisis de ingredientes
5. **Resultados**: Visualización de resultados personalizados

## Configuración

### Requisitos

- Java 11 o superior
- Maven 3.6 o superior
- Backend de MommyShops ejecutándose en puerto 8080

### Instalación

1. Clonar el repositorio
2. Navegar al directorio `mommyshops-app`
3. Ejecutar `mvn clean install`
4. Ejecutar `mvn spring-boot:run`

### Configuración del Backend

El frontend se conecta al backend en `http://localhost:8080`. Asegúrate de que el backend esté ejecutándose antes de iniciar el frontend.

## Uso

1. Accede a `http://localhost:8081`
2. Completa el cuestionario de personalización
3. Sube una imagen de tu producto cosmético
4. Revisa los resultados y recomendaciones

## API Endpoints

El frontend se comunica con el backend a través de:

- `POST /api/user/profile`: Envío del perfil del usuario
- `POST /api/analysis/analyze-with-profile`: Análisis de producto con perfil

## Desarrollo

### Estructura de Vistas

- **MainView**: Página de inicio con navegación
- **QuestionnaireView**: Cuestionario paso a paso con validación
- **ImageUploadView**: Carga de imágenes y análisis
- **ResultsView**: Visualización de resultados
- **AboutView**: Información sobre la aplicación

### Servicios

- **UserProfileService**: Maneja la comunicación con el backend
- **RestTemplateConfig**: Configuración de REST client

### Personalización

El cuestionario incluye 9 pasos:

1. Información Personal (edad)
2. Tipo de Piel
3. Preocupaciones de Piel
4. Alergias Conocidas
5. Ingredientes a Evitar
6. Preferencias de Producto
7. Presupuesto
8. Frecuencia de Uso
9. Fuentes de Información

## Contribución

1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT.