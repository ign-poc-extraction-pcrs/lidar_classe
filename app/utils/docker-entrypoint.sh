# python3 ./app/utils/drop_data.py

# python3 ./app/utils/migration.py

# python3 ./run_prod.py
gunicorn --bind 0.0.0.0:5000 run_prod:app