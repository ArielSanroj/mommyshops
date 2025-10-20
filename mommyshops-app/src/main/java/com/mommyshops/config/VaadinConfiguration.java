package com.mommyshops.config;

import com.vaadin.flow.component.page.AppShellConfigurator;
import com.vaadin.flow.server.PWA;
import com.vaadin.flow.theme.Theme;
import com.vaadin.flow.theme.lumo.Lumo;
import com.vaadin.flow.spring.annotation.EnableVaadin;
import org.springframework.context.annotation.Configuration;

@Configuration
@EnableVaadin
@Theme(themeClass = Lumo.class)
@PWA(name = "MommyShops", shortName = "MommyShops", description = "Análisis de productos cosméticos")
public class VaadinConfiguration implements AppShellConfigurator {
}