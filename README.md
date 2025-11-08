# Student Support Database


## Set up

Steps to set up enivroment 
1. Set up virtural enviroment
2. Activate enviroment 
3. Install requirements



**Set Up Enviroment (macOS)**
```shell
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
flask run
```

**Set Up Virtual Enviroment (Windows: Power Shell)**

```shell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
flask run
```
