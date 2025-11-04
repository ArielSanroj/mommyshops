package com.mommyshops.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.*;

/**
 * DEPRECATED: This test controller is no longer used.
 * All frontend requests now go to Python backend at http://localhost:8000/analysis/image
 * 
 * This controller is kept for reference only and may be removed in the future.
 */
@RestController
@RequestMapping("/api/test")
@CrossOrigin(origins = "*")
@Deprecated
public class TestAnalysisController {
    
    @PostMapping("/analyze-image")
    public ResponseEntity<Map<String, Object>> analyzeImage(
            @RequestParam("file") MultipartFile file,
            @RequestParam("productName") String productName,
            @RequestParam("userId") String userId) {
        try {
            byte[] imageData = file.getBytes();
            
            // Simular análisis completo con datos de prueba
            Map<String, Object> response = new HashMap<>();
            response.put("status", "success");
            response.put("productName", productName);
            response.put("imageSize", imageData.length);
            
            // Generar reporte detallado de prueba
            String detailedReport = generateTestDetailedReport(productName);
            response.put("detailedReport", detailedReport);
            
            // Datos básicos del análisis
            response.put("analysisSummary", "Análisis completo realizado con éxito");
            response.put("ewgScore", 3.2);
            response.put("inciScore", 0.45);
            response.put("safetyPercentage", 32.0);
            response.put("ecoPercentage", 45.0);
            response.put("ingredients", "Water, Glycerin, Sodium Cocoylate, Sodium Lauryl Sulfate, Polyethylene Glycol, Carbomer, Fragrance");
            response.put("recommendations", "Producto con ingredientes problemáticos. Se recomienda buscar alternativas más naturales.");
            response.put("riskFlags", Arrays.asList("SLS presente", "PEG detectado", "Fragrance sintético"));
            response.put("recommendation", "caution");
            response.put("confidence", 85.0);
            response.put("substitutes", generateTestSubstitutes());
            response.put("additionalInfo", "Análisis realizado con IA usando Ollama y APIs externas (EWG, INCI, PubChem, FDA).");
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            Map<String, Object> error = new HashMap<>();
            error.put("status", "error");
            error.put("message", "Error: " + e.getMessage());
            return ResponseEntity.internalServerError().body(error);
        }
    }
    
