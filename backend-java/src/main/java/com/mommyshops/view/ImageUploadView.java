package com.mommyshops.view;

import com.vaadin.flow.component.button.Button;
import com.vaadin.flow.component.html.H3;
import com.vaadin.flow.component.html.Paragraph;
import com.vaadin.flow.component.notification.Notification;
import com.vaadin.flow.component.orderedlayout.HorizontalLayout;
import com.vaadin.flow.component.orderedlayout.VerticalLayout;
import com.vaadin.flow.component.textfield.TextField;
import com.vaadin.flow.component.upload.Upload;
import com.vaadin.flow.component.upload.receivers.MemoryBuffer;
import com.vaadin.flow.router.PageTitle;
import com.vaadin.flow.router.Route;
import com.vaadin.flow.component.html.Div;
import com.mommyshops.service.AnalysisService;
import com.mommyshops.service.UserSessionService;
import org.springframework.beans.factory.annotation.Autowired;
import java.util.Map;
import java.io.IOException;

@Route("image-upload")
@PageTitle("Carga de Imagen - MommyShops")
public class ImageUploadView extends VerticalLayout {
    
    @Autowired
    private AnalysisService analysisService;
    
    @Autowired
    private UserSessionService userSessionService;
    
    private final TextField urlField = new TextField("URL de la imagen");
    private final MemoryBuffer buffer = new MemoryBuffer();
    private final Upload upload = new Upload(buffer);
    private final Button analyzeButton = new Button("Analizar Producto");
    private final VerticalLayout resultsLayout = new VerticalLayout();
    private byte[] uploadedImageBytes;
    private String uploadedFileName;
    
    public ImageUploadView() {
        setupLayout();
        setupUpload();
        setupButtons();
    }
    
    private void setupLayout() {
        setSizeFull();
        setPadding(true);
        setSpacing(true);
        
        H3 title = new H3("Carga de Imagen para Análisis");
        add(title);
        
        Paragraph description = new Paragraph(
            "Sube una imagen de tu producto cosmético o proporciona una URL para analizar sus ingredientes y obtener recomendaciones personalizadas."
        );
        add(description);
    }
    
    private void setupUpload() {
        // Configurar campo de URL
        urlField.setPlaceholder("https://ejemplo.com/imagen.jpg");
        urlField.setWidthFull();
        add(urlField);
        
        // Configurar upload de archivo
        upload.setAcceptedFileTypes("image/*");
        upload.setMaxFiles(1);
        upload.setDropLabel(new Paragraph("Arrastra una imagen aquí o haz clic para seleccionar"));
        upload.setWidthFull();
        
        upload.addSucceededListener(event -> {
            Notification.show("Imagen cargada exitosamente", 3000, Notification.Position.TOP_CENTER);
            try {
                uploadedImageBytes = buffer.getInputStream().readAllBytes();
                uploadedFileName = event.getFileName();
                analyzeButton.setEnabled(true);
            } catch (IOException ioException) {
                uploadedImageBytes = null;
                uploadedFileName = null;
                analyzeButton.setEnabled(false);
                Notification.show("Error al leer la imagen subida. Intenta nuevamente.", 5000, Notification.Position.TOP_CENTER);
            }
        });

        upload.addFileRemovedListener(event -> {
            uploadedImageBytes = null;
            uploadedFileName = null;
            analyzeButton.setEnabled(false);
        });

        add(upload);

        // Configurar layout de resultados
        resultsLayout.setPadding(false);
        resultsLayout.setSpacing(true);
        add(resultsLayout);
    }
    
    private void setupButtons() {
        analyzeButton.setEnabled(false);
        analyzeButton.addClickListener(e -> analyzeProduct());
        
        Button backButton = new Button("Volver al Cuestionario");
        backButton.addClickListener(e -> getUI().ifPresent(ui -> ui.navigate("questionnaire")));
        
        HorizontalLayout buttonLayout = new HorizontalLayout(backButton, analyzeButton);
        buttonLayout.setSpacing(true);
        add(buttonLayout);
    }
    
