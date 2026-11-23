# sadah: runs anywhere a container runs (port from $PORT, default 7860)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HOST=0.0.0.0 PORT=7860
RUN useradd -m -u 1000 sadah && mkdir -p /app && chown sadah:sadah /app
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=sadah:sadah . .
USER sadah
EXPOSE 7860
CMD ["python", "app.py"]
