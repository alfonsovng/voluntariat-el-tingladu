-- taula temporal de torns
CREATE TEMP TABLE tmp_shifts (
    task_id integer DEFAULT 0 NOT NULL,
    task_name character varying NOT NULL,
    name character varying NOT NULL,
    description character varying DEFAULT ''::character varying NOT NULL,
    slots integer DEFAULT 0 NOT NULL,
    assignations character varying[] DEFAULT '{}'::character varying[] NOT NULL,
    reward integer DEFAULT 0 NOT NULL
);

-- carrego la taula temporal
\copy tmp_shifts(task_name, name, description, slots, reward, assignations) from '/docker-entrypoint-initdb.d/csv/shifts.csv' delimiter ',' csv header;

-- trobo el task_id de cada tasca
update tmp_shifts set task_id = tasks.id from tasks where tasks.name = tmp_shifts.task_name;

-- fico les dades a la taula de torns auténtica
insert into shifts (task_id, name, description, slots, reward, assignations)
select task_id, name, description, slots, reward, assignations from tmp_shifts;

-- esborro la taula temporal
DROP TABLE tmp_shifts;
