package com.mommyshops.cache;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.TimeUnit;
import java.util.function.Function;

/**
 * Multi-level cache service implementing L1 (in-memory), L2 (Redis), and L3 (database) caching
 */
@Service
public class MultiLevelCacheService {

    private static final Logger logger = LoggerFactory.getLogger(MultiLevelCacheService.class);

    @Autowired
    private RedisTemplate<String, Object> redisTemplate;

    @Autowired
    private ObjectMapper objectMapper;

    // L1 Cache - In-memory cache
    private final Map<String, CacheEntry> l1Cache = new ConcurrentHashMap<>();
    private final int l1MaxSize = 1000;
    private final Duration l1Ttl = Duration.ofMinutes(5);

    // L2 Cache - Redis cache
    private final Duration l2Ttl = Duration.ofHours(1);

    // L3 Cache - Database cache (placeholder)
    private final Duration l3Ttl = Duration.ofDays(1);

    // Cache statistics
    private final CacheStats cacheStats = new CacheStats();

    /**
     * Get value from cache (L1 -> L2 -> L3)
     */
    public <T> Optional<T> get(String key, Class<T> type) {
        // Try L1 cache first
        Optional<T> value = getFromL1(key, type);
        if (value.isPresent()) {
            cacheStats.incrementL1Hits();
            return value;
        }

        // Try L2 cache
        value = getFromL2(key, type);
        if (value.isPresent()) {
            cacheStats.incrementL2Hits();
            // Populate L1 cache
            setInL1(key, value.get());
            return value;
        }

        // Try L3 cache
        value = getFromL3(key, type);
        if (value.isPresent()) {
            cacheStats.incrementL3Hits();
            // Populate L1 and L2 caches
            setInL1(key, value.get());
            setInL2(key, value.get());
            return value;
        }

        cacheStats.incrementMisses();
        return Optional.empty();
    }

    /**
     * Set value in cache
     */
    public <T> boolean set(String key, T value, Duration ttl) {
        try {
            // Set in L1 cache
            setInL1(key, value);

            // Set in L2 cache
            setInL2(key, value, ttl);

            // Set in L3 cache
            setInL3(key, value, ttl);

            cacheStats.incrementSets();
            return true;
        } catch (Exception e) {
            logger.error("Error setting cache value for key: {}", key, e);
            cacheStats.incrementErrors();
            return false;
        }
    }

    /**
     * Set value in cache with default TTL
     */
    public <T> boolean set(String key, T value) {
        return set(key, value, Duration.ofMinutes(30));
    }

    /**
     * Delete value from cache
     */
    public boolean delete(String key) {
        try {
            // Delete from all levels
            l1Cache.remove(key);
            redisTemplate.delete(key);
            deleteFromL3(key);

            cacheStats.incrementDeletes();
            return true;
        } catch (Exception e) {
            logger.error("Error deleting cache value for key: {}", key, e);
            cacheStats.incrementErrors();
            return false;
        }
    }

    /**
     * Clear all cache levels
     */
    public boolean clear() {
        try {
            l1Cache.clear();
            redisTemplate.getConnectionFactory().getConnection().flushDb();
            clearL3();

            return true;
        } catch (Exception e) {
            logger.error("Error clearing cache", e);
            cacheStats.incrementErrors();
            return false;
        }
    }

    /**
     * Get cache statistics
     */
    public CacheStats getStats() {
        return cacheStats;
    }

    /**
     * Get value from L1 cache (in-memory)
     */
    private <T> Optional<T> getFromL1(String key, Class<T> type) {
        try {
            CacheEntry entry = l1Cache.get(key);
            if (entry == null) {
                return Optional.empty();
            }

            // Check TTL
            if (entry.isExpired()) {
                l1Cache.remove(key);
                return Optional.empty();
            }

            return Optional.of(type.cast(entry.getValue()));
        } catch (Exception e) {
            logger.error("Error getting from L1 cache for key: {}", key, e);
            return Optional.empty();
        }
    }

    /**
     * Set value in L1 cache (in-memory)
     */
    private <T> void setInL1(String key, T value) {
        try {
            // Evict if at capacity
            if (l1Cache.size() >= l1MaxSize && !l1Cache.containsKey(key)) {
                evictLruFromL1();
            }

            l1Cache.put(key, new CacheEntry(value, System.currentTimeMillis()));
        } catch (Exception e) {
            logger.error("Error setting in L1 cache for key: {}", key, e);
        }
    }

