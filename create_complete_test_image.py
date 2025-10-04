#!/usr/bin/env python3
"""
Crear imagen sintética completa con todos los 17 ingredientes esperados
para testear el sistema con precisión real.
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_complete_test_image():
    """Crear imagen sintética con todos los ingredientes esperados."""
    
    # Lista completa de ingredientes esperados
    ingredients = [
        "Water (Aqua)",
        "Cetearyl Alcohol", 
        "Glyceryl Stearate",
        "PEG-100 Stearate",
        "Glycerin",
        "Phenoxyethanol",
        "Ethylhexylglycerin",
        "Stearic Acid",
        "Parfum (Fragrance)",
        "Isopropyl Palmitate",
        "Triethanolamine",
        "Acrylates/C10-30 Alkyl Acrylate Crosspolymer",
        "Helianthus Annuus Seed Oil",
        "Aloe Barbadensis Leaf Extract",
        "Avena Sativa Kernel Extract",
        "Gossypium Herbaceum Seed Oil",
        "Citric Acid"
    ]
    
    # Crear imagen más grande para acomodar todos los ingredientes
    img = Image.new('RGB', (1000, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    # Usar fuente más pequeña para simular texto denso
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 14)
    except:
        font = ImageFont.load_default()
    
    # Dibujar título
    draw.text((20, 20), "INGREDIENTS / INGREDIENTES", fill='black', font=font)
    
    # Dibujar ingredientes en múltiples columnas
    y_offset = 60
    x_offset = 20
    max_width = 480  # Ancho máximo por columna
    
    for i, ingredient in enumerate(ingredients):
        # Cambiar a segunda columna si es necesario
        if i == len(ingredients) // 2:
            x_offset = 520
            y_offset = 60
        
        # Dibujar ingrediente
        draw.text((x_offset, y_offset), ingredient, fill='black', font=font)
        y_offset += 25
    
    # Guardar imagen
    img.save('complete_test_image.png')
    print(f"✅ Created complete test image with {len(ingredients)} ingredients")
    print(f"   Image size: {img.size}")
    print(f"   Saved as: complete_test_image.png")
    
    return 'complete_test_image.png'

if __name__ == "__main__":
    create_complete_test_image()