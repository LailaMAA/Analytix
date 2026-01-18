@echo off
echo [1/3] Activation de l'environnement virtuel...
call venv\Scripts\activate

echo [2/3] Deplacement vers le dossier du projet...
cd project_manufacturing_good

echo [3/3] Lancement de l'API...
python api/main.py

pause
