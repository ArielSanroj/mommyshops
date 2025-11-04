package com.mommyshops.view;

import com.mommyshops.auth.service.AuthService;
import com.mommyshops.profile.service.UserProfileService;
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

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;

@Route("questionnaire")
@PageTitle("Cuestionario de Personalización - MommyShops")
public class QuestionnaireView extends VerticalLayout {

    @Autowired
    private UserSessionService userSessionService;
    
    @Autowired
    private UserProfileService userProfileService;
    
    @Autowired
    private AuthService authService;

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
            "Información personal",
            "¿Cuál es tu rango de edad?",
            Arrays.asList("18-24", "25-34", "35-44", "45-54", "55-64", "65+", "Prefiero no decir"),
            "age",
            false,
            "El rango de edad orienta la concentración de activos y ciclos hormonales que debemos priorizar."
        ),
        new QuestionStep(
            "Contexto hormonal y etapa de vida",
            "¿En qué etapa te encuentras actualmente?",
            Arrays.asList(
                "No estoy embarazada ni lactando",
                "Estoy en el primer trimestre de embarazo",
                "Estoy en el segundo o tercer trimestre",
                "Estoy en etapa de lactancia",
                "Estoy planificando embarazo / fertilidad asistida",
                "Tengo SOP, endometriosis u otros desequilibrios hormonales",
                "Perimenopausia o menopausia",
                "Prefiero no decir"
            ),
            "pregnancy_status",
            false,
            "Conocer tu contexto hormonal es clave para descartar ingredientes sensibles y ajustar dosis."
        ),
        new QuestionStep(
            "Tipo de piel",
            "¿Qué tipo de piel tienes actualmente?",
            Arrays.asList(
                "Normal equilibrada",
                "Seca o deshidratada",
                "Grasa",
                "Mixta (zona T grasa, mejillas secas)",
                "Sensible / reactiva",
                "Con tendencia a rosácea o dermatitis",
                "No estoy segura"
            ),
            "skin_type",
            false,
            "Selecciona la opción que mejor describa tu piel en su estado habitual."
        ),
        new QuestionStep(
            "Reactividad cutánea",
            "¿Cómo responde tu piel a los productos y activos nuevos?",
            Arrays.asList(
                "Tolero la mayoría de los activos sin problema",
                "A veces me irrito con ácidos o fragancias",
                "Mi piel se inflama o enrojece con facilidad",
                "Estoy en tratamiento dermatológico activo",
                "Prefiero que lo evaluemos juntos"
            ),
            "skin_reactivity",
            false,
            "Nos ayuda a modular concentraciones, pH y frecuencia de aplicación."
        ),
        new QuestionStep(
            "Preocupaciones de piel prioritarias",
            "¿Cuáles son tus principales preocupaciones de piel?",
            Arrays.asList(
                "Sensibilidad e irritación",
                "Acné activo",
                "Brotes hormonales",
                "Manchas postinflamatorias",
                "Hiperpigmentación solar",
                "Arrugas y firmeza",
                "Pérdida de luminosidad",
                "Deshidratación",
                "Poros dilatados",
                "Textura irregular",
                "Enrojecimiento crónico"
            ),
            "skin_concerns",
            true,
            "Selecciona todas las que apliquen para ajustar las prioridades de formulación."
        ),
        new QuestionStep(
            "Objetivos de cuidado facial",
            "¿Qué objetivos quieres alcanzar con tu rutina?",
            Arrays.asList(
                "Rutina limpia y segura",
                "Calmar inflamación",
                "Uniformar tono y manchas",
                "Prevención anti-edad",
                "Hidratación profunda 24h",
                "Control de grasa y brillo",
                "Reparación de la barrera cutánea",
                "Glow inmediato",
                "Preparar la piel para tratamientos clínicos"
            ),
            "skin_goals",
            true,
            "Usamos estos objetivos para definir la secuencia y los activos protagonistas."
        ),
        new QuestionStep(
            "Zonas prioritarias del rostro",
            "¿Cómo se comportan tus zonas faciales cuando aplicas productos?",
            Arrays.asList(
                "Equilibrado en todo el rostro",
                "Zona T grasa y mejillas secas",
                "Mejillas sensibles o rojizas",
                "Tendencia a manchas en pómulos",
                "Contorno de ojos delicado",
                "No estoy segura"
            ),
            "face_shape",
            false,
            "Esto nos ayuda a identificar ingredientes que deben equilibrar zonas grasas, hidratar mejillas o proteger áreas delicadas."
        ),
        new QuestionStep(
            "Tipo de cabello",
            "¿Cómo describirías tu patrón de rizo o forma del cabello?",
            Arrays.asList(
                "Liso 1A-1C",
                "Ondulado 2A-2C",
                "Rizado 3A-3C",
                "Coily / Afro 4A-4C",
                "Cabello en transición",
                "No estoy segura"
            ),
            "hair_type",
            false,
            "Esto define la estructura base para hidratar, nutrir y proteger."
        ),
        new QuestionStep(
            "Porosidad o estructura del cabello",
            "¿Cómo sientes que absorbe y retiene productos tu cabello?",
            Arrays.asList(
                "Baja (repela el agua, se satura rápido)",
                "Media (equilibrada, responde bien)",
                "Alta (absorbe todo y se seca rápido)",
                "No estoy segura"
            ),
            "hair_porosity",
            false,
            "La porosidad define el tipo de lípidos y proteínas que debemos priorizar."
        ),
        new QuestionStep(
            "Condición del cuero cabelludo",
            "¿Cómo describirías tu cuero cabelludo?",
            Arrays.asList(
                "Equilibrado",
                "Seco con descamación",
                "Graso / con exceso de sebo",
                "Sensibilidad o picor frecuente",
                "Caspa controlada",
                "Dermatitis seborréica diagnosticada"
            ),
            "scalp_condition",
            false,
            "Necesitamos saberlo para ajustar tensioactivos, pH y activos calmantes."
        ),
        new QuestionStep(
            "Preocupaciones capilares",
            "¿Qué retos estás viviendo con tu cabello?",
            Arrays.asList(
                "Frizz constante",
                "Caída o debilitamiento",
                "Resequedad extrema",
                "Falta de brillo",
                "Puntas abiertas",
                "Cabello teñido o decolorado",
                "Encrespamiento por humedad",
                "Crecimiento lento"
            ),
            "hair_concerns",
            true,
            "Selecciona todo lo que aplique para crear boosters y mascarillas específicas."
        ),
        new QuestionStep(
            "Hábitos y tratamientos actuales",
            "¿Qué hábitos o tratamientos realizas con tu cabello?",
            Arrays.asList(
                "Uso herramientas de calor a diario",
                "Alisados o permanentes químicos",
                "Tinte o decoloración reciente (últimos 3 meses)",
                "Nado con frecuencia en piscina o mar",
                "Uso casco, gorro o velo a diario",
                "Practico deporte intenso y sudo mucho",
                "Rutina low-poo / co-wash",
                "Protejo el cabello mientras duermo (bonnet, trenzas)"
            ),
            "hair_routine",
            true,
            "Nos ayuda a proteger tu fibra y ajustar refuerzos de proteínas y lípidos."
        ),
        new QuestionStep(
            "Niveles de fragancia",
            "¿Qué nivel de fragancia prefieres en tus productos?",
            Arrays.asList(
                "Sin fragancia / hipoalergénico",
                "Aromas suaves y naturales",
                "Aromas frescos o limpios moderados",
                "Aromas envolventes e intensos"
            ),
            "fragrance_preference",
            false,
            "Esto define si usamos fragancias hipoalergénicas, aceites esenciales o alternativas neutras."
        ),
        new QuestionStep(
            "Texturas favoritas",
            "¿Qué texturas disfrutas más en tus productos?",
            Arrays.asList(
                "Gel ligero o acuoso",
                "Serum fluido",
                "Crema media",
                "Bálsamo denso",
                "Aceite seco",
                "Espuma o mousse"
            ),
            "texture_preferences",
            true,
            "Selecciona todas las texturas que te resulten cómodas y sensorialmente agradables."
        ),
        new QuestionStep(
            "Alergias confirmadas o sensibilidades",
            "Selecciona los ingredientes o familias que debamos excluir por alergias confirmadas.",
            Arrays.asList(
                "No tengo alergias conocidas",
                "Fragancias (parfum)",
                "Preservantes MIT / MCI",
                "Niquel / metales pesados",
                "Derivados del coco",
                "Latex / resinas",
                "Sulfatos (SLS / SLES)",
                "Otros (lo especificaré en la sesión)"
            ),
            "allergies",
            true,
            "Puedes elegir varias opciones o dejarnos notas específicas más adelante."
        ),
        new QuestionStep(
            "Ingredientes a evitar por preferencia",
            "¿Hay ingredientes que prefieres evitar por filosofía o experiencia?",
            Arrays.asList(
                "Parabenos",
                "Sulfatos fuertes (SLS / SLES)",
                "Siliconas no solubles",
                "Aceites minerales / petrolatos",
                "Alcoholes secantes (SD alcohol, denat)",
                "Fragancias sintéticas",
                "Colorantes artificiales",
                "Ingredientes de origen animal",
                "Ftalatos",
                "Microplásticos",
                "Ninguno en particular"
            ),
            "avoid_ingredients",
            true,
            "Esto guía la selección de bases y conservantes compatibles con tus valores."
        ),
        new QuestionStep(
            "Activos que te entusiasman",
            "¿Qué activos o tecnologías te interesa incorporar?",
            Arrays.asList(
                "Niacinamida",
                "Ácido hialurónico",
                "Retinoides / bakuchiol",
                "Vitamina C",
                "Ceramidas y lípidos",
                "Péptidos reafirmantes",
                "Probióticos / fermentos",
                "Ácidos suaves (AHA / BHA / PHA)",
                "Botánicos calmantes (centella, avena, manzanilla)",
                "Proteínas / aminoácidos",
                "Extractos antioxidantes (té verde, resveratrol)"
            ),
            "ingredient_focus",
            true,
            "Nos da pista de los activos que disfrutas y podemos potenciar."
        ),
        new QuestionStep(
            "Entorno y estilo de vida",
            "¿Qué factores ambientales influyen en tu piel y cabello?",
            Arrays.asList(
                "Clima húmedo",
                "Clima seco / altitud",
                "Ciudad con alta contaminación",
                "Aire acondicionado o calefacción constante",
                "Agua dura en casa",
                "Exposición solar intensa",
                "Uso maquillaje todo el día",
                "Entrenamientos al aire libre frecuentes"
            ),
            "environment_factors",
            true,
            "Nos ayuda a equilibrar antioxidantes, humectación y protección ambiental."
        ),
        new QuestionStep(
            "Tipo de productos que usas más",
            "¿Qué categorías son indispensables en tu rutina?",
            Arrays.asList(
                "Rutina facial minimalista (1-3 pasos)",
                "Ritual facial completo (5+ pasos)",
                "Cuidado capilar intensivo",
                "Spa corporal en casa",
                "Productos para embarazo / postparto",
                "Productos para bebés o niños",
                "Maquillaje híbrido con skincare"
            ),
            "product_preferences",
            false,
            "Elige la categoría que más define tu rutina diaria actual."
        ),
        new QuestionStep(
            "Presupuesto objetivo",
            "¿En qué rango de inversión te sientes cómoda por producto?",
            Arrays.asList(
                "Económico (menos de $20)",
                "Medio ($20 - $45)",
                "Alto ($46 - $80)",
                "Premium (más de $80)",
                "Depende del tipo de producto"
            ),
            "budget",
            false,
            "Ajustamos fórmulas y proveedores para maximizar valor dentro de tu rango."
        ),
        new QuestionStep(
            "Frecuencia de renovación",
            "¿Con qué frecuencia sueles renovar o ajustar tu rutina?",
            Arrays.asList(
                "Cada 4-6 semanas",
                "Cada 2-3 meses",
                "Cada 6 meses",
                "Solo cuando se terminan los productos",
                "Cuando hay cambios de estación"
            ),
            "purchase_frequency",
            false,
            "Esto define la cadencia del seguimiento y la duración esperada de cada fórmula."
        ),
        new QuestionStep(
            "Cómo quieres recibir las recomendaciones",
            "¿De qué forma prefieres recibir la información y los planes de acción?",
            Arrays.asList(
                "Análisis detallado con fundamentos científicos",
                "Resumen accionable y concreto",
                "Recomendaciones directas paso a paso",
                "Comparaciones y tablas rápidas",
                "Mix entre detalle y resúmenes"
            ),
            "information_preference",
            false,
            "Así personalizamos los reportes, dashboards y recordatorios automáticos."
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

        progressBar.setMin(0);
        progressBar.setMax(steps.size());
        progressBar.setValue(1);
        progressBar.setWidthFull();
        add(progressBar);

        contentLayout.setPadding(false);
        contentLayout.setSpacing(true);
        contentLayout.setWidthFull();
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
        question.getStyle().set("fontWeight", "500");
        contentLayout.add(question);

        if (step.getHelperText() != null && !step.getHelperText().isBlank()) {
            Paragraph helper = new Paragraph(step.getHelperText());
            helper.getStyle().set("color", "var(--lumo-secondary-text-color)");
            helper.getStyle().set("marginTop", "-0.5rem");
            helper.getStyle().set("marginBottom", "0.75rem");
            contentLayout.add(helper);
        }

        if (step.isMultiple()) {
            MultiSelectComboBox<String> multiSelect = new MultiSelectComboBox<>();
            multiSelect.setItems(step.getOptions());
            multiSelect.setPlaceholder("Selecciona una o más opciones");
            multiSelect.setWidthFull();
            multiSelect.setClearButtonVisible(true);

            Object savedAnswer = answers.get(step.getKey());
            if (savedAnswer instanceof List) {
                @SuppressWarnings("unchecked")
                List<String> savedList = (List<String>) savedAnswer;
                multiSelect.setValue(new HashSet<>(savedList));
            }

            multiSelect.addValueChangeListener(e -> {
                if (e.getValue() == null || e.getValue().isEmpty()) {
                    answers.remove(step.getKey());
                } else {
                    answers.put(step.getKey(), new ArrayList<>(e.getValue()));
                }
                updateButtons(step);
            });

            contentLayout.add(multiSelect);
        } else {
            ComboBox<String> comboBox = new ComboBox<>();
            comboBox.setItems(step.getOptions());
            comboBox.setPlaceholder("Selecciona una opción");
            comboBox.setWidthFull();
            comboBox.setClearButtonVisible(true);

            Object savedAnswer = answers.get(step.getKey());
            if (savedAnswer instanceof String) {
                comboBox.setValue((String) savedAnswer);
            }

            comboBox.addValueChangeListener(e -> {
                if (e.getValue() == null || e.getValue().isBlank()) {
                    answers.remove(step.getKey());
                } else {
                    answers.put(step.getKey(), e.getValue());
                }
                updateButtons(step);
            });

            contentLayout.add(comboBox);
        }

        progressBar.setValue(currentStep + 1);

        previousButton.setEnabled(currentStep > 0);
        nextButton.setEnabled(false);
        completeButton.setEnabled(false);
        updateButtons(step);
    }

    private void updateButtons(QuestionStep step) {
        Object value = answers.get(step.getKey());
        boolean hasAnswer = false;

        if (step.isMultiple()) {
            if (value instanceof List) {
                hasAnswer = !((List<?>) value).isEmpty();
            }
        } else if (value instanceof String) {
            hasAnswer = !((String) value).isBlank();
        }

        if (currentStep < steps.size() - 1) {
            nextButton.setEnabled(hasAnswer);
            completeButton.setEnabled(false);
        } else {
            nextButton.setEnabled(false);
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
        Notification.show("Progreso guardado exitosamente", 3000, Notification.Position.TOP_CENTER);
    }

    private void completeQuestionnaire() {
        try {
            Map<String, Object> normalizedAnswers = new HashMap<>();
            answers.forEach((key, value) -> {
                if (value == null) {
                    return;
                }
                normalizedAnswers.put(key, value);
                switch (key) {
                    case "skin_type":
                        normalizedAnswers.put("skinType", value);
                        break;
                    case "skin_concerns":
                        normalizedAnswers.put("skinConcerns", value);
                        break;
                    case "skin_goals":
                        normalizedAnswers.put("skinGoals", value);
                        break;
                    case "skin_reactivity":
                        normalizedAnswers.put("skinReactivity", value);
                        break;
                    case "face_shape":
                        normalizedAnswers.put("faceShape", value);
                        break;
                    case "hair_type":
                        normalizedAnswers.put("hairType", value);
                        break;
                    case "hair_porosity":
                        normalizedAnswers.put("hairPorosity", value);
                        break;
                    case "scalp_condition":
                        normalizedAnswers.put("scalpCondition", value);
                        break;
                    case "hair_concerns":
                        normalizedAnswers.put("hairConcerns", value);
                        break;
                    case "hair_routine":
                        normalizedAnswers.put("hairRoutine", value);
                        break;
                    case "fragrance_preference":
                        normalizedAnswers.put("fragrancePreference", value);
                        break;
                    case "texture_preferences":
                        normalizedAnswers.put("texturePreferences", value);
                        break;
                    case "avoid_ingredients":
                        normalizedAnswers.put("avoidIngredients", value);
                        break;
                    case "ingredient_focus":
                        normalizedAnswers.put("ingredientFocus", value);
                        break;
                    case "environment_factors":
                        normalizedAnswers.put("environmentFactors", value);
                        break;
                    case "product_preferences":
                        normalizedAnswers.put("productPreferences", value);
                        break;
                    case "purchase_frequency":
                        normalizedAnswers.put("purchaseFrequency", value);
                        break;
                    case "information_preference":
                        normalizedAnswers.put("informationPreference", value);
                        break;
                    case "pregnancy_status":
                        normalizedAnswers.put("pregnancyStatus", value);
                        break;
                    default:
                        break;
                }
            });

            // Save to session first
            userSessionService.saveUserProfile(normalizedAnswers);
            
            // Persist to database if user is authenticated
            try {
                var currentUser = authService.getCurrentUser();
                if (currentUser != null && currentUser.getId() != null) {
                    userProfileService.saveProfileFromMap(currentUser.getId(), normalizedAnswers);
                }
            } catch (Exception dbError) {
                // Log but don't block - session is already saved
                System.err.println("Warning: Could not persist profile to database: " + dbError.getMessage());
            }

            Notification.show("¡Cuestionario completado! Ahora puedes subir una imagen para analizar.", 5000, Notification.Position.TOP_CENTER);

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
        private final String helperText;

        public QuestionStep(String title, String question, List<String> options, String key, boolean multiple, String helperText) {
            this.title = title;
            this.question = question;
            this.options = options;
            this.key = key;
            this.multiple = multiple;
            this.helperText = helperText;
        }

        public String getTitle() {
            return title;
        }

        public String getQuestion() {
            return question;
        }

        public List<String> getOptions() {
            return options;
        }

        public String getKey() {
            return key;
        }

        public boolean isMultiple() {
            return multiple;
        }

        public String getHelperText() {
            return helperText;
        }
    }
}
