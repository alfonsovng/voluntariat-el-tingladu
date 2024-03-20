# Voluntariat El Tingladu

Aplicació web desenvolupada amb Python per a gestionar el voluntariat d'[El Tingladu](https://www.eltingladu.cat/), un festival de música i cultura catalana que se celebra des de 2008 a Vilanova i la Geltrú.

Web application developed with Python to manage the volunteers of [El Tingladu](https://www.eltingladu.cat/), a Catalan music and culture festival that has been held since 2008 in Vilanova i la Geltrú.

## Python Virtual Environment

Preparation:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

To generate the requirements file:

```bash
pip freeze > requirements.txt
deactivate
```

## Database

PostgreSQL is the database of the application. To run it you need `docker compose` installed:

```bash
apt-get install docker-compose-plugin
```

To run the database execute:

```bash
docker compose up
```

To open a psql console, run:

```
docker exec -it voluntariat-el-tingladu-postgres-1 psql -U postgres
```

To create file `0_squema.sql` with all the tables:

```
docker exec -it voluntariat-el-tingladu-postgres-1 pg_dump -U postgres -s > 0_schema.sql
```

To create file `dump.sql` with all the tables and the data:
```
docker exec -it voluntariat-el-tingladu-postgres-1 pg_dump -U postgres --column-inserts > dump.sql
```

To reset the database, stop it, and start agin after removing the volume:

```
docker volume rm voluntariat-el-tingladu_postgres_volume

```

## CSS and Javascript

The original CSS and JS files can be found here:

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/css/bootstrap.min.css">
<script src="https://cdn.jsdelivr.net/npm/jquery@3.6.1/dist/jquery.slim.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/popper.js@1.16.1/dist/umd/popper.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/js/bootstrap.bundle.min.js"></script>
```

## Demo users

Check the file [1_users_demo.sql](./postgres/1_users_demo.sql). Password of both users is **demo**.

## Launch the application in Development

First launch the database:

```
docker compose up
```

Then run the flask app:

```
flask run --debug
```

Open a browser to `http://127.0.0.1:8080/`

## Launch the application in Developement

The application is launched with HTTP:

```
docker compose -f docker-compose-developement.yml up
```

Open a browser to the port `80` of the test server.


## Launch the application in Production

Run script [certbot.sh](./nginx/certbot.sh) to obtain or renew a certificate for the domain(s):

```
bash ./nginx/certbot.sh certonly
```

Launch the application with HTTPS:

```
docker compose -f docker-compose-production.yml up
```

Open a browser to the port `443` of the production server.
