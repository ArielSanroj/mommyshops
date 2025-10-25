package com.mommyshops.cache;

import java.lang.reflect.Method;
import java.util.Arrays;
import java.util.Objects;

/**
 * Default cache key generator
 */
public class DefaultCacheKeyGenerator implements CacheKeyGenerator {
    
    @Override
    public String generate(Method method, Object target, Object... args) {
        StringBuilder key = new StringBuilder();
        
        // Add class name
        key.append(target.getClass().getSimpleName());
        key.append(".");
        
        // Add method name
        key.append(method.getName());
        key.append("(");
        
        // Add parameter types
        Class<?>[] paramTypes = method.getParameterTypes();
        for (int i = 0; i < paramTypes.length; i++) {
            if (i > 0) {
                key.append(",");
            }
            key.append(paramTypes[i].getSimpleName());
        }
        key.append(")");
        
        // Add arguments
        if (args != null && args.length > 0) {
            key.append("[");
            for (int i = 0; i < args.length; i++) {
                if (i > 0) {
                    key.append(",");
                }
                key.append(Objects.toString(args[i]));
            }
            key.append("]");
        }
        
        return key.toString();
    }
}
