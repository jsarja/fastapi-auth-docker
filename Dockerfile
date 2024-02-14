# 
FROM python:3.12

# 
WORKDIR /code

# 
COPY ./requirements.txt /code/requirements.txt

# 
RUN pip install --upgrade pip

# 
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# 
COPY ./app /code/app

#
COPY ./tests /code/tests

# 
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--reload"]