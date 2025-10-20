package com.mommyshops.integration.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.ResponseEntity;
import java.util.Map;

@Service
public class ExternalApiService {
    
    private final RestTemplate restTemplate;
    private final EWGService ewgService;
    private final String fdaApiKey;
    
    public ExternalApiService(RestTemplate restTemplate,
                            EWGService ewgService,
                            @Value("${external.api.fda.key:}") String fdaApiKey,
                            ) {
        this.restTemplate = restTemplate;
        this.ewgService = ewgService;
        this.fdaApiKey = fdaApiKey;
    }
    
    public Map<String, Object> getFdaAdverseEvents(String ingredient) {
        try {
            String url = String.format(
                "https://api.fda.gov/drug/event.json?search=patient.drug.medicinalproduct:%s&limit=10&api_key=%s",
                ingredient, fdaApiKey
            );
            ResponseEntity<Map> response = restTemplate.getForEntity(url, Map.class);
            return response.getBody();
        } catch (Exception e) {
            return Map.of("error", "FDA API unavailable");
        }
    }
    
    public Map<String, Object> getPubChemData(String ingredient) {
        try {
            String url = String.format(
                "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/%s/property/Description/JSON",
                ingredient
            );
            ResponseEntity<Map> response = restTemplate.getForEntity(url, Map.class);
            return response.getBody();
        } catch (Exception e) {
            return Map.of("error", "PubChem API unavailable");
        }
    }
    
    public Map<String, Object> getEwgSkinDeepData(String ingredient) {
        try {
            // Use the new EWGService for web scraping
            return ewgService.getIngredientData(ingredient);
        } catch (Exception e) {
            return Map.of("error", "EWG data unavailable", "message", e.getMessage());
        }
    }
    
    public Map<String, Object> getWhoHealthData(String ingredient) {
        try {
            String url = String.format(
                "https://ghoapi.azureedge.net/api/Indicator?$filter=contains(IndicatorName,'%s')",
                ingredient
            );
            ResponseEntity<Map> response = restTemplate.getForEntity(url, Map.class);
            return response.getBody();
        } catch (Exception e) {
            return Map.of("error", "WHO API unavailable");
        }
    }
}