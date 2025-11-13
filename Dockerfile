FROM python:3.10-slim

WORKDIR /app

# Copy requirements first
COPY requirements.txt .

# Install dependencies with better error handling
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

# Copy app code
COPY . .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]