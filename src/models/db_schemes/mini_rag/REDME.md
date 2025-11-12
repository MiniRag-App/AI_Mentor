### Run Alembic Migrations

change dir to your db schems in cmd

```bash
cmd
alembic init alembic
```

### Configration

```bash
cmd
copy  alembic.ini  alembic.ini.example
```

- update alembic.ini with your database credentials(`sqlalchemy.url`)

### Alter env.py file from alembic folder 

```bash
target_metadata = SQLAlchemyBase.metadata
```

### Create new migration 
each time you make any update in tables schems you should run 

```bash
alembic revision --autogenerate -m "Add ..."

```
And then 
```bash
alembic upgrade head
```
### To downgrade to the previous migration
```bash
alembic downgrade -1
```
