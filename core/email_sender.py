import smtplib
from email.mime.text import MIMEText
from logger import logger

def send_report_email(recipients, text, config):
    ec = config.get('email', {})
    sender, pwd, srv = ec.get('from'), ec.get('password'), ec.get('smtp')
    port = ec.get('port',587); subj = ec.get('subject','Meeting Protocol')
    if not all([sender,pwd,srv]):
        logger.error('Email config incomplete')
        raise ValueError('Email settings missing')
    msg = MIMEText(text,'plain','utf-8')
    msg['Subject'], msg['From'], msg['To'] = subj, sender, ','.join(recipients)
    try:
        with smtplib.SMTP(srv, port) as s:
            s.starttls(); s.login(sender,pwd); s.sendmail(sender, recipients, msg.as_string())
        logger.info('Email sent')
    except Exception as e:
        logger.error(f'Failed to send email: {e}')
