# bookly
Book management system


```shell
fastapi dev ./src
celery -A src.celery_tasks.c_app worker --concurrency=1
celery -A src.celery_tasks.c_app flower
st run http://localhost:8000/api/v1/openapi.json --experimental=openapi-3.1
```