FROM pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /opt/ml/code

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


ENV HF_HOME=/tmp/huggingface
ENV XDG_CACHE_HOME=/tmp/huggingface
ENV HF_METRICS_CACHE=/tmp/huggingface/metrics
ENV HF_MODULES_CACHE=/tmp/huggingface/modules
ENV HF_TOKENIZERS_CACHE=/tmp/huggingface/tokenizers
ENV HF_TRANSFORMERS_CACHE=/tmp/huggingface/transformers
ENV HF_HUB_CACHE=/tmp/huggingface/hub
ENV HF_DATASETS_CACHE=/tmp/huggingface/datasets


# SageMaker-required entrypoint
ENTRYPOINT ["python", "-m", "sagemaker-inference"]