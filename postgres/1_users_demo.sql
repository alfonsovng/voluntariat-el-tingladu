-- password is patata
INSERT INTO public.users (name, surname, email, dni, role, password) 
VALUES ('Superadmin', 'Test', 'superadmin@test.cat', '1TEST', 'superadmin', 'scrypt:32768:8:1$lwqNpblQ9OiKBfeM$4d63ebdf494cc8e363f14494bca1c5246f6689b45904431f69fbcb535b7e41bd012e9b41c850125d7f8b790cb320579a46427b69eda892517669eba0244b77b4');

-- password is patata
INSERT INTO public.users (name, surname, email, dni, role, password) 
VALUES ('Admin', 'Test', 'admin@test.cat', '2TEST', 'admin', 'scrypt:32768:8:1$lwqNpblQ9OiKBfeM$4d63ebdf494cc8e363f14494bca1c5246f6689b45904431f69fbcb535b7e41bd012e9b41c850125d7f8b790cb320579a46427b69eda892517669eba0244b77b4');

-- password is patata and check email at https://cryptogmail.com/
INSERT INTO public.users (name, surname, email, dni, role, password) 
VALUES ('Partner', 'Test', 'partner@test.cat', '3TEST', 'partner', 'scrypt:32768:8:1$lwqNpblQ9OiKBfeM$4d63ebdf494cc8e363f14494bca1c5246f6689b45904431f69fbcb535b7e41bd012e9b41c850125d7f8b790cb320579a46427b69eda892517669eba0244b77b4');

-- password is patata and check email at https://cryptogmail.com/
INSERT INTO public.users (name, surname, email, dni, role, password) 
VALUES ('Volunteer', 'Test', 'volunteer@test.cat', '4TEST', 'volunteer', 'scrypt:32768:8:1$lwqNpblQ9OiKBfeM$4d63ebdf494cc8e363f14494bca1c5246f6689b45904431f69fbcb535b7e41bd012e9b41c850125d7f8b790cb320579a46427b69eda892517669eba0244b77b4');