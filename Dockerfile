FROM python:3
WORKDIR usrsrcapp

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 3000
CMD ["python3", "./main.py"]