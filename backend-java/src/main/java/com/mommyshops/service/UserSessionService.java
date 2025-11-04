package com.mommyshops.service;

import org.springframework.stereotype.Service;
import org.springframework.web.context.annotation.SessionScope;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

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
        Object value = resolveValue("skin_type", "skinType");
        return value != null ? value.toString() : "normal";
    }
    
    public String getSkinConcerns() {
        Object concerns = resolveValue("skin_concerns", "skinConcerns");
        return formatList(concerns, "");
    }
    
    public String getAllergies() {
        Object allergies = resolveValue("allergies", "allergyPreferences");
        return formatList(allergies, "none");
    }
    
    public String getAvoidIngredients() {
        Object avoid = resolveValue("avoid_ingredients", "avoidIngredients");
        return formatList(avoid, "");
    }
    
    private Object resolveValue(String... keys) {
        for (String key : keys) {
            if (userProfile.containsKey(key)) {
                return userProfile.get(key);
            }
        }
        return null;
    }
    
    private String formatList(Object value, String defaultValue) {
        if (value instanceof List) {
            List<?> list = (List<?>) value;
            if (list.isEmpty()) {
                return defaultValue;
            }
            return list.stream()
                .map(Object::toString)
                .collect(Collectors.joining(", "));
        }
        if (value instanceof String) {
            String str = (String) value;
            return str.isBlank() ? defaultValue : str;
        }
        return defaultValue;
    }
}
