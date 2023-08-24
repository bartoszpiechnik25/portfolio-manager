from typing import Callable, Dict

import torch
import random
from datasets import DatasetDict, load_dataset
from peft import LoraConfig, PeftModel, get_peft_model
from transformers import (
    AutoTokenizer,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    T5ForConditionalGeneration,
)

MODEL_NAME = "google/flan-t5-large"
DATASET = "b-mc2/sql-create-context"
LORA_PATH = f"./models/lora_{MODEL_NAME.split('/')[-1]}_{DATASET.split('/')[-1]}"
TRAIN_DIR = "./models/checkpoints_local"


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


def generate_prompt(
    dataset_record: Dict[str, str],
    tokenizer: Callable,
    prompt_cloumn: str = "prompt",
    ans_column: str = "output",
    max_prompt_len: int = 512,
    max_ans_len: int = 512,
) -> Dict[str, torch.Tensor]:
    """
    Generate the prompt for the model.

    Returns:
        Dict[str, torch.Tensor]: Record with the prompt and the answer tokenized.
    """

    dataset_record["input_ids"] = tokenizer(
        dataset_record[prompt_cloumn],
        return_tensors="pt",
        truncation=True,
        padding="max_length",
        max_length=max_prompt_len,
    ).input_ids.squeeze(0)

    label_input_ids = tokenizer(
        dataset_record[ans_column],
        return_tensors="pt",
        padding="max_length",
        max_length=max_ans_len,
        truncation=True,
    ).input_ids.squeeze(0)

    # Set label padding token to -100 so that it is ignored in the loss function
    dataset_record["labels"] = label_input_ids.masked_fill(label_input_ids == 0, -100)

    return dataset_record


def prepare_qa_dataset(name: str, tokenizer: Callable) -> DatasetDict:
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


def prepare_sql2text_dataset(dataset_name: str, tokenizer: Callable) -> DatasetDict:
    """
    Prepare the dataset for training and testing.

    Returns:
        DatasetDict: Preprocessed dataset.
    """
    dataset = load_dataset(dataset_name)["train"]
    prompt = "{}\n{}\nGenerate SQL query to answer the folowing question.\n{}\nAnswer: "
    start = [
        "Given the context.",
        "Given the following table.",
        "Given SQL code to create a table.",
        "Given the following SQL code.",
        "Consider the SQL code below:",
        "Review the following SQL snippet:",
        "Examine the table creation query provided:",
        "Take a look at the SQL code segment:",
        "Here's an SQL snippet defining a table:",
        "Below is an SQL statement for creating a table:",
        "Provided is an SQL code snippet that creates a table:",
        "Explore the given SQL code for table creation:",
        "Given the subsequent SQL code for table setup:",
        "The following SQL code demonstrates table creation:",
    ]

    def process(x):
        prompt_beginning = random.choice(start)
        d = {"prompt": prompt.format(prompt_beginning, x["context"], x["question"])}
        d["len"] = len(d["prompt"].split(" "))
        d["ans_len"] = len(x["answer"].split(" "))
        return d

    dataset = dataset.map(lambda x: process(x), num_proc=12)
    # add 15 to max len to account for ., ?, !, etc.
    max_prompt_len, max_ans_len = max(dataset["len"]) + 20, max(dataset["ans_len"]) + 20
    dataset = dataset.map(
        generate_prompt,
        fn_kwargs={
            "tokenizer": tokenizer,
            "max_prompt_len": max_prompt_len,
            "max_ans_len": max_ans_len,
            "ans_column": "answer",
        },
        num_proc=12,
    )
    dataset = dataset.remove_columns(["len", "ans_len", "context", "question", "answer", "prompt"])
    dataset.set_format(type="torch", columns=["input_ids", "labels"])
    dataset = dataset.train_test_split(test_size=0.2, shuffle=True, seed=2137)

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
        print("Loading existing LoRA model...")
        model = PeftModel.from_pretrained(model, LORA_PATH, is_trainable=True)
    else:
        print("Creating new LoRA model...")
        lora_config = LoraConfig(
            r=16,
            task_type="SEQ_2_SEQ_LM",
            lora_dropout=0.1,
            lora_alpha=32,
            target_modules=["q", "v", "o"],
            bias="all",
        )

        model = get_peft_model(model, lora_config)

    print("Loading dataset...")
    if DATASET == "b-mc2/sql-create-context":
        dataset = prepare_sql2text_dataset(DATASET, tokenizer)
    else:
        dataset = prepare_qa_dataset(DATASET, tokenizer)

    print(f"Training data shape: {dataset['train'].shape}")
    print(f"Test data shape: {dataset['test'].shape}")

    t = str(int(time.time()))
    out_dir = TRAIN_DIR + f"/lora-{MODEL_NAME.split('/')[-1]}-{t}"

    training_args = Seq2SeqTrainingArguments(
        learning_rate=1e-3,
        lr_scheduler_type="cosine",
        num_train_epochs=3,
        auto_find_batch_size=True,
        gradient_accumulation_steps=8,
        output_dir=out_dir,
        optim="adamw_torch",
        logging_steps=40,
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
