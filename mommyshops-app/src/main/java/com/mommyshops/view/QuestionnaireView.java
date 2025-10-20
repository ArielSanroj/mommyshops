package com.mommyshops.view;

import com.mommyshops.service.UserSessionService;
import com.vaadin.flow.component.button.Button;
import com.vaadin.flow.component.combobox.ComboBox;
import com.vaadin.flow.component.combobox.MultiSelectComboBox;
import com.vaadin.flow.component.html.H3;
import com.vaadin.flow.component.html.Paragraph;
import com.vaadin.flow.component.notification.Notification;
import com.vaadin.flow.component.orderedlayout.HorizontalLayout;
import com.vaadin.flow.component.orderedlayout.VerticalLayout;
import com.vaadin.flow.component.progressbar.ProgressBar;
import com.vaadin.flow.router.PageTitle;
import com.vaadin.flow.router.Route;
import org.springframework.beans.factory.annotation.Autowired;

import java.util.*;

@Route("questionnaire")
@PageTitle("Cuestionario de Personalización - MommyShops")
public class QuestionnaireView extends VerticalLayout {
    
    @Autowired
    private UserSessionService userSessionService;
    
    private final Map<String, Object> answers = new HashMap<>();
    private int currentStep = 0;
    private final ProgressBar progressBar = new ProgressBar();
    private final VerticalLayout contentLayout = new VerticalLayout();
    private final HorizontalLayout buttonLayout = new HorizontalLayout();
    
    private final Button previousButton = new Button("Anterior");
    private final Button nextButton = new Button("Siguiente");
    private final Button saveButton = new Button("Guardar");
    private final Button completeButton = new Button("Completar");
    
    private final List<QuestionStep> steps = Arrays.asList(
        new QuestionStep(
            "Información Personal",
            "¿Cuál es tu edad?",
            Arrays.asList("18-25", "26-35", "36-45", "46-55", "56-65", "65+"),
            "age",
            false
        ),
        new QuestionStep(
            "Tipo de Piel",
            "¿Qué tipo de piel tienes?",
            Arrays.asList("Normal", "Seca", "Grasa", "Mixta", "Sensible", "No estoy seguro/a"),
            "skin_type",
            false
        ),
        new QuestionStep(
            "Preocupaciones de Piel",
            "¿Cuáles son tus principales preocupaciones de piel? (Puedes seleccionar varias)",
            Arrays.asList("Acné", "Líneas de expresión", "Manchas", "Piel seca", "Piel grasa", "Sensibilidad", "Pigmentación irregular", "Poros dilatados"),
            "skin_concerns",
            true
        ),
        new QuestionStep(
            "Alergias Conocidas",
            "¿Tienes alergias conocidas a ingredientes cosméticos?",
            Arrays.asList("Sí, tengo alergias específicas", "No, no tengo alergias conocidas", "No estoy seguro/a"),
            "allergies",
            false
        ),
        new QuestionStep(
            "Ingredientes a Evitar",
            "¿Hay ingredientes específicos que prefieres evitar? (Puedes seleccionar varios)",
            Arrays.asList("Parabenos", "Sulfatos", "Ftalatos", "Fragancias sintéticas", "Colorantes artificiales", "Conservantes", "Aceites minerales", "Ninguno específico"),
            "avoid_ingredients",
            true
        ),
        new QuestionStep(
            "Preferencias de Producto",
            "¿Qué tipo de productos cosméticos usas más frecuentemente?",
            Arrays.asList("Cuidado facial", "Maquillaje", "Cuidado corporal", "Cuidado capilar", "Productos para bebés", "Todos los anteriores"),
            "product_preferences",
            false
        ),
        new QuestionStep(
            "Presupuesto",
            "¿Cuál es tu rango de presupuesto para productos cosméticos?",
            Arrays.asList("Económico (menos de $20)", "Medio ($20-$50)", "Alto ($50-$100)", "Premium (más de $100)", "No es importante"),
            "budget",
            false
        ),
        new QuestionStep(
            "Frecuencia de Uso",
            "¿Con qué frecuencia compras productos cosméticos?",
            Arrays.asList("Mensualmente", "Cada 2-3 meses", "Cada 6 meses", "Anualmente", "Solo cuando necesito"),
            "purchase_frequency",
            false
        ),
        new QuestionStep(
            "Fuentes de Información",
            "¿Cómo prefieres recibir información sobre productos?",
            Arrays.asList("Análisis detallado", "Resumen simple", "Recomendaciones directas", "Comparaciones", "Todas las anteriores"),
            "information_preference",
            false
        )
    );
    
    public QuestionnaireView() {
        setupLayout();
        setupButtons();
        showCurrentStep();
    }
    
