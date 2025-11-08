# Student Support Database

## Overview 



## Set up

Steps to set up an environment 
1. Set up/Activate virtual environment
2. Install requirements


### Set up/Activate


**Set Up Environment (macOS)**
```shell
python3 -m venv db-project
source db-project/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
flask run
```

**Set Up Virtual Environment (Windows: PowerShell)**

```shell
py -3 -m venv db-project
.\db-project\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
flask run
```

### Install Requirements

Now that your Environment is up and running, you can install all of your requirements. They live 
in the `requirements.txt` file. Install all of them by running:
```shell
pip install -r requirements.txt
```


### Test Flask App
URL to test Flask App: http://127.0.0.1:5000/ will display. 


