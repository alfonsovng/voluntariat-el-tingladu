\copy partner_dnis(dni) from '/docker-entrypoint-initdb.d/csv/dnis_demo.csv' delimiter ',' csv header;
update partner_dnis set dni = upper(dni); -- tots en majúscules