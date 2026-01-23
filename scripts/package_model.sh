echo "Welcome to the StableLM-3B model downloader!"

# Clean Workspace
rm -rf ../models/
cd models


# Download StableLM-3B-4E1T model from Hugging Face
hf download stabilityai/stablelm-3b-4e1t \
  --local-dir ./models/stablelm-3b

## Package the model into a tar.gz file for sageMaker deployment
cd models/stablelm-3b
tar -czvf ../stablelm-3b-model.tar.gz *

aws s3 cp ../models/stablelm-3b-model.tar.gz s3://$MODEL_BUCKET_NAME/models/stablelm-3b/

echo "Model downloaded and uploaded to S3 successfully!"





