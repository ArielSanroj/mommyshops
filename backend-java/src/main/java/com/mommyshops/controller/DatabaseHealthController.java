package com.mommyshops.controller;

import com.mommyshops.service.DatabaseIndexingService;
import com.mommyshops.service.QueryOptimizationService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Map;
import java.util.HashMap;

@RestController
@RequestMapping("/api/database")
@CrossOrigin(origins = {"${cors.allowed-origins:http://localhost:3000,http://localhost:8080}"})
public class DatabaseHealthController {

    private static final Logger logger = LoggerFactory.getLogger(DatabaseHealthController.class);

    @Autowired
    private DatabaseIndexingService indexingService;

    @Autowired
    private QueryOptimizationService optimizationService;

    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> getDatabaseHealth() {
        try {
            Map<String, Object> health = new HashMap<>();
            health.put("status", "healthy");
            health.put("timestamp", System.currentTimeMillis());
            
            // Get connection pool stats
            Map<String, Object> connectionStats = optimizationService.getConnectionPoolStats();
            health.put("connection_pool", connectionStats);
            
            // Get query performance stats
            Map<String, Object> queryStats = optimizationService.getQueryPerformanceStats();
            health.put("query_performance", queryStats);
            
            // Get index statistics
            Map<String, Object> indexStats = indexingService.getIndexStatistics();
            health.put("indexes", indexStats);
            
            return ResponseEntity.ok(health);
        } catch (Exception e) {
            logger.error("Database health check failed: {}", e.getMessage());
            Map<String, Object> error = new HashMap<>();
            error.put("status", "unhealthy");
            error.put("error", e.getMessage());
            return ResponseEntity.status(500).body(error);
        }
    }

    @PostMapping("/optimize")
    public ResponseEntity<Map<String, Object>> optimizeDatabase() {
        try {
            logger.info("Starting database optimization...");
            
            // Create indexes
            indexingService.createOptimizedIndexes();
            
            // Analyze tables
            indexingService.analyzeTables();
            
            // Optimize settings
            optimizationService.optimizeDatabaseSettings();
            
            // Vacuum tables
            optimizationService.vacuumTables();
            
            Map<String, Object> result = new HashMap<>();
            result.put("status", "success");
            result.put("message", "Database optimization completed");
            result.put("timestamp", System.currentTimeMillis());
            
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            logger.error("Database optimization failed: {}", e.getMessage());
            Map<String, Object> error = new HashMap<>();
            error.put("status", "error");
            error.put("error", e.getMessage());
            return ResponseEntity.status(500).body(error);
        }
    }

    @GetMapping("/stats")
    public ResponseEntity<Map<String, Object>> getDatabaseStats() {
        try {
            Map<String, Object> stats = new HashMap<>();
            
            // Get query performance stats
            Map<String, Object> queryStats = optimizationService.getQueryPerformanceStats();
            stats.put("query_performance", queryStats);
            
            // Get connection pool stats
            Map<String, Object> connectionStats = optimizationService.getConnectionPoolStats();
            stats.put("connection_pool", connectionStats);
            
            // Get index statistics
            Map<String, Object> indexStats = indexingService.getIndexStatistics();
            stats.put("indexes", indexStats);
            
            return ResponseEntity.ok(stats);
        } catch (Exception e) {
            logger.error("Failed to get database stats: {}", e.getMessage());
            Map<String, Object> error = new HashMap<>();
            error.put("error", e.getMessage());
            return ResponseEntity.status(500).body(error);
        }
    }
}
