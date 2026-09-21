FROM python:3.11-slim
RUN pip install pika mysql-connector-python
COPY contact_monitor.py /app/contact_monitor.py
WORKDIR /app
CMD ["python", "contact_monitor.py"]
