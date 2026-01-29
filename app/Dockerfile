FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y git-lfs && git lfs install

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 7860

# Launch the app
CMD ["python", "app.py"]