    private void analyzeProduct() {
        try {
            String imageUrl = getImageUrl();
            boolean hasUrl = imageUrl != null && !imageUrl.isEmpty();
            boolean hasUploadedImage = uploadedImageBytes != null && uploadedImageBytes.length > 0;

        if (!hasUrl && !hasUploadedImage) {
                Notification.show("Por favor, sube una imagen o proporciona una URL válida", 5000, Notification.Position.TOP_CENTER);
                return;
            }

            // Mostrar indicador de carga
            analyzeButton.setEnabled(false);
            analyzeButton.setText("Analizando...");
            
            // Obtener perfil de usuario real del cuestionario
            Map<String, Object> userProfile = userSessionService.getUserProfile();
            
            // Si no hay perfil guardado, mostrar mensaje y redirigir al cuestionario
            if (!userSessionService.isQuestionnaireCompleted()) {
                Notification.show("Por favor, completa el cuestionario primero", 5000, Notification.Position.TOP_CENTER);
                getUI().ifPresent(ui -> ui.navigate("questionnaire"));
                return;
            }
            
            // Llamar al backend real
            Map<String, Object> analysisResult;
            if (hasUrl) {
                analysisResult = analysisService.analyzeProduct(imageUrl, userProfile);
            } else {
                analysisResult = analysisService.analyzeUploadedImage(uploadedImageBytes, uploadedFileName);
                // establecer flag para indicar que la ejecución usó upload
                if (analysisResult != null) {
                    analysisResult.put("usedUpload", true);
                }
            }
            
            // Mostrar resultados reales
            displayRealResults(analysisResult);
            
            // Restaurar botón
            analyzeButton.setEnabled(true);
            analyzeButton.setText("Analizar Producto");
            
        } catch (Exception e) {
            Notification.show("Error al analizar el producto: " + e.getMessage(), 5000, Notification.Position.TOP_CENTER);
            analyzeButton.setEnabled(true);
            analyzeButton.setText("Analizar Producto");
        }
    }
    
    private String getImageUrl() {
        // Priorizar URL si está proporcionada
        String url = urlField.getValue();
        if (url != null && !url.trim().isEmpty()) {
            return url.trim();
        }
        return null;
    }
    
    
    private void displayRealResults(Map<String, Object> analysisResult) {
        resultsLayout.removeAll();

        if ("fallback".equals(analysisResult.get("status"))) {
            Notification.show(
                "No se pudo analizar la imagen. Vuelve a capturarla o pega la URL del producto.",
                5000,
                Notification.Position.TOP_CENTER
            );

            boolean usedUpload = Boolean.TRUE.equals(analysisResult.get("usedUpload"));
            String retryText = usedUpload
                ? "No se pudieron leer los ingredientes desde la imagen. Asegúrate de que la foto sea legible y vuelve a subirla."
                : "No se pudieron leer los ingredientes. Intenta nuevamente con una foto más clara o ingresa la URL del producto.";
            resultsLayout.add(new Paragraph(retryText));
            analyzeButton.setEnabled(true);
            analyzeButton.setText("Analizar Producto");
            return;
        }
        
        // Mostrar el reporte detallado completo si está disponible
        if (analysisResult.containsKey("detailedReport")) {
            String detailedReport = (String) analysisResult.get("detailedReport");
            displayDetailedReport(detailedReport);
        } else {
            // Fallback al formato anterior si no hay reporte detallado
            displayBasicResults(analysisResult);
        }
        
        // Botón para nuevo análisis
        Button newAnalysisButton = new Button("Nuevo Análisis");
        newAnalysisButton.addClickListener(e -> {
            urlField.clear();
            upload.clearFileList();
            resultsLayout.removeAll();
            analyzeButton.setEnabled(false);
            uploadedImageBytes = null;
            uploadedFileName = null;
        });
        
        resultsLayout.add(newAnalysisButton);
    }
    
    private void displayDetailedReport(String detailedReport) {
        // Dividir el reporte en secciones
        String[] sections = detailedReport.split("---");
        
        for (String section : sections) {
            if (section.trim().isEmpty()) continue;
            
            // Crear un div para cada sección
            Div sectionDiv = new Div();
            sectionDiv.getStyle().set("margin", "10px 0");
            sectionDiv.getStyle().set("padding", "15px");
            sectionDiv.getStyle().set("border", "1px solid #e0e0e0");
            sectionDiv.getStyle().set("border-radius", "8px");
            sectionDiv.getStyle().set("background-color", "#f9f9f9");
            
            // Aplicar estilos específicos según el tipo de sección
            applySectionStyles(sectionDiv, section);
            
            // Procesar el contenido de la sección
            String processedContent = processSectionContent(section);
            
            // Crear párrafo con el contenido procesado
            Paragraph sectionPara = new Paragraph();
            sectionPara.getElement().setProperty("innerHTML", processedContent);
            sectionDiv.add(sectionPara);
            
            resultsLayout.add(sectionDiv);
        }
    }
    
