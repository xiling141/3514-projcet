# /bin/bash
source .env
python ./config/import_csv.py
python app.py