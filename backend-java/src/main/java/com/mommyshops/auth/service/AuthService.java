package com.mommyshops.auth.service;

import com.mommyshops.auth.domain.UserAccount;
import com.mommyshops.auth.repository.UserAccountRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.stereotype.Service;

import java.util.Optional;
import java.util.UUID;

@Service
public class AuthService {
    
    private final UserAccountRepository userAccountRepository;
    
    @Autowired
    public AuthService(UserAccountRepository userAccountRepository) {
        this.userAccountRepository = userAccountRepository;
    }
    
    public UserAccount getCurrentUser() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        if (auth == null || !auth.isAuthenticated()) {
            return null;
        }
        
        if (auth.getPrincipal() instanceof OAuth2User oauth2User) {
            String email = oauth2User.getAttribute("email");
            if (email != null) {
                return getUserByEmail(email);
            }
        }
        
        return null;
    }
    
    public UserAccount getUserByEmail(String email) {
        Optional<UserAccount> user = userAccountRepository.findByEmail(email);
        if (user.isPresent()) {
            return user.get();
        }
        
        // Create new user if not found
        return createUserFromOAuth(email);
    }
    
    private UserAccount createUserFromOAuth(String email) {
        UserAccount user = new UserAccount(
            UUID.randomUUID(),
            email,
            email, // Will be updated from OAuth data
            UUID.randomUUID().toString(), // Placeholder
            java.time.OffsetDateTime.now(),
            java.util.Set.of("USER"),
            false
        );
        
        return userAccountRepository.save(user);
    }
}