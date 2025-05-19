# min_rag
this is a minimal implementaion of the RAG model for question
answering 

## requirments
- python 3.8 or later

#### Install python using minicodna
1) Download and install MIniconda from [her](https://www.anaconda.com/docs/getting-started/miniconda/main)
2) Create new enviroment using the following command:
```bash
$ conda create -n min-rag-app python=3.8
```
3) Activate enviroment using the following command:
```bash
$ conda activate min-rag-app
```

### (optinal) setup your command line interface for better readability
```bash
export PS1="\[\033[01;32m\]\u@\h:\w\n\[\033[00m\]\$ "
```

### Install required pakages
```bash
$ pip install -r requirments.txt
```
### Setup enviroment variables
```bash
$ cp .env.example .env
```
set your enviroment variables in the .env file like GROQ_API_KEY value