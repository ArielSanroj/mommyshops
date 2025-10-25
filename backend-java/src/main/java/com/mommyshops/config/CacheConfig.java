package com.mommyshops.config;

import com.mommyshops.cache.MultiLevelCacheService;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.connection.RedisConnectionFactory;
import org.springframework.data.redis.connection.RedisStandaloneConfiguration;
import org.springframework.data.redis.connection.lettuce.LettuceConnectionFactory;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.serializer.GenericJackson2JsonRedisSerializer;
import org.springframework.data.redis.serializer.StringRedisSerializer;

/**
 * Cache configuration for multi-level caching
 */
@Configuration
public class CacheConfig {

    @Value("${spring.redis.host:localhost}")
    private String redisHost;

    @Value("${spring.redis.port:6379}")
    private int redisPort;

    @Value("${spring.redis.password:}")
    private String redisPassword;

    @Value("${spring.redis.database:0}")
    private int redisDatabase;

    @Value("${cache.l1.enabled:true}")
    private boolean l1Enabled;

    @Value("${cache.l1.max-size:1000}")
    private int l1MaxSize;

    @Value("${cache.l1.ttl:300}")
    private long l1Ttl;

    @Value("${cache.l2.enabled:true}")
    private boolean l2Enabled;

    @Value("${cache.l2.ttl:3600}")
    private long l2Ttl;

    @Value("${cache.l3.enabled:true}")
    private boolean l3Enabled;

    @Value("${cache.l3.ttl:86400}")
    private long l3Ttl;

    @Value("${cache.default-ttl:1800}")
    private long defaultTtl;

    @Bean
    public RedisConnectionFactory redisConnectionFactory() {
        RedisStandaloneConfiguration config = new RedisStandaloneConfiguration();
        config.setHostName(redisHost);
        config.setPort(redisPort);
        config.setDatabase(redisDatabase);
        
        if (redisPassword != null && !redisPassword.isEmpty()) {
            config.setPassword(redisPassword);
        }
        
        return new LettuceConnectionFactory(config);
    }

    @Bean
    public RedisTemplate<String, Object> redisTemplate(RedisConnectionFactory connectionFactory) {
        RedisTemplate<String, Object> template = new RedisTemplate<>();
        template.setConnectionFactory(connectionFactory);
        
        // Use String serializer for keys
        template.setKeySerializer(new StringRedisSerializer());
        template.setHashKeySerializer(new StringRedisSerializer());
        
        // Use JSON serializer for values
        template.setValueSerializer(new GenericJackson2JsonRedisSerializer());
        template.setHashValueSerializer(new GenericJackson2JsonRedisSerializer());
        
        template.afterPropertiesSet();
        return template;
    }

    @Bean
    public MultiLevelCacheService multiLevelCacheService(RedisTemplate<String, Object> redisTemplate) {
        return new MultiLevelCacheService();
    }
}