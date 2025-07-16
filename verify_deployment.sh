#!/bin/bash

# Script de Verificação do Deploy
echo "Verificando deployment do Contestare Doc Express..."

# Verificar frontend
echo "Testando frontend..."
curl -I https://contestaredocexpress.com
curl -I https://app.contestaredocexpress.com

# Verificar backend
echo "Testando backend..."
curl -I https://api.contestaredocexpress.com/api/health

# Verificar endpoints principais
echo "Testando endpoints..."
curl https://api.contestaredocexpress.com/api/contracts
curl https://api.contestaredocexpress.com/api/health

echo "Verificação concluída!"
