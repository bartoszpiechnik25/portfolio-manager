# FINE-TUNING

## Details

Model was fine-tuned on the [finance-alpaca](https://huggingface.co/datasets/gbharti/finance-alpaca) dataset, rows that were longer than 512 tokens (instruction + context) were truncated.

Training was done locally on my PC on GTX 1080Ti 12GB VRAM using Low Rank Adaptation ([LoRA](https://arxiv.org/pdf/2106.09685.pdf)) method, it took approximately 7 hours for one epoch with LLM weights set to bfloat16, batch size was set to the value that will maximally utilize GPU memory.

After some tests I decided to use FLAN-T5-large because perfomance "out of the box" (without fine-tuning) was better than FLAN-T5-base after fine tunning with LoRA.

I was also considering using 'google/flan-t5-xl' (3B parameter model) and fine-tune it with QLoRA in 4bit precision, but loading such model requires GPU and my cloud machine that will host the model has only CPU.

### Financial QA task

#### Training loss curve

![Training loss curve](./plots/financial_qa_2_epochs.png)

```cpp
Training data shape: (43441, 2)
Test data shape: (4827, 2)
Memory footprint of FLAN-T5-large with LoRA layers: 1.60 GB
Trainable parameters 9,437,184 || All parameters 792,587,264 || Trainable parameter percentage: 1.19%
```

#### Rouge scores

|| Rouge-1 | Rouge-2 | Rouge-L | Rouge-Lsum |
|---|---------|---------|---------|---------|
| LoRA Model | 0.2899 | 0.1144 | 0.2285 | 0.2286 |
| Base Model | 0.1131 | 0.0352 | 0.0966 | 0.0963 |

### Text to SQL task

Dataset used for fine-tunning to generate SQL queries from text was [Text2SQL](https://huggingface.co/datasets/b-mc2/sql-create-context). Thanks to smaller number of tokens (mostly < 100) in the context I was able to run training for 3 epochs on my GPU, training took approximately 6 hours.

### SQL-CREATE-CONTEXT dataset

#### Training loss curve (Text2SQL)

![Training loss curve](./plots/text2sql_3-epochs.png)

#### Rouge scores (Text2SQL)

|| Rouge-1 | Rouge-2 | Rouge-L | Rouge-Lsum |
|---|---------|---------|---------|---------|
| LoRA Model | 0.9879 | 0.9879 | 0.9879 | 0.9879 |
| Base Model | 0.2554 | 0.1066| 0.2200 | 0.2200 |

### Llama-2-SQL-dataset

Model weights achieved in the previous fine-tuning on the dataset mentioned above were used to further fine-tune and imporve model's ability to generate SQL queries from text. Dataset used for this task was [Llama-2 SQL](https://huggingface.co/datasets/ChrisHayduk/Llama-2-SQL-Dataset).

#### Training loss curve (Llama-2 SQL Dataset)

![Training loss curve](./plots/llama2sql_2-epochs.png)

#### Validation loss curve (Llama-2 SQL Dataset)

![Validation loss curve](./plots/llama2sql_2-epochs_eval.png)

#### Rouge scores (Llama-2 SQL Dataset)s

|| Rouge-1 | Rouge-2 | Rouge-L | Rouge-Lsum |
|---|---------|---------|---------|---------|
| LoRA Model | 0.9931 | 0.9832 | 0.9909 | 0.9909 |
| Base Model | 0.1912 | 0.0771 | 0.1775 | 0.1777 |

### CNN_DailyMail dataset

3rd model fine-tuning was done on the [CNN_DailyMail](https://huggingface.co/datasets/cnn_dailymail) dataset, which is a dataset for summarization task. Articles that were longet than context window (512 tokens) were truncated, which resulted in 40347 training samples and 4484 test samples. Fine-tuning with LoRA gave better results with a window for even further improvement, since eval loss was still decreasing after 2 epochs and was smaller than training loss.

#### Training loss curve (CNN_DailyMail) - 2 epochs

![Training loss curve](./plots/cnn_dailymail_2-epochs.png)

#### Validation loss

|  | Epoch 1 | Epoch 2 |
| --- | --- | --- |
| Eval loss | 1.1708 | 1.1682 |

#### Rouge scores (CNN_DailyMail)

|| Rouge-1 | Rouge-2 | Rouge-L | Rouge-Lsum |
|---|---------|---------|---------|---------|
| LoRA Model | 0.4285 | 0.2144 | 0.3203 | 0.3202 |
| Base Model | 0.3492 | 0.1576 | 0.2582 | 0.2583 |

## Future work

- Try FLAN-T5-XL/XXL (3B/11B) with QLoRA to fine-tune on financial QA task (since the FLAN-T5-large performance is not satisfactory).
