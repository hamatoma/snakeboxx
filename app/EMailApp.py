#! /usr/bin/python3
'''
Created: 2020.06.24
@license: CC0 https://creativecommons.org/publicdomain/zero/1.0
@author: hm
'''
import sys
import os
import snakeboxx

import base.StringUtils
import base.JobController
import net.EMail
import app.BaseApp


class EmailJobController(base.JobController.JobController):
    '''Executes email tasks.
    '''

    def __init__(self, emailApp, jobDirectory, cleanInterval):
        '''Constructor.
        @param emailApp: the parent process
        @param jobDirectory: the directory hosting the job files
        @param cleanInterval: files older than this amount of seconds will be deleted
        '''
        base.JobController.JobController.__init__(
            self, jobDirectory, cleanInterval, emailApp._logger)
        self._emailApp = emailApp

    def process(self, name, args):
        '''Processes a job found in a job file.
        @param name: the job name, e.g. 'send'
        @param args: the job arguments, e.g. ['a@bc.de', 'subject', 'body']
        @return: True: success
        '''
        rc = self._emailApp.process(name, args)
        return rc


class EMailApp(app.BaseApp.BaseApp):
    '''Sends an email.
    '''

    def __init__(self, args):
        '''Constructor.
        @param args: the program arguments, e.g. ['test', 'a@bc.de']
        '''
        app.BaseApp.BaseApp.__init__(self, 'EMailApp', args, True)
        self._daemonJobController = None

    def buildConfig(self):
        '''Creates an useful configuration example.
        '''
        content = '''# created by EMailApp
smtp.host=smtp.gmx.de
smtp.port=587
smtp.user=hm.neutral@gmx.de
smtp.code=TopSecret
smtp.with.tls=True
sender=hm.neutral@gmx.de
# jobs should be written to this dir:
job.directory=/tmp/emailboxx/jobs
# files older than this amount of seconds will be deleted (in job.directory):
job.clean.interval=3600
'''
        self.buildStandardConfig(content)

    def buildUsage(self):
        '''Builds the usage message.
        '''
        self._usageInfo.appendDescription('''APP-NAME <global-opts> <mode> [<opts>]
 Offers email services.
''')
        self._usageInfo.addMode('send', '''send [<opts>] <recipient <subject> <body>
 <recipent>: the email address of the receipient. Separate more than one with '+'
 <subject>: the text of the subject field
 <body>: the body of the email or (if preceeded by '@' a filename with the body.
''', '''APP-NAME send --carbon-copy=jonny@x.de eva@x.com+adam@x.fr "Greetings" "Hi guys"
APP-NAME send --blind-carbon-copy=jonny@x.de+joe@x.de eva@x.com+adam@x.fr "Greetings" @birthday.html
''')

    def buildUsageOptions(self, mode=None):
        '''Adds the options for a given mode.
        @param mode: None or the mode for which the option is added
        '''
        def add(mode, opt):
            self._usageInfo.addModeOption(mode, opt)

        if mode is None:
            mode = self._mainMode
        if mode == 'send':
            add(mode, base.UsageInfo.Option('carbon-copy', 'c',
                                            'additional recipient(s) seen by all recipients. Separate more than one with "+"'))
            add(mode, base.UsageInfo.Option('blind-carbon-copy', 'b',
                                            'additional recipient(s) not seen by all recipients. Separate more than one with "+"'))

    def daemonAction(self, reloadRequest):
        '''Does the real thing in the daemon (= service).
        @param reloadRequest: True: a reload request has been done
        '''
        if reloadRequest or self._daemonJobController is None:
            jobDir = self._configuration.getString('job.directory')
            cleanInterval = self._configuration.getInt('job.clean.interval')
            self._daemonJobController = EmailJobController(
                self, jobDir, cleanInterval)
        self._daemonJobController.check()

    def install(self):
        '''Installs the application and the related service.
        '''
        app.BaseApp.BaseApp.install(self)
        self.createSystemDScript(
            'emailboxx', 'emailboxx', 'emailboxx', 'emailboxx', 'Offers an email send service')
        self.installAsService('emailboxx', True)

    def process(self, name, args):
        '''Processes a job found in a job file.
        @param name: the job name, e.g. 'send'
        @param args: the job arguments, e.g. ['a@bc.de', 'subject', 'body']
        @return: True: success
        '''
        rc = False
        if name == 'send':
            args2 = []
            options = []
            for arg in args:
                if arg.startwith('-'):
                    options.append(arg)
                else:
                    args2.append(arg)
            self.send(args2, options)
            rc = True
        elif name == 'test':
            recipient = 'test@hamatoma.de' if not args else args[0]
            self._logger.log('job "test" recogniced: ' +
                             ' '.join(args), base.Const.LEVEL_SUMMARY)
            host = self._configuration.getString('smtp.host')
            sender = self._configuration.getString('smtp.sender')
            port = self._configuration.getInt('smtp.port')
            user = self._configuration.getString('smtp.user')
            sender = self._configuration.getString('smtp.sender', user)
            code = self._configuration.getString('smtp.code')
            withTls = self._configuration.getBool('smtp.with.tls')
            net.EMail.sendSimpleEMail(recipient, 'Test EMailApp Daemon', 'it works', sender, host,
                                      port, user, code, withTls, self._logger)
            rc = True
        else:
            self._logger.error()
        return rc

    def run(self):
        '''Implements the tasks of the application
        '''
        if self._mainMode == 'send':
            self.send()
        elif self._mainMode == 'daemon':
            self.daemon()
        else:
            self.abort('unknown mode: ' + self._mainMode)

    def send(self, args=None, options=None):
        '''Sends an email.
        '''
        cc = []
        bcc = []
        if args is None:
            args = self._programArguments
        if options is None:
            options = self._programOptions
        stopped = False
        for opt in options:
            if opt.startswith('--cc='):
                cc.append(opt[5:])
            elif opt.startswith('-c'):
                cc.append(opt[2:])
            elif opt.startswith('--bcc='):
                bcc.append(opt[6:])
            elif opt.startswith('-b'):
                bcc.append(opt[2:])
            else:
                self.abort('unknown option: ' + opt)
                stopped = True
                break
        cc = None if not cc else '+'.join(cc)
        bcc = None if not bcc else '+'.join(bcc)
        if not stopped:
            if len(args) < 3:
                self.abort('too few arguments')
            else:
                receipient = args[0]
                subject = args[1]
                body = args[2]
                if body.startswith('@'):
                    fn = body[1:]
                    if not os.path.exists(fn):
                        self.abort('body file not found: ' + fn)
                        stopped = True
                    else:
                        body = base.StringUtils.fromFile(body)
                if not stopped:
                    isHtml = body.startswith('<')
                    if isHtml:
                        text = None
                        html = body
                    else:
                        text = body
                        html = None
                    email = net.EMail.EMail(subject, text, html)
                    host = self._configuration.getString('smtp.host')
                    port = self._configuration.getInt('smtp.port')
                    username = self._configuration.getString('smtp.user')
                    code = self._configuration.getString('smtp.code')
                    withTls = self._configuration.getBool('smtp.with.tls')
                    sender = self._configuration.getString('sender', username)
                    if host is None or port is None or username is None or code is None:
                        self.abort('missing email configuration')
                    else:
                        email.setSmtpLogin(
                            host, port, username, code, withTls, sender)
                        email.sendTo(receipient, cc, bcc, self._logger)


def main(args):
    '''Main function.
    @param args: the program arguments
    '''
    snakeboxx.startApplication()
    application = EMailApp(args)
    application.main()


if __name__ == '__main__':
    main(sys.argv[1:])
