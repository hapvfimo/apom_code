# TODO: create PM image from aod and temp (PM regression)
# 
# Author: phamha
###############################################################################

#import library
library(gstat)
library(base)
library(RPostgreSQL)
library(stringr)
library(raster)
library(gdalUtils)
library(rgdal)
library(automap)
#library(rPython)


# host_name = '118.70.72.13'
# database_name = 'apom'
# user_name = 'postgres'
# password = 'fimopostgre54321'
# port = '8100'

host_name = '192.168.0.61'
database_name = 'apom'
user_name = 'postgres'
password = 'fimopostgre54321'
port = '5432'

host_local = 'localhost'
database_local = 'apom'
user_local = 'postgres'
pass_local = '1234'
port_local = '5432'


data_ratio = 1

mean_aod_mod = 0.366114584
abs_aod_mod = 1.029983261
mean_aod_myd = 0.410938839
abs_aod_myd = 1.098215224

mean_avg_temp_mod = 28.58782188
abs_avg_temp_mod = 12.02451107
mean_avg_temp_myd = 28.63081177
abs_avg_temp_myd = 12.06750096


min_aod_mod = 0.0015
max_aod_mod = 1.165031427
min_temp_mod = 291.8899935
max_temp_mod = 317.5399929

min_aod_myd = 0.057872928
max_aod_myd = 1.509154063
min_temp_myd = 281.2699937
max_temp_myd = 316.6299929

data_folder ="/home/apom/"
res_folder_mod = "res/SatResampMOD04"
res_folder_myd = "res/SatResampMYD04"

prod_folder_mod = "prod/ProdMODPM"
prod_folder_myd = "prod/ProdMYDPM"

met_folder = "/var/www/html/MODIS_Quytrinh/MetTiff/"
## myd_folder = "/var/www/html/fimo/apom/Product/ProdMYDPM/"
## mod_folder = "/var/www/html/fimo/apom/Product/ProdMODPM/"
shape_file = "/var/www/html/MODIS_Quytrinh/BDNEN/VNM_adm0.shp"
tif2raster_file = "/var/www/html/MODIS_Quytrinh/tif2rasref.py"
raster2sql_file = "/var/www/html/MODIS_Quytrinh/a.sql"
create_aqi_file = "/var/www/html/MODIS_Quytrinh/MODIS_CLIP_PM_AQI.py" 
create_png_file = "/var/www/html/MODIS_Quytrinh/create_png.py"
create_aot_file = "/var/www/html/MODIS_Quytrinh/aot_processing.py"


get_time_query = "select aqstime from %s where filename like "

#insert_mod_query = "INSERT INTO prodpm.prodmodispm_vn_collection0(aqstime, rasref, filename, filepath, gridid,pmid,max,min,avg, type,sourceid) VALUES ('"
update_query = "UPDATE %s SET  aqstime='%s'::timestamp, rasref='%s'::raster,filename='%s', filepath='%s', gridid =%s,pmid=%s,max=%s,min=%s,avg=%s,type=%s,sourceid=%s WHERE filename='%s';"

insert_query ="INSERT INTO %s (aqstime, rasref, filename, filepath, gridid,pmid,max,min,avg, type,sourceid) SELECT '%s'::timestamp, '%s'::raster, '%s', '%s', %s, %s,%s,%s,%s,%s,%s WHERE NOT EXISTS (SELECT 1 FROM %s WHERE filename='%s')"



regress_predict = function(sate_data,aod,avg_temp){
	if(sate_data=="mod"){
		pm25 = 21.44446906 * aod + (-26.98361769)*avg_temp + 25.28728856
	}else{
		pm25 = 27.4005404 * aod + (-18.90869037)*avg_temp + 18.99322277
	}
	
	return(pm25)
}

#get data from DB
getDataFromDB = function(sql_command){
	driver = dbDriver("PostgreSQL")
	connect = dbConnect(driver,dbname = database_name,host = host_name,port=port,user = user_name,password= password)
	rs = dbSendQuery(connect,sql_command)
	data=fetch(rs,n=-1)
	dbDisconnect(connect)
	dbUnloadDriver(driver)
	return (data)
}
insertDataToDB = function(sql_command){
	driver = dbDriver("PostgreSQL")
	connect = dbConnect(driver,dbname = database_name,host = host_name,port=port,user = user_name,password= password)
	rs = dbSendQuery(connect,sql_command)
	dbDisconnect(connect)
	dbUnloadDriver(driver)
}
insertDataToDB_local= function(sql_command){
	driver = dbDriver("PostgreSQL")
	connect = dbConnect(driver,dbname = database_local,host = host_local,port=port_local,user = user_local,password= pass_local)
	rs = dbSendQuery(connect,sql_command)
	dbDisconnect(connect)
	dbUnloadDriver(driver)
}


