package com.mommyshops.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.boot.web.servlet.FilterRegistrationBean;
import org.springframework.web.filter.CommonsRequestLoggingFilter;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.boot.web.servlet.FilterRegistrationBean;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.filter.CommonsRequestLoggingFilter;

import javax.servlet.Filter;
import javax.servlet.FilterChain;
import javax.servlet.FilterConfig;
import javax.servlet.ServletException;
import javax.servlet.ServletRequest;
import javax.servlet.ServletResponse;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.UUID;
import java.util.regex.Pattern;
import java.util.regex.Matcher;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;

@Configuration
public class LoggingConfig {
    
    private static final Logger logger = LoggerFactory.getLogger(LoggingConfig.class);
    
    @Bean
    public FilterRegistrationBean<RequestLoggingFilter> requestLoggingFilter() {
        FilterRegistrationBean<RequestLoggingFilter> registrationBean = new FilterRegistrationBean<>();
        registrationBean.setFilter(new RequestLoggingFilter());
        registrationBean.addUrlPatterns("/*");
        registrationBean.setOrder(Ordered.HIGHEST_PRECEDENCE);
        return registrationBean;
    }
    
    @Bean
    public CommonsRequestLoggingFilter commonsRequestLoggingFilter() {
        CommonsRequestLoggingFilter filter = new CommonsRequestLoggingFilter();
        filter.setIncludeQueryString(true);
        filter.setIncludePayload(true);
        filter.setMaxPayloadLength(1000);
        filter.setIncludeHeaders(true);
        filter.setIncludeClientInfo(true);
        return filter;
    }
    
    public static class RequestLoggingFilter implements Filter {
        
        private static final Logger logger = LoggerFactory.getLogger(RequestLoggingFilter.class);
        private static final Pattern SECRET_PATTERN = Pattern.compile(
            "(?i)(password|passwd|pwd|secret|token|key|api_key|access_token|refresh_token|auth|authorization|jwt|bearer|credential|private_key|public_key)\\s*[:=]\\s*[\"']?([^\"'\\s]+)[\"']?",
            Pattern.CASE_INSENSITIVE
        );
        
        @Override
        public void init(FilterConfig filterConfig) throws ServletException {
            // Initialization logic
        }
        
        @Override
        public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
                throws IOException, ServletException {
            
            HttpServletRequest httpRequest = (HttpServletRequest) request;
            HttpServletResponse httpResponse = (HttpServletResponse) response;
            
            // Generate request ID
            String requestId = UUID.randomUUID().toString();
            MDC.put("requestId", requestId);
            
            // Log request
            logRequest(httpRequest);
            
            long startTime = System.currentTimeMillis();
            
            try {
                chain.doFilter(request, response);
            } finally {
                long duration = System.currentTimeMillis() - startTime;
                
                // Log response
                logResponse(httpRequest, httpResponse, duration);
                
                // Clear MDC
                MDC.clear();
            }
        }
        
        @Override
        public void destroy() {
            // Cleanup logic
        }
        
        private void logRequest(HttpServletRequest request) {
            String method = request.getMethod();
            String uri = request.getRequestURI();
            String queryString = request.getQueryString();
            String userAgent = request.getHeader("User-Agent");
            String remoteAddr = request.getRemoteAddr();
            
            logger.info("Request: {} {} - User-Agent: {} - IP: {}", 
                method, uri + (queryString != null ? "?" + queryString : ""), userAgent, remoteAddr);
        }
        
        private void logResponse(HttpServletRequest request, HttpServletResponse response, long duration) {
            String method = request.getMethod();
            String uri = request.getRequestURI();
            int status = response.getStatus();
            
            logger.info("Response: {} {} - Status: {} - Duration: {}ms", 
                method, uri, status, duration);
        }
    }
    
    public static class SecretSanitizer {
        
        private static final Pattern[] SECRET_PATTERNS = {
            Pattern.compile("(?i)password\\s*[:=]\\s*[\"']?([^\"'\\s]+)[\"']?"),
            Pattern.compile("(?i)secret\\s*[:=]\\s*[\"']?([^\"'\\s]+)[\"']?"),
            Pattern.compile("(?i)token\\s*[:=]\\s*[\"']?([^\"'\\s]+)[\"']?"),
            Pattern.compile("(?i)key\\s*[:=]\\s*[\"']?([^\"'\\s]+)[\"']?"),
            Pattern.compile("(?i)api_key\\s*[:=]\\s*[\"']?([^\"'\\s]+)[\"']?"),
            Pattern.compile("(?i)access_token\\s*[:=]\\s*[\"']?([^\"'\\s]+)[\"']?"),
            Pattern.compile("(?i)refresh_token\\s*[:=]\\s*[\"']?([^\"'\\s]+)[\"']?"),
            Pattern.compile("(?i)auth\\s*[:=]\\s*[\"']?([^\"'\\s]+)[\"']?"),
            Pattern.compile("(?i)authorization\\s*[:=]\\s*[\"']?([^\"'\\s]+)[\"']?"),
            Pattern.compile("(?i)jwt\\s*[:=]\\s*[\"']?([^\"'\\s]+)[\"']?"),
            Pattern.compile("(?i)bearer\\s*[:=]\\s*[\"']?([^\"'\\s]+)[\"']?"),
            Pattern.compile("(?i)credential\\s*[:=]\\s*[\"']?([^\"'\\s]+)[\"']?"),
            Pattern.compile("(?i)private_key\\s*[:=]\\s*[\"']?([^\"'\\s]+)[\"']?"),
            Pattern.compile("(?i)public_key\\s*[:=]\\s*[\"']?([^\"'\\s]+)[\"']?")
        };
        
        public static String sanitize(String input) {
            if (input == null) {
                return null;
            }
            
            String sanitized = input;
            
            for (Pattern pattern : SECRET_PATTERNS) {
                Matcher matcher = pattern.matcher(sanitized);
                sanitized = matcher.replaceAll("$1=\"***\"");
            }
            
            return sanitized;
        }
    }
    
    public static class StructuredLogger {
        
        private final Logger logger;
        
        public StructuredLogger(Class<?> clazz) {
            this.logger = LoggerFactory.getLogger(clazz);
        }
        
        public void info(String message, Object... args) {
            logger.info(message, args);
        }
        
        public void warn(String message, Object... args) {
            logger.warn(message, args);
        }
        
        public void error(String message, Object... args) {
            logger.error(message, args);
        }
        
        public void error(String message, Throwable throwable) {
            logger.error(message, throwable);
        }
        
        public void debug(String message, Object... args) {
            logger.debug(message, args);
        }
        
        public void logRequest(String method, String uri, int statusCode, long duration) {
            logger.info("Request: {} {} - Status: {} - Duration: {}ms", method, uri, statusCode, duration);
        }
        
        public void logError(String operation, Throwable throwable) {
            logger.error("Error in {}: {}", operation, throwable.getMessage(), throwable);
        }
        
        public void logPerformance(String operation, long duration) {
            logger.info("Performance: {} took {}ms", operation, duration);
        }
    }
}
