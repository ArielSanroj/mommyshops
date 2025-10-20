package com.mommyshops.config;

import io.github.resilience4j.circuitbreaker.CircuitBreaker;
import io.github.resilience4j.circuitbreaker.CircuitBreakerConfig;
import io.github.resilience4j.ratelimiter.RateLimiter;
import io.github.resilience4j.ratelimiter.RateLimiterConfig;
import io.github.resilience4j.bulkhead.BulkheadConfig;
import io.github.resilience4j.bulkhead.Bulkhead;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.time.Duration;

/**
 * Resilience configuration for rate limiting, circuit breakers, and bulkheads
 */
@Configuration
public class ResilienceConfig {
    
    // Circuit Breaker Configuration
    @Bean
    public CircuitBreaker circuitBreaker() {
        CircuitBreakerConfig config = CircuitBreakerConfig.custom()
                .failureRateThreshold(50)
                .waitDurationInOpenState(Duration.ofSeconds(60))
                .slidingWindowSize(10)
                .minimumNumberOfCalls(5)
                .permittedNumberOfCallsInHalfOpenState(3)
                .build();
        
        return CircuitBreaker.of("external-api", config);
    }
    
    // Rate Limiter Configuration
    @Bean
    public RateLimiter rateLimiter() {
        RateLimiterConfig config = RateLimiterConfig.custom()
                .limitForPeriod(100)
                .limitRefreshPeriod(Duration.ofMinutes(1))
                .timeoutDuration(Duration.ofSeconds(1))
                .build();
        
        return RateLimiter.of("external-api", config);
    }
    
    // Bulkhead Configuration
    @Bean
    public Bulkhead bulkhead() {
        BulkheadConfig config = BulkheadConfig.custom()
                .maxConcurrentCalls(50)
                .maxWaitDuration(Duration.ofSeconds(1))
                .build();
        
        return Bulkhead.of("external-api", config);
    }
    
    // FDA API specific rate limiter
    @Bean("fdaRateLimiter")
    public RateLimiter fdaRateLimiter() {
        RateLimiterConfig config = RateLimiterConfig.custom()
                .limitForPeriod(60)
                .limitRefreshPeriod(Duration.ofMinutes(1))
                .timeoutDuration(Duration.ofSeconds(5))
                .build();
        
        return RateLimiter.of("fda-api", config);
    }
    
    // PubChem API specific rate limiter
    @Bean("pubchemRateLimiter")
    public RateLimiter pubchemRateLimiter() {
        RateLimiterConfig config = RateLimiterConfig.custom()
                .limitForPeriod(5)
                .limitRefreshPeriod(Duration.ofMinutes(1))
                .timeoutDuration(Duration.ofSeconds(10))
                .build();
        
        return RateLimiter.of("pubchem-api", config);
    }
    
    // EWG API specific rate limiter
    @Bean("ewgRateLimiter")
    public RateLimiter ewgRateLimiter() {
        RateLimiterConfig config = RateLimiterConfig.custom()
                .limitForPeriod(10)
                .limitRefreshPeriod(Duration.ofMinutes(1))
                .timeoutDuration(Duration.ofSeconds(5))
                .build();
        
        return RateLimiter.of("ewg-api", config);
    }
}