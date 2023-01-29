\copy rewards(id, name, description) from '/docker-entrypoint-initdb.d/csv/rewards.csv' delimiter ',' csv header;
SELECT pg_catalog.setval('public.rewards_id_seq', (SELECT MAX(id) FROM rewards));