FROM python:3-onbuild
#RUN mkdir ~/python-ecobee-api
#ADD python-ecobee-api-0.0.19.tar.gz ~/python-ecobee-api
#WORKDIR ~/python-ecobee-api/python-ecobee-api-0.0.19
#RUN python setup.py install
COPY . /usr/src/app
WORKDIR /usr/src/app
#RUN echo "America/Montreal" > /etc/timezone
ENV TZ=America/Montreal
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
CMD ["python", "ecobeeapi.py"]
