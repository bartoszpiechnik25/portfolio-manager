from typing import Callable, Dict

import torch
import re
import numpy as np
import random
from datasets import DatasetDict, Dataset, load_dataset, concatenate_datasets
from peft import LoraConfig, PeftModel, get_peft_model
from transformers import (
    AutoTokenizer,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    T5ForConditionalGeneration,
)

MODEL_NAME = "google/flan-t5-large"
DATASET = "cnn_dailymail"
LORA_PATH = f"./models/lora_{MODEL_NAME.split('/')[-1]}_{DATASET.split('/')[-1]}"
TRAIN_DIR = "./models/checkpoints_local"
HEADS = [
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
PERCENTILE = 99.9
ANS_PERCENTILE = 97


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
    prompt_column: str = "prompt",
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
        dataset_record[prompt_column],
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
    dataset_record["labels"] = label_input_ids.masked_fill(
        label_input_ids == tokenizer.pad_token_id, -100
    )

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
    qa_prompt = "{}\nAnswer: "
    instruct_prompt = "Given the context.\n{}\n{}\nAnswer: "

    def process(x, tok=tokenizer):
        p = None
        if len(x["input"]) == 0:
            p = qa_prompt.format(x["instruction"])
        else:
            p = instruct_prompt.format(x["input"], x["instruction"])
        d = {"prompt": p}
        d["len"] = tok(d["prompt"], return_length=True)["length"][0]
        d["ans_len"] = tok(x["output"], return_length=True)["length"][0]
        return d

    dataset = load_dataset(name)["train"]
    dataset = dataset.map(lambda x: process(x), num_proc=12)
    max_prompt_len = int(np.percentile(dataset["len"], PERCENTILE))
    print(f"Max prompt length: {max_prompt_len}")
    max_ans_len = int(np.percentile(dataset["ans_len"], ANS_PERCENTILE))
    print(f"Max answer length: {max_ans_len}")

    dataset = dataset.filter(
        lambda x: x["len"] <= max_prompt_len and x["ans_len"] <= max_ans_len, num_proc=12
    )
    dataset = dataset.map(
        generate_prompt,
        fn_kwargs={
            "tokenizer": tokenizer,
            "max_prompt_len": max_prompt_len,
            "max_ans_len": max_ans_len,
        },
        num_proc=12,
    )
    dataset = dataset.remove_columns(
        ["input", "output", "instruction", "text", "len", "ans_len", "prompt"]
    )
    dataset.set_format(type="torch", columns=["input_ids", "labels"])
    dataset = dataset.train_test_split(test_size=0.1, shuffle=True, seed=2137)

    return dataset


def prepare_text2sql_dataset(
    dataset_name: str, tokenizer: Callable, preprocessed_dataset: Dataset = None
) -> DatasetDict:
    """
    Prepare the dataset for training and testing.

    Returns:
        DatasetDict: Preprocessed dataset.
    """
    dataset = (
        load_dataset(dataset_name)["train"]
        if preprocessed_dataset is None
        else preprocessed_dataset
    )
    prompt = "{}\n{}\nGenerate SQL query to answer the folowing question.\n{}\nAnswer: "

    def process(x, tok=tokenizer):
        prompt_beginning = random.choice(HEADS)
        d = {"prompt": prompt.format(prompt_beginning, x["context"], x["question"])}
        d["len"] = tok(d["prompt"], return_tensors="pt").input_ids.shape[1]
        d["ans_len"] = tok(x["answer"], return_tensors="pt").input_ids.shape[1]
        return d

    dataset = dataset.map(lambda x: process(x), num_proc=12)

    # select prompts lying in PERCENTILE of prompts lengths (better memory usage)
    # because having lets say one prompt that length is 400 will make every prompt
    # having length 400 due to padding so we will unecessarily process a lot of zeros.
    max_prompt_len = int(np.percentile(dataset["len"], PERCENTILE))
    print(f"Max prompt length: {max_prompt_len}")
    max_ans_len = int(np.percentile(dataset["ans_len"], PERCENTILE))
    print(f"Max answer length: {max_ans_len}")

    dataset = dataset.filter(
        lambda x: x["len"] <= max_prompt_len and x["ans_len"] <= max_ans_len, num_proc=12
    )
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
    dataset = dataset.train_test_split(test_size=0.1, shuffle=True, seed=2137)

    return dataset


def preprocess_llama2_text2sql_dataset(record: Dict[str, str]) -> Dict[str, str]:
    """
    Preprocess dataset to match the format of the different dataset for which I have methods.

    Args:
        record (Dict[str, str]): Record to preprocess.

    Returns:
        Dict[str, str]: Preprocessed record.
    """
    separated_input = list(
        map(
            lambda x: x.strip(),
            re.split(r"### Instruction:|### Input:|### Response:", record["input"]),
        )
    )
    return {
        "context": separated_input[2],
        "question": separated_input[1],
        "answer": record["output"],
    }


def prepare_cnn_dataset(name: str, version: str, tokenizer: Callable) -> DatasetDict:
    def preprocess_cnn_dataset(record: Dict[str, str]) -> Dict[str, str]:
        record["article"] = f"Summarize the following article:\n{record['article']}\nSummary:"
        record["article_len"] = tokenizer(record["article"], return_length=True, verbose=False)[
            "length"
        ][0]
        record["highlights_len"] = tokenizer(
            record["highlights"], return_length=True, verbose=False
        )["length"][0]
        return record

    dataset = load_dataset(name, version)
    dataset = concatenate_datasets([dataset["train"], dataset["validation"], dataset["test"]])
    dataset = dataset.map(preprocess_cnn_dataset, num_proc=12)

    dataset = dataset.filter(
        lambda x: x["article_len"] <= 512 and x["highlights_len"] <= 512,
        num_proc=12,
    )

    max_prompt_len = max(dataset["article_len"])
    max_ans_len = max(dataset["highlights_len"])
    print(f"Max prompt length: {max_prompt_len}")
    print(f"Max answer length: {max_ans_len}")

    dataset = dataset.map(
        generate_prompt,
        fn_kwargs={
            "tokenizer": tokenizer,
            "prompt_column": "article",
            "ans_column": "highlights",
            "max_prompt_len": max_prompt_len,
            "max_ans_len": max_ans_len,
        },
        num_proc=12,
        remove_columns=["article_len", "highlights_len", "id"],
    )
    dataset.set_format(type="torch", columns=["input_ids", "labels"])
    dataset = dataset.train_test_split(test_size=0.1, shuffle=True, seed=2137)
    return dataset


if __name__ == "__main__":
    import os
    import time

    print("Loading model and tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = T5ForConditionalGeneration.from_pretrained(MODEL_NAME, torch_dtype=torch.bfloat16)

    print("Creating LoRA model...")
    if os.path.isdir(LORA_PATH):
        print("Loading existing LoRA model...")
        model = PeftModel.from_pretrained(model, LORA_PATH, is_trainable=True)

    elif DATASET == "ChrisHayduk/Llama-2-SQL-Dataset":
        print("Loading existing LoRA model for fine-tunning on Llama 2 SQL dataset...")
        model = PeftModel.from_pretrained(
            model, "./models/lora_flan-t5-large_sql-create-context", is_trainable=True
        )
    else:
        print("Creating new LoRA model...")
        lora_config = LoraConfig(
            r=16,
            task_type="SEQ_2_SEQ_LM",
            lora_dropout=0.05,
            lora_alpha=32,
            target_modules=["q", "v", "o"],
            bias="all",
        )

        model = get_peft_model(model, lora_config)

    print("Loading dataset...")
    if DATASET == "b-mc2/sql-create-context":
        dataset = prepare_text2sql_dataset(DATASET, tokenizer)
    elif DATASET == "ChrisHayduk/Llama-2-SQL-Dataset":
        dataset = load_dataset(DATASET)
        dataset = concatenate_datasets([dataset["train"], dataset["eval"]])
        dataset = dataset.map(
            preprocess_llama2_text2sql_dataset, num_proc=12, remove_columns=["input", "output"]
        )
        dataset = prepare_text2sql_dataset(DATASET, tokenizer, dataset)
    elif DATASET == "cnn_dailymail":
        dataset = prepare_cnn_dataset(DATASET, "3.0.0", tokenizer)
    else:
        dataset = prepare_qa_dataset(DATASET, tokenizer)

    print(f"Training data shape: {dataset['train'].shape}")
    print(f"Test data shape: {dataset['test'].shape}")

    t = str(int(time.time()))
    out_dir = TRAIN_DIR + f"/lora-{MODEL_NAME.split('/')[-1]}-{t}"

    training_args = Seq2SeqTrainingArguments(
        learning_rate=3e-3,
        lr_scheduler_type="cosine",
        num_train_epochs=1,
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

    print("Saving model...")
    trainer.save_model(LORA_PATH)
    trainer.save_state()
