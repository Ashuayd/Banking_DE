FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    gcc \
    libc-dev \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get remove -y gcc libc-dev \
    && apt-get autoremove -y \
    && apt-get clean
COPY . .
EXPOSE 8080
ENV PORT=8080
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8080"]