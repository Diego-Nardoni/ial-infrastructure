#!/bin/bash
set -e

echo "🧪 Testando Deployment Completo do IAL"
echo "========================================"

# 1. Preparar Lambdas
echo ""
echo "📦 Step 1: Preparando Lambda artifacts..."
cd /home/ial/lambdas
for handler in ias_validation_handler cost_estimation_handler phase_builder_handler git_commit_pr_handler wait_pr_approval_handler deploy_cloudformation_handler proof_of_creation_handler post_deploy_analysis_handler drift_detection_handler; do
    if [ -f "${handler}.py" ]; then
        zip -q ${handler}.zip ${handler}.py
        echo "   ✅ ${handler}.zip"
    else
        echo "   ❌ ${handler}.py NOT FOUND"
    fi
done

# 2. Preparar Layer
echo ""
echo "📦 Step 2: Preparando Lambda Layer..."
cd /home/ial/lambda-layer
zip -qr ial-pipeline-layer.zip python/
echo "   ✅ ial-pipeline-layer.zip"

# 3. Verificar S3 bucket
echo ""
echo "☁️  Step 3: Verificando S3 bucket..."
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
BUCKET_NAME="ial-artifacts-${ACCOUNT_ID}"

if aws s3 ls "s3://${BUCKET_NAME}" 2>/dev/null; then
    echo "   ✅ Bucket exists: ${BUCKET_NAME}"
else
    echo "   📦 Creating bucket: ${BUCKET_NAME}"
    aws s3 mb "s3://${BUCKET_NAME}"
fi

# 4. Upload artifacts
echo ""
echo "☁️  Step 4: Uploading artifacts to S3..."
cd /home/ial/lambdas
for handler in ias_validation_handler cost_estimation_handler phase_builder_handler git_commit_pr_handler wait_pr_approval_handler deploy_cloudformation_handler proof_of_creation_handler post_deploy_analysis_handler drift_detection_handler; do
    aws s3 cp ${handler}.zip s3://${BUCKET_NAME}/lambdas/${handler}.zip --quiet
    echo "   ✅ Uploaded ${handler}.zip"
done

aws s3 cp /home/ial/lambda-layer/ial-pipeline-layer.zip s3://${BUCKET_NAME}/lambda-layer/ial-pipeline-layer.zip --quiet
echo "   ✅ Uploaded ial-pipeline-layer.zip"

# 5. Deploy CloudFormation
echo ""
echo "🚀 Step 5: Deploying CloudFormation stack..."
aws cloudformation deploy \
    --stack-name ial-nl-intent-pipeline \
    --template-file /home/ial/phases/00-foundation/17-nl-intent-pipeline.yaml \
    --capabilities CAPABILITY_NAMED_IAM \
    --no-fail-on-empty-changeset

echo ""
echo "✅ Deployment completo!"
echo ""
echo "🎯 Próximo: Testar pipeline"
echo "   IAL> quero um ECS privado com Redis"
