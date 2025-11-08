# Student Support Database


## Set up

Steps to set up enivroment 
1. Set up/Activate virtural enviroment
2. Install requirements


### Set up/Activate


**Set Up Enviroment (macOS)**
```shell
python3 -m venv db-project
source db-project/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
flask run
```

**Set Up Virtual Enviroment (Windows: Power Shell)**

```shell
py -3 -m venv db-project
.\db-project\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
flask run
```

### Install Requirements

Now that your enviroment is up and running you can install all of your requirements. They live 
in the `requirements.txt` file. Install all of them by running:
```shell
pip install -r requirements.txt
```



