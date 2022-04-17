from datasets import *
from transformers import BertTokenizerFast
import os
import json

def encode_with_truncation(examples):
  """Mapping function to tokenize the sentences passed with truncation"""
  return tokenizer(examples["text"], truncation=True, padding="max_length", max_length=max_length, return_special_tokens_mask=True)

def encode_without_truncation(examples):
  """Mapping function to tokenize the sentences passed without truncation"""
  return tokenizer(examples["text"], return_special_tokens_mask=True)

# Main data processing function that will concatenate all texts from our dataset and generate chunks of
# max_seq_length.
def group_texts(examples):
    # Concatenate all texts.
    concatenated_examples = {k: sum(examples[k], []) for k in examples.keys()}
    total_length = len(concatenated_examples[list(examples.keys())[0]])
    # We drop the small remainder, we could add padding if the model supported it instead of this drop, you can
    # customize this part to your needs.
    if total_length >= max_length:
        total_length = (total_length // max_length) * max_length
    # Split by chunks of max_len.
    result = {
        k: [t[i : i + max_length] for i in range(0, total_length, max_length)]
        for k, t in concatenated_examples.items()
    }
    return result

if __name__ == '__main__':
    print("Started!")
    files = ["train_try.txt"]
    dataset = load_dataset("text", data_files=files, split="train")
    tokenizer = BertTokenizerFast.from_pretrained('bert-base-uncased')

    truncate_longer_samples = True
    max_length = tokenizer.model_max_length

    # the encode function will depend on the truncate_longer_samples variable
    encode = encode_with_truncation if truncate_longer_samples else encode_without_truncation

    # tokenizing the train dataset
    train_dataset = dataset.map(encode, batched=True)

    if truncate_longer_samples:
      # remove other columns and set input_ids and attention_mask as 
      train_dataset.set_format(type="torch", columns=["input_ids", "attention_mask"])
    else:
      train_dataset.set_format(columns=["input_ids", "attention_mask", "special_tokens_mask"])
    print(train_dataset)

    if not truncate_longer_samples:
      train_dataset = train_dataset.map(group_texts, batched=True, batch_size=2_000,
                                        desc=f"Grouping texts in chunks of {max_length}")

    print("Success")