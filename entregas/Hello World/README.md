# Hello World

## Visão Geral

Este diretório contém um script Python simples que imprime "Hello, World!" no console. O objetivo é demonstrar uma aplicação básica e uma configuração mínima de Docker.

## Estrutura do Projeto

```
/Hello World
├── Dockerfile
├── README.md
└── sistema_gerado.py
```

## Requisitos

Certifique-se de que você tenha o Python instalado em sua máquina ou utilize o Docker.

## Como Executar o Sistema

Execute o script utilizando o Python:
```bash
python sistema_gerado.py
```

**Saída esperada**:
```
Hello, World!
```

### Usando Docker

Você também pode rodar usando o Docker:

```bash
docker build -t hello-world-python .
docker run --rm hello-world-python
```
