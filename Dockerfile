FROM python:3.12.3-slim

RUN useradd -m -u 1000 agentuser

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R agentuser:agentuser /app

USER agentuser

CMD ["python", "main.py"]