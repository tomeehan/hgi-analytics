FROM python:3.11-slim

WORKDIR /airbyte/integration_code

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY setup.py .
COPY source_prospect_crm ./source_prospect_crm
COPY main.py .

RUN pip install --no-cache-dir -e .

ENV AIRBYTE_ENTRYPOINT "python /airbyte/integration_code/main.py"
ENTRYPOINT ["python", "/airbyte/integration_code/main.py"]
