"""
OpenAPI/Swagger configuration for MommyShops Python API
"""

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Dict, Any
import os

def create_openapi_schema(app: FastAPI) -> Dict[str, Any]:
    """
    Create comprehensive OpenAPI schema for MommyShops API
    """
    
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        
        openapi_schema = get_openapi(
            title="MommyShops API",
            version="3.0.1",
            description="""
            # MommyShops API Documentation
            
            ## Overview
            The MommyShops API provides comprehensive ingredient analysis and product safety evaluation services.
            This API is designed to help users make informed decisions about cosmetic and personal care products.
            
            ## Key Features
            - **Image Analysis**: OCR-based ingredient extraction from product images
            - **Text Analysis**: Direct ingredient list analysis
            - **Safety Evaluation**: Comprehensive safety scoring using multiple databases
            - **AI Recommendations**: AI-powered ingredient alternatives and suggestions
            - **User Management**: Secure authentication and user profile management
            
            ## Authentication
            The API uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header:
            ```
            Authorization: Bearer <your-jwt-token>
            ```
            
            ## Rate Limiting
            - **Standard**: 60 requests per minute
            - **Burst**: 10 requests per minute
            - **Analysis**: 5 requests per minute (slower due to AI processing)
            
            ## Error Handling
            All endpoints return standardized error responses:
            ```json
            {
                "success": false,
                "error": "Error message",
                "error_code": "ERROR_CODE",
                "timestamp": "2024-01-01T00:00:00Z"
            }
            ```
            
            ## Support
            For support and questions, please contact:
            - Email: support@mommyshops.com
            - Documentation: https://docs.mommyshops.com
            - Status: https://status.mommyshops.com
            """,
            routes=app.routes,
            servers=[
                {
                    "url": "http://localhost:8000",
                    "description": "Development server"
                },
                {
                    "url": "https://api.mommyshops.com",
                    "description": "Production server"
                }
            ]
        )
        
        # Add custom schema information
        openapi_schema["info"]["contact"] = {
            "name": "MommyShops Support",
            "email": "support@mommyshops.com",
            "url": "https://mommyshops.com/support"
        }
        
        openapi_schema["info"]["license"] = {
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT"
        }
        
        openapi_schema["info"]["x-logo"] = {
            "url": "https://mommyshops.com/logo.png"
        }
        
        # Add security schemes
        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "JWT token for authentication"
            },
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "API key for service-to-service communication"
            }
        }
        
        # Add global security
        openapi_schema["security"] = [
            {"BearerAuth": []},
            {"ApiKeyAuth": []}
        ]
        
        # Add tags for better organization
        openapi_schema["tags"] = [
            {
                "name": "Authentication",
                "description": "User authentication and authorization endpoints"
            },
            {
                "name": "Analysis",
                "description": "Product and ingredient analysis endpoints"
            },
            {
                "name": "Recommendations",
                "description": "AI-powered recommendations and alternatives"
            },
            {
                "name": "Health",
                "description": "System health and monitoring endpoints"
            },
            {
                "name": "Java Integration",
                "description": "Endpoints optimized for Java backend integration"
            },
            {
                "name": "Ollama AI",
                "description": "AI model endpoints using Ollama"
            },
            {
                "name": "External APIs",
                "description": "External API integration endpoints"
            }
        ]
        
        # Add examples for common requests
        openapi_schema["components"]["examples"] = {
            "ProductAnalysisRequest": {
                "summary": "Product Analysis Request",
                "description": "Example request for product analysis",
                "value": {
                    "text": "Aqua, Glycerin, Hyaluronic Acid, Niacinamide, Retinol",
                    "user_need": "sensitive skin"
                }
            },
            "ProductAnalysisResponse": {
                "summary": "Product Analysis Response",
                "description": "Example response for product analysis",
                "value": {
                    "success": True,
                    "product_name": "Anti-Aging Serum",
                    "ingredients_details": [
                        {
                            "name": "Hyaluronic Acid",
                            "risk_level": "low",
                            "eco_score": 85.0,
                            "benefits": "Hydrating, plumping",
                            "risks_detailed": "None known",
                            "sources": "EWG, FDA"
                        }
                    ],
                    "avg_eco_score": 85.0,
                    "suitability": "excellent",
                    "recommendations": "This product is excellent for sensitive skin",
                    "analysis_id": "analysis_123",
                    "processing_time_ms": 1500
                }
            },
            "ErrorResponse": {
                "summary": "Error Response",
                "description": "Example error response",
                "value": {
                    "success": False,
                    "error": "Invalid input data",
                    "error_code": "INVALID_INPUT",
                    "timestamp": "2024-01-01T00:00:00Z"
                }
            }
        }
        
        # Add response schemas
        openapi_schema["components"]["schemas"]["ProductAnalysisRequest"] = {
            "type": "object",
            "required": ["text"],
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Product ingredients text",
                    "example": "Aqua, Glycerin, Hyaluronic Acid, Niacinamide"
                },
                "user_need": {
                    "type": "string",
                    "description": "User's skin type or concern",
                    "enum": ["sensitive skin", "acne-prone", "anti-aging", "general safety"],
                    "default": "general safety"
                }
            }
        }
        
        openapi_schema["components"]["schemas"]["ProductAnalysisResponse"] = {
            "type": "object",
            "properties": {
                "success": {
                    "type": "boolean",
                    "description": "Whether the analysis was successful"
                },
                "product_name": {
                    "type": "string",
                    "description": "Name of the analyzed product"
                },
                "ingredients_details": {
                    "type": "array",
                    "items": {
                        "$ref": "#/components/schemas/IngredientAnalysis"
                    },
                    "description": "Detailed analysis of each ingredient"
                },
                "avg_eco_score": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 100,
                    "description": "Average eco score of the product"
                },
                "suitability": {
                    "type": "string",
                    "enum": ["excellent", "good", "fair", "poor", "not recommended"],
                    "description": "Overall suitability for the user"
                },
                "recommendations": {
                    "type": "string",
                    "description": "Personalized recommendations"
                },
                "analysis_id": {
                    "type": "string",
                    "description": "Unique identifier for this analysis"
                },
                "processing_time_ms": {
                    "type": "integer",
                    "description": "Processing time in milliseconds"
                },
                "error": {
                    "type": "string",
                    "description": "Error message if analysis failed"
                }
            }
        }
        
        openapi_schema["components"]["schemas"]["IngredientAnalysis"] = {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Ingredient name"
                },
                "risk_level": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "unknown"],
                    "description": "Risk level of the ingredient"
                },
                "eco_score": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 100,
                    "description": "Eco score of the ingredient"
                },
                "benefits": {
                    "type": "string",
                    "description": "Benefits of the ingredient"
                },
                "risks_detailed": {
                    "type": "string",
                    "description": "Detailed risk information"
                },
                "sources": {
                    "type": "string",
                    "description": "Data sources used for analysis"
                }
            }
        }
        
        # Add health check schema
        openapi_schema["components"]["schemas"]["HealthResponse"] = {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["healthy", "unhealthy", "degraded"],
                    "description": "Overall system status"
                },
                "timestamp": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Health check timestamp"
                },
                "service": {
                    "type": "string",
                    "description": "Service name"
                },
                "version": {
                    "type": "string",
                    "description": "Service version"
                },
                "components": {
                    "type": "object",
                    "description": "Individual component health status"
                }
            }
        }
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    
    return custom_openapi

def add_cors_middleware(app: FastAPI):
    """
    Add CORS middleware for API documentation
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

def add_custom_docs_endpoints(app: FastAPI):
    """
    Add custom documentation endpoints
    """
    
    @app.get("/docs/health", tags=["Health"])
    async def docs_health():
        """
        Health check endpoint for documentation
        """
        return {"status": "healthy", "service": "docs"}
    
    @app.get("/docs/status", tags=["Health"])
    async def docs_status():
        """
        Documentation status endpoint
        """
        return {
            "docs_available": True,
            "openapi_version": "3.0.1",
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_json": "/openapi.json"
        }
