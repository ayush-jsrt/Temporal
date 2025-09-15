# Temporal


Database

```bash
docker run --name temporal-db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=root \
  -e POSTGRES_DB=temporal_db \
  -p 5432:5432 \
  ankane/pgvector
```
