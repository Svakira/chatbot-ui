#!/bin/bash

# Script de inicio para Research Assistant - Context Chatbot

echo "========================================="
echo "Research Assistant - Context Chatbot"
echo "========================================="
echo ""

# Verificar si existe el entorno virtual
if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual..."
    python3 -m venv venv
fi

# Activar entorno virtual
echo "🔧 Activando entorno virtual..."
source venv/bin/activate

# Instalar dependencias
echo "📚 Instalando dependencias..."
pip install -q -r requirements.txt

# Crear directorio de uploads si no existe
if [ ! -d "uploads" ]; then
    mkdir uploads
fi

# Obtener IP local
IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "localhost")

echo ""
echo "✅ Todo listo!"
echo ""
echo "========================================="
echo "Accede a la aplicación en:"
echo "  Local:   http://localhost:5000"
echo "  Red:     http://$IP:5000"
echo "========================================="
echo ""
echo "Presiona Ctrl+C para detener el servidor"
echo ""

# Ejecutar aplicación
python app.py
