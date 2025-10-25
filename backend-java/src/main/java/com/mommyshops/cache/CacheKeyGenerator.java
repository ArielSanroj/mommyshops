package com.mommyshops.cache;

import java.lang.reflect.Method;

/**
 * Interface for cache key generation
 */
public interface CacheKeyGenerator {
    
    /**
     * Generate cache key for method invocation
     * 
     * @param method the method being invoked
     * @param target the target object
     * @param args the method arguments
     * @return the cache key
     */
    String generate(Method method, Object target, Object... args);
}
