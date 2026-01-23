import gradio as gr
import os
import sys
import json
import boto3

sys.path.append(os.path.abspath(".."))


# ===============================
# Configuration
# ===============================

ENDPOINT_NAME = os.environ.get("SM_ENDPOINT_NAME", "stablelm-3b-endpoint")
REGION= os.environ.get("AWS_REGION", "ca-central-1")
BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "llm-rag-bucket-ca-central")


# Create SageMaker runtime client
runtime = boto3.client(
    "sagemaker-runtime",
    region_name=REGION
)

# ===============================
# Inference function
# ===============================
def generate_text(prompt):
    payload = {
        "inputs": prompt
    }

    response = runtime.invoke_endpoint(
        EndpointName=ENDPOINT_NAME,
        ContentType="application/json",
        Body=json.dumps(payload)
    )
    result = json.loads(response["Body"].read().decode("utf-8"))
    return result["generated_text"]

# ===============================
# Gradio UI
# ===============================
with gr.Blocks(
    theme=gr.themes.Ocean(),
    title="StableLM-3B | AWS SageMaker"
) as demo:

    gr.Markdown(
        """
        # 🚀 StableLM-3B on AWS SageMaker  
        **Custom Hugging Face LLM deployed using Bring-Your-Own-Container (BYOC)**  
        """
    )

    with gr.Row(equal_height=True):

        # ===== Left: Input =====
        with gr.Column(scale=1):
            gr.Markdown("### ✍️ Input Prompt")
            prompt = gr.Textbox(
                placeholder="Explain transformers in simple terms...",
                lines=10
            )

            submit = gr.Button("Generate 🚀", variant="primary")

        # ===== Right: Output =====
        with gr.Column(scale=1):
            gr.Markdown("### 🤖 Model Output")
            output = gr.Textbox(
                lines=10,
                label="Generated Text",
            )

    submit.click(
        fn=generate_text,
        inputs=prompt,
        outputs=output
    )

    gr.Markdown(
        """
        ---
        **Inference powered by Amazon SageMaker real-time endpoints**  
        """
    )

# ===============================
# Launch
# ===============================
if __name__ == "__main__":
    demo.launch()