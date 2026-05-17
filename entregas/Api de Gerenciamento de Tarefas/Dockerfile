# Usar uma imagem oficial do Python, versão slim (mais leve)
FROM python:3.11-slim

# Definir o diretório de trabalho dentro do container
WORKDIR /app

# Copiar o arquivo de dependências
COPY requirements.txt .

# Instalar as dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo o código fonte e o arquivo HTML para dentro do container
COPY . .

# Expor a porta que o servidor vai rodar
EXPOSE 8000

# Comando para iniciar o servidor
CMD ["python", "sistema_gerado.py", "--serve"]
