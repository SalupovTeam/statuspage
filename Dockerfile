FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY templates/ templates/
COPY api_docs.md .

RUN mkdir -p instance
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PORT=1487

RUN echo '#!/bin/bash\n\
echo "Starting Status Page..." >&2\n\
python3 << EOF\n\
import string\n\
import random\n\
from app import app, db, ApiKey\n\
\n\
with app.app_context():\n\
    api_key = "".join(random.choices(string.ascii_letters + string.digits, k=10))\n\
    db.create_all()\n\
    key = ApiKey(key=api_key)\n\
    db.session.add(key)\n\
    db.session.commit()\n\
    print("\\n=================================", flush=True)\n\
    print("Generated API Key:", api_key, flush=True)\n\
    print("=================================\\n", flush=True)\n\
EOF\n\
\n\
exec flask run --host=0.0.0.0 --port=1487' > /app/start.sh

RUN chmod +x /app/start.sh

EXPOSE 1487

CMD ["/app/start.sh"]