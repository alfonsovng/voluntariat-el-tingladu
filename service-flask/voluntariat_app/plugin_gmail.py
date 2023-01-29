import smtplib
from flask import url_for, render_template
from email.message import EmailMessage
from email.utils import formataddr

# https://leimao.github.io/blog/Python-Send-Gmail/
class GmailManager:

    def __init__(self, app=None):
        self.port = 587  # For TLS
        self.smtp_server = "smtp.gmail.com"
        self.sender_email = None
        self.password = None
        self.subject_prefix = "[VOLUNTARIAT EL TINGLADU] "
        self.cc_incidences = []
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        sender_name = "Voluntariat El Tingladu"
        self.sender_email = app.config.get('GMAIL_ACCOUNT')
        self.sender_email_with_name = formataddr((sender_name, self.sender_email))

        self.password = app.config.get('GMAIL_PASSWORD')

        self.cc_incidences = app.config.get('GMAIL_CC_INCIDENCES')

    def send(self, receiver_email, cc_emails, subject, content):
        msg = EmailMessage()
        msg.set_content(content)
        msg['Subject'] = self.subject_prefix + subject
        msg['From'] = self.sender_email_with_name
        msg['To'] = receiver_email
        msg['Cc'] = ','.join(cc_emails)

        to_addrs = [receiver_email] + cc_emails

        server = smtplib.SMTP(self.smtp_server, self.port)
        server.starttls()
        server.login(self.sender_email, self.password)
        server.send_message(msg, from_addr=self.sender_email, to_addrs=to_addrs)

    
from .helper import Task
class TaskEmail(Task):
    def __init__(self, receiver_email, subject, content, cc_emails = []):
        super().__init__()
        self.receiver_email = receiver_email
        self.cc_emails = cc_emails
        self.subject = subject
        self.content = content
        
    def do_it(self):
        from . import gmail_manager
        gmail_manager.send(
            receiver_email = self.receiver_email,
            cc_emails = self.cc_emails,
            subject = self.subject, 
            content = self.content
        )


class TaskSignUpEmail(TaskEmail):
    def __init__(self, name, email, token):
        from . import params_manager

        subject = 'Registre'
        url = params_manager.external_url + url_for("auth_bp.reset", token = token)
        content = render_template("email/sign_up_email.txt", 
            name = name,
            url = url,
            app_url = params_manager.external_url
        )

        super().__init__(
            receiver_email=email,
            subject=subject,
            content=content
        )


class TaskResetPasswordEmail(TaskEmail):
    def __init__(self, name, email, token):
        from . import params_manager

        subject = 'Petició de canvi de contrasenya'
        url = params_manager.external_url + url_for("auth_bp.reset", token = token)
        content = render_template("email/reset_password_email.txt", 
            name = name, 
            url = url,
            app_url = params_manager.external_url
        )

        super().__init__(
            receiver_email=email,
            subject=subject,
            content=content
        )


class TaskConfirmPasswordChangeEmail(TaskEmail):
    def __init__(self, name, email):
        from . import params_manager

        subject = 'Canvi de contrasenya efectuat'
        content = render_template("email/confirm_password_change_email.txt", 
            name = name,
            app_url = params_manager.external_url
        )

        super().__init__(
            receiver_email=email,
            subject=subject,
            content=content
        )


class TaskIncidenceEmail(TaskEmail):
    def __init__(self, incidence_user, incidence_type, incidence_description):
        from . import gmail_manager, params_manager
        
        email = gmail_manager.sender_email
        subject = 'Incidència'
        content = render_template("email/incidence_email.txt",
            incidence_user = incidence_user,
            incidence_type = incidence_type,
            incidence_description = incidence_description,
            app_url = params_manager.external_url
        )

        super().__init__(
            receiver_email=email,
            cc_emails=gmail_manager.cc_incidences,
            subject=subject,
            content=content
        )


class TaskMessageEmail(TaskEmail):
    def __init__(self, user, subject, body):
        from . import params_manager
   
        email = user.email
        content = render_template("email/message_email.txt",
            name = user.name,
            body = body,
            app_url = params_manager.external_url
        )

        super().__init__(
            receiver_email=email,
            subject=subject,
            content=content
        )