    private void applySectionStyles(Div sectionDiv, String section) {
        String sectionLower = section.toLowerCase();
        
        if (sectionLower.contains("resumen ejecutivo")) {
            sectionDiv.getStyle().set("background-color", "#e8f5e8");
            sectionDiv.getStyle().set("border-color", "#4caf50");
        } else if (sectionLower.contains("ingredientes")) {
            sectionDiv.getStyle().set("background-color", "#fff3e0");
            sectionDiv.getStyle().set("border-color", "#ff9800");
        } else if (sectionLower.contains("análisis de seguridad") || sectionLower.contains("seguridad")) {
            sectionDiv.getStyle().set("background-color", "#ffebee");
            sectionDiv.getStyle().set("border-color", "#f44336");
        } else if (sectionLower.contains("sustitutos") || sectionLower.contains("recomendados")) {
            sectionDiv.getStyle().set("background-color", "#e3f2fd");
            sectionDiv.getStyle().set("border-color", "#2196f3");
        } else if (sectionLower.contains("productos sustitutos") || sectionLower.contains("productos recomendados")) {
            sectionDiv.getStyle().set("background-color", "#f3e5f5");
            sectionDiv.getStyle().set("border-color", "#9c27b0");
        } else if (sectionLower.contains("conclusiones") || sectionLower.contains("recomendaciones")) {
            sectionDiv.getStyle().set("background-color", "#e0f2f1");
            sectionDiv.getStyle().set("border-color", "#009688");
        } else if (sectionLower.contains("sistema funcionando") || sectionLower.contains("funcionando al 100%")) {
            sectionDiv.getStyle().set("background-color", "#f1f8e9");
            sectionDiv.getStyle().set("border-color", "#8bc34a");
        }
    }
    
    private String processSectionContent(String content) {
        // Convertir markdown básico a HTML
        String processed = content
            .replaceAll("\\*\\*(.*?)\\*\\*", "<strong>$1</strong>") // **texto** -> <strong>texto</strong>
            .replaceAll("\\*(.*?)\\*", "<em>$1</em>") // *texto* -> <em>texto</em>
            .replaceAll("• ", "&bull; ") // • -> &bull;
            .replaceAll("✅", "&#10004; ") // ✅ -> checkmark
            .replaceAll("⚠️", "&#9888; ") // ⚠️ -> warning
            .replaceAll("❌", "&#10060; ") // ❌ -> X
            .replaceAll("📋", "&#128203; ") // 📋 -> clipboard
            .replaceAll("🧪", "&#128137; ") // 🧪 -> test tube
            .replaceAll("📊", "&#128202; ") // 📊 -> bar chart
            .replaceAll("🔄", "&#128260; ") // 🔄 -> refresh
            .replaceAll("💡", "&#128161; ") // 💡 -> lightbulb
            .replaceAll("🛍️", "&#128717; ") // 🛍️ -> shopping bags
            .replaceAll("🚨", "&#128680; ") // 🚨 -> rotating light
            .replaceAll("🔧", "&#128295; ") // 🔧 -> wrench
            .replaceAll("\n", "<br>"); // Saltos de línea
        
        // Procesar tablas si existen
        processed = processTables(processed);
        
        return processed;
    }
    
