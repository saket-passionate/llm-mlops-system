#!/bin/bash
set -e

echo "🚀 Welcome to the StableLM-3B model downloader!"

cd $CODEBUILD_SRC_DIR

# Clean workspace
rm -rf models
mkdir -p models
cd models

echo "📥 Downloading StableLM-3B-4E1T from Hugging Face..."

hf download stabilityai/stablelm-3b-4e1t \
  --local-dir stablelm-3b

echo "📦 Packaging model..."

cd stablelm-3b
tar -czvf ../stablelm-3b-model.tar.gz .

echo "☁️ Uploading model to S3..."

aws s3 cp ../stablelm-3b-model.tar.gz \
  s3://${MODEL_BUCKET_NAME}/models/stablelm-3b/model.tar.gz

echo "✅ Model downloaded and uploaded successfully!"
