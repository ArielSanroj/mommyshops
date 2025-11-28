#!/usr/bin/env python3
"""
Análisis completo del catálogo de ingredientes
Detecta inconsistencias, valores atípicos y posibles errores
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple
from collections import Counter, defaultdict

CATALOG_PATH = Path(__file__).parent.parent / "backend-python" / "app" / "data" / "ingredient_catalog.json"


class CatalogAnalyzer:
    """Analizador completo del catálogo de ingredientes"""
    
    def __init__(self):
        self.catalog = self._load_catalog()
        self.issues = []
        self.stats = {}
    
    def _load_catalog(self) -> Dict[str, Any]:
        """Cargar catálogo"""
        with open(CATALOG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def analyze_all(self) -> Dict[str, Any]:
        """Ejecutar todos los análisis"""
        print("=" * 70)
        print("🔬 ANÁLISIS COMPLETO DEL CATÁLOGO DE INGREDIENTES")
        print("=" * 70)
        print(f"📁 Archivo: {CATALOG_PATH}")
        print(f"📊 Total ingredientes: {len(self.catalog)}\n")
        
        # Análisis de estadísticas básicas
        self._analyze_basic_stats()
        
        # Análisis de consistencia de scores
        self._analyze_score_consistency()
        
        # Análisis de valores atípicos
        self._detect_outliers()
        
        # Análisis de campos faltantes
        self._check_missing_fields()
        
        # Análisis de clasificación de riesgo
        self._analyze_risk_classification()
        
        # Análisis de baby metadata
        self._analyze_baby_data()
        
        # Análisis de duplicados potenciales
        self._detect_potential_duplicates()
        
        # Generar reporte
        return self._generate_report()
    
    def _analyze_basic_stats(self):
        """Estadísticas básicas del catálogo"""
        print("📊 ESTADÍSTICAS BÁSICAS")
        print("-" * 70)
        
        scores = []
        ewg_scores = []
        risk_levels = []
        eco_friendly = []
        has_baby_data = []
        
        for name, data in self.catalog.items():
            scores.append(data.get('score', 0))
            ewg_scores.append(data.get('ewg', 0))
            risk_levels.append(data.get('risk', 'unknown'))
            eco_friendly.append(data.get('eco', False))
            has_baby_data.append(bool(data.get('baby')))
        
        self.stats['basic'] = {
            'total_ingredients': len(self.catalog),
            'avg_score': sum(scores) / len(scores) if scores else 0,
            'avg_ewg': sum(ewg_scores) / len(ewg_scores) if ewg_scores else 0,
            'min_score': min(scores) if scores else 0,
            'max_score': max(scores) if scores else 0,
            'min_ewg': min(ewg_scores) if ewg_scores else 0,
            'max_ewg': max(ewg_scores) if ewg_scores else 0,
            'eco_friendly_count': sum(eco_friendly),
            'eco_friendly_pct': (sum(eco_friendly) / len(eco_friendly) * 100) if eco_friendly else 0,
            'with_baby_data': sum(has_baby_data),
            'with_baby_data_pct': (sum(has_baby_data) / len(has_baby_data) * 100) if has_baby_data else 0
        }
        
        risk_counter = Counter(risk_levels)
        
        print(f"  Score promedio: {self.stats['basic']['avg_score']:.2f}/100")
        print(f"  EWG promedio: {self.stats['basic']['avg_ewg']:.2f}/10")
        print(f"  Score rango: {self.stats['basic']['min_score']} - {self.stats['basic']['max_score']}")
        print(f"  EWG rango: {self.stats['basic']['min_ewg']} - {self.stats['basic']['max_ewg']}")
        print(f"  Eco-friendly: {self.stats['basic']['eco_friendly_count']}/{self.stats['basic']['total_ingredients']} ({self.stats['basic']['eco_friendly_pct']:.1f}%)")
        print(f"  Con datos de bebé: {self.stats['basic']['with_baby_data']}/{self.stats['basic']['total_ingredients']} ({self.stats['basic']['with_baby_data_pct']:.1f}%)")
        print(f"\n  Distribución de riesgo:")
        for risk, count in risk_counter.most_common():
            pct = (count / len(risk_levels) * 100)
            print(f"    • {risk}: {count} ({pct:.1f}%)")
        print()
    
    def _analyze_score_consistency(self):
        """Analizar consistencia entre score, ewg y risk"""
        print("🔍 ANÁLISIS DE CONSISTENCIA (Score vs EWG vs Risk)")
        print("-" * 70)
        
        inconsistencies = []
        
        for name, data in self.catalog.items():
            score = data.get('score', 0)
            ewg = data.get('ewg', 0)
            risk = data.get('risk', 'unknown')
            
            # Regla 1: Score alto (>80) debería tener EWG bajo (<3) y risk bajo
            if score >= 80:
                if ewg > 3:
                    inconsistencies.append({
                        'ingredient': name,
                        'issue': 'high_score_high_ewg',
                        'score': score,
                        'ewg': ewg,
                        'risk': risk,
                        'severity': 'medium'
                    })
                if risk in ['high', 'moderate']:
                    inconsistencies.append({
                        'ingredient': name,
                        'issue': 'high_score_high_risk',
                        'score': score,
                        'ewg': ewg,
                        'risk': risk,
                        'severity': 'high'
                    })
            
            # Regla 2: Score bajo (<50) debería tener EWG alto (>6) o risk alto
            if score < 50:
                if ewg < 5 and risk not in ['high', 'moderate']:
                    inconsistencies.append({
                        'ingredient': name,
                        'issue': 'low_score_low_ewg',
                        'score': score,
                        'ewg': ewg,
                        'risk': risk,
                        'severity': 'medium'
                    })
            
            # Regla 3: EWG muy alto (8-10) debería tener score bajo (<40) y risk high
            if ewg >= 8:
                if score > 50:
                    inconsistencies.append({
                        'ingredient': name,
                        'issue': 'high_ewg_high_score',
                        'score': score,
                        'ewg': ewg,
                        'risk': risk,
                        'severity': 'high'
                    })
                if risk not in ['high', 'critical']:
                    inconsistencies.append({
                        'ingredient': name,
                        'issue': 'high_ewg_low_risk',
                        'score': score,
                        'ewg': ewg,
                        'risk': risk,
                        'severity': 'high'
                    })
            
            # Regla 4: Risk "high" debería tener score bajo (<50) y EWG alto (>6)
            if risk == 'high':
                if score > 60:
                    inconsistencies.append({
                        'ingredient': name,
                        'issue': 'high_risk_high_score',
                        'score': score,
                        'ewg': ewg,
                        'risk': risk,
                        'severity': 'high'
                    })
        
        self.issues.extend(inconsistencies)
        
        high_severity = [i for i in inconsistencies if i['severity'] == 'high']
        medium_severity = [i for i in inconsistencies if i['severity'] == 'medium']
        
        print(f"  ⚠️  Inconsistencias encontradas: {len(inconsistencies)}")
        print(f"    • Alta severidad: {len(high_severity)}")
        print(f"    • Media severidad: {len(medium_severity)}")
        
        if high_severity:
            print(f"\n  🚨 Top 10 inconsistencias de alta severidad:")
            for issue in high_severity[:10]:
                print(f"    • {issue['ingredient']}")
                print(f"      Problema: {issue['issue']}")
                print(f"      Valores: score={issue['score']}, ewg={issue['ewg']}, risk={issue['risk']}")
        print()
    
    def _detect_outliers(self):
        """Detectar valores atípicos estadísticos"""
        print("📈 ANÁLISIS DE VALORES ATÍPICOS")
        print("-" * 70)
        
        outliers = []
        
        # Obtener estadísticas
        scores = [data.get('score', 0) for data in self.catalog.values()]
        ewgs = [data.get('ewg', 0) for data in self.catalog.values()]
        
        import statistics
        
        # Valores extremos de score
        score_mean = statistics.mean(scores)
        score_stdev = statistics.stdev(scores) if len(scores) > 1 else 0
        
        for name, data in self.catalog.items():
            score = data.get('score', 0)
            ewg = data.get('ewg', 0)
            
            # Score muy desviado (>2 desviaciones estándar)
            if score_stdev > 0:
                z_score = abs(score - score_mean) / score_stdev
                if z_score > 2.5:
                    outliers.append({
                        'ingredient': name,
                        'type': 'score_outlier',
                        'value': score,
                        'z_score': z_score,
                        'mean': score_mean
                    })
            
            # EWG score inválido (fuera de rango 0-10)
            if ewg < 0 or ewg > 10:
                outliers.append({
                    'ingredient': name,
                    'type': 'invalid_ewg',
                    'value': ewg,
                    'valid_range': '0-10'
                })
            
            # Score inválido (fuera de rango 0-100)
            if score < 0 or score > 100:
                outliers.append({
                    'ingredient': name,
                    'type': 'invalid_score',
                    'value': score,
                    'valid_range': '0-100'
                })
        
        self.issues.extend(outliers)
        
        print(f"  ⚠️  Valores atípicos: {len(outliers)}")
        if outliers:
            print(f"\n  Primeros 10 valores atípicos:")
            for outlier in outliers[:10]:
                print(f"    • {outlier['ingredient']}: {outlier['type']} = {outlier.get('value')}")
        print()
    
    def _check_missing_fields(self):
        """Verificar campos faltantes o vacíos"""
        print("📋 ANÁLISIS DE CAMPOS FALTANTES")
        print("-" * 70)
        
        missing = defaultdict(list)
        
        required_fields = ['score', 'ewg', 'risk', 'eco', 'description']
        recommended_fields = ['categories', 'baby']
        
        for name, data in self.catalog.items():
            # Campos requeridos
            for field in required_fields:
                if field not in data or data[field] is None or data[field] == '':
                    missing[field].append(name)
            
            # Campos recomendados
            for field in recommended_fields:
                if field not in data:
                    missing[f'{field}_missing'].append(name)
            
            # Descripción muy corta
            desc = data.get('description', '')
            if len(desc) < 20:
                missing['description_too_short'].append(name)
        
        total_missing = sum(len(v) for v in missing.values())
        
        print(f"  ⚠️  Campos con problemas: {len(missing)} tipos")
        print(f"  Total ingredientes afectados: {total_missing}")
        
        for field, ingredients in sorted(missing.items(), key=lambda x: len(x[1]), reverse=True):
            if len(ingredients) > 0:
                print(f"    • {field}: {len(ingredients)} ingredientes")
                if len(ingredients) <= 5:
                    for ing in ingredients:
                        print(f"      - {ing}")
        print()
    
    def _analyze_risk_classification(self):
        """Analizar clasificación de riesgo"""
        print("⚠️  ANÁLISIS DE CLASIFICACIÓN DE RIESGO")
        print("-" * 70)
        
        risk_score_ranges = defaultdict(list)
        
        for name, data in self.catalog.items():
            risk = data.get('risk', 'unknown')
            score = data.get('score', 0)
            risk_score_ranges[risk].append(score)
        
        print(f"  Rangos de score por nivel de riesgo:")
        for risk in ['none', 'low', 'moderate', 'high', 'critical']:
            if risk in risk_score_ranges:
                scores = risk_score_ranges[risk]
                avg = sum(scores) / len(scores)
                min_s = min(scores)
                max_s = max(scores)
                print(f"    • {risk}: promedio={avg:.1f}, rango={min_s}-{max_s}, count={len(scores)}")
        print()
    
    def _analyze_baby_data(self):
        """Analizar datos específicos para bebés"""
        print("👶 ANÁLISIS DE DATOS PARA BEBÉS")
        print("-" * 70)
        
        with_baby = 0
        without_baby = 0
        baby_risk_counts = Counter()
        
        for name, data in self.catalog.items():
            baby = data.get('baby')
            if baby:
                with_baby += 1
                baby_risk = baby.get('risk', 'unknown')
                baby_risk_counts[baby_risk] += 1
            else:
                without_baby += 1
        
        print(f"  Ingredientes con datos de bebé: {with_baby}/{len(self.catalog)} ({with_baby/len(self.catalog)*100:.1f}%)")
        print(f"  Sin datos de bebé: {without_baby}/{len(self.catalog)} ({without_baby/len(self.catalog)*100:.1f}%)")
        
        print(f"\n  Distribución de baby risk:")
        for risk, count in baby_risk_counts.most_common():
            print(f"    • {risk}: {count} ({count/with_baby*100:.1f}%)")
        print()
    
    def _detect_potential_duplicates(self):
        """Detectar posibles duplicados por nombre similar"""
        print("🔍 ANÁLISIS DE POSIBLES DUPLICADOS")
        print("-" * 70)
        
        from difflib import SequenceMatcher
        
        names = list(self.catalog.keys())
        potential_duplicates = []
        
        # Comparar nombres (solo los primeros 500 para no tardar mucho)
        check_names = names[:500] if len(names) > 500 else names
        
        for i, name1 in enumerate(check_names):
            for name2 in names[i+1:]:
                # Calcular similitud
                similarity = SequenceMatcher(None, name1.lower(), name2.lower()).ratio()
                
                if similarity > 0.85 and name1 != name2:
                    potential_duplicates.append({
                        'name1': name1,
                        'name2': name2,
                        'similarity': similarity
                    })
        
        print(f"  ⚠️  Posibles duplicados: {len(potential_duplicates)}")
        if potential_duplicates:
            print(f"\n  Top 10 más similares:")
            for dup in sorted(potential_duplicates, key=lambda x: x['similarity'], reverse=True)[:10]:
                print(f"    • {dup['name1']} ≈ {dup['name2']} ({dup['similarity']*100:.1f}% similar)")
        print()
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generar reporte final"""
        print("=" * 70)
        print("📝 RESUMEN EJECUTIVO")
        print("=" * 70)
        
        total_issues = len(self.issues)
        high_priority = len([i for i in self.issues if i.get('severity') == 'high'])
        
        print(f"\n✅ Ingredientes totales: {len(self.catalog)}")
        print(f"⚠️  Issues detectados: {total_issues}")
        print(f"🚨 Alta prioridad: {high_priority}")
        
        if high_priority > 0:
            print(f"\n🎯 RECOMENDACIONES:")
            print(f"  1. Revisar {high_priority} inconsistencias de alta severidad")
            print(f"  2. Validar ingredientes con EWG score > 8")
            print(f"  3. Completar datos faltantes en baby metadata")
            print(f"  4. Estandarizar descripciones cortas")
        
        print("\n" + "=" * 70)
        
        return {
            'stats': self.stats,
            'issues': self.issues,
            'summary': {
                'total_ingredients': len(self.catalog),
                'total_issues': total_issues,
                'high_priority_issues': high_priority
            }
        }


def main():
    """Main analysis function"""
    analyzer = CatalogAnalyzer()
    report = analyzer.analyze_all()
    
    # Guardar reporte detallado
    output_path = Path(__file__).parent / "catalog_analysis_report.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Reporte detallado guardado en: {output_path}")


if __name__ == "__main__":
    main()
