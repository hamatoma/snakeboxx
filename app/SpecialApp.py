#! /usr/bin/python3
'''
Created: 2020.06.24
@license: CC0 https://creativecommons.org/publicdomain/zero/1.0
@author: hm
'''
import sys
import os.path
import snakeboxx

import base.FileHelper
import app.BaseApp


class GeoAtBuilder:
    '''Builds the import file for the table geo with Austrian data.
    Glossar:
    NUTS: Nomenclature des unités territoriales statistiques
        Hierarchical structure of "political regions" with 3 Levels
    '''

    def __init__(self, logger):
        '''Constructor.
        @param logger: for logging
        '''
        self._logger = logger
        #
        self._fnGemeinden = 'gemliste_knz.csv'
        self._fnLaender = 'nuts_3.csv'
        self._fnPolitischeBezirke = 'polbezirke.csv'
        # id -> name, e.g. "1" -> "Burgenland"
        self._mapLand = {}
        # id => name, e.g. "101" -> "Eisenstadt(Stadt)"
        self._mapPolitischerBezirk = {}
        # gemeindenr (ags) => name, e.g. 10512 => 'Südburgenland'
        self._mapTeilland = {}
        # name => NUTS-3, e.g. "Nordburgenland" => "AT112"
        self._mapNutsTeilland = {}
        # ags => name, e.g. 10512 => 'Mühlgraben'
        self._mapGemeinde = {}

    def readNuts(self):
        '''Creates the maps _mapLand and _mapPolitischerBezierk from _fnPolitischeBezirke and _mapTeilland from _fnLaender
        '''
        with open(self._fnLaender, 'r') as fp:
            lineNo = 0
            expected = 'NUTS 3-Code;NUTS 3- Name;LAU 2 - Code Gemeinde- kennziffer'
            for line in fp:
                lineNo += 1
                if lineNo == 3 and not line.startswith(expected):
                    msg = 'wrong file format:\n{}\nexpected:\n{}'.format(
                        line, expected)
                    self._logger.error(msg)
                    raise ValueError(msg)
                if lineNo < 4:
                    continue
                if line.startswith(';;;') or line.startswith('Q: STATISTIK AUSTRIA'):
                    continue
                # NUTS 3-Code;NUTS 3-
                # Name;Gemeindekennziffer;Gemeindename;Fläche;Bevölkerungszahl
                cols = line.strip().split(';')
                if len(cols) < 5:
                    self._logger.error('unknown input: ' + line)
                    continue
                ags = int(cols[2])
                self._mapTeilland[ags] = cols[1]
                self._mapGemeinde[ags] = cols[3]
                self._mapNutsTeilland[cols[1]] = cols[0]
        with open(self._fnPolitischeBezirke, 'r') as fp:
            lineNo = 0
            expected = 'Bundeslandkennziffer;Bundesland;Kennziffer pol. Bezirk'
            for line in fp:
                lineNo += 1
                if lineNo == 3 and not line.startswith(expected):
                    msg = 'wrong file format:\n{}\nexpected:\n{}'.format(
                        line, expected)
                    self._logger.error(msg)
                    raise ValueError(msg)
                if lineNo < 4:
                    continue
                cols = line.strip().split(';')
                if len(cols) < 5:
                    if not line.startswith('Quelle: STATISTIK AUSTRIA'):
                        self._logger.error('unknown input: ' + line)
                else:
                    idPolitischerBezirk = int(cols[4])
                    self._mapPolitischerBezirk[idPolitischerBezirk] = cols[3]
                    if cols[2] != cols[4]:
                        self._logger.log('different codes: {} {} {}'.format(
                            cols[2], cols[4], cols[3]))
            self._logger.log(
                'Land: {} Teilland: {} Pol. Bezirk: {}'.format(len(self._mapLand.keys()),
                                                               len(self._mapTeilland.keys(
                                                               )),
                                                               len(self._mapPolitischerBezirk.keys())))

    def createGeoAt(self):
        '''Creates the geo_at.csv from _fnGemeinden
        '''
        with open('geo_at.sql', 'w') as fpOut, open(self._fnGemeinden, 'r') as fpIn:
            fpOut.write('''insert into geo (geo_id,geo_staat,geo_land,geo_landnuts,geo_bezirk,geo_bezirknuts,geo_kreis,
  geo_kreisnuts,geo_gemeinde,geo_ort,geo_gemeindeags,geo_plz) VALUES
''')
            lineNo = 0
            written = 0
            for line in fpIn:
                lineNo += 1
                if lineNo == 3 and not line.startswith('Gemeindekennziffer;Gemeindename;'):
                    self._logger.error(
                        'missing Gemeindekennziffer;Gemeindename: ' + line)
                    raise ValueError(
                        'wrong file format: ' + self._fnGemeinden)
                if lineNo < 4:
                    continue
                # Gemeindekennziffer;Gemeindename;Gemeindecode;Status;PLZ
                # desGem.Amtes;weitere Postleitzahlen
                cols = line.strip().split(';')
                if len(cols) < 6:
                    if not line.startswith('Quelle: STATISTIK AUSTRIA'):
                        self._logger.error('unknown input: ' + line)
                else:
                    ags = int(cols[2])
                    # NUTS level 2: "Bundesland"
                    idLand = ags // 10000
                    id2Land = 1200 + idLand
                    # NUTS level 3: Teilland"
                    teillandName = self._mapTeilland[ags] if ags in self._mapTeilland else ''
                    if teillandName == '':
                        if ags in [61060, 61061]:
                            teillandName = self._mapTeilland[61059]
                        elif ags >= 90001:
                            teillandName = self._mapTeilland[90001]
                        else:
                            self._logger.error(
                                f'missing teilland in map: {ags}')
                    nutsTeilland = self._mapNutsTeilland[teillandName] if teillandName in self._mapNutsTeilland else ''
                    # Kreis: politischer Bezirk
                    idPolitischerBezirk = ags // 100
                    namePolitischerBezirk = (self._mapPolitischerBezirk[idPolitischerBezirk]
                                             if idPolitischerBezirk in self._mapPolitischerBezirk else '')
                    if namePolitischerBezirk == '':
                        self._logger.error(
                            f'missing PolitischerBezirk for {idPolitischerBezirk}')
                    info1 = (f",'at',{id2Land},'AT{idLand}','{teillandName}','{nutsTeilland}',"
                             + f"'{namePolitischerBezirk}','{idPolitischerBezirk}','{cols[1]}','{cols[1]}',{ags},")
                    info = info1 + f'{cols[4]})'
                    primary = 20000001 + ags * 100
                    written += 1
                    if written > 1:
                        fpOut.write(',\n')
                    fpOut.write('(' + str(primary) + info)
                    for aZip in cols[5].split(' '):
                        if aZip == '':
                            continue
                        primary += 1
                        written += 1
                        fpOut.write(',\n(' + str(primary) + info1 + aZip + ')')
            fpOut.write('\n;')
            self._logger.log(f'written: geo_at.sql: {written} recs')
        fn = 'ImportGeo.sh'
        base.StringUtils.toFile(fn, '''#! /bin/bash
if [ "$3" = "" ]; then
  echo "Usage: ImportGeo.sh DB USER DB
  echo "Example: ImportGeo.sh appcovidmars covidmars TopSecret"
else
  test geo.csf && rm geo.csv
  ln -s geo_at.csv geo.csv
  mysqlimport --ignore-lines=1 --fields-terminated-by=, --local \
  --columns=geo_id,geo_staat,geo_land,geo_bezirk,geo_kreis,geo_gemeindeags,geo_gemeinde,geo_plz \
  -u $2 "-p$3" $1  geo.csv
fi
''', fileMode=0o777)
        self._logger.log('written: {} usage: {} DB USER PW'.format(fn, fn))

    def check(self):
        '''Checks the preconditions.
        @return: True: success
        '''
        rc = True
        if not os.path.exists(self._fnGemeinden):
            rc = self._logger.error('missing file ' + self._fnGemeinden)
        if not os.path.exists(self._fnLaender):
            rc = self._logger.error('missing file ' + self._fnLaender)
        if not os.path.exists(self._fnPolitischeBezirke):
            rc = self._logger.error(
                'missing file ' + self._fnPolitischeBezirke)
        return rc

    def buildImport(self):
        '''Builds the CSV file for importing the geo data.
        '''
        if self.check():
            self.readNuts()
            self.createGeoAt()


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
        self._usageInfo.addMode('geo-at', '''geo-at
 Builds the geodb data of Austria
 ''', '''APP-NAME geo-at
''')

    def geoAt(self):
        '''Builds an import file for the db table geo with Austrian data.
        '''
        builder = GeoAtBuilder(self._logger)
        builder.buildImport()

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
        elif self._mainMode == 'geo-at':
            self.geoAt()
        else:
            self.abort('unknown mode: ' + self._mainMode)


def main(args):
    '''Main function.
    @param args: the program arguments
    '''
    snakeboxx.startApplication()
    application = SpecialApp(args)
    application.main()


if __name__ == '__main__':
    main(sys.argv[1:])
