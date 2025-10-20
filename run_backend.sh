#!/bin/bash

echo "🚀 Iniciando backend sin Vaadin..."

cd /Users/arielsanroj/Mommyshops/mommyshops/mommyshops-app

# Configurar variables de entorno
export VAADIN_PRODUCTION_MODE=true
export SPRING_PROFILES_ACTIVE=backend-only

# Ejecutar solo las clases compiladas
java -cp "target/classes:$(mvn dependency:build-classpath -q -Dmdep.outputFile=/dev/stdout)" \
     -Dvaadin.productionMode=true \
     -Dspring.profiles.active=backend-only \
     com.mommyshops.MommyshopsApplication