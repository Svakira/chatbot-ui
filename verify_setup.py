#!/usr/bin/env python3
"""
Script de verificación del proyecto
Verifica que todos los archivos y configuraciones estén correctos
"""

import os
import sys

def check_file(filepath, description):
    """Verifica si un archivo existe"""
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        print(f"✅ {description:40} ({size:,} bytes)")
        return True
    else:
        print(f"❌ {description:40} [NO ENCONTRADO]")
        return False

def check_directory(dirpath, description):
    """Verifica si un directorio existe"""
    if os.path.exists(dirpath) and os.path.isdir(dirpath):
        count = len(os.listdir(dirpath))
        print(f"✅ {description:40} ({count} archivos)")
        return True
    else:
        print(f"⚠️  {description:40} [NO EXISTE - se creará]")
        return False

def main():
    print("="*70)
    print("VERIFICACIÓN DEL PROYECTO - CONTEXT CHATBOT")
    print("="*70)
    print()
    
    all_ok = True
    
    # Archivos principales
    print("📁 ARCHIVOS PRINCIPALES:")
    print("-"*70)
    all_ok &= check_file("app.py", "Servidor Flask")
    all_ok &= check_file("templates/index.html", "Interfaz Web")
    all_ok &= check_file("requirements.txt", "Dependencias")
    print()
    
    # Scripts
    print("🔧 SCRIPTS:")
    print("-"*70)
    check_file("start.sh", "Script inicio Mac")
    check_file("start_ubuntu.sh", "Script inicio Ubuntu")
    check_file("test_connection.py", "Test de conexión")
    print()
    
    # Documentación
    print("📚 DOCUMENTACIÓN:")
    print("-"*70)
    check_file("README.md", "Documentación general")
    check_file("QUICK_START.md", "Guía rápida")
    check_file("DEPLOYMENT_UBUNTU.md", "Guía despliegue Ubuntu")
    check_file("FILES_OVERVIEW.md", "Vista general archivos")
    print()
    
    # Directorios
    print("📂 DIRECTORIOS:")
    print("-"*70)
    check_directory("templates", "Directorio templates")
    check_directory("uploads", "Directorio uploads")
    print()
    
    # Permisos de scripts (solo en Unix)
    if os.name != 'nt':
        print("🔐 PERMISOS DE SCRIPTS:")
        print("-"*70)
        scripts = ["start.sh", "start_ubuntu.sh", "test_connection.py"]
        for script in scripts:
            if os.path.exists(script):
                if os.access(script, os.X_OK):
                    print(f"✅ {script:40} [EJECUTABLE]")
                else:
                    print(f"⚠️  {script:40} [NO EJECUTABLE]")
                    print(f"   Ejecuta: chmod +x {script}")
        print()
    
    # Verificar variables de entorno
    print("🔍 VARIABLES DE ENTORNO:")
    print("-"*70)
    
    env_file_exists = os.path.exists(".env")
    env_example_exists = os.path.exists(".env.example")
    
    if env_file_exists:
        print("✅ Archivo .env encontrado")
        
        # Cargar y mostrar configuración
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            model_url = os.getenv('MODEL_API_URL', 'No configurado')
            model_name = os.getenv('MODEL_NAME', 'No configurado')
            flask_port = os.getenv('FLASK_PORT', '5000')
            flask_debug = os.getenv('FLASK_DEBUG', 'True')
            
            print(f"   API URL: {model_url}")
            print(f"   Modelo: {model_name[:50]}...")
            print(f"   Puerto: {flask_port}")
            print(f"   Debug: {flask_debug}")
            
            if flask_debug.lower() == 'true':
                print("   ⚠️  Para producción, cambia FLASK_DEBUG=False en .env")
        except ImportError:
            print("⚠️  python-dotenv no instalado   [pip install python-dotenv]")
    else:
        print("⚠️  Archivo .env no encontrado")
        print("   Crea uno desde: cp .env.example .env")
    
    if env_example_exists:
        print("✅ Archivo .env.example disponible como plantilla")
    
    print()
    
    # Verificar dependencias
    print("📦 DEPENDENCIAS:")
    print("-"*70)
    
    try:
        import flask
        print(f"✅ Flask instalado               [v{flask.__version__}]")
    except ImportError:
        print("❌ Flask NO instalado            [pip install Flask]")
        all_ok = False
    
    try:
        import requests
        print(f"✅ Requests instalado            [v{requests.__version__}]")
    except ImportError:
        print("❌ Requests NO instalado         [pip install requests]")
        all_ok = False
    
    try:
        import ebooklib
        print("✅ ebooklib instalado")
    except ImportError:
        print("⚠️  ebooklib NO instalado        [pip install ebooklib]")
        print("   (Opcional - solo para archivos EPUB)")
    
    try:
        import bs4
        print(f"✅ BeautifulSoup4 instalado      [v{bs4.__version__}]")
    except ImportError:
        print("⚠️  BeautifulSoup4 NO instalado  [pip install beautifulsoup4]")
        print("   (Opcional - solo para archivos EPUB)")
    
    print()
    
    # Resumen
    print("="*70)
    if all_ok:
        print("✅ VERIFICACIÓN COMPLETADA - TODO OK")
        print()
        print("🚀 PRÓXIMOS PASOS:")
        print()
        print("   1. Probar localmente:")
        print("      ./start.sh                    (Mac)")
        print("      ./start_ubuntu.sh             (Ubuntu)")
        print()
        print("   2. Verificar conexión con el modelo:")
        print("      ./test_connection.py")
        print()
        print("   3. Abrir en navegador:")
        print("      http://localhost:5000")
        print()
        print("   4. Para desplegar en Ubuntu, lee:")
        print("      DEPLOYMENT_UBUNTU.md")
    else:
        print("⚠️  VERIFICACIÓN CON ADVERTENCIAS")
        print()
        print("Revisa los mensajes arriba y corrige los problemas marcados con ❌")
        print()
        print("Para instalar dependencias:")
        print("   pip install -r requirements.txt")
    
    print("="*70)
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
