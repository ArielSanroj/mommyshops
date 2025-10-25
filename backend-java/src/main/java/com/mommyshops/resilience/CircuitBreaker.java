package com.mommyshops.resilience;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;

@Component
public class CircuitBreaker {
    
    private static final Logger logger = LoggerFactory.getLogger(CircuitBreaker.class);
    
    public enum State {
        CLOSED, OPEN, HALF_OPEN
    }
    
    private final String name;
    private final int failureThreshold;
    private final int recoveryTimeoutSeconds;
    private final int successThreshold;
    
    private final AtomicReference<State> state = new AtomicReference<>(State.CLOSED);
    private final AtomicInteger failureCount = new AtomicInteger(0);
    private final AtomicInteger successCount = new AtomicInteger(0);
    private final AtomicReference<LocalDateTime> lastFailureTime = new AtomicReference<>();
    
    public CircuitBreaker(String name, int failureThreshold, int recoveryTimeoutSeconds, int successThreshold) {
        this.name = name;
        this.failureThreshold = failureThreshold;
        this.recoveryTimeoutSeconds = recoveryTimeoutSeconds;
        this.successThreshold = successThreshold;
    }
    
    public boolean canExecute() {
        State currentState = state.get();
        
        if (currentState == State.CLOSED) {
            return true;
        }
        
        if (currentState == State.OPEN) {
            if (shouldAttemptReset()) {
                state.set(State.HALF_OPEN);
                return true;
            }
            return false;
        }
        
        if (currentState == State.HALF_OPEN) {
            return true;
        }
        
        return false;
    }
    
    public void recordSuccess() {
        State currentState = state.get();
        
        if (currentState == State.HALF_OPEN) {
            int currentSuccessCount = successCount.incrementAndGet();
            if (currentSuccessCount >= successThreshold) {
                reset();
            }
        } else if (currentState == State.CLOSED) {
            failureCount.set(0);
        }
    }
    
    public void recordFailure() {
        int currentFailureCount = failureCount.incrementAndGet();
        lastFailureTime.set(LocalDateTime.now());
        
        if (currentFailureCount >= failureThreshold) {
            state.set(State.OPEN);
            logger.warn("Circuit breaker {} opened due to {} failures", name, currentFailureCount);
        }
    }
    
    private boolean shouldAttemptReset() {
        LocalDateTime lastFailure = lastFailureTime.get();
        if (lastFailure == null) {
            return true;
        }
        
        return ChronoUnit.SECONDS.between(lastFailure, LocalDateTime.now()) >= recoveryTimeoutSeconds;
    }
    
    private void reset() {
        state.set(State.CLOSED);
        failureCount.set(0);
        successCount.set(0);
        lastFailureTime.set(null);
        logger.info("Circuit breaker {} reset to closed state", name);
    }
    
    public State getState() {
        return state.get();
    }
    
    public int getFailureCount() {
        return failureCount.get();
    }
    
    public int getSuccessCount() {
        return successCount.get();
    }
    
    public String getName() {
        return name;
    }
}
