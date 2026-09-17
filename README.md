pip install -r requirements.txt

parquet exploral

aprés chaque modification de table utilisateur il faut exécuter cette commande :

alembic revision --autogenerate -m "ajout google_id a utilisateur"(définir exactement l'ajout ou seulement autogenerate) et la commande de 
alembic upgrade head


uvicorn app.main:app --reload

netstat -an | findstr :8000

#démarrage de celery worker
celery -A app.celery_app worker --loglevel=info --pool=solo    

#démarrage de celery beat 
celery -A app.celery_app beat --loglevel=info