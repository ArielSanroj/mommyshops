package com.mommyshops.resilience;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.web.client.RestClientException;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.function.Supplier;

@Component
public class ResilientAPIClient {
    
    private static final Logger logger = LoggerFactory.getLogger(ResilientAPIClient.class);
    
    @Autowired
    private RestTemplate restTemplate;
    
    private final Map<String, CircuitBreaker> circuitBreakers = new ConcurrentHashMap<>();
    private final Map<String, RetryHandler> retryHandlers = new ConcurrentHashMap<>();
    
    public <T> T executeWithResilience(String operationName, Supplier<T> operation) {
        CircuitBreaker circuitBreaker = getCircuitBreaker(operationName);
        RetryHandler retryHandler = getRetryHandler(operationName);
        
        // Check circuit breaker
        if (!circuitBreaker.canExecute()) {
            throw new RuntimeException("Circuit breaker is open for operation: " + operationName);
        }
        
        try {
            T result = retryHandler.executeWithRetry(operation, operationName);
            circuitBreaker.recordSuccess();
            return result;
        } catch (Exception e) {
            circuitBreaker.recordFailure();
            throw e;
        }
    }
    
    public <T> ResponseEntity<T> get(String url, Class<T> responseType, Map<String, String> headers) {
        return executeWithResilience("GET_" + url, () -> {
            HttpHeaders httpHeaders = new HttpHeaders();
            if (headers != null) {
                headers.forEach(httpHeaders::set);
            }
            HttpEntity<?> entity = new HttpEntity<>(httpHeaders);
            return restTemplate.exchange(url, HttpMethod.GET, entity, responseType);
        });
    }
    
    public <T> ResponseEntity<T> post(String url, Object requestBody, Class<T> responseType, Map<String, String> headers) {
        return executeWithResilience("POST_" + url, () -> {
            HttpHeaders httpHeaders = new HttpHeaders();
            if (headers != null) {
                headers.forEach(httpHeaders::set);
            }
            HttpEntity<Object> entity = new HttpEntity<>(requestBody, httpHeaders);
            return restTemplate.exchange(url, HttpMethod.POST, entity, responseType);
        });
    }
    
    private CircuitBreaker getCircuitBreaker(String operationName) {
        return circuitBreakers.computeIfAbsent(operationName, name -> 
            new CircuitBreaker(name, 5, 60, 3)
        );
    }
    
    private RetryHandler getRetryHandler(String operationName) {
        return retryHandlers.computeIfAbsent(operationName, name -> 
            new RetryHandler.Builder()
                .maxAttempts(3)
                .baseDelay(java.time.Duration.ofSeconds(1))
                .maxDelay(java.time.Duration.ofMinutes(1))
                .strategy(RetryHandler.Strategy.EXPONENTIAL)
                .backoffFactor(2.0)
                .jitter(true)
                .build()
        );
    }
    
    public Map<String, Object> getResilienceStats() {
        Map<String, Object> stats = new ConcurrentHashMap<>();
        
        circuitBreakers.forEach((name, breaker) -> {
            stats.put("circuit_breaker_" + name, Map.of(
                "state", breaker.getState().toString(),
                "failure_count", breaker.getFailureCount(),
                "success_count", breaker.getSuccessCount()
            ));
        });
        
        return stats;
    }
}
