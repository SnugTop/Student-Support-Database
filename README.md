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


---

### Database Setup
We are using sqllite. We will build and populate the database using the `create.sql` and `insert.sql` files.

**Steps to build:**

1. Build
```shell
sqlite3 student_support_center.db < create.sql
```
2. Populate
```shell
 sqlite3 student_support_center.db < insert.sql
```

3. Shell into database to run queries
```shell
sqlite3 student_support_center.db
```

4. Test queries
```shell 
sqlite> SELECT COUNT(*) FROM Student;
sqlite> SELECT COUNT(*) FROM Issue_Type;
sqlite> SELECT COUNT(*) FROM Visit_Counselor;
```

5. Delete Database
```shell
rm student_support_center.db
```
---
## Test Queries 
All the queries can be found in the `queries.sql` file. 
- 1 - 17 will directly respond to the requirements of the project. 
- 18 - 20 are for security purposes. 


Example of a failed SQL injection query:
![img.png](img.png)