"""
Update database.py with INCI Beauty data
Comprehensive script to enhance the local database with INCI Beauty data
"""

import asyncio
import httpx
import json
import os
import re
from typing import Dict, List, Optional
from inci_beauty_api import INCIClient
from database import LOCAL_INGREDIENT_DATABASE

class DatabaseUpdater:
    def __init__(self):
        self.api_key = os.getenv("INCI_BEAUTY_API_KEY")
        self.enhanced_database = LOCAL_INGREDIENT_DATABASE.copy()
        
    async def enhance_with_inci_beauty_api(self) -> Dict[str, Dict]:
        """Enhance database using INCI Beauty Pro API."""
        if not self.api_key or self.api_key == "your_inci_beauty_api_key_here":
            print("⚠️  INCI_BEAUTY_API_KEY not configured")
            print("💡 To use INCI Beauty Pro API, add your API key to .env file:")
            print("   INCI_BEAUTY_API_KEY=your_actual_api_key_here")
            return self.enhanced_database
        
        print("🔌 Enhancing database with INCI Beauty Pro API...")
        
        async with INCIClient() as client:
            enhanced_count = 0
            
            for ingredient_name in self.enhanced_database.keys():
                try:
                    print(f"   Fetching data for: {ingredient_name}")
                    result = await client.get_ingredient_data(ingredient_name)
                    
                    if result.success:
                        data = result.data
                        
                        # Enhance existing data
                        if ingredient_name in self.enhanced_database:
                            existing = self.enhanced_database[ingredient_name]
                            
                            # Update with INCI Beauty data if available
                            if data.get("benefits") and data["benefits"] != "No disponible":
                                existing["benefits"] = f"{existing['benefits']} | {data['benefits']}"
                            
                            if data.get("risks_detailed") and data["risks_detailed"] != "No disponible":
                                existing["risks_detailed"] = f"{existing['risks_detailed']} | {data['risks_detailed']}"
                            
                            if data.get("eco_score"):
                                existing["eco_score"] = data["eco_score"]
                            
                            if data.get("risk_level") and data["risk_level"] != "desconocido":
                                existing["risk_level"] = data["risk_level"]
                            
                            existing["sources"] = f"{existing['sources']}, INCI Beauty Pro"
                            enhanced_count += 1
                        else:
                            # Add new ingredient
                            self.enhanced_database[ingredient_name] = {
                                "eco_score": data.get("eco_score", 50.0),
                                "risk_level": data.get("risk_level", "desconocido"),
                                "benefits": data.get("benefits", "No disponible"),
                                "risks_detailed": data.get("risks_detailed", "No disponible"),
                                "sources": "INCI Beauty Pro"
                            }
                            enhanced_count += 1
                    
                    await asyncio.sleep(1)  # Rate limiting
                    
                except Exception as e:
                    print(f"   ❌ Error fetching {ingredient_name}: {e}")
                    continue
            
            print(f"✅ Enhanced {enhanced_count} ingredients with INCI Beauty Pro data")
            return self.enhanced_database
    
    def add_common_cosmetic_ingredients(self) -> Dict[str, Dict]:
        """Add common cosmetic ingredients to the database."""
        print("📝 Adding common cosmetic ingredients...")
        
        common_ingredients = {
            "glycerin": {
                "eco_score": 85.0,
                "risk_level": "seguro",
                "benefits": "Hidratante intenso, mejora la textura de la piel, suavizante",
                "risks_detailed": "Muy seguro, raramente causa irritación",
                "sources": "Local Database + FDA + CIR"
            },
            "dimethicone": {
                "eco_score": 60.0,
                "risk_level": "riesgo bajo",
                "benefits": "Suavizante, mejora textura, protege barrera cutánea",
                "risks_detailed": "No biodegradable, puede acumularse en el medio ambiente",
                "sources": "Local Database + CIR Research"
            },
            "niacinamide": {
                "eco_score": 80.0,
                "risk_level": "riesgo bajo",
                "benefits": "Regula producción de sebo, mejora textura, antiinflamatorio",
                "risks_detailed": "Puede causar irritación leve en concentraciones altas",
                "sources": "Local Database + FDA + CIR"
            },
            "salicylic acid": {
                "eco_score": 70.0,
                "risk_level": "riesgo bajo",
                "benefits": "Exfoliante químico, trata acné, mejora textura",
                "risks_detailed": "Puede causar irritación, evitar durante embarazo",
                "sources": "Local Database + FDA Research"
            },
            "titanium dioxide": {
                "eco_score": 75.0,
                "risk_level": "riesgo bajo",
                "benefits": "Filtro UV físico, protege contra rayos UVA/UVB",
                "risks_detailed": "Precaución con nanopartículas, puede dejar residuo blanco",
                "sources": "Local Database + FDA Research"
            },
            "zinc oxide": {
                "eco_score": 80.0,
                "risk_level": "riesgo bajo",
                "benefits": "Filtro UV físico, antiinflamatorio, cicatrizante",
                "risks_detailed": "Puede dejar residuo blanco, precaución con nanopartículas",
                "sources": "Local Database + FDA Research"
            },
            "vitamin c": {
                "eco_score": 75.0,
                "risk_level": "riesgo bajo",
                "benefits": "Antioxidante, ilumina la piel, estimula colágeno",
                "risks_detailed": "Puede causar irritación, inestable con la luz",
                "sources": "Local Database + FDA + CIR"
            },
            "peptides": {
                "eco_score": 85.0,
                "risk_level": "seguro",
                "benefits": "Anti-envejecimiento, mejora elasticidad, reduce arrugas",
                "risks_detailed": "Muy seguro, raramente causa efectos adversos",
                "sources": "Local Database + FDA + CIR"
            },
            "ceramides": {
                "eco_score": 90.0,
                "risk_level": "seguro",
                "benefits": "Restaura barrera cutánea, hidrata, protege",
                "risks_detailed": "Muy seguro, componente natural de la piel",
                "sources": "Local Database + FDA + CIR"
            },
            "squalane": {
                "eco_score": 85.0,
                "risk_level": "seguro",
                "benefits": "Hidratante natural, suavizante, no comedogénico",
                "risks_detailed": "Muy seguro, similar a los lípidos naturales de la piel",
                "sources": "Local Database + FDA + CIR"
            },
            "hyaluronic acid": {
                "eco_score": 85.0,
                "risk_level": "seguro",
                "benefits": "Hidratante intenso, mejora elasticidad, reduce arrugas",
                "risks_detailed": "Muy seguro, raramente causa irritación",
                "sources": "Local Database + FDA + CIR"
            },
            "alpha hydroxy acids": {
                "eco_score": 65.0,
                "risk_level": "riesgo bajo",
                "benefits": "Exfoliante químico, mejora textura, reduce manchas",
                "risks_detailed": "Puede causar irritación, aumenta sensibilidad al sol",
                "sources": "Local Database + FDA Research"
            },
            "beta hydroxy acid": {
                "eco_score": 70.0,
                "risk_level": "riesgo bajo",
                "benefits": "Exfoliante químico, trata acné, mejora textura",
                "risks_detailed": "Puede causar irritación, evitar durante embarazo",
                "sources": "Local Database + FDA Research"
            },
            "mineral oil": {
                "eco_score": 40.0,
                "risk_level": "riesgo medio",
                "benefits": "Hidratante, protector, económico",
                "risks_detailed": "Puede ser comedogénico, derivado del petróleo",
                "sources": "Local Database + EWG Research"
            },
            "lanolin": {
                "eco_score": 50.0,
                "risk_level": "riesgo medio",
                "benefits": "Hidratante natural, emoliente",
                "risks_detailed": "Puede causar alergias, derivado de ovejas",
                "sources": "Local Database + EWG Research"
            }
        }
        
        added_count = 0
        for ingredient, data in common_ingredients.items():
            if ingredient not in self.enhanced_database:
                self.enhanced_database[ingredient] = data
                added_count += 1
        
        print(f"✅ Added {added_count} new common cosmetic ingredients")
        return self.enhanced_database
    
    def add_high_risk_ingredients(self) -> Dict[str, Dict]:
        """Add known high-risk ingredients to the database."""
        print("⚠️  Adding high-risk ingredients...")
        
        high_risk_ingredients = {
            "formaldehyde": {
                "eco_score": 20.0,
                "risk_level": "riesgo alto",
                "benefits": "Conservante, previene crecimiento bacteriano",
                "risks_detailed": "Carcinógeno conocido, irritante de piel y ojos, puede causar alergias",
                "sources": "Local Database + IARC + FDA"
            },
            "benzene": {
                "eco_score": 10.0,
                "risk_level": "riesgo alto",
                "benefits": "Solvente industrial",
                "risks_detailed": "Carcinógeno conocido, puede causar leucemia, irritante",
                "sources": "Local Database + IARC + FDA"
            },
            "toluene": {
                "eco_score": 15.0,
                "risk_level": "riesgo alto",
                "benefits": "Solvente industrial",
                "risks_detailed": "Neurotóxico, puede causar daño al sistema nervioso",
                "sources": "Local Database + IARC + FDA"
            },
            "lead": {
                "eco_score": 5.0,
                "risk_level": "riesgo alto",
                "benefits": "Colorante (prohibido en cosméticos)",
                "risks_detailed": "Neurotóxico, prohibido en cosméticos en la mayoría de países",
                "sources": "Local Database + FDA + EU Regulations"
            },
            "mercury": {
                "eco_score": 5.0,
                "risk_level": "riesgo alto",
                "benefits": "Conservante (prohibido en cosméticos)",
                "risks_detailed": "Neurotóxico, prohibido en cosméticos en la mayoría de países",
                "sources": "Local Database + FDA + EU Regulations"
            },
            "parabens": {
                "eco_score": 30.0,
                "risk_level": "riesgo medio",
                "benefits": "Conservante efectivo, previene contaminación microbiana",
                "risks_detailed": "Disruptor endocrino potencial, puede interferir con hormonas",
                "sources": "Local Database + EWG Research"
            },
            "sodium lauryl sulfate": {
                "eco_score": 40.0,
                "risk_level": "riesgo medio",
                "benefits": "Agente espumante, limpiador efectivo",
                "risks_detailed": "Puede causar irritación en piel sensible, reseca la piel",
                "sources": "Local Database + EWG Research"
            },
            "triclosan": {
                "eco_score": 25.0,
                "risk_level": "riesgo alto",
                "benefits": "Antibacteriano, conservante",
                "risks_detailed": "Disruptor endocrino, puede contribuir a resistencia bacteriana",
                "sources": "Local Database + FDA + EWG Research"
            },
            "phthalates": {
                "eco_score": 20.0,
                "risk_level": "riesgo alto",
                "benefits": "Plastificante, mejora textura",
                "risks_detailed": "Disruptor endocrino, puede afectar desarrollo reproductivo",
                "sources": "Local Database + EWG Research"
            },
            "coal tar": {
                "eco_score": 10.0,
                "risk_level": "riesgo alto",
                "benefits": "Colorante, tratamiento de psoriasis",
                "risks_detailed": "Carcinógeno conocido, puede causar cáncer de piel",
                "sources": "Local Database + IARC + FDA"
            }
        }
        
        added_count = 0
        for ingredient, data in high_risk_ingredients.items():
            if ingredient not in self.enhanced_database:
                self.enhanced_database[ingredient] = data
                added_count += 1
        
        print(f"✅ Added {added_count} high-risk ingredients for safety awareness")
        return self.enhanced_database
    
    def generate_database_code(self) -> str:
        """Generate the updated database.py code."""
        print("📝 Generating updated database.py code...")
        
        # Sort ingredients alphabetically
        sorted_ingredients = dict(sorted(self.enhanced_database.items()))
        
        # Generate the code
        code = '''# Comprehensive local ingredient database
LOCAL_INGREDIENT_DATABASE = {
'''
        
        for ingredient, data in sorted_ingredients.items():
            code += f'    "{ingredient}": {{\n'
            code += f'        "eco_score": {data["eco_score"]},\n'
            code += f'        "risk_level": "{data["risk_level"]}",\n'
            code += f'        "benefits": "{data["benefits"]}",\n'
            code += f'        "risks_detailed": "{data["risks_detailed"]}",\n'
            code += f'        "sources": "{data["sources"]}"\n'
            code += '    },\n'
        
        code += '}\n'
        
        return code
    
    def update_database_file(self):
        """Update the database.py file with enhanced data."""
        print("📁 Updating database.py file...")
        
        try:
            # Read current database.py
            with open('database.py', 'r') as f:
                content = f.read()
            
            # Generate new database code
            new_database_code = self.generate_database_code()
            
            # Replace the LOCAL_INGREDIENT_DATABASE section
            pattern = r'LOCAL_INGREDIENT_DATABASE = \{[^}]*\}'
            updated_content = re.sub(pattern, new_database_code.strip(), content, flags=re.DOTALL)
            
            # Write updated file
            with open('database.py', 'w') as f:
                f.write(updated_content)
            
            print("✅ Successfully updated database.py")
            print(f"📊 Total ingredients in database: {len(self.enhanced_database)}")
            
        except Exception as e:
            print(f"❌ Error updating database.py: {e}")
    
    async def run_full_update(self):
        """Run the complete database update process."""
        print("🚀 Starting comprehensive database update...")
        print("=" * 60)
        
        # Step 1: Add common ingredients
        self.add_common_cosmetic_ingredients()
        
        # Step 2: Add high-risk ingredients
        self.add_high_risk_ingredients()
        
        # Step 3: Enhance with INCI Beauty Pro API
        await self.enhance_with_inci_beauty_api()
        
        # Step 4: Update database file
        self.update_database_file()
        
        print("\\n🎉 Database update completed!")
        print(f"📊 Final database contains {len(self.enhanced_database)} ingredients")
        
        # Show summary
        risk_levels = {}
        for ingredient, data in self.enhanced_database.items():
            risk = data["risk_level"]
            risk_levels[risk] = risk_levels.get(risk, 0) + 1
        
        print("\\n📈 Risk Level Distribution:")
        for risk, count in sorted(risk_levels.items()):
            print(f"   {risk}: {count} ingredients")

# Test function
async def test_database_updater():
    """Test the database updater."""
    updater = DatabaseUpdater()
    await updater.run_full_update()

if __name__ == "__main__":
    asyncio.run(test_database_updater())