#!/bin/bash

file="/var/www/html/MODIS_Quytrinh/GroundStation/MODIS_CALL.log"
arguments=$(cat "$file")
#echo $arguments
command="php /var/www/html/MODIS_Quytrinh/groundstation.php "
log=" >> /var/www/html/MODIS_Quytrinh/GroundStation/out.log"
full_command=$command$arguments$log
#/bin/echo $full_command
$full_command
sleep 600
# remove file
#remv="rm -fr "
#comm=$remv$file
#eval $comm
