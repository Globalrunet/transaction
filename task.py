import time
from celery import shared_task
from django.core.mail import EmailMessage
from celery.exceptions import Retry

SIMULATE_FAILURE = True

@shared_task(bind=True, max_retries=3)
def message_notification_api_call(self, txid):

    should_fail_simulation = SIMULATE_FAILURE and self.request.retries < self.max_retries

    try:
        send_notification_mail()
        time.sleep(5)

        if should_fail_simulation:
            raise self.retry(countdown=3)

        return {"status": "Success", "result": f"Operation completed after {self.request.retries} retries."}

    except Exception as e:
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=3)
        else:
            raise


def send_notification_mail():
    recipient_email = "globalrunet@gmail.com"
    from_email = "globalrunet@yandex.ru"
    subject = "Notification"
    html_content = "html_body <h1>Hello!</h1><p>This is HTML content.</p>"

    try:
        email = EmailMessage(
            subject=subject,
            body=html_content,
            from_email=from_email,
            to=[recipient_email]
        )

        email.content_subtype = 'html'
        email.send()

    except Exception:
        pass