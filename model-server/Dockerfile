FROM pytorch/pytorch:1.13.1-cuda11.6-cudnn8-runtime
WORKDIR /code
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY code/ . 
EXPOSE 8000
CMD ["python" "-u" "./server.py"]
