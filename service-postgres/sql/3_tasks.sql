\copy tasks(id, name, description, password) from '/docker-entrypoint-initdb.d/csv/tasks.csv' delimiter ',' csv header;
SELECT pg_catalog.setval('public.tasks_id_seq', (SELECT MAX(id) FROM tasks));