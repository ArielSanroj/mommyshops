package com.mommyshops.cache;

/**
 * Cache level enumeration
 */
public enum CacheLevel {
    L1("l1", "In-memory cache"),
    L2("l2", "Redis cache"),
    L3("l3", "Database cache");
    
    private final String code;
    private final String description;
    
    CacheLevel(String code, String description) {
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
