FROM python:3.13-slim

# build tools for the llm model (gcc, g++, make, cmake)
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    && rm -rf /var/lib/apt/lists/*


RUN adduser --disabled-password --gecos '' appuser

RUN mkdir /app
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install --upgrade pip

COPY requirements.txt  /app/
RUN pip install --no-cache-dir -r requirements.txt

USER appuser

COPY . /app/
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]