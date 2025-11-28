#!/usr/bin/env python3
"""
Finalizar catálogo: validar EWG alto y resolver duplicados
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List
import httpx

CATALOG_PATH = Path(__file__).parent.parent / "backend-python" / "app" / "data" / "ingredient_catalog.json"


def load_catalog() -> Dict[str, Any]:
    with open(CATALOG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_catalog(catalog: Dict[str, Any]):
    with open(CATALOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
        f.write('\n')


async def validate_high_ewg_ingredients():
    """Validar ingredientes con EWG > 8"""
    catalog = load_catalog()
    
    print("=" * 70)
    print("🔬 VALIDANDO INGREDIENTES CON EWG > 8")
    print("=" * 70)
    
    high_ewg = [(name, data) for name, data in catalog.items() if data.get('ewg', 0) >= 8]
    
    print(f"\n📊 Encontrados: {len(high_ewg)} ingredientes con EWG ≥ 8")
    print("\nIngredientes:")
    for name, data in high_ewg:
        print(f"  • {name}: EWG={data.get('ewg')}, Score={data.get('score')}, Risk={data.get('risk')}")
    
    print("\n🔍 Validando contra datos conocidos...")
    
    # Validaciones basadas en literatura científica
    validations = {
        'Sodium Lauryl Sulfate': {
            'ewg_correct': True,  # EWG efectivamente da 1-2 (moderado) no 8
            'recommended_ewg': 2,
            'note': 'SLS es irritante pero EWG score real es 1-2, no 8'
        },
        'Fragrance (Parfum)': {
            'ewg_correct': True,  # EWG sí da 8-10
            'recommended_ewg': 10,
            'note': 'Correcto - mezcla no revelada con alto riesgo alergénico'
        },
        'Fragrance': {
            'ewg_correct': True,
            'recommended_ewg': 8,
            'note': 'Correcto - similar a Fragrance (Parfum)'
        },
        'Parfum': {
            'ewg_correct': True,
            'recommended_ewg': 8,
            'note': 'Correcto - sinónimo de Fragrance'
        },
        'Methylparaben': {
            'ewg_correct': False,  # EWG da 4, no 8
            'recommended_ewg': 4,
            'note': 'EWG real es 4 - conservante controvertido pero no extremo'
        },
        'Propylparaben': {
            'ewg_correct': False,  # EWG da 4, no 8
            'recommended_ewg': 4,
            'note': 'EWG real es 4 - similar a Methylparaben'
        },
        'Butylparaben': {
            'ewg_correct': False,  # EWG da 6, no 8
            'recommended_ewg': 6,
            'note': 'EWG real es 6 - el más problemático de los parabenos'
        },
        'Tetrasodium EDTA': {
            'ewg_correct': False,  # EWG da 3, no 8
            'recommended_ewg': 3,
            'note': 'EWG real es 3 - quelante seguro en cosméticos'
        },
    }
    
    print("\n🔧 Aplicando correcciones...")
    corrections = 0
    
    for name, validation in validations.items():
        if name in catalog and not validation['ewg_correct']:
            old_ewg = catalog[name]['ewg']
            new_ewg = validation['recommended_ewg']
            catalog[name]['ewg'] = new_ewg
            
            # Ajustar score y risk también
            if new_ewg <= 3:
                catalog[name]['score'] = max(75, catalog[name].get('score', 50))
                catalog[name]['risk'] = 'low'
            elif new_ewg <= 6:
                catalog[name]['score'] = max(60, catalog[name].get('score', 50))
                catalog[name]['risk'] = 'moderate'
            
            print(f"  ✅ {name}: EWG {old_ewg} → {new_ewg}")
            print(f"     {validation['note']}")
            corrections += 1
    
    print(f"\n✅ Correcciones aplicadas: {corrections}")
    
    # Guardar
    save_catalog(catalog)
    
    return corrections


def resolve_similar_duplicates():
    """Resolver duplicados similares manualmente"""
    catalog = load_catalog()
    
    print("\n" + "=" * 70)
    print("🔍 RESOLVIENDO DUPLICADOS SIMILARES")
    print("=" * 70)
    
    # Duplicados a fusionar o eliminar
    duplicates_to_merge = {
        # Parabenos ya están bien (Methylparaben, etc.)
        # Phosphates
        'Dipotassium Phosphate': {
            'keep': True,
            'note': 'Diferente de Potassium Phosphate (uno tiene 2 K+)'
        },
        # Ceramides  
        'Ceramide AP': {
            'keep': True,
            'note': 'Diferente tipo de ceramida que Ceramide NP'
        },
        # Alcoholes
        'Cetyl alcohol': {
            'keep': True,
            'add_alias': ['Cetyl Alcohol']
        },
        'Stearyl alcohol': {
            'keep': True,
            'add_alias': ['Stearyl Alcohol']
        },
        # Proteínas
        'Hydrolyzed Corn Protein': {
            'keep': True,
            'note': 'Diferente fuente que Hydrolyzed Soy Protein'
        },
        # Calendula
        'Calendula': {
            'merge_into': 'Caléndula',
            'note': 'Mismo ingrediente, preferir español'
        },
    }
    
    print("\n📝 Procesando duplicados similares...")
    
    resolved = 0
    for name, action in duplicates_to_merge.items():
        if name in catalog:
            if action.get('keep'):
                # Agregar aliases
                if 'add_alias' in action:
                    if 'aliases' not in catalog[name]:
                        catalog[name]['aliases'] = []
                    for alias in action['add_alias']:
                        if alias not in catalog[name]['aliases']:
                            catalog[name]['aliases'].append(alias)
                    print(f"  ✅ {name}: agregados aliases {action['add_alias']}")
                    resolved += 1
            
            elif 'merge_into' in action:
                target = action['merge_into']
                if target in catalog:
                    # Merge data
                    if 'aliases' not in catalog[target]:
                        catalog[target]['aliases'] = []
                    if name not in catalog[target]['aliases']:
                        catalog[target]['aliases'].append(name)
                    
                    # Delete duplicate
                    del catalog[name]
                    print(f"  ✅ {name} → {target} (merged)")
                    resolved += 1
    
    print(f"\n✅ Duplicados resueltos: {resolved}")
    
    # Guardar
    save_catalog(catalog)
    
    return resolved


async def main():
    """Main function"""
    print("\n" + "=" * 70)
    print("🎯 FINALIZACIÓN DEL CATÁLOGO DE INGREDIENTES")
    print("=" * 70)
    
    # Validar EWG alto
    ewg_corrections = await validate_high_ewg_ingredients()
    
    # Resolver duplicados
    duplicates_resolved = resolve_similar_duplicates()
    
    # Resumen final
    catalog = load_catalog()
    
    print("\n" + "=" * 70)
    print("📊 RESUMEN FINAL")
    print("=" * 70)
    print(f"  • Total ingredientes: {len(catalog)}")
    print(f"  • Correcciones EWG: {ewg_corrections}")
    print(f"  • Duplicados resueltos: {duplicates_resolved}")
    
    # Estadísticas finales
    with_baby = sum(1 for d in catalog.values() if d.get('baby'))
    with_categories = sum(1 for d in catalog.values() if d.get('categories'))
    avg_score = sum(d.get('score', 0) for d in catalog.values()) / len(catalog)
    avg_ewg = sum(d.get('ewg', 0) for d in catalog.values()) / len(catalog)
    
    print(f"\n  Calidad del Catálogo:")
    print(f"    • Con baby metadata: {with_baby}/{len(catalog)} ({with_baby/len(catalog)*100:.1f}%)")
    print(f"    • Con categorías: {with_categories}/{len(catalog)} ({with_categories/len(catalog)*100:.1f}%)")
    print(f"    • Score promedio: {avg_score:.2f}/100")
    print(f"    • EWG promedio: {avg_ewg:.2f}/10")
    
    print("\n✅ ¡Catálogo finalizado exitosamente!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
