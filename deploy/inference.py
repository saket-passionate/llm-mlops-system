import os
import json
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# Tranformer Config
os.environ['TRANSFORMERS_CACHE'] = '/tmp/huggingface/transformers'
os.environ['HF_HOME'] = '/tmp/huggingface'


MODEL_DIR = "/opt/ml/model"

device = "cuda" if torch.cuda.is_available() else "cpu"

def model_fn(model_dir):
    """
    Load the model for inference.
    """
    print("Loading model from {}".format(model_dir))
    tokenizer = AutoTokenizer.from_pretrained(
        model_dir,
        use_fast=True,
        local_files_only=True,
        )
    
    model = AutoModelForCausalLM.from_pretrained(
        model_dir,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        low_cpu_mem_usage=True,
        device_map="auto" if device == "cuda" else None,
        local_files_only=True,
        trust_remote_code=True,
        )
    
    model.eval()
    return (tokenizer, model)

def input_fn(request_body, request_content_type):
    """
    Deserialize the request body.
    """
    if request_content_type == "application/json":
        request = json.loads(request_body)
        return request["inputs"]
    else:
        raise ValueError("Unsupported content type: {}".format(request_content_type))

def predict_fn(input_data, model):
    """
    Perform inference on the input data.
    """
    
    tokenizer, model = model
    inputs = tokenizer(input_data, return_tensors="pt").to(
        device
    )
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=256,
            do_sample=True,
            top_p=0.9,
            temperature=0.6,
            repetition_penalty=1.2,
        )
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return generated_text


def output_fn(prediction, response_content_type):
    """
    Serialize the prediction output.
    """
    if response_content_type == "application/json":
        return json.dumps({"generated_text": prediction})
    else:
        raise ValueError("Unsupported content type: {}".format(response_content_type))