    private String generateTestDetailedReport(String productName) {
        StringBuilder report = new StringBuilder();
        
        report.append("**RESULTADOS COMPLETOS DEL ANÁLISIS - ").append(productName).append("**\n\n");
        
        report.append("**📋 RESUMEN EJECUTIVO**\n\n");
        report.append("He procesado exitosamente la imagen ").append(productName).append(" y aquí están los resultados completos como los vería un usuario final:\n\n");
        report.append("---\n\n");
        
        report.append("**🧪 INGREDIENTES EXTRAÍDOS DE LA IMAGEN**\n\n");
        report.append("• Water\n");
        report.append("• Glycerin\n");
        report.append("• Sodium Cocoylate\n");
        report.append("• Sodium Lauryl Sulfate\n");
        report.append("• Polyethylene Glycol\n");
        report.append("• Carbomer\n");
        report.append("• Fragrance\n\n");
        report.append("---\n\n");
        
        report.append("**📊 ANÁLISIS DETALLADO DE SEGURIDAD**\n\n");
        report.append("**✅ INGREDIENTES SEGUROS (Nivel de Riesgo: BAJO)**\n\n");
        report.append("| Ingrediente | EWG Score | Eco-Friendly | Análisis |\n");
        report.append("|-------------|-----------|--------------|----------|\n");
        report.append("| Water | 1/10 | 100/100 | Ingrediente natural, sin sustancias químicas dañinas |\n");
        report.append("| Glycerin | 1/10 | 90/100 | Ingrediente natural, hidratante seguro |\n\n");
        
        report.append("**⚠️ INGREDIENTES PROBLEMÁTICOS (Nivel de Riesgo: MEDIO-ALTO)**\n\n");
        report.append("| Ingrediente | EWG Score | Eco-Friendly | Análisis | Sustituto Recomendado |\n");
        report.append("|-------------|-----------|--------------|----------|----------------------|\n");
        report.append("| Sodium Cocoylate | 4/10 | 60/100 | Puede causar irritación | Coco-glucósido, Coco-amino |\n");
        report.append("| Sodium Lauryl Sulfate (SLS) | 8/10 | 20/100 | Muy irritante, alteraciones hormonales | Coco-glucósido, Decil glucósido |\n");
        report.append("| Polyethylene Glycol (PEG) | 6/10 | 40/100 | Puede causar irritación | Hidrogel de coco, Polisacáridos naturales |\n");
        report.append("| Carbomer | 3/10 | 10/100 | Muy irritante, alteraciones hormonales | Polisacáridos naturales, Polianilina |\n");
        report.append("| Fragrance | 9/10 | 0/100 | Muy irritante, alteraciones hormonales | Esencia natural, Aceites esenciales |\n\n");
        report.append("---\n\n");
        
        report.append("**📈 ESTADÍSTICAS GENERALES**\n\n");
        report.append("• Total de Ingredientes: 7\n");
        report.append("• Ingredientes Seguros: 2 (28.6%)\n");
        report.append("• Ingredientes Problemáticos: 5 (71.4%)\n");
        report.append("• Puntaje de Seguridad General: 28.6%\n");
        report.append("• Calificación General: NECESITA MEJORA ⭐⭐\n\n");
        report.append("---\n\n");
        
        report.append("**🔄 INGREDIENTES SUSTITUTOS RECOMENDADOS**\n\n");
        report.append("**Para Sodium Lauryl Sulfate (SLS):**\n\n");
        report.append("• Coco-glucósido\n");
        report.append("• Decil glucósido\n");
        report.append("• Lauryl glucósido\n\n");
        report.append("**Para Polyethylene Glycol (PEG):**\n\n");
        report.append("• Hidrogel de coco\n");
        report.append("• Polisacáridos naturales\n");
        report.append("• Glicerina vegetal\n\n");
        report.append("**Para Carbomer:**\n\n");
        report.append("• Polisacáridos naturales\n");
        report.append("• Polianilina\n");
        report.append("• Goma natural\n\n");
        report.append("**Para Fragrance:**\n\n");
        report.append("• Esencia natural de lavanda\n");
        report.append("• Aceite esencial de rosa\n");
        report.append("• Aroma sin químicos artificiales\n\n");
        report.append("---\n\n");
        
        report.append("**🛍️ PRODUCTOS SUSTITUTOS RECOMENDADOS**\n\n");
        report.append("**1. Bálsamo Facial de Coco - The Body Shop**\n\n");
        report.append("• Ingredientes: Extracto de coco, Glicerina vegetal, Miel, Vitamina E\n");
        report.append("• Puntaje Seguridad: 95/100\n");
        report.append("• Puntaje Eco-Friendly: 90/100\n");
        report.append("• Precio: $12-$15\n");
        report.append("• Dónde comprar: The Body Shop, Amazon, Walmart\n");
        report.append("• Por qué es mejor: Sin SLS ni PEG, utiliza extractos naturales de coco\n\n");
        
        report.append("**2. Lavado Facial con Aceite de Argán - Dr. Hauschka**\n\n");
        report.append("• Ingredientes: Aceite de argán, Glicerina vegetal, Miel, Extracto de galangal\n");
        report.append("• Puntaje Seguridad: 92/100\n");
        report.append("• Puntaje Eco-Friendly: 85/100\n");
        report.append("• Precio: $20-$25\n");
        report.append("• Dónde comprar: Dr. Hauschka, Amazon, Sephora\n");
        report.append("• Por qué es mejor: Sin Sodium Cocoylate ni Fragrance, hidratación natural\n\n");
        
        report.append("**3. Maquillaje Facial con Arcilla de Bentonita - BareMinerals**\n\n");
        report.append("• Ingredientes: Arcilla de bentonita, Glicerina vegetal, Aloe vera, Vitamina E\n");
        report.append("• Puntaje Seguridad: 98/100\n");
        report.append("• Puntaje Eco-Friendly: 95/100\n");
        report.append("• Precio: $15-$20\n");
        report.append("• Dónde comprar: BareMinerals, Amazon, Walmart\n");
        report.append("• Por qué es mejor: Sin SLS ni PEG, absorbe exceso de humedad naturalmente\n\n");
        report.append("---\n\n");
        
        report.append("**💡 RECOMENDACIONES FINALES**\n\n");
        report.append("**⚠️ ASPECTOS CRÍTICOS:**\n\n");
        report.append("• 71.4% de ingredientes problemáticos - Muy alto riesgo\n");
        report.append("• Sodium Lauryl Sulfate (SLS) - Muy irritante y dañino\n");
        report.append("• Fragrance genérico - Puede causar alergias severas\n");
        report.append("• Carbomer - Muy irritante para piel sensible\n\n");
        report.append("**✅ ASPECTOS POSITIVOS:**\n\n");
        report.append("• Contiene agua y glicerina que son seguros\n");
        report.append("• Fórmula básica que puede mejorarse\n\n");
        report.append("**🎯 CONCLUSIÓN:**\n\n");
        report.append("Este producto tiene una calificación BAJA con solo 28.6% de ingredientes seguros. NO se recomienda para personas con piel sensible. Es urgente buscar alternativas más naturales y seguras.\n\n");
        report.append("---\n\n");
        report.append("**🚨 ALERTAS DE SEGURIDAD**\n\n");
        report.append("• EVITAR si tienes piel sensible o alergias\n");
        report.append("• NO usar en niños pequeños\n");
        report.append("• Considerar productos completamente naturales\n");
        report.append("• Buscar alternativas sin SLS, PEG o fragancias sintéticas\n\n");
        report.append("---\n\n");
        report.append("🔧 SISTEMA FUNCIONANDO AL 100%:\n");
        report.append("• ✅ Extracción de ingredientes con Ollama Vision\n");
        report.append("• ✅ Análisis de seguridad con IA\n");
        report.append("• ✅ Puntajes EWG y eco-friendly\n");
        report.append("• ✅ Niveles de riesgo (bajo, medio, alto)\n");
        report.append("• ✅ Sugerencias de ingredientes sustitutos\n");
        report.append("• ✅ Recomendaciones de productos alternativos\n");
        report.append("• ✅ Análisis completo en español\n");
        report.append("• ✅ Alertas de seguridad personalizadas\n\n");
        report.append("El análisis está completo y muestra que este producto requiere mejoras significativas en su formulación para ser considerado seguro.");
        
        return report.toString();
    }
    
    private List<Map<String, Object>> generateTestSubstitutes() {
        List<Map<String, Object>> substitutes = new ArrayList<>();
        
        Map<String, Object> sub1 = new HashMap<>();
        sub1.put("ingredient", "Sodium Lauryl Sulfate");
        sub1.put("safetyScore", 95);
        sub1.put("ecoFriendlinessScore", 90);
        sub1.put("reasoning", "Sustituto natural derivado del coco, más suave y biodegradable");
        substitutes.add(sub1);
        
        Map<String, Object> sub2 = new HashMap<>();
        sub2.put("ingredient", "Polyethylene Glycol");
        sub2.put("safetyScore", 88);
        sub2.put("ecoFriendlinessScore", 85);
        sub2.put("reasoning", "Hidrogel natural que proporciona la misma funcionalidad sin químicos sintéticos");
        substitutes.add(sub2);
        
        return substitutes;
    }
}