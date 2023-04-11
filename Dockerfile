FROM python

COPY ./client.py /home/client.py
COPY ./server.py /home/server.py

CMD python /home/server.py
