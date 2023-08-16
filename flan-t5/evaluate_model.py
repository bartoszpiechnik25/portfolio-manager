import torch
from evaluate import load
from peft import PeftModel
from train_flan_t5 import DATASET, MODEL_NAME, prepare_dataset
from transformers import AutoTokenizer, GenerationConfig, T5ForConditionalGeneration

PEFT_MODEL = "./models/checkpoints-local/lora"

if __name__ == "__main__":
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    baseline_model = T5ForConditionalGeneration.from_pretrained(MODEL_NAME)
    dataset = prepare_dataset(DATASET, tokenizer)
    fine_tuned_model = PeftModel.from_pretrained(baseline_model, PEFT_MODEL)

    rouge = load("rouge")

    human, base, fine_tuned = [], [], []
    config = GenerationConfig(max_length=512)

    with torch.no_grad():
        for idx, data in enumerate(dataset["test"]):
            human.append(tokenizer.decode(data["labels"], skip_special_tokens=True))

            baseline_model_output = baseline_model.generate(input_ids=data["input_ids"], generation_config=config)
            base.append(tokenizer.decode(baseline_model_output[0], skip_special_tokens=True))

            fine_tuned_model_output = fine_tuned_model.generate(input_ids=data["input_ids"], generation_config=config)
            fine_tuned.append(tokenizer.decode(fine_tuned_model_output[0], skip_special_tokens=True))

        baseline_result = rouge.compute(predictions=base, references=human, use_stemmer=True, use_agregator=True)
        lora_result = rouge.compute(predictions=fine_tuned, references=human, use_stemmer=True, use_agregator=True)

    print(f"Baseline model: {baseline_result}")
    print(f"Fine-tuned model: {lora_result}")
