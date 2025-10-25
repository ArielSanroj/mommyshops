package com.mommyshops.cache;

/**
 * Cache strategy enumeration
 */
public enum CacheStrategy {
    WRITE_THROUGH("write_through", "Write to all cache levels immediately"),
    WRITE_BACK("write_back", "Write to L1 first, L2 and L3 later"),
    WRITE_AROUND("write_around", "Write to L2 and L3, skip L1"),
    READ_THROUGH("read_through", "Read through cache to data source"),
    CACHE_ASIDE("cache_aside", "Application manages cache and data source");
    
    private final String code;
    private final String description;
    
    CacheStrategy(String code, String description) {
        this.code = code;
        this.description = description;
    }
    
    public String getCode() {
        return code;
    }
    
    public String getDescription() {
        return description;
    }
}
