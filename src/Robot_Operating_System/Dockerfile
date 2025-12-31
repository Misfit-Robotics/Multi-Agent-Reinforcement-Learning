FROM python:3.13-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN apt-get update && apt-get install -y gcc libc6-dev

RUN pip install -r requirements.txt

COPY . .

EXPOSE 5005

CMD ["python", "limb.py"]
