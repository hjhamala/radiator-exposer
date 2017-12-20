all: myenv

myenv:
	virtualenv -p python3 myenv
	(. myenv/bin/activate && pip install -r requirements.txt)
