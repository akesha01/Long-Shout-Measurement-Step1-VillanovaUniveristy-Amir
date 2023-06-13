#!/bin/bash


ORCHNAME="orch"

EMUBOOT=/var/emulab/boot
EMUSAVE=/var/emulab/save
REPODIR=/local/repository
SHOUTSRC=/local/repository/shout
CLILOG=/var/tmp/controller.log

# Install dependencies for GRC
REQUIRED_PKG="python3-gi"
PKG_OK=$(dpkg-query -W --showformat='${Status}\n' $REQUIRED_PKG|grep "install ok installed")
echo Checking for $REQUIRED_PKG: $PKG_OK
if [ "" = "$PKG_OK" ]; then
  echo "No $REQUIRED_PKG. Setting up $REQUIRED_PKG."
  sudo apt-get update
  sudo apt -y install python3-gi gobject-introspection gir1.2-gtk-3.0
fi
pip3 install scipy

cd $REPODIR
#git submodule update --init --remote || { echo "Failed to update git submodules!" && exit 1; }

cd $EMUSAVE
sudo ntpdate -u ops.emulab.net && \
    sudo ntpdate -u ops.emulab.net || \
	echo "Failed to update clock via NTP!"  &> ntpdate.txt  

sudo rm $CLILOG

ORCHDOM=`$REPODIR/bin/getexpdom.py`
ORCHHOST="$ORCHNAME.$ORCHDOM"
echo "$ORCHHOST"
$SHOUTSRC/meascli.py -s $ORCHHOST #--useoffset

exit 0
