#!/bin/bash

# Script de inicio para Ubuntu Server
# Research Assistant - Context Chatbot

echo "========================================="
echo "Research Assistant - Context Chatbot"
echo "========================================="
echo ""

# Colores para el output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar si existe el entorno virtual
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creando entorno virtual...${NC}"
    python3 -m venv venv
fi

# Activar entorno virtual
echo -e "${BLUE}🔧 Activando entorno virtual...${NC}"
source venv/bin/activate

# Instalar dependencias
echo -e "${BLUE}📚 Instalando dependencias...${NC}"
pip install -q -r requirements.txt

# Crear directorio de uploads si no existe
if [ ! -d "uploads" ]; then
    echo -e "${BLUE}📁 Creando directorio uploads...${NC}"
    mkdir uploads
fi

# Obtener IPs
PRIVATE_IP=$(hostname -I | awk '{print $1}')
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || echo "N/A")

echo ""
echo -e "${GREEN}✅ Todo listo!${NC}"
echo ""
echo "========================================="
echo "Accede a la aplicación en:"
echo ""
echo -e "  ${BLUE}Red local:${NC}    http://$PRIVATE_IP:5000"
echo -e "  ${BLUE}Localhost:${NC}    http://localhost:5000"

if [ "$PUBLIC_IP" != "N/A" ]; then
    echo -e "  ${BLUE}Público:${NC}      http://$PUBLIC_IP:5000"
    echo ""
    echo -e "${YELLOW}⚠️  Asegúrate de configurar el firewall:${NC}"
    echo "   sudo ufw allow 5000/tcp"
fi

echo "========================================="
echo ""
echo -e "${YELLOW}📝 Nota:${NC} Presiona Ctrl+C para detener el servidor"
echo ""

# Ejecutar aplicación
python app.py
