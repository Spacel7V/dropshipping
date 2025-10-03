# Dropshipping default model

#### Packages
```
asgiref==3.9.2
certifi==2025.8.3
charset-normalizer==3.4.3
Django==5.2.4
django-allauth==65.9.0
django-browser-reload==1.18.0
django-cleanup==9.0.0
django-environ==0.12.0
django-htmx==1.23.2
idna==3.10
pillow==11.3.0
requests==2.32.5
sqlparse==0.5.3
stripe==12.5.1
typing_extensions==4.15.0
urllib3==2.5.0

```

<br><br>

## Setup

#### - Create Virtual Environment
###### # Mac
```
python3 -m venv venv
source venv/bin/activate
```

###### # Windows
```
python3 -m venv venv
(Powershell:) .\venv\Scripts\Activate.ps1
```
```
(or Command Prompt:) venv\Scripts\activate 
(or Git Bash:) source venv/Scripts/activate
```

<br>

#### - Install dependencies
```
pip install --upgrade pip
pip install -r requirements.txt
```

<br>

#### - Migrate to database
```
python manage.py migrate
python manage.py createsuperuser
```

<br>

#### - Run application
```
python manage.py runserver
```

<br>

#### - Generate Secret Key ( ! Important for deployment ! )
```
python manage.py shell
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
exit()
```


### - for stripe webhook : 
```
checkout > checkout.session.completed
```