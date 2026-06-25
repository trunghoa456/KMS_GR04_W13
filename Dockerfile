FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    STREAMLIT_SERVER_HEADLESS=true

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY app.py rag_engine.py ingest_to_vector.py access_matrix.md ./

EXPOSE 8501

CMD ["sh", "-c", "if [ ! -f \"${VECTOR_PERSIST_DIR:-/app/chroma_db}/chroma.sqlite3\" ]; then python ingest_to_vector.py || exit 1; fi; exec streamlit run app.py --server.address=0.0.0.0 --server.port=8501"]
