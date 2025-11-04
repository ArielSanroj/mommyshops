package com.mommyshops.profile.service;

import com.mommyshops.profile.domain.UserProfile;
import com.mommyshops.profile.repository.UserProfileRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import java.util.Map;
import java.util.stream.Collectors;

@Service
@Transactional
public class UserProfileService {
    
    private final UserProfileRepository userProfileRepository;
    
    @Autowired
    public UserProfileService(UserProfileRepository userProfileRepository) {
        this.userProfileRepository = userProfileRepository;
    }
    
    public UserProfile createProfile(UUID userId, String hairPreferences, String facialSkinPreferences, 
                                   String bodySkinPreferences, String budgetPreferences, String brandPreferences) {
        UserProfile profile = new UserProfile();
        profile.setId(UUID.randomUUID());
        profile.setUserId(userId);
        profile.setHairPreferences(hairPreferences);
        profile.setFacialSkinPreferences(facialSkinPreferences);
        profile.setBodySkinPreferences(bodySkinPreferences);
        profile.setBudgetPreferences(budgetPreferences);
        profile.setBrandPreferences(brandPreferences);
        profile.setCreatedAt(OffsetDateTime.now());
        profile.setUpdatedAt(OffsetDateTime.now());
        
        return userProfileRepository.save(profile);
    }
    
    public UserProfile updateProfile(UUID userId, String hairPreferences, String facialSkinPreferences, 
                                   String bodySkinPreferences, String budgetPreferences, String brandPreferences) {
        Optional<UserProfile> existingProfile = userProfileRepository.findByUserId(userId);
        
        if (existingProfile.isPresent()) {
            UserProfile profile = existingProfile.get();
            profile.setHairPreferences(hairPreferences);
            profile.setFacialSkinPreferences(facialSkinPreferences);
            profile.setBodySkinPreferences(bodySkinPreferences);
            profile.setBudgetPreferences(budgetPreferences);
            profile.setBrandPreferences(brandPreferences);
            profile.setUpdatedAt(OffsetDateTime.now());
            
            return userProfileRepository.save(profile);
        } else {
            return createProfile(userId, hairPreferences, facialSkinPreferences, 
                               bodySkinPreferences, budgetPreferences, brandPreferences);
        }
    }
    
    public Optional<UserProfile> getProfileByUserId(UUID userId) {
        return userProfileRepository.findByUserId(userId);
    }
    
    public UserProfile saveProfile(UserProfile profile) {
        return userProfileRepository.save(profile);
    }
    
    /**
     * Save or update user profile from questionnaire answers map
     * Handles both snake_case and camelCase keys, and converts lists to comma-separated strings
     */
    public UserProfile saveProfileFromMap(UUID userId, Map<String, Object> profileMap) {
        Optional<UserProfile> existingProfile = userProfileRepository.findByUserId(userId);
        UserProfile profile = existingProfile.orElse(new UserProfile());
        
        if (profile.getId() == null) {
            profile.setId(UUID.randomUUID());
            profile.setUserId(userId);
            profile.setCreatedAt(OffsetDateTime.now());
        }
        profile.setUpdatedAt(OffsetDateTime.now());
        
        // Helper to resolve value (supports both snake_case and camelCase)
        java.util.function.Function<String[], Object> resolveValue = keys -> {
            for (String key : keys) {
                Object value = profileMap.get(key);
                if (value != null) {
                    return value;
                }
            }
            return null;
        };
        
        // Helper to format list values
        java.util.function.Function<Object, String> formatList = value -> {
            if (value instanceof List) {
                List<?> list = (List<?>) value;
                return list.stream()
                        .map(Object::toString)
                        .collect(Collectors.joining(", "));
            }
            return value != null ? value.toString() : null;
        };
        
        // Map all fields from questionnaire
        Object value;
        
        if ((value = resolveValue.apply(new String[]{"age", "age"})) != null) {
            profile.setAge(value.toString());
        }
        if ((value = resolveValue.apply(new String[]{"pregnancy_status", "pregnancyStatus"})) != null) {
            profile.setPregnancyStatus(value.toString());
        }
        if ((value = resolveValue.apply(new String[]{"skin_type", "skinType"})) != null) {
            profile.setSkinType(value.toString());
        }
        if ((value = resolveValue.apply(new String[]{"skin_reactivity", "skinReactivity"})) != null) {
            profile.setSkinReactivity(value.toString());
        }
        if ((value = resolveValue.apply(new String[]{"skin_concerns", "skinConcerns"})) != null) {
            profile.setSkinConcerns(formatList.apply(value));
        }
        if ((value = resolveValue.apply(new String[]{"skin_goals", "skinGoals"})) != null) {
            profile.setSkinGoals(formatList.apply(value));
        }
        if ((value = resolveValue.apply(new String[]{"face_shape", "faceShape"})) != null) {
            profile.setFaceShape(value.toString());
        }
        if ((value = resolveValue.apply(new String[]{"hair_type", "hairType"})) != null) {
            profile.setHairType(value.toString());
        }
        if ((value = resolveValue.apply(new String[]{"hair_porosity", "hairPorosity"})) != null) {
            profile.setHairPorosity(value.toString());
        }
        if ((value = resolveValue.apply(new String[]{"scalp_condition", "scalpCondition"})) != null) {
            profile.setScalpCondition(value.toString());
        }
        if ((value = resolveValue.apply(new String[]{"hair_concerns", "hairConcerns"})) != null) {
            profile.setHairConcerns(formatList.apply(value));
        }
        if ((value = resolveValue.apply(new String[]{"hair_routine", "hairRoutine"})) != null) {
            profile.setHairRoutine(formatList.apply(value));
        }
        if ((value = resolveValue.apply(new String[]{"fragrance_preference", "fragrancePreference"})) != null) {
            profile.setFragrancePreference(value.toString());
        }
        if ((value = resolveValue.apply(new String[]{"texture_preferences", "texturePreferences"})) != null) {
            profile.setTexturePreferences(formatList.apply(value));
        }
        if ((value = resolveValue.apply(new String[]{"allergies", "allergyPreferences"})) != null) {
            profile.setAllergies(formatList.apply(value));
        }
        if ((value = resolveValue.apply(new String[]{"avoid_ingredients", "avoidIngredients"})) != null) {
            profile.setAvoidIngredients(formatList.apply(value));
        }
        if ((value = resolveValue.apply(new String[]{"ingredient_focus", "ingredientFocus"})) != null) {
            profile.setIngredientFocus(formatList.apply(value));
        }
        if ((value = resolveValue.apply(new String[]{"environment_factors", "environmentFactors"})) != null) {
            profile.setEnvironmentFactors(formatList.apply(value));
        }
        if ((value = resolveValue.apply(new String[]{"product_preferences", "productPreferences"})) != null) {
            profile.setProductPreferences(value.toString());
        }
        if ((value = resolveValue.apply(new String[]{"budget", "budget"})) != null) {
            profile.setBudget(value.toString());
        }
        if ((value = resolveValue.apply(new String[]{"purchase_frequency", "purchaseFrequency"})) != null) {
            profile.setPurchaseFrequency(value.toString());
        }
        if ((value = resolveValue.apply(new String[]{"information_preference", "informationPreference"})) != null) {
            profile.setInformationPreference(value.toString());
        }
        
        return userProfileRepository.save(profile);
    }
}