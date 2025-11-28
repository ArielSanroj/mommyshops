#!/usr/bin/env python3
"""
Script completo para agregar metadata faltante al catálogo
- Baby metadata (risk, summary, avoid_in, flags)
- Descripciones detalladas
- Categorías por función
- Corrección de inconsistencias restantes
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

CATALOG_PATH = Path(__file__).parent.parent / "backend-python" / "app" / "data" / "ingredient_catalog.json"


def load_catalog() -> Dict[str, Any]:
    with open(CATALOG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_catalog(catalog: Dict[str, Any]):
    with open(CATALOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
        f.write('\n')


class MetadataCompleter:
    """Completa metadata faltante de forma inteligente"""
    
    def __init__(self, catalog: Dict[str, Any]):
        self.catalog = catalog
        self.stats = {
            'baby_added': 0,
            'descriptions_improved': 0,
            'categories_added': 0,
            'inconsistencies_fixed': 0
        }
    
    def generate_baby_metadata(self, name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Genera baby metadata basado en score, ewg y características"""
        score = data.get('score', 70)
        ewg = data.get('ewg', 5)
        risk = data.get('risk', 'moderate')
        name_lower = name.lower()
        
        # Determinar baby risk
        if score >= 85 and ewg <= 2 and risk in ['none', 'low']:
            baby_risk = 'good'
        elif score >= 70 and ewg <= 4:
            baby_risk = 'ok'
        elif ewg >= 7 or risk == 'high' or score < 50:
            baby_risk = 'bad'
        else:
            baby_risk = 'caution'
        
        # Generar summary
        summaries = {
            'good': self._generate_good_summary(name, data),
            'ok': self._generate_ok_summary(name, data),
            'caution': self._generate_caution_summary(name, data),
            'bad': self._generate_bad_summary(name, data)
        }
        summary = summaries.get(baby_risk, "Verificar compatibilidad con pediatra.")
        
        # Determinar avoid_in
        avoid_in = []
        flags = []
        
        # Ingredientes problemáticos
        if 'sulfate' in name_lower and 'lauryl' in name_lower:
            avoid_in.extend(['bebes_menores_6m', 'piel_atopica', 'dermatitis_panal'])
            flags.append('tensioactivo_fuerte')
        
        if 'fragrance' in name_lower or 'parfum' in name_lower:
            avoid_in.extend(['bebes_menores_6m', 'piel_atopica', 'fragrance_free'])
            flags.append('fragancia_sintetica')
        
        if 'paraben' in name_lower:
            avoid_in.extend(['bebes_menores_3m'])
            flags.append('conservante_controvertido')
        
        if 'alcohol' in name_lower and 'cetyl' not in name_lower and 'cetearyl' not in name_lower and 'stearyl' not in name_lower:
            avoid_in.extend(['piel_muy_seca', 'piel_atopica'])
            flags.append('potencial_resecante')
        
        if 'peg' in name_lower:
            if ewg > 4:
                avoid_in.append('bebes_menores_6m')
                flags.append('derivado_PEG')
        
        # Ingredientes beneficiosos
        if 'extract' in name_lower or 'oil' in name_lower:
            if baby_risk in ['good', 'ok']:
                flags.append('origen_natural')
        
        if any(word in name_lower for word in ['glycerin', 'panthenol', 'allantoin', 'bisabolol']):
            flags.append('hidratante')
        
        if 'chamomilla' in name_lower or 'calendula' in name_lower or 'aloe' in name_lower:
            flags.append('calmante')
        
        return {
            'risk': baby_risk,
            'summary': summary,
            'avoid_in': avoid_in,
            'flags': flags
        }
    
    def _generate_good_summary(self, name: str, data: Dict[str, Any]) -> str:
        name_lower = name.lower()
        if 'water' in name_lower or 'aqua' in name_lower:
            return "Base segura para cualquier fórmula tear-free."
        if 'glycerin' in name_lower:
            return "Humectante natural que mantiene la piel hidratada y suave."
        if 'panthenol' in name_lower:
            return "Provitamina B5 que calma y repara la barrera cutánea del bebé."
        if 'extract' in name_lower:
            return f"Extracto natural suave y seguro para piel sensible de bebés."
        return "Ingrediente seguro y bien tolerado en fórmulas para bebés."
    
    def _generate_ok_summary(self, name: str, data: Dict[str, Any]) -> str:
        return "Seguro en concentraciones normales; monitorear si hay sensibilidad."
    
    def _generate_caution_summary(self, name: str, data: Dict[str, Any]) -> str:
        name_lower = name.lower()
        if 'sulfate' in name_lower:
            return "Puede resecar; preferir alternativas más suaves para uso diario."
        if 'peg' in name_lower:
            return "Usar con precaución; puede contener trazas de impurezas."
        return "Revisar tolerancia individual; puede causar reacciones en piel sensible."
    
    def _generate_bad_summary(self, name: str, data: Dict[str, Any]) -> str:
        name_lower = name.lower()
        if 'fragrance' in name_lower:
            return "Mezcla química no revelada; principal causa de alergias y brotes en bebés."
        if ewg := data.get('ewg', 0) >= 8:
            return f"Alto riesgo (EWG {ewg}/10); evitar en productos para bebés."
        return "No recomendado para piel de bebés; buscar alternativas más seguras."
    
    def improve_description(self, name: str, data: Dict[str, Any]) -> str:
        """Mejorar descripción corta o genérica"""
        current_desc = data.get('description', '')
        
        # Si ya tiene buena descripción, mantener
        if len(current_desc) > 50 and 'no disponible' not in current_desc.lower():
            return current_desc
        
        name_lower = name.lower()
        score = data.get('score', 70)
        ewg = data.get('ewg', 5)
        eco = data.get('eco', False)
        risk = data.get('risk', 'moderate')
        
        # Templates por tipo de ingrediente
        if 'water' in name_lower or 'aqua' in name_lower:
            return "Agua purificada, ingrediente base esencial y completamente seguro para productos cosméticos. No tiene efectos adversos conocidos."
        
        if 'glycerin' in name_lower:
            return "Humectante natural que atrae y retiene la humedad en la piel. Derivado de fuentes vegetales, es seguro y efectivo para todo tipo de piel."
        
        if 'extract' in name_lower or 'oil' in name_lower:
            origin = "vegetal" if eco else "natural o sintético"
            safety = "Generalmente seguro" if risk == 'low' else "Usar con precaución"
            return f"Extracto/aceite de origen {origin}. {safety} para uso cosmético. Puede proporcionar beneficios antioxidantes y nutritivos para la piel."
        
        if 'sulfate' in name_lower:
            strength = "fuerte" if 'lauryl' in name_lower else "moderado"
            return f"Tensioactivo aniónico de espuma {strength}. Limpia efectivamente pero puede resecar con uso frecuente. EWG {ewg}/10."
        
        if 'paraben' in name_lower:
            return f"Conservante ampliamente usado en cosméticos. Previene crecimiento bacteriano. Controvertido por posibles efectos hormonales. Score {score}/100."
        
        if 'alcohol' in name_lower:
            if any(word in name_lower for word in ['cetyl', 'cetearyl', 'stearyl']):
                return "Alcohol graso emoliente y acondicionador. A pesar del nombre, NO reseca; ayuda a suavizar y estabilizar fórmulas."
            else:
                return f"Alcohol que puede tener efecto resecante según concentración. Usado como solvente o conservante. EWG {ewg}/10."
        
        if 'acid' in name_lower:
            if 'citric' in name_lower:
                return "Ácido cítrico, regulador de pH derivado de cítricos. Ayuda a mantener el pH óptimo en fórmulas. Muy seguro."
            elif 'hyaluronic' in name_lower:
                return "Ácido hialurónico, humectante potente que retiene hasta 1000x su peso en agua. Excelente para hidratación."
            else:
                return f"Ácido usado para ajuste de pH, exfoliación o funciones específicas. Score {score}/100, EWG {ewg}/10."
        
        if 'vitamin' in name_lower or 'tocopherol' in name_lower:
            return "Vitamina antioxidante que protege la piel del daño ambiental. Beneficiosa para salud cutánea."
        
        # Descripción genérica mejorada
        safety_desc = {
            'none': 'completamente seguro',
            'low': 'seguro para uso normal',
            'moderate': 'generalmente seguro pero puede causar reacciones',
            'high': 'usar con precaución o evitar'
        }.get(risk, 'verificar seguridad')
        
        eco_desc = " Eco-friendly y biodegradable." if eco else ""
        
        return f"Ingrediente cosmético {safety_desc}. Score {score}/100, EWG {ewg}/10.{eco_desc} Consultar lista INCI para detalles."
    
    def assign_categories(self, name: str, data: Dict[str, Any]) -> List[str]:
        """Asignar categorías funcionales"""
        categories = set(data.get('categories', []))
        name_lower = name.lower()
        
        # Categorías por función
        if any(word in name_lower for word in ['water', 'aqua']):
            categories.add('solvent')
        
        if any(word in name_lower for word in ['glycerin', 'hyaluronic', 'panthenol', 'aloe']):
            categories.add('humectant')
        
        if any(word in name_lower for word in ['extract', 'oil', 'butter']):
            categories.add('emollient')
            if data.get('eco'):
                categories.add('natural')
        
        if any(word in name_lower for word in ['sulfate', 'glucoside', 'betaine', 'soap']):
            categories.add('surfactant')
            categories.add('cleanser')
        
        if any(word in name_lower for word in ['paraben', 'sorbate', 'benzoate', 'phenoxyethanol']):
            categories.add('preservative')
        
        if any(word in name_lower for word in ['fragrance', 'parfum', 'essential oil']):
            categories.add('fragrance')
        
        if any(word in name_lower for word in ['vitamin', 'tocopherol', 'ascorbic']):
            categories.add('antioxidant')
        
        if any(word in name_lower for word in ['acid', 'aha', 'bha', 'retinol']):
            categories.add('active')
        
        if 'alcohol' in name_lower and any(word in name_lower for word in ['cetyl', 'cetearyl', 'stearyl']):
            categories.add('emollient')
            categories.add('emulsifier')
        
        if any(word in name_lower for word in ['color', 'ci ', 'dye', 'pigment']):
            categories.add('colorant')
        
        if 'uv' in name_lower or 'titanium dioxide' in name_lower or 'zinc oxide' in name_lower:
            categories.add('sunscreen')
        
        # Categorías por tipo de producto
        score = data.get('score', 70)
        if score >= 80 and data.get('eco'):
            categories.add('baby_care')
        
        if 'hair' not in name_lower and 'shampoo' not in categories:
            categories.add('skincare')
        
        return sorted(list(categories))
    
    def fix_high_priority_inconsistencies(self):
        """Corregir las 13 inconsistencias de alta prioridad restantes"""
        print("\n🔧 Corrigiendo inconsistencias de alta prioridad...")
        
        fixes = {
            # Ingredientes con score alto pero risk alto - ajustar
            '2-Hexanediol': {'score': 55, 'risk': 'moderate'},
            'Guazuma ulmifolia leaf extract': {'risk': 'low'},
            'Titanium Dioxide': {'score': 70, 'risk': 'moderate'},
            
            # Otros ajustes necesarios
            'Cetyl Ricinoleate': {'risk': 'low'},
            'Hemp': {'risk': 'low'},
            'Revinage': {'risk': 'low'},
        }
        
        for name, updates in fixes.items():
            if name in self.catalog:
                for key, value in updates.items():
                    old_value = self.catalog[name].get(key)
                    self.catalog[name][key] = value
                    print(f"  ✅ {name}: {key} {old_value} → {value}")
                    self.stats['inconsistencies_fixed'] += 1
    
    def process_all(self):
        """Procesar todos los ingredientes"""
        print("=" * 70)
        print("🔬 COMPLETANDO METADATA DEL CATÁLOGO")
        print("=" * 70)
        
        # Fase 1: Corregir inconsistencias
        self.fix_high_priority_inconsistencies()
        
        # Fase 2: Agregar metadata
        print("\n📝 Agregando baby metadata, descripciones y categorías...")
        
        for name, data in self.catalog.items():
            modified = False
            
            # Baby metadata
            if not data.get('baby'):
                data['baby'] = self.generate_baby_metadata(name, data)
                self.stats['baby_added'] += 1
                modified = True
            
            # Mejorar descripción
            new_desc = self.improve_description(name, data)
            if new_desc != data.get('description', ''):
                data['description'] = new_desc
                self.stats['descriptions_improved'] += 1
                modified = True
            
            # Categorías
            new_categories = self.assign_categories(name, data)
            if new_categories != data.get('categories', []):
                data['categories'] = new_categories
                self.stats['categories_added'] += 1
                modified = True
            
            if modified and self.stats['baby_added'] % 20 == 0:
                print(f"  Procesados: {self.stats['baby_added']} ingredientes...")
        
        print(f"\n✅ Procesamiento completado!")
    
    def print_stats(self):
        """Imprimir estadísticas finales"""
        print("\n" + "=" * 70)
        print("📊 ESTADÍSTICAS DE ACTUALIZACIÓN")
        print("=" * 70)
        print(f"  • Baby metadata agregado: {self.stats['baby_added']}")
        print(f"  • Descripciones mejoradas: {self.stats['descriptions_improved']}")
        print(f"  • Categorías agregadas: {self.stats['categories_added']}")
        print(f"  • Inconsistencias corregidas: {self.stats['inconsistencies_fixed']}")
        print(f"  • Total de actualizaciones: {sum(self.stats.values())}")
        print("=" * 70)


def main():
    # Cargar catálogo
    catalog = load_catalog()
    print(f"📁 Catálogo cargado: {len(catalog)} ingredientes")
    
    # Crear backup
    backup_path = CATALOG_PATH.parent / "ingredient_catalog_backup_before_metadata.json"
    print(f"💾 Creando backup: {backup_path}")
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
    
    # Procesar
    completer = MetadataCompleter(catalog)
    completer.process_all()
    
    # Guardar
    print(f"\n💾 Guardando catálogo actualizado...")
    save_catalog(completer.catalog)
    
    # Estadísticas
    completer.print_stats()
    
    print(f"\n✅ ¡Catálogo completado exitosamente!")
    print(f"📁 Guardado en: {CATALOG_PATH}")


if __name__ == "__main__":
    main()
