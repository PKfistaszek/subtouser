FROM python:3.6

RUN mkdir .virtualenvs 
ARG APP_VENV=venv
RUN pip install virtualenv 
RUN pip install virtualenvwrapper
ENV WORKON_HOME ~/.virtualenvs

ENV PYTHONUNBUFFERED 1
RUN /bin/bash -c "source /usr/local/bin/virtualenvwrapper.sh"

RUN mkdir /code
WORKDIR /code
ADD requirements.txt /code/
RUN pip install -r requirements.txt

ADD . /code/
