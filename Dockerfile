# SADAH — works on Hugging Face Spaces (port 7860) and Render ($PORT)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=7860 \
    SADAH_SAFE_MODE=1

# Hugging Face Spaces runs containers as uid 1000
RUN useradd -m -u 1000 sadah && mkdir -p /app && chown sadah:sadah /app
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir -r requirements.txt

COPY --chown=sadah:sadah . .
USER sadah

# The trained brains ship in models/; train here only if they are missing
RUN test -f models/router.pt -a -f models/coder.pt || python -m core.trainer all medium --promote

EXPOSE 7860
CMD ["python", "app.py"]
