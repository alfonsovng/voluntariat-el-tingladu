-- tots els usuaris han de tenir un registre a la taula de recompenses
insert into user_rewards select id from users;