FROM python:3

WORKDIR /usr/src/app

COPY . ./

ENV TZ=America/Montreal
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "./rtlamr-mqttexporter.py"]
