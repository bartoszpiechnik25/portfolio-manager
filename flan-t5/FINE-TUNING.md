# FINE-TUNING

## Details

Model was fine-tuned on the [finance-alpaca](https://huggingface.co/datasets/gbharti/finance-alpaca) dataset, rows that were longer than 512 tokens (instruction + context) were truncated.

Training was done locally on my PC on GTX 1080Ti 12GB VRAM using Low Rank Adaptation ([LoRA](https://arxiv.org/pdf/2106.09685.pdf)) method, it took approximately 7 hours for one epoch with LLM weights set to float16, batch size was set to the value that will maximally utilize GPU memory.

### Training loss curve

![Training loss curve]()

### Validation loss curve

![Validation loss curve]()

```cpp
Training data shape: (43441, 2)
Test data shape: (4827, 2)
Memory footprint of FLAN-T5-large with LoRA layers: 1.60 GB
Trainable parameters 9,437,184 || All parameters 792,587,264 || Trainable parameter percentage: 1.19%
```

## Future work

- Try to "teach" this model SQL queries to retrieve information from the database.
- Further fine-tuning to summarize financial articles and chat with users.
