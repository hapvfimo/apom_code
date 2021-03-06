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
#library(rPython)
library(automap)

#DB info

#host_name = '172.16.81.252'
#host_name = '118.70.72.13'
#database_name = 'apom'
#user_name = 'postgres'
#password = 'fimopostgre54321'
#port_number ='8100'

host_name = '192.168.0.61'
database_name = 'apom'
user_name = 'postgres'
password = 'fimopostgre54321'
port_number ='5432'

data_folder ="/apom_data/"
met_folder = "/var/www/html/NPP_Quytrinh/MetNPP/"
shape_file = "/var/www/html/NPP_Quytrinh/BDNEN/VNM_adm0.shp"
tif2raster_file = "/var/www/html/NPP_Quytrinh/tif2rasref.py"
raster2sql_file = "/var/www/html/NPP_Quytrinh/a.sql"
create_aqi_file = "/var/www/html/NPP_Quytrinh/NPP_CLIP_PM_AQI.py"
create_png_file = "/var/www/html/NPP_Quytrinh/create_png.py"
create_aot_file = "/var/www/html/NPP_Quytrinh/aot_processing.py"

#DATA RANGE
#N5 normal

mean_aod = 0.5364641855
abs_aod = 1.3321115665

mean_temp = 308.3684438101
abs_temp = 27.3287709101

mean_avg_temp = 28.0048105047
abs_avg_temp = 11.4414996947

mean_avg_rh = 70.9174167463
abs_avg_rh = 8.5982613337

mean_avg_preci = 221.3783777473
abs_avg_preci = 616.7870543527


#APOM folder

res_folder = "res/SatResampleViirsAOT"
prod_folder = "prod/ProdVIIRS"
			

#SQL query
#insert_all_query = "INSERT INTO %s(aqstime, rasref, filename, filepath, gridid,pmid,max,min,avg, type,sourceid) VALUES ('"
get_time_query = "select aqstime from %s where filename like "

update_query = "UPDATE %s SET  aqstime='%s'::timestamp, rasref='%s'::raster,filename='%s', filepath='%s', gridid =%s,pmid=%s,max=%s,min=%s,avg=%s,type=%s,sourceid=%s WHERE filename='%s';"

insert_query ="INSERT INTO %s (aqstime, rasref, filename, filepath, gridid,pmid,max,min,avg, type,sourceid) SELECT '%s'::timestamp, '%s'::raster, '%s', '%s', %s, %s,%s,%s,%s,%s,%s WHERE NOT EXISTS (SELECT 1 FROM %s WHERE filename='%s')"


