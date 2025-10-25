package com.mommyshops.view;

import com.vaadin.flow.component.button.Button;
import com.vaadin.flow.component.html.H3;
import com.vaadin.flow.component.html.Paragraph;
import com.vaadin.flow.component.orderedlayout.HorizontalLayout;
import com.vaadin.flow.component.orderedlayout.VerticalLayout;
import com.vaadin.flow.router.PageTitle;
import com.vaadin.flow.router.Route;

@Route("about")
@PageTitle("Acerca de - MommyShops")
public class AboutView extends VerticalLayout {
    
    public AboutView() {
        setupLayout();
        setupButtons();
    }
    
    private void setupLayout() {
        setSizeFull();
        setPadding(true);
        setSpacing(true);
        
        H3 title = new H3("Acerca de MommyShops");
        add(title);
        
        Paragraph description = new Paragraph(
            "MommyShops es una plataforma innovadora que utiliza inteligencia artificial " +
            "para analizar productos cosméticos y proporcionar recomendaciones personalizadas " +
            "basadas en tu perfil y necesidades específicas."
        );
        add(description);
        
        H3 featuresTitle = new H3("Características Principales");
        add(featuresTitle);
        
        VerticalLayout featuresList = new VerticalLayout();
        featuresList.setPadding(false);
        featuresList.setSpacing(true);
        
        String[] features = {
            "Análisis detallado de ingredientes usando múltiples bases de datos (EWG, INCI, COSING)",
            "Cuestionario de personalización para adaptar las recomendaciones a tu perfil",
            "Identificación de ingredientes de riesgo y sus alternativas más seguras",
            "Recomendaciones de productos sustitutos basadas en tus preferencias",
            "Interfaz intuitiva y fácil de usar"
        };
        
        for (String feature : features) {
            Paragraph featureItem = new Paragraph("• " + feature);
            featuresList.add(featureItem);
        }
        
        add(featuresList);
        
        H3 howItWorksTitle = new H3("Cómo Funciona");
        add(howItWorksTitle);
        
        String[] steps = {
            "Completa nuestro cuestionario de personalización",
            "Sube una imagen de tu producto o proporciona una URL",
            "Nuestro sistema analiza los ingredientes usando IA",
            "Recibe un reporte detallado con recomendaciones personalizadas"
        };
        
        for (int i = 0; i < steps.length; i++) {
            Paragraph step = new Paragraph((i + 1) + ". " + steps[i]);
            add(step);
        }
    }
    
    private void setupButtons() {
        Button backButton = new Button("Volver al Inicio");
        backButton.addClickListener(e -> getUI().ifPresent(ui -> ui.navigate("")));
        
        Button startButton = new Button("Comenzar Análisis");
        startButton.getStyle().set("background-color", "#4CAF50");
        startButton.getStyle().set("color", "white");
        startButton.addClickListener(e -> getUI().ifPresent(ui -> ui.navigate("questionnaire")));
        
        HorizontalLayout buttonLayout = new HorizontalLayout(backButton, startButton);
        buttonLayout.setSpacing(true);
        add(buttonLayout);
    }
}