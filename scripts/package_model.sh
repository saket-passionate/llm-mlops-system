#!/bin/bash
set -e

# ----------- VARIABLES ----------
echo "🚀 Welcome to the StableLM-3B model downloader!"

echo "S3 Model Path is: $S3_MODEL_PATH"
cd $CODEBUILD_SRC_DIR

# Clean workspace
rm -rf models
mkdir -p models
cd models

echo "📍 Working directory: $(pwd)"

# ---------- CHECK S3 ----------
echo "🔍 Checking if model already exists in S3..."
if aws s3 ls "$S3_MODEL_PATH" > /dev/null 2>&1; then
    echo "✅ Model already exists in S3. Skipping download."
    exit 0
else
    echo "Model missing → download + upload"
fi

echo "❌ Model not found in S3. Proceeding with download."


# ---------- DOWNLOAD & PACKAGE MODEL ----------
echo "📥 Downloading StableLM-3B-4E1T from Hugging Face..."

hf download stabilityai/stablelm-3b-4e1t \
  --local-dir stablelm-3b

echo "📦 Packaging model..."

cd stablelm-3b
tar -czvf ../stablelm-3b-model.tar.gz .

echo "☁️ Uploading model to S3..."

aws s3 cp ../stablelm-3b-model.tar.gz \
  s3://${MODEL_BUCKET_NAME}/models/stablelm-3b/stable-3b-model.tar.gz

echo "✅ Model downloaded and uploaded successfully!"

