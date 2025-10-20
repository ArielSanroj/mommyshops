package com.mommyshops.security.oauth2;

import com.mommyshops.auth.domain.UserAccount;
import com.mommyshops.auth.repository.UserAccountRepository;
import com.mommyshops.profile.domain.UserProfile;
import com.mommyshops.profile.repository.UserProfileRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.oauth2.client.oidc.userinfo.OidcUserRequest;
import org.springframework.security.oauth2.client.oidc.userinfo.OidcUserService;
import org.springframework.security.oauth2.core.oidc.user.OidcUser;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.OffsetDateTime;
import java.util.UUID;
import java.util.Set;

/**
 * Custom OIDC User Service
 * Handles OAuth2 user creation and profile management
 */
@Service
public class CustomOidcUserService extends OidcUserService {
    
    @Autowired
    private UserAccountRepository userAccountRepository;
    
    @Autowired
    private UserProfileRepository userProfileRepository;
    
    @Override
    @Transactional
    public OidcUser loadUser(OidcUserRequest userRequest) {
        OidcUser oidcUser = super.loadUser(userRequest);
        
        // Extract user information
        String email = oidcUser.getEmail();
        String name = oidcUser.getFullName();
        String picture = oidcUser.getPicture();
        
        // Check if user exists
        String googleSub = userRequest.getIdToken().getSubject();
        UserAccount userAccount = userAccountRepository.findByEmail(email)
            .orElseGet(() -> createUserAccount(email, name, picture, googleSub));
        
        // Update last login
        userAccount.setLastLoginAt(OffsetDateTime.now());
        userAccountRepository.save(userAccount);
        
        // Ensure user has a profile
        if (userProfileRepository.findByUserId(userAccount.getId()).isEmpty()) {
            createUserProfile(userAccount);
        }
        
        return oidcUser;
    }
    
    private UserAccount createUserAccount(String email, String name, String picture, String googleSub) {
        UserAccount userAccount = new UserAccount(
            UUID.randomUUID(),
            email,
            name,
            googleSub,
            OffsetDateTime.now(),
            Set.of("USER"),
            false,
            picture,
            "google",
            googleSub,
            OffsetDateTime.now(),
            true
        );
        userAccount.setId(UUID.randomUUID());
        userAccount.setEmail(email);
        userAccount.setName(name);
        userAccount.setPicture(picture);
        userAccount.setProvider("google");
        userAccount.setProviderId(email);
        userAccount.setCreatedAt(OffsetDateTime.now());
        userAccount.setLastLoginAt(OffsetDateTime.now());
        userAccount.setActive(true);
        
        return userAccountRepository.save(userAccount);
    }
    
    private void createUserProfile(UserAccount userAccount) {
        UserProfile userProfile = new UserProfile();
        userProfile.setId(UUID.randomUUID());
        userProfile.setUserId(userAccount.getId());
        userProfile.setFacialSkinPreferences("normal");
        userProfile.setEmail(userAccount.getEmail());
        userProfile.setSkinType("unknown");
        userProfile.setSkinConcerns("");
        userProfile.setAllergies("");
        userProfile.setPregnancyStatus("unknown");
        userProfile.setCreatedAt(OffsetDateTime.now());
        userProfile.setUpdatedAt(OffsetDateTime.now());
        
        userProfileRepository.save(userProfile);
    }
}