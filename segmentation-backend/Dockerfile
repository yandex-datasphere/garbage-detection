# set base image (host OS)
FROM pytorch/pytorch:1.13.1-cuda11.6-cudnn8-runtime

# set the working directory in the container
WORKDIR /code

# copy the dependencies file to the working directory
COPY requirements.txt .

# install dependencies
RUN pip install -r requirements.txt

# copy the content of the local src directory to the working directory
COPY src/ .

EXPOSE 8000

# command to run on container start
CMD [ "python", "-u", "./server.py" ]