from typing import Callable, Dict

import torch
from datasets import DatasetDict, load_dataset
from peft import LoraConfig, PeftModel, get_peft_model
from transformers import (
    AutoTokenizer,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    T5ForConditionalGeneration,
)

MODEL_NAME = "google/flan-t5-large"
LORA_PATH = f"./models/lora-{MODEL_NAME.split('/')[-1]}-finance-alpaca"
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

    prompt = f"Answer the following question.\n{dataset_record['instruction']}\n\nAnswer: "

    dataset_record["input_ids"] = tokenizer(
        prompt, return_tensors="pt", truncation=True, padding="max_length"
    ).input_ids.squeeze(0)
    label_input_ids = tokenizer(
        dataset_record["output"],
        return_tensors="pt",
        padding="max_length",
        truncation=True,
    ).input_ids.squeeze(0)
    # Set label padding token to -100 so that it is ignored in the loss function
    dataset_record["labels"] = label_input_ids.masked_fill(label_input_ids == 0, -100)

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
        lambda x: len(x["instruction"].split(" ")) < 512
        and len(x["output"].split(" ")) < 512
        and len(x["input"]) == 0,
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
    if os.path.isdir(LORA_PATH):
        model = PeftModel.from_pretrained(model, LORA_PATH, is_trainable=True)
    else:
        lora_config = LoraConfig(
            r=32,
            task_type="SEQ_2_SEQ_LM",
            lora_dropout=0.1,
            lora_alpha=32,
            target_modules=["q", "v"],
            bias="all",
        )

        model = get_peft_model(model, lora_config)

    print("Loading dataset...")
    dataset = prepare_dataset(DATASET, tokenizer)

    print(f"Training data shape: {dataset['train'].shape}")
    print(f"Test data shape: {dataset['test'].shape}")

    t = str(int(time.time()))
    out_dir = TRAIN_DIR + f"/lora-{MODEL_NAME.split('/')[-1]}-{t}"

    training_args = Seq2SeqTrainingArguments(
        learning_rate=1e-3,
        lr_scheduler_type="cosine",
        num_train_epochs=1,
        auto_find_batch_size=True,
        gradient_accumulation_steps=32,
        output_dir=out_dir,
        optim="adamw_torch",
        logging_steps=50,
        logging_strategy="steps",
        logging_first_step=True,
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        evaluation_strategy="epoch",
    )

    print(
        f"Memory footprint of {MODEL_NAME.split('/')[-1]} with LoRA layers: "
        + f"{model.get_memory_footprint()*1e-9:.2f} GB"
    )

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset["train"],
        eval_dataset=dataset["test"],
    )

    print_trainable_parameters(model)

    print("Training...")
    trainer.train()

    logs_dir = out_dir + "/logs"
    if not os.path.isdir(logs_dir):
        os.makedirs(logs_dir, exist_ok=True)

    with open(logs_dir + "/log_metrics.pkl", "wb") as f:
        pickle.dump(trainer.state.log_history, f)

    print("Saving model...")
    trainer.save_model(LORA_PATH)
    trainer.save_state()
