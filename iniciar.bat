@echo off
title VISTOP
echo Iniciando VISTOP...
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" "http://localhost:3000/app.html"
npx serve . --listen 3000