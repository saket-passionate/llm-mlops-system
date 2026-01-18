FROM pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime

ENV DEBIAN_FRONTEND=noninteractive

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY inference.py .

ENV TRANSFORMERS_CACHE=/opt/ml/model
ENV HF_HOME=/opt/ml/model

ENTRYPOINT ["python", "inference.py"]