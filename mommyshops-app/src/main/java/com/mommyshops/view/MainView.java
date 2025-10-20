package com.mommyshops.view;

import com.vaadin.flow.component.button.Button;
import com.vaadin.flow.component.html.H1;
import com.vaadin.flow.component.html.Paragraph;
import com.vaadin.flow.component.orderedlayout.HorizontalLayout;
import com.vaadin.flow.component.orderedlayout.VerticalLayout;
import com.vaadin.flow.router.PageTitle;
import com.vaadin.flow.router.Route;

@Route("")
@PageTitle("MommyShops - Análisis de Productos Cosméticos")
public class MainView extends VerticalLayout {
    
    public MainView() {
        setupLayout();
        setupButtons();
    }
    
    private void setupLayout() {
        setSizeFull();
        setPadding(true);
        setSpacing(true);
        setAlignItems(Alignment.CENTER);
        
        H1 title = new H1("MommyShops");
        title.getStyle().set("color", "#2E7D32");
        add(title);
        
        Paragraph subtitle = new Paragraph("Análisis inteligente de productos cosméticos para tu familia");
        subtitle.getStyle().set("font-size", "1.2em");
        subtitle.getStyle().set("color", "#666");
        add(subtitle);
        
        Paragraph description = new Paragraph(
            "Descubre qué ingredientes contienen tus productos cosméticos y obtén recomendaciones " +
            "personalizadas basadas en tu perfil y necesidades específicas."
        );
        description.getStyle().set("text-align", "center");
        description.getStyle().set("max-width", "600px");
        add(description);
    }
    
    private void setupButtons() {
        Button startButton = new Button("Comenzar Análisis");
        startButton.getStyle().set("background-color", "#4CAF50");
        startButton.getStyle().set("color", "white");
        startButton.getStyle().set("padding", "15px 30px");
        startButton.getStyle().set("font-size", "1.1em");
        startButton.addClickListener(e -> 
            getUI().ifPresent(ui -> ui.navigate("questionnaire"))
        );
        
        Button learnMoreButton = new Button("Aprender Más");
        learnMoreButton.getStyle().set("background-color", "#2196F3");
        learnMoreButton.getStyle().set("color", "white");
        learnMoreButton.getStyle().set("padding", "15px 30px");
        learnMoreButton.getStyle().set("font-size", "1.1em");
        learnMoreButton.addClickListener(e -> 
            getUI().ifPresent(ui -> ui.navigate("about"))
        );
        
        HorizontalLayout buttonLayout = new HorizontalLayout(startButton, learnMoreButton);
        buttonLayout.setSpacing(true);
        add(buttonLayout);
    }
}