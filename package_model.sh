echo "Welcome to the StableLM-3B model downloader!"

# Clean Workspace
rm -rf ./models/
mkdir -p ./models/stablelm-3b/code

# Download StableLM-3B-4E1T model from Hugging Face
hf download stabilityai/stablelm-3b-4e1t \
  --local-dir ./models/stablelm-3b

echo "Creating model tar.gz for SageMaker..."

## Package the model into a tar.gz file for sageMaker deployment
cd models/stablelm-3b
tar -czvf ../stablelm-3b-model.tar.gz *

aws cp stablelm-3b-model.tar.gz s3://llm-rag-bucket-ca-central/models/stablelm-3b/
echo "Model downloaded and uploaded to S3 successfully!"





