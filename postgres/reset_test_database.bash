#!/bin/bash

PGPORT=54330
PGDATABASE=postgres
PGUSER=postgres
export PGPASSWORD=patata

psql -p $PGPORT -h 127.0.0.1 -U $PGUSER -c "DROP DATABASE IF EXISTS $PGDATABASE;" -c "CREATE DATABASE $PGDATABASE;"
psql -p $PGPORT -h 127.0.0.1 -U $PGUSER -d $PGDATABASE -a -f 0_schema.sql 
psql -p $PGPORT -h 127.0.0.1 -U $PGUSER -d $PGDATABASE -a -f 1_users_demo.sql 
psql -p $PGPORT -h 127.0.0.1 -U $PGUSER -d $PGDATABASE -a -f 2_diets.sql 
psql -p $PGPORT -h 127.0.0.1 -U $PGUSER -d $PGDATABASE -a -f 3_tasks.sql 
psql -p $PGPORT -h 127.0.0.1 -U $PGUSER -d $PGDATABASE -a -f 4_shifts.sql 
psql -p $PGPORT -h 127.0.0.1 -U $PGUSER -d $PGDATABASE -a -f 5_meals.sql 
psql -p $PGPORT -h 127.0.0.1 -U $PGUSER -d $PGDATABASE -a -f 6_tickets.sql 
psql -p $PGPORT -h 127.0.0.1 -U $PGUSER -d $PGDATABASE -a -f 7_rewards.sql 
psql -p $PGPORT -h 127.0.0.1 -U $PGUSER -d $PGDATABASE -a -f 8_dnis_demo.sql