package com.mommyshops.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.info.Contact;
import io.swagger.v3.oas.models.info.License;
import io.swagger.v3.oas.models.servers.Server;
import io.swagger.v3.oas.models.tags.Tag;
import io.swagger.v3.oas.models.Components;
import io.swagger.v3.oas.models.security.SecurityScheme;
import io.swagger.v3.oas.models.security.SecurityRequirement;
import io.swagger.v3.oas.models.examples.Example;
import io.swagger.v3.oas.models.media.MediaType;
import io.swagger.v3.oas.models.media.Schema;
import io.swagger.v3.oas.models.media.StringSchema;
import io.swagger.v3.oas.models.media.NumberSchema;
import io.swagger.v3.oas.models.media.BooleanSchema;
import io.swagger.v3.oas.models.media.ArraySchema;
import io.swagger.v3.oas.models.media.ObjectSchema;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.List;
import java.util.Map;

/**
 * Swagger/OpenAPI configuration for MommyShops Java API
 */
@Configuration
public class SwaggerConfig {

    @Bean
    public OpenAPI customOpenAPI() {
        return new OpenAPI()
                .info(new Info()
                        .title("MommyShops API")
                        .version("3.0.1")
                        .description("""
                                # MommyShops API Documentation
                                
                                ## Overview
                                The MommyShops API provides comprehensive ingredient analysis and product safety evaluation services.
                                This API is designed to help users make informed decisions about cosmetic and personal care products.
                                
                                ## Key Features
                                - **Product Analysis**: Comprehensive analysis of cosmetic products
                                - **Ingredient Safety**: Detailed safety evaluation using multiple databases
                                - **AI Recommendations**: AI-powered ingredient alternatives and suggestions
                                - **User Management**: Secure authentication and user profile management
                                - **Integration**: Seamless integration with Python AI services
                                
                                ## Authentication
                                The API uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header:
                                ```
                                Authorization: Bearer <your-jwt-token>
                                ```
                                
                                ## Rate Limiting
                                - **Standard**: 60 requests per minute
                                - **Analysis**: 5 requests per minute (slower due to AI processing)
                                - **Burst**: 10 requests per minute
                                
                                ## Error Handling
                                All endpoints return standardized error responses:
                                ```json
                                {
                                    "success": false,
                                    "error": "Error message",
                                    "errorCode": "ERROR_CODE",
                                    "timestamp": "2024-01-01T00:00:00Z"
                                }
                                ```
                                
                                ## Support
                                For support and questions, please contact:
                                - Email: support@mommyshops.com
                                - Documentation: https://docs.mommyshops.com
                                - Status: https://status.mommyshops.com
                                """)
                        .contact(new Contact()
                                .name("MommyShops Support")
                                .email("support@mommyshops.com")
                                .url("https://mommyshops.com/support"))
                        .license(new License()
                                .name("MIT")
                                .url("https://opensource.org/licenses/MIT")))
                .servers(List.of(
                        new Server()
                                .url("http://localhost:8080")
                                .description("Development server"),
                        new Server()
                                .url("https://api.mommyshops.com")
                                .description("Production server")
                ))
                .tags(List.of(
                        new Tag()
                                .name("Product Analysis")
                                .description("Product and ingredient analysis endpoints"),
                        new Tag()
                                .name("Substitution")
                                .description("Ingredient substitution and alternatives"),
                        new Tag()
                                .name("Health")
                                .description("System health and monitoring endpoints"),
                        new Tag()
                                .name("Integration")
                                .description("External API integration endpoints"),
                        new Tag()
                                .name("Authentication")
                                .description("User authentication and authorization")
                ))
                .components(new Components()
                        .addSecuritySchemes("BearerAuth", new SecurityScheme()
                                .type(SecurityScheme.Type.HTTP)
                                .scheme("bearer")
                                .bearerFormat("JWT")
                                .description("JWT token for authentication"))
                        .addSecuritySchemes("ApiKeyAuth", new SecurityScheme()
                                .type(SecurityScheme.Type.APIKEY)
                                .in(SecurityScheme.In.HEADER)
                                .name("X-API-Key")
                                .description("API key for service-to-service communication"))
                        .addExamples("ProductAnalysisRequest", new Example()
                                .summary("Product Analysis Request")
                                .description("Example request for product analysis")
                                .value(Map.of(
                                        "text", "Aqua, Glycerin, Hyaluronic Acid, Niacinamide, Retinol",
                                        "userNeed", "sensitive skin"
                                )))
                        .addExamples("ProductAnalysisResponse", new Example()
                                .summary("Product Analysis Response")
                                .description("Example response for product analysis")
                                .value(Map.of(
                                        "success", true,
                                        "productName", "Anti-Aging Serum",
                                        "ingredientsDetails", List.of(Map.of(
                                                "name", "Hyaluronic Acid",
                                                "riskLevel", "low",
                                                "ecoScore", 85.0,
                                                "benefits", "Hydrating, plumping",
                                                "risksDetailed", "None known",
                                                "sources", "EWG, FDA"
                                        )),
                                        "avgEcoScore", 85.0,
                                        "suitability", "excellent",
                                        "recommendations", "This product is excellent for sensitive skin",
                                        "analysisId", "analysis_123",
                                        "processingTimeMs", 1500
                                )))
                        .addExamples("ErrorResponse", new Example()
                                .summary("Error Response")
                                .description("Example error response")
                                .value(Map.of(
                                        "success", false,
                                        "error", "Invalid input data",
                                        "errorCode", "INVALID_INPUT",
                                        "timestamp", "2024-01-01T00:00:00Z"
                                )))
                        .addSchemas("ProductAnalysisRequest", new Schema<>()
                                .type("object")
                                .required(List.of("text"))
                                .addProperty("text", new StringSchema()
                                        .description("Product ingredients text to analyze")
                                        .example("Aqua, Glycerin, Hyaluronic Acid, Niacinamide")
                                        .minLength(1)
                                        .maxLength(10000))
                                .addProperty("userNeed", new StringSchema()
                                        .description("User's skin type or concern")
                                        .example("sensitive skin")
                                        ._enum(List.of("sensitive skin", "acne-prone", "anti-aging", "general safety"))
                                        .defaultValue("general safety")))
                        .addSchemas("IngredientAnalysis", new Schema<>()
                                .type("object")
                                .addProperty("name", new StringSchema()
                                        .description("Ingredient name"))
                                .addProperty("riskLevel", new StringSchema()
                                        .description("Risk level")
                                        ._enum(List.of("low", "medium", "high", "unknown")))
                                .addProperty("ecoScore", new NumberSchema()
                                        .description("Eco score (0-100)")
                                        .minimum(0.0)
                                        .maximum(100.0))
                                .addProperty("benefits", new StringSchema()
                                        .description("Benefits of the ingredient"))
                                .addProperty("risksDetailed", new StringSchema()
                                        .description("Detailed risk information"))
                                .addProperty("sources", new StringSchema()
                                        .description("Data sources used")))
                        .addSchemas("ProductAnalysisResponse", new Schema<>()
                                .type("object")
                                .addProperty("success", new BooleanSchema()
                                        .description("Whether the analysis was successful"))
                                .addProperty("productName", new StringSchema()
                                        .description("Name of the analyzed product"))
                                .addProperty("ingredientsDetails", new ArraySchema()
                                        .items(new Schema<>().$ref("#/components/schemas/IngredientAnalysis"))
                                        .description("Detailed analysis of each ingredient"))
                                .addProperty("avgEcoScore", new NumberSchema()
                                        .description("Average eco score")
                                        .minimum(0.0)
                                        .maximum(100.0))
                                .addProperty("suitability", new StringSchema()
                                        .description("Overall suitability")
                                        ._enum(List.of("excellent", "good", "fair", "poor", "not recommended")))
                                .addProperty("recommendations", new StringSchema()
                                        .description("Personalized recommendations"))
                                .addProperty("analysisId", new StringSchema()
                                        .description("Unique identifier for this analysis"))
                                .addProperty("processingTimeMs", new NumberSchema()
                                        .description("Processing time in milliseconds"))
                                .addProperty("error", new StringSchema()
                                        .description("Error message if analysis failed")))
                        .addSchemas("HealthResponse", new Schema<>()
                                .type("object")
                                .addProperty("status", new StringSchema()
                                        .description("Overall system status")
                                        ._enum(List.of("healthy", "unhealthy", "degraded")))
                                .addProperty("timestamp", new StringSchema()
                                        .description("Health check timestamp"))
                                .addProperty("service", new StringSchema()
                                        .description("Service name"))
                                .addProperty("version", new StringSchema()
                                        .description("Service version"))
                                .addProperty("components", new ObjectSchema()
                                        .description("Individual component health status"))))
                .addSecurityItem(new SecurityRequirement().addList("BearerAuth"))
                .addSecurityItem(new SecurityRequirement().addList("ApiKeyAuth"));
    }
}
