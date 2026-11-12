import logging
import smtplib
import os
from dotenv import load_dotenv
from email.message import EmailMessage

logger = logging.getLogger(__name__)
load_dotenv()

#push for email testing
class EmailSender:
    """Sends plain-text emails through an SMTP server (Gmail by default).

    send() never raises: it returns True if the server accepted the email
    and False otherwise, and logs the reason.
    """

    def __init__(self, sender_address, app_password,
                 host="smtp.gmail.com", port=465):
        self.__sender_address = sender_address
        self.__app_password = app_password
        self.__host = host
        self.__port = port

    def is_configured(self):
        return bool(self.__sender_address and self.__app_password)

    def send(self, to_address, subject, body):
        """Send one email. Returns True on success, False on failure."""
        if not self.is_configured():
            logger.error("Email is not set up: EMAIL_ADDRESS or "
                         "EMAIL_APP_PASSWORD is missing.")
            return False

        try:
            message = EmailMessage()
            message["From"] = self.__sender_address
            message["To"] = to_address
            message["Subject"] = subject
            message.set_content(body)

            with smtplib.SMTP_SSL(self.__host, self.__port, timeout=15) as server:
                server.login(self.__sender_address, self.__app_password)
                server.send_message(message)
            return True
        except (smtplib.SMTPException, OSError, ValueError) as error:
            logger.error("Could not send email to %s: %s", to_address, error)
            return False



sender = EmailSender(os.environ.get("EMAIL_ADDRESS"), os.environ.get("EMAIL_APP_PASSWORD"))
print(sender.send("kshent.sgs@gmail.com", "Test", "hello this is a test email from team8-project"))