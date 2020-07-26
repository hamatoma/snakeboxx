#! /bin/bash
FN=/usr/lib/python3/dist-packages/snakeboxx.py

function First(){
  if [ ! -f $FN ]; then
    cat >$FN <<EOS
'''Prepare for usage of snakeboxx modules.
'''
import sys
if '/usr/share/snakeboxx' not in sys.path:
    sys.path.insert(0, '/usr/share/snakeboxx')
if '/usr/share/pyrshell' in sys.path:
    sys.path.remove('/usr/share/pyrshell')
def startApplication():
    '''Starts the application.
    In this version: do nothing
    '''
EOS
    echo "created: $FN"
  fi
}
First
CLAZZ=$1
if [ -z "$CLAZZ" ]; then
  echo "usage: snake_install <class>"
  echo "example: snake_install DirApp"
elif [ ! -f app/$CLAZZ.py ]; then
  echo "not a class: $CLAZZ"
else
  python3 app/$CLAZZ.py -v4 install
fi
  