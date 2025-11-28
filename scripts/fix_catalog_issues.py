#!/usr/bin/env python3
"""
Script para corregir automáticamente las inconsistencias detectadas
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any

CATALOG_PATH = Path(__file__).parent.parent / "backend-python" / "app" / "data" / "ingredient_catalog.json"
REPORT_PATH = Path(__file__).parent / "catalog_analysis_report.json"


def load_json(path: Path) -> Dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(path: Path, data: Dict):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write('\n')


def fix_aqua_water(catalog: Dict) -> int:
    """Aqua/Water debería ser risk=none, no moderate"""
    fixed = 0
    for name in ["Aqua/Water/Eau", "Aqua", "Water"]:
        if name in catalog:
            if catalog[name].get('risk') == 'moderate':
                catalog[name]['risk'] = 'none'
                print(f"  ✅ {name}: risk moderate → none")
                fixed += 1
    return fixed


def fix_natural_extracts(catalog: Dict) -> int:
    """Extractos naturales con score alto deberían tener risk=low"""
    fixed = 0
    natural_keywords = ['extract', 'leaf', 'fruit', 'flower', 'seed', 'root']
    
    for name, data in catalog.items():
        name_lower = name.lower()
        
        # Si es un extracto natural
        if any(kw in name_lower for kw in natural_keywords):
            score = data.get('score', 0)
            ewg = data.get('ewg', 0)
            risk = data.get('risk', '')
            
            # Si tiene buen score y bajo EWG pero risk alto/moderate, corregir
            if score >= 80 and ewg <= 3 and risk in ['moderate', 'high']:
                catalog[name]['risk'] = 'low'
                print(f"  ✅ {name}: risk {risk} → low (extracto natural)")
                fixed += 1
    
    return fixed


def fix_score_risk_mismatch(catalog: Dict) -> int:
    """Corregir desajustes entre score y risk level"""
    fixed = 0
    
    for name, data in catalog.items():
        score = data.get('score', 0)
        risk = data.get('risk', '')
        
        # Score muy alto (>85) con risk high es inconsistente
        if score >= 85 and risk == 'high':
            # Ajustar score o risk según EWG
            ewg = data.get('ewg', 0)
            if ewg >= 7:
                # EWG alto: bajar score
                catalog[name]['score'] = 50
                print(f"  ✅ {name}: score 85+ → 50 (por EWG alto)")
            else:
                # EWG bajo: bajar risk
                catalog[name]['risk'] = 'moderate'
                print(f"  ✅ {name}: risk high → moderate")
            fixed += 1
        
        # Score bajo (<50) con risk low es inconsistente
        elif score < 50 and risk == 'low':
            catalog[name]['risk'] = 'moderate'
            print(f"  ✅ {name}: risk low → moderate (score bajo)")
            fixed += 1
    
    return fixed


def fix_potassium_sorbate(catalog: Dict) -> int:
    """Potassium Sorbate tiene todos los campos vacíos"""
    fixed = 0
    
    if "Potassium Sorbate" in catalog:
        ps = catalog["Potassium Sorbate"]
        
        # Restaurar desde el catálogo original (valores seguros conocidos)
        ps['score'] = 80
        ps['ewg'] = 3
        ps['risk'] = 'low'
        ps['eco'] = True
        ps['description'] = "Conservante suave derivado del ácido sórbico. Ampliamente usado en alimentos y cosméticos. Seguro en concentraciones normales."
        ps['categories'] = ['preservative', 'baby_care']
        
        print(f"  ✅ Potassium Sorbate: restaurado completamente")
        fixed += 1
    
    return fixed


def remove_duplicates(catalog: Dict) -> int:
    """Eliminar duplicados exactos (mayúsculas/minúsculas)"""
    fixed = 0
    to_remove = []
    seen_lowercase = {}
    
    for name in catalog.keys():
        name_lower = name.lower()
        if name_lower in seen_lowercase:
            # Duplicado encontrado
            original = seen_lowercase[name_lower]
            print(f"  ⚠️  Duplicado: '{name}' vs '{original}'")
            
            # Mantener el que tiene más datos
            if len(str(catalog[name])) < len(str(catalog[original])):
                to_remove.append(name)
                print(f"    → Eliminando '{name}' (menos datos)")
            else:
                to_remove.append(original)
                seen_lowercase[name_lower] = name
                print(f"    → Eliminando '{original}' (menos datos)")
            fixed += 1
        else:
            seen_lowercase[name_lower] = name
    
    for name in to_remove:
        del catalog[name]
    
    return fixed


def fix_parabens(catalog: Dict) -> int:
    """Estandarizar nombres de parabenos"""
    fixed = 0
    
    paraben_mapping = {
        "Methyl paraben": "Methylparaben",
        "Propyl paraben": "Propylparaben",
        "Butyl paraben": "Butylparaben",
        "Ethyl paraben": "Ethylparaben"
    }
    
    for old_name, new_name in paraben_mapping.items():
        if old_name in catalog and new_name in catalog:
            # Merge data (preferir el que tiene más información)
            if len(str(catalog[old_name])) > len(str(catalog[new_name])):
                catalog[new_name] = catalog[old_name]
            
            # Agregar alias
            if 'aliases' not in catalog[new_name]:
                catalog[new_name]['aliases'] = []
            if old_name not in catalog[new_name]['aliases']:
                catalog[new_name]['aliases'].append(old_name)
            
            del catalog[old_name]
            print(f"  ✅ {old_name} → {new_name} (merged)")
            fixed += 1
        elif old_name in catalog:
            # Solo renombrar
            catalog[new_name] = catalog[old_name]
            del catalog[old_name]
            print(f"  ✅ {old_name} → {new_name} (renamed)")
            fixed += 1
    
    return fixed


def main():
    print("=" * 70)
    print("🔧 CORRECCIÓN AUTOMÁTICA DE INCONSISTENCIAS")
    print("=" * 70)
    
    # Cargar catálogo
    catalog = load_json(CATALOG_PATH)
    print(f"📁 Catálogo cargado: {len(catalog)} ingredientes\n")
    
    total_fixed = 0
    
    # Aplicar correcciones
    print("🔹 Corrigiendo Aqua/Water...")
    total_fixed += fix_aqua_water(catalog)
    
    print("\n🔹 Corrigiendo extractos naturales...")
    total_fixed += fix_natural_extracts(catalog)
    
    print("\n🔹 Corrigiendo desajustes score-risk...")
    total_fixed += fix_score_risk_mismatch(catalog)
    
    print("\n🔹 Reparando Potassium Sorbate...")
    total_fixed += fix_potassium_sorbate(catalog)
    
    print("\n🔹 Eliminando duplicados...")
    total_fixed += remove_duplicates(catalog)
    
    print("\n🔹 Estandarizando parabenos...")
    total_fixed += fix_parabens(catalog)
    
    # Guardar catálogo corregido
    backup_path = CATALOG_PATH.parent / "ingredient_catalog_backup.json"
    print(f"\n💾 Creando backup: {backup_path}")
    save_json(backup_path, load_json(CATALOG_PATH))
    
    print(f"💾 Guardando catálogo corregido...")
    save_json(CATALOG_PATH, catalog)
    
    print("\n" + "=" * 70)
    print(f"✅ CORRECCIONES COMPLETADAS")
    print("=" * 70)
    print(f"  Total correcciones aplicadas: {total_fixed}")
    print(f"  Ingredientes finales: {len(catalog)}")
    print(f"  Backup guardado en: {backup_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