    private void setupLayout() {
        setSizeFull();
        setPadding(true);
        setSpacing(true);
        
        H3 title = new H3("Cuestionario de Personalización");
        add(title);
        
        progressBar.setValue(0);
        progressBar.setMax(1);
        add(progressBar);
        
        contentLayout.setPadding(false);
        contentLayout.setSpacing(true);
        add(contentLayout);
        
        buttonLayout.setPadding(false);
        buttonLayout.setSpacing(true);
        add(buttonLayout);
    }
    
    private void setupButtons() {
        previousButton.setEnabled(false);
        previousButton.addClickListener(e -> previousStep());
        
        nextButton.addClickListener(e -> nextStep());
        
        saveButton.addClickListener(e -> saveProgress());
        
        completeButton.addClickListener(e -> completeQuestionnaire());
        completeButton.setEnabled(false);
        
        buttonLayout.add(previousButton, nextButton, saveButton, completeButton);
    }
    
    private void showCurrentStep() {
        contentLayout.removeAll();
        
        QuestionStep step = steps.get(currentStep);
        
        H3 stepTitle = new H3(step.getTitle());
        contentLayout.add(stepTitle);
        
        Paragraph question = new Paragraph(step.getQuestion());
        contentLayout.add(question);
        
        if (step.isMultiple()) {
            MultiSelectComboBox<String> multiSelect = new MultiSelectComboBox<>();
            multiSelect.setItems(step.getOptions());
            multiSelect.setPlaceholder("Selecciona una o más opciones");
            multiSelect.setWidthFull();
            
            // Cargar respuesta guardada
            Object savedAnswer = answers.get(step.getKey());
            if (savedAnswer instanceof List) {
                @SuppressWarnings("unchecked")
                List<String> savedList = (List<String>) savedAnswer;
                multiSelect.setValue(new HashSet<>(savedList));
            }
            
            multiSelect.addValueChangeListener(e -> {
                answers.put(step.getKey(), new ArrayList<>(e.getValue()));
                updateButtons();
            });
            
            contentLayout.add(multiSelect);
        } else {
            ComboBox<String> comboBox = new ComboBox<>();
            comboBox.setItems(step.getOptions());
            comboBox.setPlaceholder("Selecciona una opción");
            comboBox.setWidthFull();
            
            // Cargar respuesta guardada
            Object savedAnswer = answers.get(step.getKey());
            if (savedAnswer instanceof String) {
                comboBox.setValue((String) savedAnswer);
            }
            
            comboBox.addValueChangeListener(e -> {
                answers.put(step.getKey(), e.getValue());
                updateButtons();
            });
            
            contentLayout.add(comboBox);
        }
        
        // Actualizar barra de progreso
        progressBar.setValue((double) (currentStep + 1) / steps.size());
        
        // Actualizar botones
        previousButton.setEnabled(currentStep > 0);
        nextButton.setEnabled(currentStep < steps.size() - 1);
        completeButton.setEnabled(currentStep == steps.size() - 1);
    }
    
    private void updateButtons() {
        QuestionStep currentStepObj = steps.get(currentStep);
        boolean hasAnswer = answers.containsKey(currentStepObj.getKey());
        
        if (currentStep < steps.size() - 1) {
            nextButton.setEnabled(hasAnswer);
        } else {
            completeButton.setEnabled(hasAnswer);
        }
    }
    
    private void previousStep() {
        if (currentStep > 0) {
            currentStep--;
            showCurrentStep();
        }
    }
    
    private void nextStep() {
        if (currentStep < steps.size() - 1) {
            currentStep++;
            showCurrentStep();
        }
    }
    
    private void saveProgress() {
        try {
            Notification.show("Progreso guardado exitosamente", 3000, Notification.Position.TOP_CENTER);
        } catch (Exception e) {
            Notification.show("Error al guardar el progreso: " + e.getMessage(), 5000, Notification.Position.TOP_CENTER);
        }
    }
    
    private void completeQuestionnaire() {
        try {
            // Guardar el perfil del usuario en la sesión
            userSessionService.saveUserProfile(answers);
            
            Notification.show("¡Cuestionario completado! Ahora puedes subir una imagen para analizar.", 5000, Notification.Position.TOP_CENTER);
            
            // Redirigir a la vista de carga de imagen
            getUI().ifPresent(ui -> ui.navigate("image-upload"));
            
        } catch (Exception e) {
            Notification.show("Error al completar el cuestionario: " + e.getMessage(), 5000, Notification.Position.TOP_CENTER);
        }
    }
    
    private static class QuestionStep {
        private final String title;
        private final String question;
        private final List<String> options;
        private final String key;
        private final boolean multiple;
        
        public QuestionStep(String title, String question, List<String> options, String key, boolean multiple) {
            this.title = title;
            this.question = question;
            this.options = options;
            this.key = key;
            this.multiple = multiple;
        }
        
        public String getTitle() { return title; }
        public String getQuestion() { return question; }
        public List<String> getOptions() { return options; }
        public String getKey() { return key; }
        public boolean isMultiple() { return multiple; }
    }
}