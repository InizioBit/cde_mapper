# CDE-Mapper: Using Retrieval-Augmented Language Models for Mapping Clinical Data Elements to Controlled Vocabularies

![image](https://github.com/user-attachments/assets/54577286-9d04-45a3-852e-66684bd1a2fc)

CDE-Mapper is an automated concept linking tool designed to find appropriate standardized terms in OMOP Athena vocabularies for clinical terms found in data dictionaries. Built with advanced Retrieval Augmented Generation (RAG) methods, CT_Mapper leverages the power of generative models and vector stores to enhance the accuracy of linking composite concepts. This tool enables data custodians to transform ambiguous and semi-structured clinical data into a harmonized schema effectively. Checkout the article at https://arxiv.org/abs/2505.04365


## Table of Contents

- [Task Description](#task-description)
- [Installation Requirements](#installation-requirements)
- [Usage](#usage)
  - [Running Experiments on BC5CDR-Disease Dataset](#running-experiments-on-ncbi-dataset)
    - [Standard Inference](#standard-inference)
    - [LLAMA3.1 Inference](#llama31-inference)
- [Contributing](#contributing)
- [License](#license)

## Task Description

To harmonize clinical data effectively, it is crucial to understand the varying levels of conceptual representation within it. Many existing frameworks have attempted to address the challenge of concept linking, focusing primarily on clinical terms with atomic representation. However, in the context of challenges encountered in mapping cohort studies for the ICARE4CVD project, we propose a solution that leverages retrieval-augmented generation and in-context learning.

Instead of mapping individual terms, we focus on mapping data dictionaries presented in a horizontal table format, where each row is treated as a single query. Each query may include multiple components such as labels, descriptions, methods, formulas, units, and categorical values. To standardize and extract clinical terms from each query, we employ in-context learning with generative models like LLAMA and GPT-4. For retrieval, we utilize a hybrid vector search combined with metadata filtering on a structured schema to enhance precision. To further refine the results, we propose a multi-stage ranking method, including a large language model-based cross-ranking approach to filter out irrelevant candidates, followed by relevance-based scoring and relationship prediction. The cumulative score from these steps is used to identify the final candidate.



## Installation Requirements

To run **CDE-Mapper**, you need to install the packages mentioned in requirements.in file:

You can install these dependencies using `pip`:

```bash
pip install pandas tqdm torch transformers python-dotenv qdrant-client langchain langchain_openai ctransformers pydantic>=1.10.8 typing-extensions>=4.8.0 torch>=2.2.2 openai>=1.19.0 qdrant-client>=1.8.2 langchain-community togather faiss-cpu faiss-gpu langchain-togather simstring-fast
```
## Usage

Running Experiments on NCBI Dataset
Below are examples of how to run experiments using the {NCBI} dataset or anyother dataset with CDE-Mapper. These examples demonstrate both standard inference and using the LLAMA3.1 model for enhanced performance.

## Baseline Smoke Audit

For the research audit baseline, use WSL with the `cde-mapper` conda environment:

```bash
wsl -e bash -lc "cd /mnt/d/Program/cde_mapper && bash scripts/audit_baseline_wsl.sh"
```

This smoke audit checks local imports, custom data loading, mapping template JSON, and temporary SQLite reservoir initialization without calling Qdrant, Athena, or an LLM.

## Standard Inference

To perform standard inference through the current baseline entry point, use `run.py`:

```
python run.py \
  --flag inference \
  --input_file data/input/baseline_smoke.csv \
  --custom_data \
  --is_omop_data \
  --collection_name concept_mapping_1 \
  --llm_id google/gemma-3n-E4B-it \
  --topk 5 \
  --output_file data/output/baseline_smoke_mapped.csv
```

## Explanation of Parameters:

* **flag inference:** Use an existing vector collection. Use `recreate` only when rebuilding a collection from `--document_file_path`.
* **collection_name concept_mapping_1:** Specifies the Qdrant collection name.
* **input_file:** Path to the CSV, TXT, or JSON input file.
* **custom_data:** Treat CSV input as a data dictionary with fields such as `variablename`, `variablelabel`, `categorical`, `units`, `formula`, and `visits`.
* **is_omop_data:** Enable OMOP-specific domain and vocabulary filtering.
* **output_file:** Path where the output results will be saved.

## LLAMA3.1 Inference

For enhanced inference using the LLAMA3.1 model, execute the following command:

```
python run.py \
  --flag inference \
  --input_file data/input/baseline_smoke.csv \
  --custom_data \
  --is_omop_data \
  --collection_name concept_mapping_1 \
  --llm_id google/gemma-3n-E4B-it \
  --topk 5 \
  --output_file data/output/baseline_smoke_llama31_mapped.csv
```


## Contributing

Contributions are welcome! Please follow these steps to contribute:

Fork the Repository: Click the "Fork" button at the top-right corner of this page.
Clone Your Fork:
```git clone https://github.com/komi786/cde_mapper.git ```
Create a New Branch:
```git checkout -b feature/YourFeature```
Make Your Changes: Implement your feature or bug fix.
Commit Your Changes:
```git commit -m "Add your descriptive commit message"```
Push to Your Fork:
```git push origin feature/YourFeature```
Create a Pull Request: Navigate to the original repository and click "New Pull Request".
Please ensure your contributions adhere to the existing code style and include appropriate tests where applicable.

```markdown
![License](https://img.shields.io/badge/license-MIT-blue.svg)
