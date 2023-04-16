FROM python

COPY ./client.py /home/client.py
COPY ./server.py /home/server.py

RUN pip install requests

CMD python /home/server.py
