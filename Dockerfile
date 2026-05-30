FROM python:3.11

WORKDIR /app

# dependencias backend
COPY backend/ backend/
COPY backend/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# frontend build (React/Vite)
RUN apt-get update && apt-get install -y nodejs npm

COPY frontend/ frontend/

RUN cd frontend && npm install && npm run build

# expone backend
EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]