    private String processTables(String content) {
        // Buscar patrones de tabla en el contenido
        // Patrón: | Columna1 | Columna2 | Columna3 |
        String tablePattern = "\\|([^|]+)\\|([^|]+)\\|([^|]+)\\|";
        
        if (content.contains("|") && content.contains("---")) {
            // Convertir tabla markdown a HTML
            String[] lines = content.split("\n");
            StringBuilder htmlTable = new StringBuilder();
            boolean inTable = false;
            boolean isHeader = true;
            
            for (String line : lines) {
                if (line.trim().startsWith("|") && line.trim().endsWith("|")) {
                    if (!inTable) {
                        htmlTable.append("<table style='border-collapse: collapse; width: 100%; margin: 10px 0;'>");
                        inTable = true;
                    }
                    
                    if (line.contains("---")) {
                        isHeader = false;
                        continue; // Saltar línea de separación
                    }
                    
                    String[] cells = line.split("\\|");
                    StringBuilder row = new StringBuilder();
                    row.append("<tr>");
                    
                    for (int i = 1; i < cells.length - 1; i++) { // Ignorar primer y último elemento vacío
                        String cell = cells[i].trim();
                        String tag = isHeader ? "th" : "td";
                        String style = isHeader 
                            ? "background-color: #f0f0f0; font-weight: bold; padding: 8px; border: 1px solid #ccc;"
                            : "padding: 8px; border: 1px solid #ccc;";
                        row.append("<").append(tag).append(" style='").append(style).append("'>")
                           .append(cell).append("</").append(tag).append(">");
                    }
                    
                    row.append("</tr>");
                    htmlTable.append(row.toString());
                } else if (inTable) {
                    htmlTable.append("</table>");
                    inTable = false;
                    isHeader = true;
                }
            }
            
            if (inTable) {
                htmlTable.append("</table>");
            }
            
            return htmlTable.toString();
        }
        
        return content;
    }
    
    private void displayBasicResults(Map<String, Object> analysisResult) {
        H3 resultsTitle = new H3("Resultados del Análisis");
        resultsLayout.add(resultsTitle);
        
        // Mostrar nombre del producto
        String productName = (String) analysisResult.getOrDefault("productName", "Producto Analizado");
        Paragraph productNamePara = new Paragraph("Producto: " + productName);
        resultsLayout.add(productNamePara);
        
        // Mostrar resumen del análisis
        String summary = (String) analysisResult.getOrDefault("analysisSummary", "Análisis completado");
        Paragraph summaryPara = new Paragraph(summary);
        resultsLayout.add(summaryPara);
        
        // Mostrar puntuaciones si están disponibles
        if (analysisResult.containsKey("ewgScore") || analysisResult.containsKey("inciScore")) {
            H3 safetyTitle = new H3("Puntuaciones de Seguridad");
            resultsLayout.add(safetyTitle);
            
            if (analysisResult.containsKey("ewgScore")) {
                Number ewgScoreNum = (Number) analysisResult.get("ewgScore");
                Double ewgScore = ewgScoreNum.doubleValue();
                Paragraph ewgPara = new Paragraph("EWG Score: " + ewgScore + "/10");
                resultsLayout.add(ewgPara);
            }
            
            if (analysisResult.containsKey("inciScore")) {
                Number inciScoreNum = (Number) analysisResult.get("inciScore");
                Double inciScore = inciScoreNum.doubleValue();
                Paragraph inciPara = new Paragraph("INCI Score: " + inciScore + "/4");
                resultsLayout.add(inciPara);
            }
            
            if (analysisResult.containsKey("safetyPercentage")) {
                Number safetyPercentageNum = (Number) analysisResult.get("safetyPercentage");
                Double safetyPercentage = safetyPercentageNum.doubleValue();
                Paragraph safetyPara = new Paragraph("Porcentaje de Seguridad: " + safetyPercentage + "%");
                resultsLayout.add(safetyPara);
            }
        }
        
        // Mostrar ingredientes si están disponibles
        if (analysisResult.containsKey("ingredients")) {
            H3 ingredientsTitle = new H3("Ingredientes Detectados");
            resultsLayout.add(ingredientsTitle);
            
            String ingredients = (String) analysisResult.get("ingredients");
            Paragraph ingredientsPara = new Paragraph(ingredients);
            resultsLayout.add(ingredientsPara);
        }
        
        // Mostrar recomendaciones si están disponibles
        if (analysisResult.containsKey("recommendations")) {
            H3 recommendationsTitle = new H3("Recomendaciones");
            resultsLayout.add(recommendationsTitle);
            
            String recommendations = (String) analysisResult.get("recommendations");
            Paragraph recommendationsPara = new Paragraph(recommendations);
            resultsLayout.add(recommendationsPara);
        }
        
        // Mostrar información adicional si está disponible
        if (analysisResult.containsKey("additionalInfo")) {
            H3 additionalTitle = new H3("Información Adicional");
            resultsLayout.add(additionalTitle);
            
            String additionalInfo = (String) analysisResult.get("additionalInfo");
            Paragraph additionalPara = new Paragraph(additionalInfo);
            resultsLayout.add(additionalPara);
        }
    }
}