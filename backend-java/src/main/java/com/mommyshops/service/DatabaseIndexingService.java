package com.mommyshops.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.List;
import java.util.Map;

@Service
@Transactional
public class DatabaseIndexingService {

    private static final Logger logger = LoggerFactory.getLogger(DatabaseIndexingService.class);

    @Autowired
    private JdbcTemplate jdbcTemplate;

    public void createOptimizedIndexes() {
        logger.info("Creating optimized database indexes...");
        
        List<String> indexes = List.of(
            // User indexes
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active)",
            
            // Product analysis indexes
            "CREATE INDEX IF NOT EXISTS idx_product_analysis_user_id ON product_analysis(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_product_analysis_created_at ON product_analysis(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_product_analysis_eco_score ON product_analysis(avg_eco_score)",
            "CREATE INDEX IF NOT EXISTS idx_product_analysis_suitability ON product_analysis(suitability)",
            
            // Ingredient analysis indexes
            "CREATE INDEX IF NOT EXISTS idx_ingredient_analysis_name ON ingredient_analysis(name)",
            "CREATE INDEX IF NOT EXISTS idx_ingredient_analysis_risk_level ON ingredient_analysis(risk_level)",
            "CREATE INDEX IF NOT EXISTS idx_ingredient_analysis_eco_score ON ingredient_analysis(eco_score)",
            "CREATE INDEX IF NOT EXISTS idx_ingredient_analysis_created_at ON ingredient_analysis(created_at)",
            
            // Analysis result indexes
            "CREATE INDEX IF NOT EXISTS idx_analysis_results_analysis_id ON analysis_results(analysis_id)",
            "CREATE INDEX IF NOT EXISTS idx_analysis_results_ingredient_id ON analysis_results(ingredient_id)",
            "CREATE INDEX IF NOT EXISTS idx_analysis_results_risk_level ON analysis_results(risk_level)",
            
            // User preferences indexes
            "CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_preferences_skin_type ON user_preferences(skin_type)",
            "CREATE INDEX IF NOT EXISTS idx_user_preferences_concerns ON user_preferences(concerns)",
            
            // Composite indexes for common queries
            "CREATE INDEX IF NOT EXISTS idx_product_analysis_user_created ON product_analysis(user_id, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_ingredient_analysis_name_risk ON ingredient_analysis(name, risk_level)",
            "CREATE INDEX IF NOT EXISTS idx_analysis_results_analysis_ingredient ON analysis_results(analysis_id, ingredient_id)"
        );

        for (String indexSql : indexes) {
            try {
                jdbcTemplate.execute(indexSql);
                logger.info("Created index: {}", indexSql);
            } catch (Exception e) {
                logger.error("Failed to create index: {}, Error: {}", indexSql, e.getMessage());
            }
        }
        
        logger.info("Database indexing completed");
    }

    public Map<String, Object> getIndexStatistics() {
        String sql = """
            SELECT 
                schemaname,
                tablename,
                indexname,
                indexdef
            FROM pg_indexes 
            WHERE schemaname = 'public'
            ORDER BY tablename, indexname
        """;
        
        return Map.of(
            "indexes", jdbcTemplate.queryForList(sql),
            "total_indexes", jdbcTemplate.queryForList(sql).size()
        );
    }

    public void analyzeTables() {
        logger.info("Analyzing database tables for optimization...");
        
        List<String> tables = List.of(
            "users", "product_analysis", "ingredient_analysis", 
            "analysis_results", "user_preferences"
        );
        
        for (String table : tables) {
            try {
                jdbcTemplate.execute("ANALYZE " + table);
                logger.info("Analyzed table: {}", table);
            } catch (Exception e) {
                logger.error("Failed to analyze table: {}, Error: {}", table, e.getMessage());
            }
        }
        
        logger.info("Table analysis completed");
    }
}
