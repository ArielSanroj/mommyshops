package com.mommyshops.profile.domain;

import jakarta.persistence.*;
import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Table(name = "user_profiles")
public class UserProfile {
    
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;
    
    @Column(name = "user_id", nullable = false, unique = true)
    private UUID userId;
    
    @Column(name = "hair_preferences")
    private String hairPreferences;
    
    @Column(name = "facial_skin_preferences")
    private String facialSkinPreferences;
    
    @Column(name = "body_skin_preferences")
    private String bodySkinPreferences;
    
    @Column(name = "budget_preferences")
    private String budgetPreferences;
    
    @Column(name = "brand_preferences")
    private String brandPreferences;
    
    @Column(name = "email")
    private String email;
    
    @Column(name = "skin_type")
    private String skinType;
    
    @Column(name = "skin_concerns")
    private String skinConcerns;
    
    @Column(name = "allergies")
    private String allergies;
    
    @Column(name = "pregnancy_status")
    private String pregnancyStatus;
    
    // Extended questionnaire fields
    @Column(name = "age")
    private String age;
    
    @Column(name = "skin_reactivity")
    private String skinReactivity;
    
    @Column(name = "skin_goals", columnDefinition = "TEXT")
    private String skinGoals; // Stored as comma-separated list
    
    @Column(name = "face_shape")
    private String faceShape;
    
    @Column(name = "hair_type")
    private String hairType;
    
    @Column(name = "hair_porosity")
    private String hairPorosity;
    
    @Column(name = "scalp_condition")
    private String scalpCondition;
    
    @Column(name = "hair_concerns", columnDefinition = "TEXT")
    private String hairConcerns; // Stored as comma-separated list
    
    @Column(name = "hair_routine", columnDefinition = "TEXT")
    private String hairRoutine; // Stored as comma-separated list
    
    @Column(name = "fragrance_preference")
    private String fragrancePreference;
    
    @Column(name = "texture_preferences", columnDefinition = "TEXT")
    private String texturePreferences; // Stored as comma-separated list
    
    @Column(name = "avoid_ingredients", columnDefinition = "TEXT")
    private String avoidIngredients; // Stored as comma-separated list
    
    @Column(name = "ingredient_focus", columnDefinition = "TEXT")
    private String ingredientFocus; // Stored as comma-separated list
    
    @Column(name = "environment_factors", columnDefinition = "TEXT")
    private String environmentFactors; // Stored as comma-separated list
    
    @Column(name = "product_preferences")
    private String productPreferences;
    
    @Column(name = "budget")
    private String budget;
    
    @Column(name = "purchase_frequency")
    private String purchaseFrequency;
    
    @Column(name = "information_preference")
    private String informationPreference;
    
    @Column(name = "created_at", nullable = false)
    private OffsetDateTime createdAt;
    
    @Column(name = "updated_at")
    private OffsetDateTime updatedAt;
    
    // Constructors
    public UserProfile() {}
    
    public UserProfile(UUID id, UUID userId, String hairPreferences, String facialSkinPreferences, 
                      String bodySkinPreferences, String budgetPreferences, String brandPreferences, 
                      OffsetDateTime createdAt, OffsetDateTime updatedAt) {
        this.id = id;
        this.userId = userId;
        this.hairPreferences = hairPreferences;
        this.facialSkinPreferences = facialSkinPreferences;
        this.bodySkinPreferences = bodySkinPreferences;
        this.budgetPreferences = budgetPreferences;
        this.brandPreferences = brandPreferences;
        this.createdAt = createdAt;
        this.updatedAt = updatedAt;
    }
    
    // Getters and setters
    public UUID getId() { return id; }
    public void setId(UUID id) { this.id = id; }
    
    public UUID getUserId() { return userId; }
    public void setUserId(UUID userId) { this.userId = userId; }
    
    public String getHairPreferences() { return hairPreferences; }
    public void setHairPreferences(String hairPreferences) { this.hairPreferences = hairPreferences; }
    
    public String getFacialSkinPreferences() { return facialSkinPreferences; }
    public void setFacialSkinPreferences(String facialSkinPreferences) { this.facialSkinPreferences = facialSkinPreferences; }
    
