from typing import Callable, Dict

import torch
from datasets import DatasetDict, load_dataset
from peft import LoraConfig, get_peft_model
from transformers import AutoTokenizer, T5ForConditionalGeneration, Trainer, TrainingArguments

MODEL_NAME = "google/flan-t5-large"
LORA_PATH = "./models/lora"
TRAIN_DIR = "./models/checkpoints-local"
DATASET = "gbharti/finance-alpaca"


def print_trainable_parameters(model: torch.nn.Module) -> None:
    """
    Print the number of trainable parameters in a model

    Args:
        model (torch.nn.Module): PyTorch model

    Returns:
        None
    """

    all_params = 0
    trainable_params = 0

    for _, parameter in model.named_parameters():
        all_params += parameter.numel()
        if parameter.requires_grad:
            trainable_params += parameter.numel()
    print(
        f"Trainable parameters {trainable_params:,} || All parameters {all_params:,} "
        + f"|| Trainable parameter percentage: {trainable_params/all_params*100:.2f}%"
    )


def generate_prompt(dataset_record: Dict[str, str], tokenizer: Callable) -> Dict[str, torch.Tensor]:
    """
    Generate the prompt for the model and tokenizes it.

    Args:
        dataset_record (Dict[str, str]): Record from the dataset to generate the prompt.
        tokenizer (AutoTokenizer): Tokenizer callable to tokenize the prompt.

    Returns:
        Dict[str, torch.Tensor]: Dictionary with the input_ids and labels for the model.
    """

    if len(dataset_record["input"]):
        prompt = f"{dataset_record['instruction']}\n\n{dataset_record['input']}\n\nAnswer: "
    else:
        prompt = f"{dataset_record['instruction']}\n\nAnswer: "

    dataset_record["input_ids"] = tokenizer(
        prompt, return_tensors="pt", truncation=True, padding="max_length"
    ).input_ids.squeeze(0)
    dataset_record["labels"] = tokenizer(
        dataset_record["output"],
        return_tensors="pt",
        padding="max_length",
        truncation=True,
    ).input_ids.squeeze(0)

    return dataset_record


def prepare_dataset(name: str, tokenizer: Callable) -> DatasetDict:
    """
    Preprocess the dataset for training and testing.

    Args:
        name (str): Name of the dataset to load.
        tokenizer (Callable): Tokenizer callable to tokenize the prompt.

    Returns:
        DatasetDict: Preprocessed dataset.
    """
    dataset = load_dataset(name)["train"]
    dataset = dataset.filter(
        lambda x: len(x["input"]) + len(x["instruction"]) < 512 and len(x["output"]) < 512,
        num_proc=6,
    )

    dataset = dataset.map(generate_prompt, fn_kwargs={"tokenizer": tokenizer}, num_proc=6)
    dataset = dataset.remove_columns(["input", "output", "instruction", "text"])
    dataset = dataset.train_test_split(test_size=0.1, shuffle=True, seed=2137)

    print(f"Training data shape: {dataset['train'].shape}")
    print(f"Test data shape: {dataset['test'].shape}")

    return dataset


if __name__ == "__main__":
    import os
    import pickle
    import time

    print("Loading model and tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = T5ForConditionalGeneration.from_pretrained(MODEL_NAME, torch_dtype=torch.bfloat16)

    print("Creating LoRA model...")
    lora_config = LoraConfig(
        r=32,
        task_type="SEQ_2_SEQ_LM",
        lora_dropout=0.05,
        lora_alpha=32,
        target_modules=["q", "v"],
        bias="lora_only",
    )

    lora_model = get_peft_model(model, lora_config)

    print("Loading dataset...")
    dataset = prepare_dataset(DATASET, tokenizer)

    print(f"Training data shape: {dataset['train'].shape}")
    print(f"Test data shape: {dataset['test'].shape}")

    t = str(int(time.time()))
    out_dir = TRAIN_DIR + f"/lora-flan-t5-large-{t}"

    training_args = TrainingArguments(
        learning_rate=1e-4,
        num_train_epochs=1,
        auto_find_batch_size=True,
        weight_decay=0.01,
        output_dir=out_dir,
        gradient_accumulation_steps=8,
        optim="adamw_torch",
        logging_steps=30,
        logging_strategy="steps",
        logging_first_step=True,
        save_strategy="steps",
        save_steps=500,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        evaluation_strategy="steps",
        eval_steps=500,
    )

    print("Memory footprint of FLAN-T5-large with LoRA layers: " + f"{lora_model.get_memory_footprint()*1e-9:.2f} GB")

    trainer = Trainer(
        model=lora_model,
        args=training_args,
        train_dataset=dataset["train"],
        eval_dataset=dataset["test"],
    )

    print_trainable_parameters(lora_model)

    print("Training...")
    trainer.train()

    logs_dir = out_dir + "/logs"
    if not os.path.isdir(logs_dir):
        os.makedirs(logs_dir)

    with open(logs_dir + "/log_metrics.pkl", "wb") as f:
        pickle.dump(trainer.state.log_history, f)

    print("Saving model...")
    trainer.save_model(LORA_PATH)
