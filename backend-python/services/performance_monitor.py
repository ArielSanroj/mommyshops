"""
Performance monitoring and optimization service
"""

import time
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import psutil
import json
from dataclasses import dataclass
from collections import defaultdict, deque
import threading

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    timestamp: datetime
    metric_name: str
    value: float
    unit: str
    tags: Dict[str, str] = None

class PerformanceMonitor:
    """
    Advanced performance monitoring service
    """
    
    def __init__(self):
        self.metrics_buffer = deque(maxlen=10000)  # Keep last 10k metrics
        self.performance_history = defaultdict(list)
        self.alerts = []
        self.monitoring_active = False
        self.monitor_thread = None
        
        # Performance thresholds
        self.thresholds = {
            'cpu_usage': 80.0,  # 80% CPU usage
            'memory_usage': 85.0,  # 85% memory usage
            'response_time': 2.0,  # 2 seconds
            'error_rate': 5.0,  # 5% error rate
            'cache_hit_rate': 70.0  # 70% cache hit rate
        }
    
    def start_monitoring(self, interval: int = 30):
        """
        Start continuous performance monitoring
        """
        if self.monitoring_active:
            logger.warning("Performance monitoring already active")
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info(f"Performance monitoring started with {interval}s interval")
    
    def stop_monitoring(self):
        """
        Stop performance monitoring
        """
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Performance monitoring stopped")
    
    def _monitoring_loop(self, interval: int):
        """
        Main monitoring loop
        """
        while self.monitoring_active:
            try:
                # Collect system metrics
                self._collect_system_metrics()
                
                # Collect application metrics
                self._collect_application_metrics()
                
                # Check for alerts
                self._check_alerts()
                
                # Clean up old metrics
                self._cleanup_old_metrics()
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(interval)
    
    def _collect_system_metrics(self):
        """
        Collect system-level performance metrics
        """
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available = memory.available / (1024**3)  # GB
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_free = disk.free / (1024**3)  # GB
            
            # Network metrics
            network = psutil.net_io_counters()
            
            # Record metrics
            self._record_metric('cpu_usage', cpu_percent, '%')
            self._record_metric('memory_usage', memory_percent, '%')
            self._record_metric('memory_available', memory_available, 'GB')
            self._record_metric('disk_usage', disk_percent, '%')
            self._record_metric('disk_free', disk_free, 'GB')
            self._record_metric('network_bytes_sent', network.bytes_sent, 'bytes')
            self._record_metric('network_bytes_recv', network.bytes_recv, 'bytes')
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    def _collect_application_metrics(self):
        """
        Collect application-level performance metrics
        """
        try:
            # Database connection metrics
            # This would be implemented with actual database monitoring
            
            # Cache metrics
            cache_hit_rate = self._calculate_cache_hit_rate()
            self._record_metric('cache_hit_rate', cache_hit_rate, '%')
            
            # Request metrics
            request_count = self._get_request_count()
            self._record_metric('requests_per_minute', request_count, 'requests')
            
            # Error rate
            error_rate = self._calculate_error_rate()
            self._record_metric('error_rate', error_rate, '%')
            
        except Exception as e:
            logger.error(f"Error collecting application metrics: {e}")
    
    def _record_metric(self, name: str, value: float, unit: str, tags: Dict[str, str] = None):
        """
        Record a performance metric
        """
        metric = PerformanceMetric(
            timestamp=datetime.now(),
            metric_name=name,
            value=value,
            unit=unit,
            tags=tags or {}
        )
        
        self.metrics_buffer.append(metric)
        self.performance_history[name].append(metric)
        
        # Keep only last 1000 metrics per type
        if len(self.performance_history[name]) > 1000:
            self.performance_history[name] = self.performance_history[name][-1000:]
    
    def _check_alerts(self):
        """
        Check for performance alerts
        """
        try:
            current_metrics = self._get_current_metrics()
            
            for metric_name, threshold in self.thresholds.items():
                if metric_name in current_metrics:
                    value = current_metrics[metric_name]
                    
                    if value > threshold:
                        self._create_alert(metric_name, value, threshold)
                        
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
    
    def _create_alert(self, metric_name: str, value: float, threshold: float):
        """
        Create a performance alert
        """
        alert = {
            'timestamp': datetime.now().isoformat(),
            'metric': metric_name,
            'value': value,
            'threshold': threshold,
            'severity': 'warning' if value < threshold * 1.5 else 'critical',
            'message': f"{metric_name} is {value:.2f}, exceeds threshold of {threshold}"
        }
        
        self.alerts.append(alert)
        logger.warning(f"Performance alert: {alert['message']}")
        
        # Keep only last 100 alerts
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
    
    def _get_current_metrics(self) -> Dict[str, float]:
        """
        Get current metric values
        """
        current_metrics = {}
        
        for metric_name, metrics in self.performance_history.items():
            if metrics:
                current_metrics[metric_name] = metrics[-1].value
        
        return current_metrics
    
    def _calculate_cache_hit_rate(self) -> float:
        """
        Calculate cache hit rate (simplified)
        """
        # This would be implemented with actual cache monitoring
        return 85.0  # Placeholder
    
    def _get_request_count(self) -> float:
        """
        Get requests per minute (simplified)
        """
        # This would be implemented with actual request monitoring
        return 120.0  # Placeholder
    
    def _calculate_error_rate(self) -> float:
        """
        Calculate error rate (simplified)
        """
        # This would be implemented with actual error monitoring
        return 2.5  # Placeholder
    
    def _cleanup_old_metrics(self):
        """
        Clean up old metrics to prevent memory issues
        """
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        for metric_name in list(self.performance_history.keys()):
            self.performance_history[metric_name] = [
                metric for metric in self.performance_history[metric_name]
                if metric.timestamp > cutoff_time
            ]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get performance summary
        """
        try:
            current_metrics = self._get_current_metrics()
            
            # Calculate averages for last hour
            hour_ago = datetime.now() - timedelta(hours=1)
            recent_metrics = {
                name: [m for m in metrics if m.timestamp > hour_ago]
                for name, metrics in self.performance_history.items()
            }
            
            averages = {}
            for name, metrics in recent_metrics.items():
                if metrics:
                    averages[f"{name}_avg"] = sum(m.value for m in metrics) / len(metrics)
            
            return {
                'current_metrics': current_metrics,
                'hourly_averages': averages,
                'active_alerts': len([a for a in self.alerts if a['severity'] == 'critical']),
                'total_alerts': len(self.alerts),
                'monitoring_active': self.monitoring_active,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return {'error': str(e)}
    
    def get_alerts(self, severity: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get performance alerts
        """
        alerts = self.alerts
        
        if severity:
            alerts = [a for a in alerts if a['severity'] == severity]
        
        return alerts[-limit:] if limit else alerts
    
    def clear_alerts(self):
        """
        Clear all alerts
        """
        self.alerts.clear()
        logger.info("All performance alerts cleared")
    
    def export_metrics(self, start_time: datetime = None, end_time: datetime = None) -> List[Dict[str, Any]]:
        """
        Export metrics for analysis
        """
        if not start_time:
            start_time = datetime.now() - timedelta(hours=1)
        if not end_time:
            end_time = datetime.now()
        
        exported_metrics = []
        
        for metric in self.metrics_buffer:
            if start_time <= metric.timestamp <= end_time:
                exported_metrics.append({
                    'timestamp': metric.timestamp.isoformat(),
                    'metric_name': metric.metric_name,
                    'value': metric.value,
                    'unit': metric.unit,
                    'tags': metric.tags
                })
        
        return exported_metrics