    /**
     * Get value from L2 cache (Redis)
     */
    private <T> Optional<T> getFromL2(String key, Class<T> type) {
        try {
            Object value = redisTemplate.opsForValue().get(key);
            if (value == null) {
                return Optional.empty();
            }

            return Optional.of(type.cast(value));
        } catch (Exception e) {
            logger.error("Error getting from L2 cache for key: {}", key, e);
            return Optional.empty();
        }
    }

    /**
     * Set value in L2 cache (Redis)
     */
    private <T> void setInL2(String key, T value) {
        setInL2(key, value, l2Ttl);
    }

    /**
     * Set value in L2 cache (Redis) with TTL
     */
    private <T> void setInL2(String key, T value, Duration ttl) {
        try {
            redisTemplate.opsForValue().set(key, value, ttl);
        } catch (Exception e) {
            logger.error("Error setting in L2 cache for key: {}", key, e);
        }
    }

    /**
     * Get value from L3 cache (database)
     */
    private <T> Optional<T> getFromL3(String key, Class<T> type) {
        try {
            // This would query a cache table in the database
            // For now, return empty as this is a placeholder
            return Optional.empty();
        } catch (Exception e) {
            logger.error("Error getting from L3 cache for key: {}", key, e);
            return Optional.empty();
        }
    }

    /**
     * Set value in L3 cache (database)
     */
    private <T> void setInL3(String key, T value, Duration ttl) {
        try {
            // This would insert/update a cache table in the database
            // For now, do nothing as this is a placeholder
        } catch (Exception e) {
            logger.error("Error setting in L3 cache for key: {}", key, e);
        }
    }

    /**
     * Delete value from L3 cache (database)
     */
    private void deleteFromL3(String key) {
        try {
            // This would delete from a cache table in the database
            // For now, do nothing as this is a placeholder
        } catch (Exception e) {
            logger.error("Error deleting from L3 cache for key: {}", key, e);
        }
    }

    /**
     * Clear L3 cache (database)
     */
    private void clearL3() {
        try {
            // This would clear a cache table in the database
            // For now, do nothing as this is a placeholder
        } catch (Exception e) {
            logger.error("Error clearing L3 cache", e);
        }
    }

    /**
     * Evict least recently used item from L1 cache
     */
    private void evictLruFromL1() {
        if (l1Cache.isEmpty()) {
            return;
        }

        String lruKey = l1Cache.entrySet().stream()
                .min(Map.Entry.comparingByValue((e1, e2) -> 
                        Long.compare(e1.getTimestamp(), e2.getTimestamp())))
                .map(Map.Entry::getKey)
                .orElse(null);

        if (lruKey != null) {
            l1Cache.remove(lruKey);
        }
    }

    /**
     * Cache entry for L1 cache
     */
    private static class CacheEntry {
        private final Object value;
        private final long timestamp;

        public CacheEntry(Object value, long timestamp) {
            this.value = value;
            this.timestamp = timestamp;
        }

        public Object getValue() {
            return value;
        }

        public long getTimestamp() {
            return timestamp;
        }

        public boolean isExpired() {
            return System.currentTimeMillis() - timestamp > Duration.ofMinutes(5).toMillis();
        }
    }

    /**
     * Cache statistics
     */
    public static class CacheStats {
        private long hits = 0;
        private long misses = 0;
        private long sets = 0;
        private long deletes = 0;
        private long errors = 0;
        private long l1Hits = 0;
        private long l2Hits = 0;
        private long l3Hits = 0;

        public void incrementHits() {
            hits++;
        }

        public void incrementMisses() {
            misses++;
        }

        public void incrementSets() {
            sets++;
        }

        public void incrementDeletes() {
            deletes++;
        }

        public void incrementErrors() {
            errors++;
        }

        public void incrementL1Hits() {
            l1Hits++;
            hits++;
        }

        public void incrementL2Hits() {
            l2Hits++;
            hits++;
        }

        public void incrementL3Hits() {
            l3Hits++;
            hits++;
        }

        public double getHitRate() {
            long total = hits + misses;
            return total > 0 ? (double) hits / total : 0.0;
        }

        public long getHits() {
            return hits;
        }

        public long getMisses() {
            return misses;
        }

        public long getSets() {
            return sets;
        }

        public long getDeletes() {
            return deletes;
        }

        public long getErrors() {
            return errors;
        }

        public long getL1Hits() {
            return l1Hits;
        }

        public long getL2Hits() {
            return l2Hits;
        }

        public long getL3Hits() {
            return l3Hits;
        }
    }
}
