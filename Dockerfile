FROM python:3.8

# create destination directory
RUN mkdir -p /usr/src
WORKDIR /usr/src

# copy files
COPY . .

RUN python3 -m pip install --upgrade pip
RUN pip install --upgrade setuptools
RUN pip3 install -r requirements.txt
ENTRYPOINT ["/bin/bash", "./app/utils/docker-entrypoint.sh"]