package com.mommyshops.config;

import com.mommyshops.resilience.CircuitBreaker;
import com.mommyshops.resilience.RetryHandler;
import com.mommyshops.resilience.ResilientAPIClient;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestTemplate;

import java.time.Duration;

@Configuration
public class ResilienceConfig {
    
    @Bean
    public RestTemplate restTemplate() {
        return new RestTemplate();
    }
    
    @Bean
    public ResilientAPIClient resilientAPIClient() {
        return new ResilientAPIClient();
    }
    
    @Bean
    public CircuitBreaker fdaCircuitBreaker() {
        return new CircuitBreaker("FDA_API", 3, 30, 2);
    }
    
    @Bean
    public CircuitBreaker pubchemCircuitBreaker() {
        return new CircuitBreaker("PUBCHEM_API", 5, 60, 3);
    }
    
    @Bean
    public CircuitBreaker ewgCircuitBreaker() {
        return new CircuitBreaker("EWG_API", 3, 45, 2);
    }
    
    @Bean
    public RetryHandler fdaRetryHandler() {
        return new RetryHandler.Builder()
            .maxAttempts(3)
            .baseDelay(Duration.ofSeconds(1))
            .maxDelay(Duration.ofMinutes(1))
            .strategy(RetryHandler.Strategy.EXPONENTIAL)
            .backoffFactor(2.0)
            .jitter(true)
            .build();
    }
    
    @Bean
    public RetryHandler pubchemRetryHandler() {
        return new RetryHandler.Builder()
            .maxAttempts(3)
            .baseDelay(Duration.ofSeconds(2))
            .maxDelay(Duration.ofMinutes(2))
            .strategy(RetryHandler.Strategy.EXPONENTIAL)
            .backoffFactor(2.0)
            .jitter(true)
            .build();
    }
    
    @Bean
    public RetryHandler ewgRetryHandler() {
        return new RetryHandler.Builder()
            .maxAttempts(2)
            .baseDelay(Duration.ofMillis(1500))
            .maxDelay(Duration.ofMinutes(1))
            .strategy(RetryHandler.Strategy.LINEAR)
            .backoffFactor(1.5)
            .jitter(true)
            .build();
    }
}