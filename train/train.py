from datasets import *
from transformers import BertTokenizerFast, BertConfig, BertForMaskedLM, DataCollatorForLanguageModeling, TrainingArguments, Trainer
import os
import json
import functools

def encode_with_truncation(examples, tokenizer, max_length):
	"""Mapping function to tokenize the sentences passed with truncation"""
	return tokenizer(examples["text"], truncation=True, padding="max_length", max_length=max_length, return_special_tokens_mask=True)

def encode_without_truncation(examples, tokenizer):
	"""Mapping function to tokenize the sentences passed without truncation"""
	return tokenizer(examples["text"], return_special_tokens_mask=True)

# Main data processing function that will concatenate all texts from our dataset and generate chunks of
# max_seq_length.
def group_texts(examples, max_length):
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

def prepare_dataset():
		# files = ["train_try.txt"]
		# dataset = load_dataset("text", data_files=files, split="train")
		dataset = load_dataset('wikitext', 'wikitext-103-v1', split = 'train')
		tokenizer = BertTokenizerFast.from_pretrained('bert-base-uncased')

		truncate_longer_samples = True
		max_length = tokenizer.model_max_length

		# the encode function will depend on the truncate_longer_samples variable
		encode = encode_with_truncation if truncate_longer_samples else encode_without_truncation

		# tokenizing the train dataset
		train_dataset = dataset.map(functools.partial(encode, tokenizer= tokenizer, max_length= max_length), batched=True)

		if truncate_longer_samples:
			# remove other columns and set input_ids and attention_mask as 
			train_dataset.set_format(type="torch", columns=["input_ids", "attention_mask"])
		else:
			train_dataset.set_format(columns=["input_ids", "attention_mask", "special_tokens_mask"])

		if not truncate_longer_samples:
			train_dataset = train_dataset.map(functools.partial(group_texts, max_length= max_length), batched=True, batch_size=2_000,
																				desc=f"Grouping texts in chunks of {max_length}")
		
		print(dataset)
		# initialize the model with the config
		model_config = BertConfig(vocab_size=tokenizer.vocab_size, max_position_embeddings=tokenizer.model_max_length)
		model = BertForMaskedLM(config=model_config)

		data_collator = DataCollatorForLanguageModeling(
    tokenizer=tokenizer, mlm=True, mlm_probability=0.2
		)
		training_args = TrainingArguments(
    output_dir='/scratch/rv2138/nlu/checkpoints',          # output directory to where save model checkpoint
    # evaluation_strategy="steps",    # evaluate each `logging_steps` steps
    overwrite_output_dir=True,      
    num_train_epochs=10,            # number of training epochs, feel free to tweak
    per_device_train_batch_size=10, # the training batch size, put it as high as your GPU memory fits
    gradient_accumulation_steps=8,  # accumulating the gradients before updating the weights
    per_device_eval_batch_size=64,  # evaluation batch size
    logging_steps=10,             # evaluate, log and save model checkpoints every 1000 step
    save_steps=100,
    # load_best_model_at_end=True,  # whether to load the best model (in terms of loss) at the end of training
    save_total_limit=3,           # whether you don't have much space so you let only 3 model weights saved in the disk
		)	
		
		trainer = Trainer(
    model=model,
    args=training_args,
    data_collator=data_collator,
    train_dataset=train_dataset,
    # eval_dataset=test_dataset,
		)

		trainer.train()

if __name__ == '__main__':
		train_dataset = prepare_dataset()
		# print(train_dataset)
		print("Success")