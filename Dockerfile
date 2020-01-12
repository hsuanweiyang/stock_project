FROM python:3.6.9
COPY . /app/
WORKDIR /app
RUN pip install -r requirements.txt
CMD python dashboard.py
EXPOSE 1234