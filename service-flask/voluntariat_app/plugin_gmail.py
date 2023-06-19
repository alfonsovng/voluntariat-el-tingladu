import smtplib
from flask import url_for, render_template
from email.message import EmailMessage
from email.utils import formataddr
from .helper import logger, get_timestamp, labels

class GmailManager:

    def __init__(self, app=None):
        self.port = 587  # For TLS
        self.smtp_server = "smtp.gmail.com"
        self.sender_email = None
        self.password = None
        self.subject_prefix = labels.get("subject_prefix") + " "
        self.cc_incidences = []
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        sender_name = labels.get("sender_name")
        self.sender_email = app.config.get('GMAIL_ACCOUNT')
        self.sender_email_with_name = formataddr((sender_name, self.sender_email))

        self.password = app.config.get('GMAIL_PASSWORD')

        self.admin_mailboxes = app.config.get('GMAIL_ADMIN_MAILBOXES')

    def send(self, receiver_emails, subject, content):
        msg = EmailMessage()
        msg.set_content(content)
        msg['Subject'] = self.subject_prefix + subject
        msg['From'] = self.sender_email_with_name
        to = ','.join(receiver_emails)
        msg['To'] = to
        logger.info(f"Mail [{subject}] enviat a {to}")

        server = smtplib.SMTP(self.smtp_server, self.port)
        server.starttls()
        server.login(self.sender_email, self.password)
        server.send_message(msg, from_addr=self.sender_email, to_addrs=receiver_emails)

    
from .helper import Task
class TaskEmail(Task):
    def __init__(self, receiver_emails, subject, content):
        super().__init__()
        self.receiver_emails = receiver_emails
        self.subject = subject
        self.content = content
        
    def do_it(self):
        from . import gmail_manager
        gmail_manager.send(
            receiver_emails = self.receiver_emails,
            subject = self.subject, 
            content = self.content
        )


class TaskSignUpEmail(TaskEmail):
    def __init__(self, name, email, token):
        from . import params_manager

        subject = labels.get("sign_up_subject")
        url = params_manager.external_url + url_for("auth_bp.reset", token = token)
        content = render_template("email/sign_up_email.txt", 
            name = name,
            url = url,
            app_url = params_manager.external_url
        )

        super().__init__(
            receiver_emails = [email],
            subject = subject,
            content = content
        )


class TaskResetPasswordEmail(TaskEmail):
    def __init__(self, name, email, token):
        from . import params_manager

        subject = labels.get("reset_password_subject")
        url = params_manager.external_url + url_for("auth_bp.reset", token = token)
        content = render_template("email/reset_password_email.txt", 
            name = name, 
            url = url,
            app_url = params_manager.external_url
        )

        super().__init__(
            receiver_emails = [email],
            subject = subject,
            content = content
        )


class TaskConfirmPasswordChangeEmail(TaskEmail):
    def __init__(self, name, email):
        from . import params_manager

        subject = labels.get("confirm_password_change_subject")
        content = render_template("email/confirm_password_change_email.txt", 
            name = name,
            app_url = params_manager.external_url
        )

        super().__init__(
            receiver_emails = [email],
            subject = subject,
            content = content
        )


class TaskIncidenceEmail(TaskEmail):
    def __init__(self, incidence_user, incidence_type, incidence_description):
        from . import gmail_manager, params_manager

        str_date_time = get_timestamp()

        subject = f'{labels.get("incidence_subject")} {str_date_time}-{incidence_user.id}'
        content = render_template("email/incidence_email.txt",
            incidence_user = incidence_user,
            incidence_type = incidence_type,
            incidence_description = incidence_description,
            app_url = params_manager.external_url
        )

        super().__init__(
            receiver_emails = gmail_manager.admin_mailboxes,
            subject = subject,
            content = content
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
            receiver_emails = [email],
            subject = subject,
            content = content
        )


class TaskYourShiftsEmail(TaskEmail):
    def __init__(self, user, shifts):
        from . import params_manager

        str_date_time = get_timestamp()

        body = "\n".join(shifts)

        email = user.email
        subject = f'{labels.get("your_shifts_subject")} {str_date_time}'
        content = render_template("email/your_shifts_email.txt",
            name = user.name,
            body = body,
            app_url = params_manager.external_url
        )

        super().__init__(
            receiver_emails = [email],
            subject = subject,
            content = content
        )