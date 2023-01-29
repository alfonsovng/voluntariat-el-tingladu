-- tots els usuaris han de tenir un registre a la taula de dietes
insert into user_diets select id,false,false,false,false,'' from users;