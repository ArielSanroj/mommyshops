package com.mommyshops.service;

import org.springframework.stereotype.Service;
import org.springframework.web.context.annotation.SessionScope;

import java.util.HashMap;
import java.util.Map;

@Service
@SessionScope
public class UserSessionService {
    
    private Map<String, Object> userProfile = new HashMap<>();
    private boolean questionnaireCompleted = false;
    
    public void saveUserProfile(Map<String, Object> profile) {
        this.userProfile = new HashMap<>(profile);
        this.questionnaireCompleted = true;
    }
    
    public Map<String, Object> getUserProfile() {
        return new HashMap<>(userProfile);
    }
    
    public boolean isQuestionnaireCompleted() {
        return questionnaireCompleted;
    }
    
    public void clearSession() {
        this.userProfile.clear();
        this.questionnaireCompleted = false;
    }
    
    public String getSkinType() {
        return (String) userProfile.getOrDefault("skin_type", "normal");
    }
    
    public String getSkinConcerns() {
        Object concerns = userProfile.get("skin_concerns");
        if (concerns instanceof java.util.List) {
            return String.join(", ", (java.util.List<String>) concerns);
        }
        return (String) concerns;
    }
    
    public String getAllergies() {
        return (String) userProfile.getOrDefault("allergies", "none");
    }
    
    public String getAvoidIngredients() {
        Object avoid = userProfile.get("avoid_ingredients");
        if (avoid instanceof java.util.List) {
            return String.join(", ", (java.util.List<String>) avoid);
        }
        return (String) avoid;
    }
}