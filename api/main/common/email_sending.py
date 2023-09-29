from flask_mail import Message
from threading import Thread
from api.main import mail
from flask import current_app, render_template


def send_async_email(context, msg):
    context.push()
    mail.send(msg)


def send_mail(subject, recipients, template, **kwargs):
    msg = Message(
        subject=subject,
        sender=current_app.config["FLASK_MAIL_SENDER"],
        recipients=recipients,
    )
    msg.body = render_template(template + ".txt", **kwargs)
    th = Thread(target=send_async_email, args=(current_app.app_context(), msg))
    th.start()
    return "sent"
