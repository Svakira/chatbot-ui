#!/usr/bin/env python3
"""
Script para verificar la conexión con el servidor del modelo
"""

import requests
import json

# Configuración
API_URL = "http://154.54.100.200:8090/v1/chat/completions"
MODEL_NAME = "RedHatAI/Llama-4-Scout-17B-16E-Instruct-FP8-dynamic"

def test_connection():
    print("="*70)
    print("TEST DE CONEXIÓN CON EL MODELO")
    print("="*70)
    print(f"\nURL: {API_URL}")
    print(f"Modelo: {MODEL_NAME}\n")
    
    # Preparar un mensaje de prueba simple
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hi! Just say 'Connection successful' if you receive this."}
        ],
        "max_tokens": 50,
        "temperature": 0.3
    }
    
    print("Enviando mensaje de prueba...")
    
    try:
        response = requests.post(
            API_URL,
            json=payload,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print("\n" + "="*70)
            print("✅ CONEXIÓN EXITOSA")
            print("="*70)
            
            if 'choices' in result and len(result['choices']) > 0:
                message = result['choices'][0]['message']['content']
                print(f"\nRespuesta del modelo:\n{message}")
            
            if 'usage' in result:
                usage = result['usage']
                print(f"\nTokens utilizados:")
                print(f"  - Prompt: {usage.get('prompt_tokens', 'N/A')}")
                print(f"  - Completion: {usage.get('completion_tokens', 'N/A')}")
                print(f"  - Total: {usage.get('total_tokens', 'N/A')}")
            
            print("\n✅ El servidor está funcionando correctamente!")
            return True
            
        else:
            print("\n" + "="*70)
            print("❌ ERROR EN LA RESPUESTA")
            print("="*70)
            print(f"\nStatus: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
            
    except requests.exceptions.Timeout:
        print("\n" + "="*70)
        print("❌ TIMEOUT")
        print("="*70)
        print("\nLa conexión tardó demasiado (>30s).")
        print("El servidor puede estar sobrecargado o no responde.")
        return False
        
    except requests.exceptions.ConnectionError:
        print("\n" + "="*70)
        print("❌ ERROR DE CONEXIÓN")
        print("="*70)
        print("\nNo se pudo conectar al servidor.")
        print("Verifica:")
        print("  1. La IP y puerto son correctos")
        print("  2. El servidor está en ejecución")
        print("  3. No hay firewall bloqueando la conexión")
        print("  4. Tienes conectividad de red")
        return False
        
    except Exception as e:
        print("\n" + "="*70)
        print("❌ ERROR INESPERADO")
        print("="*70)
        print(f"\nError: {e}")
        return False

if __name__ == "__main__":
    test_connection()
    print("\n" + "="*70)
