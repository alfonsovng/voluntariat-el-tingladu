-- password is demo
-- email to check: https://maildrop.cc/inbox/?mailbox=bert
INSERT INTO public.users (name, surname, email, dni, password, role) 
VALUES ('Bert', 'Admin', 'bert@maildrop.cc', '', 'sha256$A3mHKyB57VoVwSNX$0d71e26e9e32092fdcb38afaf37d933bc93a8b7572e9cca9aed6c00eb824390d', 'admin');

-- password is demo
-- email to check: https://maildrop.cc/inbox/?mailbox=ernie
INSERT INTO public.users (name, surname, email, dni, password, role) 
VALUES ('Ernie', 'Volunteer', 'ernie@maildrop.cc', '', 'sha256$A3mHKyB57VoVwSNX$0d71e26e9e32092fdcb38afaf37d933bc93a8b7572e9cca9aed6c00eb824390d', 'volunteer');