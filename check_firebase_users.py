#!/usr/bin/env python3
"""
Script para consultar usuarios en Firebase
"""

import os
import sys
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from firebase_config import initialize_firebase, get_firestore_client, is_firebase_available

def check_firebase_users():
    """Consulta usuarios en Firebase"""
    
    print("=" * 60)
    print("🔥 CONSULTANDO USUARIOS EN FIREBASE")
    print("=" * 60)
    
    # Check if Firebase is available
    if not is_firebase_available():
        print("❌ Firebase no está disponible o no está configurado correctamente")
        print("   Verifica que las credenciales de Firebase estén configuradas")
        return
    
    try:
        # Get Firestore client
        db = get_firestore_client()
        
        # Query users collection
        users_ref = db.collection('users')
        users = users_ref.stream()
        
        user_count = 0
        users_list = []
        
        for user_doc in users:
            user_count += 1
            user_data = user_doc.to_dict()
            users_list.append({
                'id': user_doc.id,
                'data': user_data
            })
        
        print(f"👥 Total de usuarios en Firebase: {user_count}")
        
        if user_count > 0:
            print("\n📋 DETALLES DE USUARIOS EN FIREBASE:")
            print("-" * 60)
            
            for user in users_list:
                user_data = user['data']
                print(f"ID: {user['id']}")
                print(f"   Email: {user_data.get('email', 'N/A')}")
                print(f"   Username: {user_data.get('username', 'N/A')}")
                print(f"   Creado: {user_data.get('created_at', 'N/A')}")
                print(f"   Actualizado: {user_data.get('updated_at', 'N/A')}")
                print()
        else:
            print("ℹ️  No hay usuarios registrados en Firebase")
            print("   Los usuarios se registran en Firebase cuando:")
            print("   - Se registran con email/contraseña usando Firebase Auth")
            print("   - Se migran desde la base de datos local")
        
        # Check analysis results
        analysis_ref = db.collection('analysis_results')
        analysis_docs = analysis_ref.stream()
        
        analysis_count = 0
        for doc in analysis_docs:
            analysis_count += 1
        
        print(f"📊 Análisis guardados en Firebase: {analysis_count}")
        
    except Exception as e:
        print(f"❌ Error al consultar Firebase: {e}")
        print("   Verifica que las credenciales de Firebase estén configuradas correctamente")

if __name__ == "__main__":
    load_dotenv()
    check_firebase_users()