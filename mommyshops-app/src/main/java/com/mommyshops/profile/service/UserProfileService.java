package com.mommyshops.profile.service;

import com.mommyshops.profile.domain.UserProfile;
import com.mommyshops.profile.repository.UserProfileRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.OffsetDateTime;
import java.util.Optional;
import java.util.UUID;

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
}