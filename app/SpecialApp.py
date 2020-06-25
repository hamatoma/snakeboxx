#! /usr/bin/python3
'''
Created: 2020.06.24
@license: CC0 https://creativecommons.org/publicdomain/zero/1.0
@author: hm
'''
import sys
import os.path

sys.path.insert(0, '/usr/share/snakeboxx')
import base.FileHelper
import app.BaseApp


class SpecialApp(app.BaseApp.BaseApp):
    '''Special task solver.
    '''

    def __init__(self, args):
        '''Constructor.
        @param args: the program arguments, e.g. ['test', 'a@bc.de']
        '''
        app.BaseApp.BaseApp.__init__(
            self, 'SpecialApp', args, None, 'specboxx')
        self._hostname = None

    def buildConfig(self):
        '''Creates an useful configuration example.
        '''
        content = '''# created by SpecialApp
logfile=/var/log/local/specboxx.log
'''
        self.buildStandardConfig(content)

    def buildUsage(self):
        '''Builds the usage message.
        '''
        self._usageInfo.appendDescription('''APP-NAME <global-opts> <mode> [<opts>]
 Convert file(s) into other.
''')
        self._usageInfo.addMode('init-project', '''init-project <project>
 Initializes a PHP project using "skeleton".
 <project>: the project name
 ''', '''APP-NAME init-project webmonitor
''')

    def initProject(self):
        '''Initializes a PHP project using "skeleton".
        '''
        projName = self.shiftProgramArgument()
        if projName is None:
            self.argumentError('missing <project>')
        elif not os.path.isdir('skeleton'):
            self.argumentError(
                'project "skeleton" must be in the current directory')
        elif os.path.isdir(projName):
            self.argumentError('project "{}" already exists'.format(projName))
        else:
            fnFileStructure = 'skeleton/tools/templates/project.structure.txt'
            if not os.path.exists(fnFileStructure):
                self.abort('missing ' + fnFileStructure)
            base.FileHelper.setLogger(self._logger)
            structure = base.StringUtils.fromFile(
                fnFileStructure).replace('${proj}', projName).split('\n')
            base.FileHelper.copyByRules(structure, 'skeleton', projName)
            msg = '''# run as root:
cat <<EOS >/etc/pyrshell/webapps.d/PROJ.dev.conf
db=appPROJ
user=PROJ
password=PROJ4PROJ
sql.file=PROJ_appPROJ
directory=/home/ws/php/PROJ
excluded=
EOS
#
dbtool create-db-and-user appPROJ PROJ PROJ4PROJ
grep PROJ.dev /etc/hosts || echo >>/etc/hosts "127.0.0.10 PROJ.dev"
FN=/etc/nginx/sites-available/PROJ.dev
perl -p -e 's/%project%/PROJ/g;' skeleton/tools/templates/nginx.project.dev > $FN
ln -s "../sites-available/PROJ.dev" /etc/nginx/sites-enabled/PROJ.dev
head $FN
dbtool import-webapp PROJ.dev skeleton/tools/templates/empty_db.sql.gz
'''.replace('PROJ', projName)
            print(msg)

    def run(self):
        '''Implements the tasks of the application
        '''
        self._hostname = self._configuration.getString('hostname', '<host>')
        if self._mainMode == 'init-project':
            self.initProject()
        else:
            self.abort('unknown mode: ' + self._mainMode)


def main(args):
    '''Main function.
    @param args: the program arguments
    '''
    application = SpecialApp(args)
    application.main()


if __name__ == '__main__':
    main(sys.argv[1:])
