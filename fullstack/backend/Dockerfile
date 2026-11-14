FROM python:3.12-slim

# TODO: Set workdir to /app

COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

# TODO: Add command to serve backend API
CMD [ -------------------, "--host", "0.0.0.0", "--port", "8000"]
