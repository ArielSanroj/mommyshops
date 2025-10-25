package com.mommyshops.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.List;
import java.util.Map;
import java.util.HashMap;

@Service
@Transactional
public class QueryOptimizationService {

    private static final Logger logger = LoggerFactory.getLogger(QueryOptimizationService.class);

    @Autowired
    private JdbcTemplate jdbcTemplate;

    public Map<String, Object> getQueryPerformanceStats() {
        String sql = """
            SELECT 
                query,
                calls,
                total_time,
                mean_time,
                rows,
                100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
            FROM pg_stat_statements 
            ORDER BY total_time DESC 
            LIMIT 10
        """;
        
        try {
            List<Map<String, Object>> slowQueries = jdbcTemplate.queryForList(sql);
            return Map.of(
                "slow_queries", slowQueries,
                "total_queries", slowQueries.size()
            );
        } catch (Exception e) {
            logger.error("Failed to get query performance stats: {}", e.getMessage());
            return Map.of("error", e.getMessage());
        }
    }

    public void optimizeDatabaseSettings() {
        logger.info("Optimizing database settings...");
        
        Map<String, String> optimizations = new HashMap<>();
        optimizations.put("shared_preload_libraries", "pg_stat_statements");
        optimizations.put("track_activity_query_size", "2048");
        optimizations.put("pg_stat_statements.max", "10000");
        optimizations.put("pg_stat_statements.track", "all");
        
        for (Map.Entry<String, String> entry : optimizations.entrySet()) {
            try {
                String sql = String.format("ALTER SYSTEM SET %s = '%s'", entry.getKey(), entry.getValue());
                jdbcTemplate.execute(sql);
                logger.info("Applied optimization: {} = {}", entry.getKey(), entry.getValue());
            } catch (Exception e) {
                logger.error("Failed to apply optimization: {} = {}, Error: {}", 
                    entry.getKey(), entry.getValue(), e.getMessage());
            }
        }
        
        logger.info("Database optimization completed");
    }

    public Map<String, Object> getConnectionPoolStats() {
        String sql = """
            SELECT 
                state,
                count(*) as connection_count
            FROM pg_stat_activity 
            GROUP BY state
        """;
        
        try {
            List<Map<String, Object>> stats = jdbcTemplate.queryForList(sql);
            return Map.of(
                "connection_stats", stats,
                "total_connections", stats.stream()
                    .mapToInt(s -> ((Number) s.get("connection_count")).intValue())
                    .sum()
            );
        } catch (Exception e) {
            logger.error("Failed to get connection pool stats: {}", e.getMessage());
            return Map.of("error", e.getMessage());
        }
    }

    public void vacuumTables() {
        logger.info("Running VACUUM on database tables...");
        
        List<String> tables = List.of(
            "users", "product_analysis", "ingredient_analysis", 
            "analysis_results", "user_preferences"
        );
        
        for (String table : tables) {
            try {
                jdbcTemplate.execute("VACUUM ANALYZE " + table);
                logger.info("Vacuumed table: {}", table);
            } catch (Exception e) {
                logger.error("Failed to vacuum table: {}, Error: {}", table, e.getMessage());
            }
        }
        
        logger.info("Table vacuum completed");
    }
}
