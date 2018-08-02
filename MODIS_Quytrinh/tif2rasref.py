import os
import sys

# def cong(a,b):
#     return a+b
# 
# c=cong(a,b)

def rasterToSql(raster_file):
    #temp_command = "/usr/pgsql-9.4/bin/raster2pgsql -a -f rasref -F {0} apom.satresampmod07temperature_daily"
    temp_command = "/usr/bin/raster2pgsql -a -f rasref -F {0} apom.satresampmod07temperature_daily"
    temp3_script=os.popen(temp_command.format(raster_file)).read()
    first_index = temp3_script.find("('")
    last_index = temp3_script.find("':")
    temp3_ref=temp3_script[first_index+2:last_index]
    return temp3_ref
raster_ref = rasterToSql(raster_file)