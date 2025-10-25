package com.mommyshops.config;

import io.github.resilience4j.ratelimiter.RateLimiter;
import io.github.resilience4j.ratelimiter.RateLimiterConfig;
import io.github.resilience4j.ratelimiter.RateLimiterRegistry;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.time.Duration;

/**
 * Rate limiting configuration to prevent DDoS attacks
 */
@Configuration
public class RateLimitConfig {

    @Bean
    public RateLimiterRegistry rateLimiterRegistry() {
        return RateLimiterRegistry.ofDefaults();
    }

    @Bean
    public RateLimiter generalRateLimiter(RateLimiterRegistry registry) {
        RateLimiterConfig config = RateLimiterConfig.custom()
                .limitForPeriod(100) // 100 requests
                .limitRefreshPeriod(Duration.ofSeconds(60)) // per minute
                .timeoutDuration(Duration.ofSeconds(1)) // wait 1 second
                .build();
        
        return registry.rateLimiter("general", config);
    }

    @Bean
    public RateLimiter analysisRateLimiter(RateLimiterRegistry registry) {
        RateLimiterConfig config = RateLimiterConfig.custom()
                .limitForPeriod(10) // 10 requests
                .limitRefreshPeriod(Duration.ofMinutes(1)) // per minute
                .timeoutDuration(Duration.ofSeconds(5)) // wait 5 seconds
                .build();
        
        return registry.rateLimiter("analysis", config);
    }

    @Bean
    public RateLimiter authRateLimiter(RateLimiterRegistry registry) {
        RateLimiterConfig config = RateLimiterConfig.custom()
                .limitForPeriod(5) // 5 requests
                .limitRefreshPeriod(Duration.ofMinutes(1)) // per minute
                .timeoutDuration(Duration.ofSeconds(2)) // wait 2 seconds
                .build();
        
        return registry.rateLimiter("auth", config);
    }
}
