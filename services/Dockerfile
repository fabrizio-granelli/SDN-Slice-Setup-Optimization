FROM python

COPY ./client.py /home/client.py
COPY ./server.py /home/server.py

RUN pip install requests

RUN apt-get update -y && apt-get install -y iputils-ping

CMD python /home/server.py
