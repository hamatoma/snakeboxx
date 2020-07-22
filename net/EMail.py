'''
Created: 2020.06.24
@license: CC0 https://creativecommons.org/publicdomain/zero/1.0
@author: hm
'''
import smtplib
import imghdr
#import email.message

import base.MemoryLogger
import base.StringUtils


class EMail:
    '''Simplifies sending of emails.
    '''

    def __init__(self, subject, text=None, html=None):
        '''Constructor.
        @param subject: the subject of the mail
        @param text: the ascii text of the mail
        @param html: the html text of the mail
        '''
        self._host = None
        self._port = None
        self._username = None
        self._code = None
        self._withTls = None
        self._sender = None
        self._subject = subject
        self._signature = ''
        self._text = text
        self._html = html
        self._multiPart = email.message.EmailMessage()
        if subject is not None:
            self._multiPart['Subject'] = subject
        if self._text is None:
            if self._html is None:
                self._multiPart.set_content('\n')
            else:
                self._multiPart.set_content(self._html, subtype='html')
        else:
            self._multiPart.set_content(self._text)
            if html is not None:
                self._multiPart.add_alternative(self._html, subtype='html')

    def addImage(self, filename):
        '''Adds a image file as attachement.
        @param filename: this file will be appended, should be MIME type "image"
        '''
        with open(filename, 'rb') as fp:
            img_data = fp.read()
            self._multiPart.add_attachment(
                img_data, maintype='image', subtype=imghdr.what(None, img_data))

    def lastSignature(self):
        '''Returns a string with all communication information.
        @return: the signature of the communication
        '''
        return self._signature

    def sendTo(self, recipient, cc=None, bcc=None, logger=None):
        '''
        Sends the email to the given recipients.
        @param sender: None or an email address of the sender
        @param recipient: the recipient or a list of recipients
        @param cc: None or carbon copy recipients separated by '+', e.g. 'a@b.c+x@y.z'
        @param bcc: None or blind carbon copy recipients separated by '+', e.g. 'a@b.c+x@y.z'
        @param logger: None or logger
        @return: dictionary: empty: success otherwise: e.g. { "three@three.org" : ( 550 ,"User unknown" ) }
        '''
        def normEmail(email1):
            rc = email1.strip(' ').replace('+', ', ')
            return rc
        self._signature = '{}|{}|{}|{}|{}|{}'.format(
            self._host, self._port, self._username, self._code, self._sender, recipient)
        rc = []
        try:
            server = smtplib.SMTP(self._host, self._port)
            server.ehlo()
            if self._withTls:
                server.starttls()
                server.ehlo()
            server.login(self._username, self._code)
            self._multiPart['From'] = self._sender
            self._multiPart['To'] = normEmail(recipient)
            if cc is not None:
                self._multiPart['Cc'] = normEmail(cc)
            if bcc is not None:
                self._multiPart['BCC'] = normEmail(bcc)
            rc = server.send_message(self._multiPart)
            if logger is not None:
                logger.log('email "{}" sent to {}'.format(
                    self._subject, recipient), base.Const.LEVEL_SUMMARY)
        except Exception as exc:
            if logger is not None:
                logger.error('sending email failed: {}\n{}\n{}'.format(
                    str(exc), self._subject, self._text))
        return rc

    def setSmtpLogin(self, host, port, username, code, withTls=True, sender=None):
        '''Sets the login data for the SMTP server.
        @param host: the SMTP server, e.g. 'smtp.gmx.net'
        @param port: the port of the SMTP service
        @param username: the user known to the SMTP service
        @param code: the password of the SMTP service
        @param withTls: True: TSL encryption will be used
        '''
        self._host = host
        self._port = port
        self._username = username
        self._code = code
        self._withTls = withTls
        self._sender = sender if sender is not None else username


def sendSimpleEMail(recipients, subject, body, sender, host, port, user, code, withTls, logger):
    '''Sends an email.
    @param recipients: the email address of the recipients separated by '+', e.g. 'a@b.c+x@y.z'
    @param subject: a short info
    @param body: HTML or plain text
    @param sender: the email address of the sender
    @param host: the SMTP host
    @param port: the SMTP port
    @param user: the SMTP user
    @param code: the SMTP password
    @param withTls: True: TLS (encryption) is used
    @param logger: for error logging
    '''
    if body.startswith('<'):
        text, html = None, body
        html = body
    else:
        text, html = body, None
    email1 = EMail(subject, text, html)
    parts = recipients.split('+')
    email1.setSmtpLogin(host, port, user, code, withTls, sender)
    cc = None if len(parts) < 2 else '+'.join(parts[1:])
    rc = email1.sendTo(parts[0], cc, None, logger)
    if not rc:
        logger.log('email sent to ' + recipients, base.Const.LEVEL_SUMMARY)
    else:
        logger.error('sending email "{}" failed: {}'.format(subject, str(rc)))
    rc = email1.lastSignature()
    return rc


def main():
    '''Main function.
    '''
    logger = base.MemoryLogger.MemoryLogger(1)
    email1 = EMail('Testmail von Python', 'Hi!\nHat funktioniert', '''
<html>
<body>
<h1>Hi</h1>
<p>Hat funktioniert!</p
</body>
</html>
    ''')
    config = base.StringUtils.privateConfig()
    code = config.getString('EMailTest.code.hm.neutral')
    user = 'hm.neutral@gmx.de'
    email1.setSmtpLogin('smtp.gmx.de', 587, user, code, True, user)
    email1.sendTo('wk64@gmx.de', None, None, logger)
    signature = email1.lastSignature()
    print(signature)


if __name__ == '__main__':
    main()
