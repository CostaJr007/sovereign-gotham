import torch
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer

print("[*] Testing model load and single forward step...")
model_id = "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"

tokenizer = AutoTokenizer.from_pretrained(model_id)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

print("[*] Loading base model...")
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    dtype=torch.float32,
    trust_remote_code=True,
)

peft_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],
    bias="none",
    task_type="CAUSAL_LM",
)
model = get_peft_model(model, peft_config)

inputs = tokenizer(["Sovereign Gotham Operational Directive test prompt."], return_tensors="pt")
inputs["labels"] = inputs["input_ids"].clone()

print("[*] Running forward pass...")
try:
    outputs = model(**inputs)
    print("[✓] Forward pass SUCCESS! Loss:", outputs.loss.item())
    outputs.loss.backward()
    print("[✓] Backward pass SUCCESS!")
except Exception as e:
    print("[!] Error:", e)
