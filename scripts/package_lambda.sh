echo "Packaging Lambda Deployment Script..."
# Clean previous package
cd ../lambda
zip -r ../lambda_package.zip .
echo "Lambda deployment package created successfully!"  


