package com.mommyshops.resilience;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.time.Duration;
import java.util.function.Supplier;

@Component
public class RetryHandler {
    
    private static final Logger logger = LoggerFactory.getLogger(RetryHandler.class);
    
    public enum Strategy {
        FIXED, EXPONENTIAL, LINEAR
    }
    
    private final int maxAttempts;
    private final Duration baseDelay;
    private final Duration maxDelay;
    private final Strategy strategy;
    private final double backoffFactor;
    private final boolean jitter;
    
    public RetryHandler(int maxAttempts, Duration baseDelay, Duration maxDelay, 
                       Strategy strategy, double backoffFactor, boolean jitter) {
        this.maxAttempts = maxAttempts;
        this.baseDelay = baseDelay;
        this.maxDelay = maxDelay;
        this.strategy = strategy;
        this.backoffFactor = backoffFactor;
        this.jitter = jitter;
    }
    
    public <T> T executeWithRetry(Supplier<T> operation, String operationName) {
        Exception lastException = null;
        
        for (int attempt = 0; attempt < maxAttempts; attempt++) {
            try {
                return operation.get();
            } catch (Exception e) {
                lastException = e;
                
                if (attempt == maxAttempts - 1) {
                    logger.error("All retry attempts failed for {}: {}", operationName, e.getMessage());
                    throw new RuntimeException("Operation failed after " + maxAttempts + " attempts", e);
                }
                
                Duration delay = calculateDelay(attempt);
                logger.warn("Attempt {} failed for {}, retrying in {}ms: {}", 
                    attempt + 1, operationName, delay.toMillis(), e.getMessage());
                
                try {
                    Thread.sleep(delay.toMillis());
                } catch (InterruptedException ie) {
                    Thread.currentThread().interrupt();
                    throw new RuntimeException("Retry interrupted", ie);
                }
            }
        }
        
        throw new RuntimeException("Operation failed after " + maxAttempts + " attempts", lastException);
    }
    
    private Duration calculateDelay(int attempt) {
        Duration delay;
        
        switch (strategy) {
            case FIXED:
                delay = baseDelay;
                break;
            case EXPONENTIAL:
                delay = Duration.ofMillis((long) (baseDelay.toMillis() * Math.pow(backoffFactor, attempt)));
                break;
            case LINEAR:
                delay = Duration.ofMillis(baseDelay.toMillis() * (attempt + 1));
                break;
            default:
                delay = baseDelay;
        }
        
        // Apply jitter
        if (jitter) {
            long jitterMs = (long) (delay.toMillis() * 0.1 * Math.random());
            delay = delay.plusMillis(jitterMs);
        }
        
        return delay.compareTo(maxDelay) > 0 ? maxDelay : delay;
    }
    
    public static class Builder {
        private int maxAttempts = 3;
        private Duration baseDelay = Duration.ofSeconds(1);
        private Duration maxDelay = Duration.ofMinutes(1);
        private Strategy strategy = Strategy.EXPONENTIAL;
        private double backoffFactor = 2.0;
        private boolean jitter = true;
        
        public Builder maxAttempts(int maxAttempts) {
            this.maxAttempts = maxAttempts;
            return this;
        }
        
        public Builder baseDelay(Duration baseDelay) {
            this.baseDelay = baseDelay;
            return this;
        }
        
        public Builder maxDelay(Duration maxDelay) {
            this.maxDelay = maxDelay;
            return this;
        }
        
        public Builder strategy(Strategy strategy) {
            this.strategy = strategy;
            return this;
        }
        
        public Builder backoffFactor(double backoffFactor) {
            this.backoffFactor = backoffFactor;
            return this;
        }
        
        public Builder jitter(boolean jitter) {
            this.jitter = jitter;
            return this;
        }
        
        public RetryHandler build() {
            return new RetryHandler(maxAttempts, baseDelay, maxDelay, strategy, backoffFactor, jitter);
        }
    }
}
