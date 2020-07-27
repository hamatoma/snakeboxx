# Creation of a Script for Cloning and Update

Be root and copy the following text into a terminal. This will create the script SnakeBoxx which inititializes and/or updates the package.
~~~
FN=/usr/local/bin/SnakeBoxx
cat <<'EOS' >$FN
URL=https://github.com/hamatoma/snakeboxx.git
BASE=/usr/share
if [ $(id -u) != 0 ]; then
  echo "be root!"
else
  cd $BASE
  if [ -d snakeboxx ]; then
    cd snakeboxx
    git pull $URL
  else
    git clone $URL
    cd snakeboxx
    bash snake_install.sh DirApp
    bash snake_install.sh TextApp
    bash snake_install.sh OperatingSystemApp
  fi
fi
EOS
chmod uog+rwx $FN
$FN
~~~