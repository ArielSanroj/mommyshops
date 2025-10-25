package com.mommyshops.cache;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;
import java.time.Duration;

/**
 * Annotation for caching method results
 */
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface Cacheable {
    
    /**
     * Cache key prefix
     */
    String keyPrefix() default "";
    
    /**
     * Time to live in seconds
     */
    long ttl() default 1800; // 30 minutes
    
    /**
     * Cache levels to use
     */
    CacheLevel[] levels() default {CacheLevel.L1, CacheLevel.L2};
    
    /**
     * Cache strategy
     */
    CacheStrategy strategy() default CacheStrategy.WRITE_THROUGH;
    
    /**
     * Whether to cache null results
     */
    boolean cacheNull() default false;
    
    /**
     * Whether to cache exceptions
     */
    boolean cacheExceptions() default false;
    
    /**
     * Cache key generator
     */
    Class<? extends CacheKeyGenerator> keyGenerator() default DefaultCacheKeyGenerator.class;
    
    /**
     * Cache condition
     */
    String condition() default "";
    
    /**
     * Cache unless condition
     */
    String unless() default "";
}
