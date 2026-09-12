from datasets import Dataset
from transformers import AutoModelForCausalLM, Trainer, TrainingArguments

print("[*] Testing PyTorch c10.dll stability test...")

# Small dummy dataset
data = [
    {"input_ids": [1, 2, 3, 4, 5], "labels": [1, 2, 3, 4, 5]},
    {"input_ids": [1, 2, 3, 4, 5, 6, 7], "labels": [1, 2, 3, 4, 5, 6, 7]},
]
ds = Dataset.from_list(data)

# Tiny model to test Trainer without pin_memory
from transformers import AutoConfig

config = AutoConfig.from_pretrained("deepseek-ai/DeepSeek-R1-Distill-Qwen-7B")
config.num_hidden_layers = 1  # 1 layer dummy for instant test
model = AutoModelForCausalLM.from_config(config)

training_args = TrainingArguments(
    output_dir="./tmp_test",
    max_steps=2,
    per_device_train_batch_size=1,
    dataloader_pin_memory=False,  # CRITICAL: Fixes c10.dll crash on Windows!
    dataloader_num_workers=0,     # CRITICAL: Avoids Windows multiprocessing crash
    report_to="none",
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=ds,
)

print("[*] Running 2 test steps...")
trainer.train()
print("[✓] c10.dll stability test PASSED 100%!")
