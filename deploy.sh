#!/bin/bash

# ----------------------
# Custom Deployment Script for Azure App Service
# ----------------------

echo "=== Starting Custom Deployment ==="

# 1. Build the Frontend
echo "--> Moving to frontend directory..."
cd frontend || { echo "Frontend directory not found!"; }

echo "--> Checking npm..."
if ! command -v npm &> /dev/null
then
    echo "npm could not be found. Please ensure Node.js is installed."
else
    echo "--> Running npm install..."
    npm install

    echo "--> Running npm run build..."
    npm run build
fi

cd ..

# 2. Build the Backend
echo "--> Handling backend deployment..."
if [ -z "$DEPLOYMENT_TARGET" ]; then
    DEPLOYMENT_TARGET="/home/site/wwwroot"
fi

if [ "$IN_ORYX_BUILD" != "true" ]; then
    echo "--> Running Oryx build..."
    oryx build . -i /tmp/build -o "$DEPLOYMENT_TARGET" --platform python --platform-version 3.11
else
    echo "--> Already in Oryx build."
fi

echo "=== Deployment completed successfully! ==="
