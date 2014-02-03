#!/bin/bash

# ggpofba wrapper script for version 0.2.96.74 (bundled with ggpo)
# (c)2013-2014 Pau Oliva Fora (@pof)

# This resets pulseaudio on Linux because otherwise FBA hangs on my computer (WTF!?).
# For best results run 'winecfg' and check the option to "Emulate a virtual desktop"
# under the Graphics tab. I've it set to 1152x672 for best full screen aspect ratio.


CONFIGFILE=~/.config/ggpo/ggpo.config
source ${CONFIGFILE}

if [ -z "${INSTALLDIR}" ]; then
	echo "-!- Please launch ggpo.py to create your config file"
	exit 1
fi

FBA="${INSTALLDIR}/ggpofba.exe"
if [ ! -e ${FBA} ]; then
	echo "-!- cannot find ${INSTALLDIR}/ggpofba.exe"
	exit 1
fi

OS=$(uname -s)
case "${OS}" in
	"Darwin")
		echo "-!- starting the real ggpofba"
		/Applications/Wine.app/Contents/Resources/bin/wine ${FBA} ${1+"$@"} &
	;;

	"Linux")
		# check if there are multiple instances running
		tot=$(ps ax |grep ggpofba.exe |grep quark |wc -l)

		# first instance resets pulseaudio, others don't
		if [ $tot -eq 0 ]; then
			VOL=$(pacmd dump |grep "^set-sink-volume" |tail -n 1 |awk '{print $3}')
			echo "-!- resetting pulseaudio"
			/usr/bin/pulseaudio -k
			/usr/bin/pulseaudio --start
		fi

		echo "-!- starting the real ggpofba"
		/usr/bin/wine ${FBA} ${1+"$@"} &

		if [ $tot -eq 0 ]; then
			sleep 1s
			echo "-!- restoring volume value"
			/usr/bin/pactl set-sink-volume 0 ${VOL}
		fi
	;;
esac
