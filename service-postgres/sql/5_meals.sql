\copy meals(id, code, name, description) from '/docker-entrypoint-initdb.d/csv/meals.csv' delimiter ',' csv header;
SELECT pg_catalog.setval('public.meals_id_seq', (SELECT MAX(id) FROM meals));