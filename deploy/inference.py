import os
import json
import torch
import uvicorn
from fastapi import FastAPI, Request, Response
from transformers import AutoModelForCausalLM, AutoTokenizer

# Transformer Config
os.environ['TRANSFORMERS_CACHE'] = '/tmp/huggingface/transformers'
os.environ['HF_HOME'] = '/tmp/huggingface'

app = FastAPI()
MODEL_OBJECT = None
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


# --- BitsAndBytes Configuration ---
# Define 4-bit quantization configuration

# bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_type=torch.float16
)   

# --- Your Existing Logic Integrated ---

def model_fn(model_dir):
    print(f"Loading model from {model_dir}")
    tokenizer = AutoTokenizer.from_pretrained(model_dir, use_fast=True, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_dir,
        torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32,
        #quantization_config=bnb_config,
        low_cpu_mem_usage=True,
        device_map="auto" if DEVICE == "cuda" else None,
        local_files_only=True,
        trust_remote_code=True,
    )
    model.eval()
    return (tokenizer, model)

def predict_fn(input_data, model_tuple):
    tokenizer, model = model_tuple
    inputs = tokenizer(input_data, return_tensors="pt").to(DEVICE)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=256,
            do_sample=True,
            top_p=0.9,
            temperature=0.6,
            repetition_penalty=1.2,
        )
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

# --- SageMaker Lifecycle Endpoints ---

@app.on_event("startup")
def startup_event():
    """Load model once on container startup."""
    global MODEL_OBJECT
    model_dir = os.environ.get("SM_MODEL_DIR", "/opt/ml/model")
    MODEL_OBJECT = model_fn(model_dir)

@app.get("/ping")
def ping():
    """Health check endpoint."""
    health = MODEL_OBJECT is not None
    return Response(content="\n", status_code=200 if health else 503)

@app.post("/invocations")
async def invocations(request: Request):
    """Inference endpoint."""
    # 1. Validate Content-Type
    if request.headers.get("Content-Type") != "application/json":
        return Response(content="Support only application/json", status_code=415)

    # 2. Get Input (input_fn logic)
    body = await request.json()
    prompt = body.get("inputs")
    
    # 3. Predict (predict_fn logic)
    prediction = predict_fn(prompt, MODEL_OBJECT)
    
    # 4. Return Output (output_fn logic)
    return Response(
        content=json.dumps({"generated_text": prediction}),
        media_type="application/json"
    )

if __name__ == "__main__":
    # SageMaker expects the container to listen on port 8080
    uvicorn.run(app, host="0.0.0.0", port=8080)