#regession function
regress_predict = function(aod,avg_temp,avg_rh,avg_preci){
	pm25 = 17.6615 * aod + (-31.0306)*avg_temp + (-9.2477)*avg_rh + (-9.2477) * avg_preci + 19.5940
	return(pm25)
}
#get data from DB
getDataFromDB = function(sql_command){
	driver = dbDriver("PostgreSQL")
	connect = dbConnect(driver,dbname = database_name,host = host_name,port=port_number,user = user_name,password= password)
	rs = dbSendQuery(connect,sql_command)
	data=fetch(rs,n=-1)
	dbDisconnect(connect)
	dbUnloadDriver(driver)
	return (data)
}
#insert data to DB
insertDataToDB = function(sql_command){
	driver = dbDriver("PostgreSQL")
	connect = dbConnect(driver,dbname = database_name,host = host_name,port=port_number,user = user_name,password= password)
	rs = dbSendQuery(connect,sql_command)
	dbDisconnect(connect)
	dbUnloadDriver(driver)
}
#Kriging function
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
	trainTable=subset(table,!is.na(pm)&pm!=-9999)
	testTable=subset(table,is.na(pm))
	
	auto_trainTable = trainTable
	coordinates(auto_trainTable) =~ x+y
	
	auto_variogram = autofitVariogram(pm~1,auto_trainTable)
	auto_model = auto_variogram$var_model$model[2]
	auto_sill = auto_variogram$var_model$psill[2]
	auto_range = auto_variogram$var_model$range[2]
	
	#caculate variogram
	empiVario = variogram(pm~1,locations=~x+y,data=trainTable)
	
	sphModel=vgm(psill=auto_sill,model=auto_model,nugget=0,range=auto_range)		
	sphFit=fit.variogram(empiVario,sphModel)
	#plot(empiVario,model=sphFit)
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
	
	## #edit error tiff
	## errorPMRaster=pmRaster
	## errorPMValue=universal_result[,4]
	## errorPMRaster[1:totalCell]=errorPMValue
	
	#save uk result to tiff
	uk_file = str_replace(regressPm_file,"_rg.tif","_uk.tif")
	writeRaster(universalPMRaster,filename=uk_file,format="GTiff",overwrite=TRUE)
	gdal_rasterize(shape_file,uk_file,b=1,i=TRUE,burn=-9999,l="VNM_adm0")
	
	#save uk error to tiff
	#error_file = str_replace(regressPm_file,".tif","_error.tif")
	#writeRaster(errorPMRaster,filename=error_file,format="GTiff")
	
	#set n/a value
	new_uk_raster = raster(uk_file)
	new_uk_value = values(new_uk_raster)
	new_uk_value[new_uk_value==-9999]<-NA
	new_uk_value[new_uk_value<0]<-0
	new_uk_raster[1:totalCell] = new_uk_value

	writeRaster(new_uk_raster,filename=uk_file,format="GTiff",overwrite=TRUE)
	if(file.exists(regressPm_mask_file)){
		file.remove(regressPm_mask_file)
	} 
	#save uk error to tiff
	#error_file = str_replace(regressPm_file,"rg.tif","error.tif")
	#writeRaster(errorPMRaster,filename=error_file,format="GTiff",overwrite=TRUE)
	#gdal_rasterize(shape_file,error_file,b=1,i=TRUE,burn=-9999,l="VNM_adm0")
	#print(uk_file)
	
}
#create regression and kiging images
create_pm_image = function(sate_data,aod_file,temp_file,source_id){

	type = 2
	#insert_query = sprintf(insert_all_query, "prodpm.prodviirspm_vn_collection0")
	time_query = sprintf(get_time_query, "res.satresampviirs")
	
	file_name = basename(aod_file)
	file_name = str_replace(file_name,".tif","")
	
	#start_index = regexpr("M[^M]*$",aod_file)
	#end_index = regexpr(".tif",aod_file) - 1
	#file_name = substr(aod_file,start_index,end_index)
	
	time_query = paste(time_query,"'",file_name,"%'",sep="")
	#print(time_query)
	data = getDataFromDB(time_query)
	
	mod04_aqstime = data$aqstime[1]
	aqstime = strptime(mod04_aqstime,format="%Y-%m-%d %H:%M:%S")
	aqstime = aqstime + 25200	
	month = format.Date(aqstime,"%m")
	year = format.Date(aqstime,"%Y")
	
	#mask VietNam base on shapfile
	aod_mask_file = str_replace(aod_file,".tif","_mask.tif")
	file.copy(aod_file,aod_mask_file)
	
	gdal_rasterize(shape_file,aod_mask_file,b=1,i=TRUE,burn=-9999,l="VNM_adm0")
	aod_dataset = raster(aod_mask_file)
	aod_dataset[aod_dataset[] == -9999] <- NA
	
	if(file.exists(aod_mask_file)){
		file.remove(aod_mask_file)
	} 
	
	aod_data = values(aod_dataset)
		
	corxy = coordinates(aod_dataset)
	x = corxy[,'x']
	y = corxy[,'y']
	
	
	temp_mask_file = str_replace(temp_file,".tif","_mask.tif")
	file.copy(temp_file,temp_mask_file)
	gdal_rasterize(shape_file,temp_mask_file,b=1,i=TRUE,burn=-9999,l="VNM_adm0")
	temp_dataset = raster(temp_mask_file)
	temp_dataset[temp_dataset[] == -9999] <- NA
	
	if(file.exists(temp_mask_file)){
		file.remove(temp_mask_file)
	} 
	
	#writeRaster(temp_dataset,filename=temp_mask_file,format="GTiff",overwrite=TRUE)
	
	temp_data = values(temp_dataset)
	
	avg_temp_file  = paste(met_folder,"temp",as.numeric(month),".tif",sep="")
	avg_rh_file    = paste(met_folder,"rh",as.numeric(month),".tif",sep="")
	avg_preci_file = paste(met_folder,"preci",as.numeric(month),".tif",sep="")
		
		
	avg_temp_dataset  =  raster(avg_temp_file)
	avg_rh_dataset    =  raster(avg_rh_file)
	avg_preci_dataset =  raster(avg_preci_file)
		
	avg_temp_data  = values(avg_temp_dataset) 
	avg_rh_data    = values(avg_rh_dataset) 
	avg_preci_data = values(avg_preci_dataset)

	#chuan hoa aod va temp,rh,preci
	aod_data = (aod_data - mean_aod)/abs_aod
	avg_temp_data = (avg_temp_data - mean_avg_temp)/abs_avg_temp
	avg_rh_data = (avg_rh_data - mean_avg_rh)/abs_avg_rh
	avg_preci_data = (avg_preci_data - mean_avg_preci)/abs_avg_preci	

	pm25 = regress_predict(aod_data,avg_temp_data,avg_rh_data,avg_preci_data)
	
	table = data.frame(x,y,aod_data,temp_data,avg_temp_data,avg_rh_data,avg_preci_data,pm25)
	table$pm25[table$aod_data< -1|table$aod_data > 1]<-NA
	
	total_pixel = sum(!is.na(table$pm25))
	ratio = total_pixel/11180*100
	
	print(paste("Pixel:",total_pixel,"Cloud ratio:",ratio,sep=" "))
	
	if(ratio>=5){
	
		#create regression image
		og_raster = aod_dataset
		totalCell = ncell(og_raster)
		og_raster[1:totalCell] = table$pm25
		
		pm_file = str_replace(aod_file,".tif","_rg.tif")
		pm_file = str_replace(pm_file,res_folder,prod_folder)
		
		#print (pm_file)
	
		#mid_index = regexpr("M[^M]*$",pm_file)
		#out_path = substr(pm_file,0,mid_index-1)
		out_path = dirname(pm_file)
		dir.create(path=out_path,showWarnings = FALSE,recursive = TRUE,mod="777")
	
		writeRaster(og_raster,filename=pm_file,format="GTiff",overwrite=TRUE)
		#gdal_rasterize(shape_file,pm_file,b=1,i=TRUE,burn=-9999,l="VNM_adm0")
		#print ("Create regression image good!");

		#create pm image
		createKrigingImage(pm_file)
		print ("Create Kriging image done");
	
		uk_file = str_replace(pm_file,"rg.tif","uk.tif")

		#python.assign("raster_file",uk_file)
		#python.load(tif2raster_file)
		#raster_ref = python.get("raster_ref")
		
		allArgs = c("-a -f rasref -F",uk_file,"prod.prodmodpm")
		system2('raster2pgsql', args=allArgs,stdout=raster2sql_file)
		out = paste(readLines(raster2sql_file),collapse="\n")
		start_index = regexpr("[(]'",out)
		end_index = regexpr("'::raster",out)
		raster_ref = substr(out,start_index + 2,end_index - 1)

		gridid = 1
		pmid = 1
		
		
		uk_raster = raster(uk_file)
		uk_value = values(uk_raster)
		uk_value = uk_value[uk_value!=-9999]
		max_value = max(uk_value,na.rm = TRUE)
		min_value = min(uk_value,na.rm = TRUE)
		avg_value = mean(uk_value,na.rm = TRUE)
	
		#start_index = regexpr("apom/prod",uk_file)
		#mid_index = regexpr("G[^G]*$",uk_file)
		#end_index = nchar(uk_file)
		#uk_file_path = substr(uk_file,start_index,mid_index-1)
		#uk_file_name = substr(uk_file,mid_index,end_index)
		
		uk_file_name = basename(uk_file)
		uk_file_path = dirname(uk_file)
		uk_file_path = str_replace(uk_file_path,data_folder,"")
	
		aqstime2 = aqstime - 25200
		#query = paste(insert_query,aqstime2,"'::timestamp, '",raster_ref,"'::raster, '",uk_file_name,"', '",uk_file_path,"', 1, 1, ",max_value,", ",min_value,", ",avg_value,", ",type,", ",source_id,")",sep="")
		
		update_mod_query = sprintf(update_query,"prodpm.prodviirspm_vn_collection0",toString(aqstime2),raster_ref,uk_file_name,uk_file_path,toString(gridid),toString(pmid),toString(max_value),toString(min_value),toString(avg_value),toString(type),toString(source_id),uk_file_name)
		
	
		insert_mod_query = sprintf(insert_query, "prodpm.prodviirspm_vn_collection0",toString(aqstime2),raster_ref,uk_file_name,uk_file_path,toString(gridid),toString(pmid),toString(max_value),toString(min_value),toString(avg_value),toString(type),toString(source_id),"prodpm.prodviirspm_vn_collection0",uk_file_name)
		
		query = paste(update_mod_query,insert_mod_query,sep="")
		
		#print(query)
		#insert pm images to database
		insertDataToDB(query)
		print ("Insert to database done");
		
		#create png
		#print ("Tao anh PNG");
		#python.load(create_png_file)
		#python.call("CreatePM25PNGImg",basename(uk_file),dirname(uk_file))
		create_png_args = c(create_png_file,basename(uk_file),dirname(uk_file))
		png_out = system2('python', args=create_png_args,stdout=TRUE)
		#print(png_out)

		#create aqi
		print ("Cat anh AQI");
		#sourceid = commandArgs(TRUE)[4]
		#tifname = basename(commandArgs(TRUE)[2])
		sourceid = 1
		tifname = basename(aod_file)
		create_aqi_args = c(create_aqi_file,uk_file_name,type,sourceid)
		system2('python', args=create_aqi_args,stdout=TRUE)
		#python.assign("pmname",uk_file_name)
		#python.assign("sat_type",type) # sat_type is mod:0, myd:1
		#python.assign("sourceid", commandArgs(TRUE)[4])
		#python.load(create_aqi_file) # sao ko thay a it may hon a

		# cat anh AOT
		print ("Cat anh AOT");
		#process_terminate("chmod -R 0777 /apom_data/apom/")
		system("chown -R apom /apom_data/apom/", wait=FALSE)
		system("chmod -R 0777 /apom_data/apom/", wait=FALSE)
		print ("Change permission done")
		create_aot_args = c(create_aot_file,tifname,type,sourceid)
		system2('python', args=create_aot_args,stdout=TRUE)
		
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
#sat_data = "npp"
#source_id = 0

#aod_file = "/apom_data/apom/res/SatResampleViirsAOT/2014/GAERO-VAOOO_npp_d20140124_t0606539_e0612325_b11618_c20140725113835527415_noaa_ops_550_resample/GAERO-VAOOO_npp_d20140124_t0606539_e0612325_b11618_c20140725113835527415_noaa_ops_550_resample.tif"
#temp_file= "/apom_data/apom/res/SatResampVIIRSTemp/2014/GMTCO-VLSTO_npp_d20140124_t0606539_e0612325_b11618_c20150119071449593020_noaa_ops/GMTCO-VLSTO_npp_d20140124_t0606539_e0612325_b11618_c20150119071449593020_noaa_ops_LST_resample.tif"

# mod/myd/npp , aot file, temp file
# Test command
#create_pm_image("npp","linear","4np",aod_file,temp_file, source_id)
#print("done")


# Real command
# command 1: type (mod/myd/npp)
# command 2: mod04
# command 3: mod07
# command 4: sourceid (0: NASA, 1: UET)
#type=2
#aot="/apom_data/apom/res/SatResampleViirsAOT/2016/GAERO-VAOOO_npp_d20160426_t0530118_e0538440_b00001_c20160426062012_550_resample/GAERO-VAOOO_npp_d20160426_t0530118_e0538440_b00001_c20160426062012_550_resample.tif"
#lst="/apom_data/apom/res/SatResampVIIRSTemp/2016/GMTCO-VLSTO_npp_d20160426_t0530118_e0538440_b00001_c20160426063723_LST_resample/GMTCO-VLSTO_npp_d20160426_t0530118_e0538440_b00001_c20160426063723_LST_resample.tif"
#sourceid = 1
#create_pm_image(type,aot,lst,sourceid)
create_pm_image(commandArgs(TRUE)[1],commandArgs(TRUE)[2],commandArgs(TRUE)[3],commandArgs(TRUE)[4])


