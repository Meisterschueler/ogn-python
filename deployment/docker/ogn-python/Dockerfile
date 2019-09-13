FROM tiangolo/meinheld-gunicorn-flask:python3.7
RUN rm /app/main.py
WORKDIR /app
ADD app app
ADD migrations migrations
COPY *.py /app/
COPY requirements.txt .
COPY README.md .
COPY setup.cfg .
RUN pip install -r requirements.txt
COPY deployment/docker/ogn-python/prestart.sh .
COPY deployment/docker/ogn-python/wait.sh .
