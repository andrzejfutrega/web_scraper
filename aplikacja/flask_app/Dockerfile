FROM python:3.9-slim

WORKDIR /flask_app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "flask_app.py"]
