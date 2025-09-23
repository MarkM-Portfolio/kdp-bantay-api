#!/bin/bash
FROM python:3.9.1

WORKDIR /app

COPY requirements.txt requirements.txt
ENV PERSONAL_ACCESS_TOKEN=${token}
RUN pip3 install -r requirements.txt \
    & pip install --upgrade 'sentry-sdk[flask]' \
    & pip install -r requirements.txt

COPY . .

COPY docker/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

#EXPOSE 5000
EXPOSE 80

#CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]
ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]
