FROM python:3-onbuild
COPY requirements.txt /usr/src/app/requirements.txt
WORKDIR /usr/src/app
RUN pip3 install --trusted-host pypi.python.org -r requirements.txt
COPY . /usr/src/app
CMD ["python", "openweather_api.py"]