createKrigingImage = function(regressPm_file){
	
	regressPm_mask_file = str_replace(regressPm_file,".tif","_mask.tif")
	file.copy(regressPm_file,regressPm_mask_file)
	gdal_rasterize(shape_file,regressPm_mask_file,b=1,i=TRUE,burn=-9999,l="VNM_adm0")
	
	#PM values
	pmRaster=raster(regressPm_mask_file)
	pm=values(pmRaster)
	corxy=coordinates(pmRaster)
	x=corxy[,'x']
	y=corxy[,'y']
	
	
	totalCell=length(pmRaster)
	cell = c(1:totalCell)
	
	table=data.frame(cell,x,y,pm)
	newTable=table
	#testTable=subset(table,pm<0)
	#trainTable=subset(table,pm>=0)
	trainTable=subset(table,!is.na(pm)&pm!=-9999)
	testTable=subset(table,is.na(pm))
	
	auto_trainTable = trainTable
	coordinates(auto_trainTable) =~ x+y
	
	auto_variogram = autofitVariogram(pm~1,auto_trainTable)
	auto_model = auto_variogram$var_model$model[2]
	auto_sill = auto_variogram$var_model$psill[2]
	auto_range = auto_variogram$var_model$range[2]
	
	#caculate variogram
	empiVario=variogram(pm~1,locations=~x+y,data=trainTable)
	
	sphModel=vgm(psill=auto_sill,model=auto_model,nugget=0,range=auto_range)		
	sphFit=fit.variogram(empiVario,sphModel)
	
	#sph fit
	#sill=min(empiVario$gamma)
	#sphModel=vgm(psill=sill,model="Sph",nugget=0,range=min(empiVario$dist))
	#sphModel=vgm(model="Sph",nugget=0,range=1)		
	#sphFit=fit.variogram(empiVario,sphModel)
	
	universal_result=krige(id="pm",formula=pm~x+y,data=trainTable,newdata=testTable,model=sphFit,locations=~x+y)
	
	#edit tiff
	newTable$pm[is.na(newTable$pm)] = universal_result[,3]
	universalPMRaster=pmRaster
	universalPMRaster[1:totalCell]=newTable$pm
	#universalPMValue=universal_result[,3]
	#universalPMRaster[1:totalCell]=universalPMValue
	
	
	#edit error tiff
	#errorPMRaster=pmRaster
	#errorPMValue=universal_result[,4]
	#errorPMRaster[1:totalCell]=errorPMValue
	
	#save uk result to tiff
	uk_file = str_replace(regressPm_file,"rg.tif","uk.tif")
	writeRaster(universalPMRaster,filename=uk_file,format="GTiff",overwrite=TRUE)
	gdal_rasterize(shape_file,uk_file,b=1,i=TRUE,burn=-9999,l="VNM_adm0")
	
	#set n/a value
	new_uk_raster = raster(uk_file)
	new_uk_value = values(new_uk_raster)
	new_uk_value[new_uk_value==-9999]<-NA
	new_uk_value[new_uk_value<0]<-0
	new_uk_raster[1:totalCell] = new_uk_value

	writeRaster(new_uk_raster,filename=uk_file,format="GTiff",overwrite=TRUE)
	
	
	#save uk error to tiff
	#error_file = str_replace(regressPm_file,"rg.tif","error.tif")
	#writeRaster(errorPMRaster,filename=error_file,format="GTiff",overwrite=TRUE)
	#gdal_rasterize(shape_file,error_file,b=1,i=TRUE,burn=-9999,l="VNM_adm0")
	print(uk_file)
	
}
create_pm_image = function(sate_data,model_type,cook_type,aod_file,temp_file,source_id){
	print(aod_file)
	print(temp_file)
	if(sate_data=="mod"){
		type = 0
		time_query = sprintf(get_time_query, "res.satresampmod04")
		res_folder = res_folder_mod
		prod_folder = prod_folder_mod
		min_aod = mean_aod_mod
		max_aod = abs_aod_mod
		min_temp = mean_avg_temp_mod
		max_temp = abs_avg_temp_mod
		
	}else{
		type = 1
		time_query = sprintf(get_time_query, "res.satresampmyd04")
		res_folder = res_folder_myd
		prod_folder = prod_folder_myd
		min_aod = mean_aod_myd
		max_aod = abs_aod_myd
		min_temp = mean_avg_temp_myd
		max_temp = abs_avg_temp_myd
	}
	
	# get aqstime base on file name
	file_name = basename(aod_file)
	file_name = str_replace(file_name,".tif","")
	
	time_query = paste(time_query,"'",file_name,"%'",sep="")
	#print(time_query)
	data = getDataFromDB(time_query)
	
	mod04_aqstime = data$aqstime[1]
	aqstime = strptime(mod04_aqstime,format="%Y-%m-%d %H:%M:%S")
	aqstime = aqstime + 25200	
	
	month = format.Date(aqstime,"%m")
	year = format.Date(aqstime,"%Y")
	
	# crop aod file base on shap file
	aod_mask_file = str_replace(aod_file,".tif","_mask.tif")
	file.copy(aod_file,aod_mask_file)
		
	gdal_rasterize(shape_file,aod_mask_file,b=1,i=TRUE,burn=-9999,l="VNM_adm0")
	aod_dataset = raster(aod_mask_file)
	aod_dataset[aod_dataset[] == -9999] <- NA
	if(file.exists(aod_mask_file)){
		file.remove(aod_mask_file)
	} 
	
	aod_data = values(aod_dataset)
	aod_data = aod_data * 0.00100000004749745
		
	corxy = coordinates(aod_dataset)
	x = corxy[,'x']
	y = corxy[,'y']

	avg_temp_file  = paste(met_folder,"temp",as.numeric(month),".tif",sep="")
	avg_temp_dataset  =  raster(avg_temp_file)
	avg_temp_data  = values(avg_temp_dataset) 
	
	# chuan hoa aod va temp
	aod_data = (aod_data - min_aod)/max_aod
	avg_temp_data = (avg_temp_data - min_temp)/max_temp
		
	#hoi quy gia tri pm
	pm25 = regress_predict(sate_data,aod_data,avg_temp_data)
		
	# Remove out of range pixel
	table = data.frame(x,y,aod_data,avg_temp_data,pm25)
	table$pm25[table$aod_data< -1|table$aod_data>1|table$avg_temp_data< -1|table$avg_temp_data>1]<-NA
	
	total_pixel = sum(!is.na(table$pm25))
	ratio = total_pixel/2024*100
	print(paste("Pixel:",total_pixel,"Cloud ratio:",ratio,sep=" "))
		
	
	if(ratio>=data_ratio){
		# create regression image
		og_raster = aod_dataset
		totalCell = ncell(og_raster)
		og_raster[1:totalCell] = table$pm25
		
		# edit file name
		#mod04
		pm_file = str_replace(aod_file,".hdf_DT_10km","")
		#myd04
		pm_file = str_replace(pm_file,".hdf_DB_10km","")
		pm_file = str_replace(pm_file,".tif","_rg.tif")
		pm_file = str_replace(pm_file,res_folder,prod_folder)

		#create output path
		out_path = dirname(pm_file)
		dir.create(path=out_path,showWarnings = FALSE,recursive = TRUE,mod="777")
		
		writeRaster(og_raster,filename=pm_file,format="GTiff",overwrite=TRUE)
		#gdal_rasterize(shape_file,pm_file,b=1,i=TRUE,burn=-9999,l="VNM_adm0")
		
		
		print ("Create regression image good!");

		#create pm image
		createKrigingImage(pm_file)
		print ("Create Kriging image good!");
	
		uk_file = str_replace(pm_file,"rg.tif","uk.tif")
		#python.assign("raster_file",uk_file)
		#python.load(tif2raster_file)
		#raster_ref = python.get("raster_ref")
	
		
		allArgs = c("-a -f rasref -F",uk_file,"prod.prodmodpm")
		system2('raster2pgsql', args=allArgs,stdout=raster2sql_file,wait=TRUE)
		out = paste(readLines(raster2sql_file),collapse="\n")
		start_index = regexpr("[(]'",out)
		end_index = regexpr("'::raster",out)
		raster_ref = substr(out,start_index + 2,end_index - 1)
		#raster_ref = "01001"
		#print(raster_ref)

		
		uk_raster = raster(uk_file)
		uk_value = values(uk_raster)
		uk_value = uk_value[uk_value!=-9999]
		max_value = max(uk_value,na.rm = TRUE)
		min_value = min(uk_value,na.rm = TRUE)
		avg_value = mean(uk_value,na.rm = TRUE)
		gridid = 1
		pmid = 1
		
		
		
		#start_index = regexpr("apom/prod",uk_file)
		#mid_index = regexpr("M[^M]*$",uk_file)
		#end_index = nchar(uk_file)
		#uk_file_path = substr(uk_file,start_index,mid_index-1)
		#uk_file_name = substr(uk_file,mid_index,end_index)
		uk_file_name = basename(uk_file)
		uk_file_path = dirname(uk_file)
		uk_file_path = str_replace(uk_file_path,data_folder,"")
		
		
		aqstime2 = aqstime - 25200
		#query = paste(insert_mod_query,aqstime2,"'::timestamp, '",raster_ref,"'::raster, '",uk_file_name,"', '",uk_file_path,"', 1, 1, ",max_value,", ",min_value,", ",avg_value,", ",type,", ",source_id,")",sep="")

		update_mod_query = sprintf(update_query,"prodpm.prodmodispm_vn_collection0",toString(aqstime2),raster_ref,uk_file_name,uk_file_path,toString(gridid),toString(pmid),toString(max_value),toString(min_value),toString(avg_value),toString(type),toString(source_id),uk_file_name)
	
		insert_mod_query = sprintf(insert_query, "prodpm.prodmodispm_vn_collection0",toString(aqstime2),raster_ref,uk_file_name,uk_file_path,toString(gridid),toString(pmid),toString(max_value),toString(min_value),toString(avg_value),toString(type),toString(source_id),"prodpm.prodmodispm_vn_collection0",uk_file_name)
		
		query = paste(update_mod_query,insert_mod_query,sep="")
		#print(query)
		
		
		#insert pm images to database
		insertDataToDB(query)
		insertDataToDB_local(query)
		print ("Insert to database good!");
		
		#create png
		print ("Tao anh PNG - cua Ha");
		create_png_args = c(create_png_file,basename(uk_file),dirname(uk_file))
		png_out = system2('python', args=create_png_args,stdout=TRUE)
		#png_out = system2('python', args=create_png_args,stdout=TRUE)
		
		#python.load(create_png_file) # error here
		#python.call("CreatePM25PNGImg",basename(uk_file),dirname(uk_file))
		#print(png_out)

		#create aqi
		#print ("Den phan cua Chuc");
		#print ("Cat anh AQI");
		#python.assign("pmname",uk_file_name)
		#python.assign("sat_type",type) # sat_type is mod:0, myd:1
		#python.assign("sourceid",commandArgs(TRUE)[4]) # sourceid
		#python.load(create_aqi_file)
		
		#type = 0
		#sourceid = 0
		create_aqi_args = c(create_aqi_file,uk_file_name,type,source_id)
		system2('python', args=create_aqi_args,stdout=TRUE)
		#print(out)

		# cat anh AOT
		#print ("Cat anh AOT");
		#tifname = basename(commandArgs(TRUE)[2])
		#create_aot_args = c(create_aot_file,tifname,type,sourceid)
		#system2('python', args=create_aot_args,stdout=TRUE)
		#print ("Cat anh AOT");
		#python.assign("tifname", basename(commandArgs(TRUE)[2])) # load the MOD04/MYD04 filename
		#python.assign("sat_type",type) # sat_type is mod:0, myd:1	
		#python.assign("sourceid",commandArgs(TRUE)[4]) # sourceid
		
		#print(aod_file)
		#print(type)
		#print(source_id)
		#python.load(create_aot_file)
		#python.call("ExecuteAll", basename(aod_file), type, source_id)
		
		
		
	}
			
}


