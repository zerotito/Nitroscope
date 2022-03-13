# Dockerfile - this is a comment. Delete me if you want.
FROM python:3.8
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
ENTRYPOINT ["python"]
RUN chmod 644 main.py
CMD ["main.py"]