    public String getBodySkinPreferences() { return bodySkinPreferences; }
    public void setBodySkinPreferences(String bodySkinPreferences) { this.bodySkinPreferences = bodySkinPreferences; }
    
    public String getBudgetPreferences() { return budgetPreferences; }
    public void setBudgetPreferences(String budgetPreferences) { this.budgetPreferences = budgetPreferences; }
    
    public String getBrandPreferences() { return brandPreferences; }
    public void setBrandPreferences(String brandPreferences) { this.brandPreferences = brandPreferences; }
    
    public OffsetDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(OffsetDateTime createdAt) { this.createdAt = createdAt; }
    
    public OffsetDateTime getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(OffsetDateTime updatedAt) { this.updatedAt = updatedAt; }
    
    // Additional getters and setters
    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }
    
    public String getSkinType() { return skinType; }
    public void setSkinType(String skinType) { this.skinType = skinType; }
    
    public String getSkinConcerns() { return skinConcerns; }
    public void setSkinConcerns(String skinConcerns) { this.skinConcerns = skinConcerns; }
    
    public String getAllergies() { return allergies; }
    public void setAllergies(String allergies) { this.allergies = allergies; }
    
    public String getPregnancyStatus() { return pregnancyStatus; }
    public void setPregnancyStatus(String pregnancyStatus) { this.pregnancyStatus = pregnancyStatus; }
    
    // Extended questionnaire getters and setters
    public String getAge() { return age; }
    public void setAge(String age) { this.age = age; }
    
    public String getSkinReactivity() { return skinReactivity; }
    public void setSkinReactivity(String skinReactivity) { this.skinReactivity = skinReactivity; }
    
    public String getSkinGoals() { return skinGoals; }
    public void setSkinGoals(String skinGoals) { this.skinGoals = skinGoals; }
    
    public String getFaceShape() { return faceShape; }
    public void setFaceShape(String faceShape) { this.faceShape = faceShape; }
    
    public String getHairType() { return hairType; }
    public void setHairType(String hairType) { this.hairType = hairType; }
    
    public String getHairPorosity() { return hairPorosity; }
    public void setHairPorosity(String hairPorosity) { this.hairPorosity = hairPorosity; }
    
    public String getScalpCondition() { return scalpCondition; }
    public void setScalpCondition(String scalpCondition) { this.scalpCondition = scalpCondition; }
    
    public String getHairConcerns() { return hairConcerns; }
    public void setHairConcerns(String hairConcerns) { this.hairConcerns = hairConcerns; }
    
    public String getHairRoutine() { return hairRoutine; }
    public void setHairRoutine(String hairRoutine) { this.hairRoutine = hairRoutine; }
    
    public String getFragrancePreference() { return fragrancePreference; }
    public void setFragrancePreference(String fragrancePreference) { this.fragrancePreference = fragrancePreference; }
    
    public String getTexturePreferences() { return texturePreferences; }
    public void setTexturePreferences(String texturePreferences) { this.texturePreferences = texturePreferences; }
    
    public String getAvoidIngredients() { return avoidIngredients; }
    public void setAvoidIngredients(String avoidIngredients) { this.avoidIngredients = avoidIngredients; }
    
    public String getIngredientFocus() { return ingredientFocus; }
    public void setIngredientFocus(String ingredientFocus) { this.ingredientFocus = ingredientFocus; }
    
    public String getEnvironmentFactors() { return environmentFactors; }
    public void setEnvironmentFactors(String environmentFactors) { this.environmentFactors = environmentFactors; }
    
    public String getProductPreferences() { return productPreferences; }
    public void setProductPreferences(String productPreferences) { this.productPreferences = productPreferences; }
    
    public String getBudget() { return budget; }
    public void setBudget(String budget) { this.budget = budget; }
    
    public String getPurchaseFrequency() { return purchaseFrequency; }
    public void setPurchaseFrequency(String purchaseFrequency) { this.purchaseFrequency = purchaseFrequency; }
    
    public String getInformationPreference() { return informationPreference; }
    public void setInformationPreference(String informationPreference) { this.informationPreference = informationPreference; }
}