# Test example

#aod_file = "/apom_data/apom/res/SatResampMOD04/2015/MOD04_L2.A2015107.0310.051.2015107141007/MOD04_L2.A2015107.0310.051.2015107141007.hdf_DT_10km.tif"
#temp_file= "/apom_data/apom/res/SatResampMOD07/2015/MOD07_L2.A2015107.0310.006.2015107140511/MOD07_L2.A2015107.0310.006.2015107140511.hdf_T_10km.tif"

#aod_file = "/apom_data/apom/res/SatResampMOD04/2015/MOD04_L2.A2015107.0310.051.2015107141007/MOD04_L2.A2015107.0310.051.2015107141007.hdf_DT_10km.tif"
#temp_file =  "/apom_data/apom/res/SatResampMOD07/2015/MOD07_L2.A2015107.0310.006.2015107140511/MOD07_L2.A2015107.0310.006.2015107140511.hdf_T_10km.tif"

#source_id = 0
#sat_data = "mod"

# mod/myd , aot file, temp file
# Test command
# create_pm_image("mod","linear","4np",aod_file,temp_file, source_id)
# print("done")


# Real command
# command 1: type (mod/myd)
# command 2: mod04
# command 3: mod07
# command 4: sourceid (0: NASA, 1: UET)
# 

list = read.csv("/home/apom/Desktop/list.csv")
for (i in 62:1){
	uk_file_name = as.character(list$filename[i])
	create_aqi_args = c(create_aqi_file,uk_file_name,0,0)
	system2('python', args=create_aqi_args,stdout=TRUE)

}


print("done")



