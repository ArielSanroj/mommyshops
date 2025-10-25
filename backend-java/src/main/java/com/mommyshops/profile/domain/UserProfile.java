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
}