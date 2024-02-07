-- password is patata
-- email to check: https://maildrop.cc/inbox/?mailbox=bert
INSERT INTO public.users (name, surname, email, dni, password, role) 
VALUES ('Bert', 'Admin', 'bert@maildrop.cc', '', 'scrypt:32768:8:1$lwqNpblQ9OiKBfeM$4d63ebdf494cc8e363f14494bca1c5246f6689b45904431f69fbcb535b7e41bd012e9b41c850125d7f8b790cb320579a46427b69eda892517669eba0244b77b4', 'admin');

-- password is patata
-- email to check: https://maildrop.cc/inbox/?mailbox=ernie
INSERT INTO public.users (name, surname, email, dni, password, role) 
VALUES ('Ernie', 'Volunteer', 'ernie@maildrop.cc', '', 'scrypt:32768:8:1$lwqNpblQ9OiKBfeM$4d63ebdf494cc8e363f14494bca1c5246f6689b45904431f69fbcb535b7e41bd012e9b41c850125d7f8b790cb320579a46427b69eda892517669eba0244b77b4', 'volunteer');