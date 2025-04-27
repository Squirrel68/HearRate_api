2. Install requirements in virtualenv
   2.1. Create virtual env
   Create virtual env ( Only first time )
   python -m venv venv

Activate virtual env (PowerShell)
.\venv\Scripts\Activate
Download requirements
pip install -r requirements.txt
pip freeze > requirements.txt

pip install -r requirements.txt
python app.py
