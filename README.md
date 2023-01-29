# Voluntariat El Tingladu

Aplicació web desenvolupada amb Python per a gestionar el voluntariat d'[El Tingladu](https://www.eltingladu.cat/), un festival de música i cultura catalana que se celebra des de 2008 a Vilanova i la Geltrú.

Web application developed with Python to manage the volunteers of [El Tingladu](https://www.eltingladu.cat/), a Catalan music and culture festival that has been held since 2008 in Vilanova i la Geltrú.

## Python Virtual Environment

Preparation:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r service-flask/requirements.txt
```

It is also possible to install the requeriments with the commands:

```bash
pip install -U pip
pip install -U flask flask-login flask-wtf Flask-SQLAlchemy
pip install -U python-dotenv psycopg2-binary email_validator hashids openpyxl
pip install -U gunicorn
```

To generate the requirements file:

```bash
pip freeze > service-flask/requirements.txt
deactivate
```

## Database

PostgreSQL is the database of the application. To run it you need `docker compose` installed:

```bash
apt-get install docker-compose-plugin
```

To run the database, run inside the `service-postgres` folder:

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

To reset the database, stop it, remove the `service-postgres/data` folder, and start it again.

## CSS and Javascript

The original CSS and JS files can be found here:

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/css/bootstrap.min.css">
<script src="https://cdn.jsdelivr.net/npm/jquery@3.6.1/dist/jquery.slim.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/popper.js@1.16.1/dist/umd/popper.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/js/bootstrap.bundle.min.js"></script>
```

## Demo users

Check the file [1_users-demo.sql](./service-postgres/sql/1_users_demo.sql). Password of both users is **demo**.

## Launch the application in development

First launch the database:

```
docker compose up
```

Enter in the `service-flask` folder and run the flask app:

```
flask run
```

Open a browser to http://127.0.0.1:8080/

## Production

```
docker compose -f docker-compose-prod.yml up
```

## Useful links

* Sending Emails Using Python and Gmail: https://leimao.github.io/blog/Python-Send-Gmail/

* Running Flask in production with Docker: https://smirnov-am.github.io/running-flask-in-production-with-docker/

* ngrok Step-by-Step Guide: Easily Share Your Local Server: https://www.sitepoint.com/use-ngrok-test-local-site/

* Dockerizing Flask with Postgres, Gunicorn, and Nginx: https://testdriven.io/blog/dockerizing-flask-with-postgres-gunicorn-and-nginx/

* Setup SSL with Docker, NGINX and Lets Encrypt: https://www.programonaut.com/setup-ssl-with-docker-nginx-and-lets-encrypt/

* How To Automate SSL With Docker And NGINX: https://www.programonaut.com/how-to-automate-ssl-with-docker-and-nginx/