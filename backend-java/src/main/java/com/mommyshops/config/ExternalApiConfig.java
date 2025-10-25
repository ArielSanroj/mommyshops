package com.mommyshops.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.client.WebClient;

@Configuration
@ConfigurationProperties(prefix = "external.api")
public class ExternalApiConfig {
    
    private String fdaKey;
    private String ewgKey;
    private String pubchemBaseUrl = "https://pubchem.ncbi.nlm.nih.gov/rest/pug";
    private String whoBaseUrl = "https://ghoapi.azureedge.net/api";
    
    @Bean
    public WebClient webClient() {
        return WebClient.builder()
            .codecs(configurer -> configurer.defaultCodecs().maxInMemorySize(10 * 1024 * 1024))
            .build();
    }
    
    // Getters and setters
    public String getFdaKey() { return fdaKey; }
    public void setFdaKey(String fdaKey) { this.fdaKey = fdaKey; }
    
    public String getEwgKey() { return ewgKey; }
    public void setEwgKey(String ewgKey) { this.ewgKey = ewgKey; }
    
    public String getPubchemBaseUrl() { return pubchemBaseUrl; }
    public void setPubchemBaseUrl(String pubchemBaseUrl) { this.pubchemBaseUrl = pubchemBaseUrl; }
    
    public String getWhoBaseUrl() { return whoBaseUrl; }
    public void setWhoBaseUrl(String whoBaseUrl) { this.whoBaseUrl = whoBaseUrl; }
}