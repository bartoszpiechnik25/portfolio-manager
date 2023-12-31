from typing import List, Tuple, Union

import torch
import tqdm
from datasets import DatasetDict, load_dataset, concatenate_datasets
from evaluate import load
from peft import PeftModel
from train_flan_t5 import (
    DATASET,
    LORA_PATH,
    MODEL_NAME,
    prepare_text2sql_dataset,
    print_trainable_parameters,
    preprocess_llama2_text2sql_dataset,
    prepare_qa_dataset,
    prepare_cnn_dataset,
)
from transformers import AutoTokenizer, GenerationConfig, T5ForConditionalGeneration


def evaluate_test(
    model: Union[T5ForConditionalGeneration, PeftModel],
    tokenizer: AutoTokenizer,
    config: GenerationConfig,
    dataset: DatasetDict,
    batch_size: int = 64,
) -> Tuple[List[str], List[str]]:
    """
    Evaluate the model on the test dataset.

    Args:
        model (Union[T5ForConditionalGeneration, PeftModel]): Model to evaluate.
        tokenizer (AutoTokenizer): Tokenizer to decode the generated tokens.
        config (GenerationConfig): Configuration for the generation.
        dataset (DatasetDict): Dataset to evaluate the model on.
        batch_size (int, optional): Batch size. Defaults to 64.

    Returns:
        Tuple[List[str], List[str]]: Tuple with the generated and human answers.
    """
    model.eval()
    model_results, human_generated = [], []

    with torch.no_grad():
        for i in tqdm.tqdm(range(0, len(dataset) // batch_size), desc="Evaluating"):
            data = dataset[i * batch_size : (i + 1) * batch_size]
            # fill -100 (token used for training) with pad token
            data["labels"].masked_fill_(data["labels"] == -100, tokenizer.pad_token_id)
            human_generated.extend(tokenizer.batch_decode(data["labels"], skip_special_tokens=True))

            generated_ids = model.generate(
                input_ids=data["input_ids"].to("cuda"), generation_config=config
            )
            model_results.extend(tokenizer.batch_decode(generated_ids, skip_special_tokens=True))
            del data, generated_ids

    return model_results, human_generated


if __name__ == "__main__":
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    model = T5ForConditionalGeneration.from_pretrained(
        MODEL_NAME, torch_dtype=torch.bfloat16, device_map="cuda:0"
    )
    if DATASET == "ChrisHayduk/Llama-2-SQL-Dataset":
        dataset = load_dataset(DATASET)
        dataset = concatenate_datasets([dataset["train"], dataset["eval"]])
        dataset = dataset.map(
            preprocess_llama2_text2sql_dataset, num_proc=12, remove_columns=["input", "output"]
        )
        dataset = prepare_text2sql_dataset(DATASET, tokenizer, dataset)
    elif DATASET == "b-mc2/sql-create-context":
        dataset = prepare_text2sql_dataset(DATASET, tokenizer)
    elif DATASET == "cnn_dailymail":
        dataset = prepare_cnn_dataset(DATASET, "3.0.0", tokenizer)
    else:
        dataset = prepare_qa_dataset(DATASET, tokenizer)

    model = PeftModel.from_pretrained(model, LORA_PATH)

    print_trainable_parameters(model)

    rouge = load("rouge")
    print(f"Evaluating {DATASET}")

    config = GenerationConfig(max_new_tokens=512, temperature=1, repetition_penalty=1)

    generated, human = evaluate_test(model, tokenizer, config, dataset["test"], batch_size=32)
    lora_result = rouge.compute(predictions=generated, references=human, use_stemmer=True)
    print(f"Fine-tuned model: {lora_result}")

    del model
    torch.cuda.empty_cache()

    model = T5ForConditionalGeneration.from_pretrained(
        MODEL_NAME, torch_dtype=torch.bfloat16, device_map="cuda:0"
    )
    model.eval()
    baseline_generated, baseline_human = evaluate_test(
        model, tokenizer, config, dataset["test"], batch_size=64
    )
    baseline_result = rouge.compute(
        predictions=baseline_generated, references=baseline_human, use_stemmer=True
    )

    print(f"Baseline model: {baseline_result}")
