<?php
ini_set("display_errors", true);
error_reporting( E_ALL );
date_default_timezone_set('Asia/Ho_Chi_Minh'); // need set default timezone


// This class with get the input as success file to download
// Output: file outputs and insert to DB
class ModisHandle
{
  public $log = array(); // write log when create image;	
  public $collection = ""; // collection of image (51, 6)
  public $home_folder = "/home/apom/";
 // connect to database
 function connect()
 {
   //$host = "112.137.129.222";
   // $host = "118.70.72.13";
   // $port = "8100";
   // $dbname = "apom"; // XXX: fix here before test
   // $user = "postgres";
   // $password = "fimopostgre54321";
   // $link = pg_connect("host=$host port=$port dbname=$dbname user=$user password=$password");

   $host = "192.168.0.61";
   $port = "5432";
   $dbname = "apom"; // XXX: fix here before test
   $user = "postgres";
   $password = "fimopostgre54321";
   $link = pg_connect("host=$host port=$port dbname=$dbname user=$user password=$password");



   if(!$link)
   {
	echo "Cannot connect to database! <br/>";
	exit(1);
   }
   return $link;    
 } // end function connect		
  
 // collection is image version
  public function index($fileNameNoExtension, $filePath, $folderPath, $satType, $fileType, $tableName, $collection, $sourceid)
  { 
     // sourceID = 0;
    /* echo $fileNameNoExtension . "<br/>";
     echo $filePath . "<br/>";
     echo $folderPath . "<br/>";
     echo $satType . "<br/>";
     echo $fileType . "<br/>"; 		
     echo $tableName . "<br/>"; 

     return;*/

     // Create image thumbnail roi moi create metadata and write corner
     // $filePath is file in output folder to convert to file _convert.png and file _thumbnail.png
    /* if($this->createImageThumbnail($fileType, $satType, $filePath, $folderPath, $fileNameNoExtension) == 1)
     {
	//continue; // error then continue
	//return; // maybe image thumbnail has been created so why need to continue
	echo "Maybe file is created before! \n";
     }*/
	
    //echo "\n\nResult create thumbnail: " . $this->createImageThumbnail($fileType, $satType, $filePath, $folderPath, $fileNameNoExtension) . "\n";
	
   $this->collection = $collection; // set collection if image MOD04 (51), MOD07 (51, 6)
   $this->createImageThumbnail($fileType, $satType, $filePath, $folderPath, $fileNameNoExtension, $sourceid);

    // Mảng dữ liệu để ghi metadata
    $data = array();

    //echo $filePath;
    // echo $folderFilePath . basename($fileName, $fileType);
    // **** write metdata to $data array
    if ($fileType == ".tif") {
        // default is fileTif
        exec("gdalinfo " . $filePath, $data, $return); // nối chuỗi   ,execute command, output is array, ?????????? RETURN
    } else if ($fileType == ".hdf") { // fileType = .hdf then get metadata from file tif
        // file .tif extract from HDF
        $fileTif = $folderPath . $fileNameNoExtension . "_convert.tif";
        exec("gdalinfo " . $fileTif, $data, $return); // execute command, output is array       
	//echo "gdalinfo " . $fileTif . "\n";
    }

    //echo "File Type: " . $fileType . "\n";
    

    // Create metadata output file (only get fileName without extension by $fileType)
    $dataFile = $folderPath . $fileNameNoExtension . "_metadata.txt";
    $cornerFile = $folderPath . $fileNameNoExtension . "_corner.txt";

    // **** Write meta data to file _metadata.txt and _corner.txt
    $this->writeCornerFile($data, $dataFile, $cornerFile);

    //exit(1);	
    // return;

    // **** Insert image information (fileName, filePath, Corner, SourceID) to database

    return $this->insertImageInfoToDatabase($tableName, $satType, $folderPath, $fileNameNoExtension, $collection, $sourceid); // return fileResample	

    echo "\n\n\n";
		
  } // end function index

  
  /**
     * [createImageThumbnail Create image convert, thumbnail from $filePath]
     * @param  [string] $fileType [.tif or .hdf]
     * @param  [string] $satType  [DEM, MOD04, MOD07,..]
     * @param  [string] $fileInput [file .tif or file .hdf input]
     * @param  [string] $folderPath [Folder path to file input]
     * @param  [string] $fileName [file name without extension]
     * @return [type]           [description]
     */
    public function createImageThumbnail($fileType, $satType, $fileInput, $folderPath, $fileName, $sourceid) {
        // Neu loai anh la DEM thi dung image magick de tao anh thumbnail
        // Create image output in folder file path
        //*** $folderFilePath = /temp/SatOrgMOD04/image folder/image name (without extension)
        $folderFilePath = $folderPath . $fileName; // ex: /temp/SatOrgMOD04/image1/image1 without extension

	//echo $folderFilePath;
	//exit(1);

  

    if ($satType == "MOD04_L2" || $satType == "MYD04_L2") { //MODIS 4 get subdataset 9: AOD Land and Ocean
        ///gdaltranslate HDF4_EOS:EOS_SWATH:"test.hdf":mod04:Image_Optical_Depth_Land_And_Ocean output.tif
	
	if($sourceid == 0 || ($sourceid == 1 && $satType == "MYD04_L2")) // NASA, MYD04_L2 UET use mod04 not Swath00
	{

        	exec("gdal_translate HDF4_EOS:EOS_SWATH:\"" . $fileInput . "\":mod04:Optical_Depth_Land_And_Ocean " . $folderPath .
 "temp.tif");
		//echo "gdal_translate HDF4_EOS:EOS_SWATH:\"" . $fileInput . "\":mod04:Image_Optical_Depth_Land_And_Ocean " . $folderPath .
 //"temp.tif";

	}
	else // DHCN
	{

		// (only MOD04 use IMAPP version 2.3)
		exec("gdal_translate HDF4_EOS:EOS_SWATH:\"" . $fileInput . "\":Swath00:Optical_Depth_Land_And_Ocean " . $folderPath . "temp.tif");
		// NOTE: Tram thu dung Swath00, NASA: dung mod04
	//	echo "gdal_translate HDF4_EOS:EOS_SWATH:\"" . $fileInput . "\":mod04:Optical_Depth_Land_And_Ocean " . $folderPath . "temp.tif";	
		

	} // else image of DHCN
	
	

    } else if ($satType == "MOD07_L2" || $satType == "MYD07_L2") {
        //     echo "gdal_translate HDF4_EOS:EOS_SWATH:\"" . $fileInput . "\":mod07:Surface_Pressure " . $folderFilePath . "temp.tif";
	if($sourceid == 0 || ($sourceid == 1 && $satType == "MYD07_L2")) // NASA or UET (MYD07_L2) use mod07 not Swath00
	{
        	exec("gdal_translate HDF4_EOS:EOS_SWATH:\"" . $fileInput . "\":mod07:Surface_Pressure " . $folderPath . "temp.tif");
	}
	else // Tram thu (only MOD07 use IMAPP version 2.3)
	{
		exec("gdal_translate HDF4_EOS:EOS_SWATH:\"" . $fileInput . "\":Swath00:Surface_Pressure " . $folderPath . "temp.tif");
		//echo "gdal_translate HDF4_EOS:EOS_SWATH:\"" . $fileInput . "\":Swath00:Surface_Pressure " . $folderPath . "temp.tif";
	}

    } else if ($satType == "MOD03_L2" || $satType == "MYD03_L2") {
	exec("gdal_translate HDF4_EOS:EOS_SWATH:\"" . $fileInput . "\":MODIS_Swath_Type_GEO:Height " . $folderPath . "temp.tif");

    }

    // MODIS MOD04, MOD07 not need projection  as MCD12Q1, NPP (no float value, no gcp)
    // gdalwarp -t_srs '+proj=longlat +datum=WGS84 +no_defs' -ot Float32 -tps output.tif output1.tif
    exec("gdalwarp -t_srs '+proj=longlat +datum=WGS84 + no_defs' -ot Float32 -tps -srcnodata '0' -dstnodata '0' -dstalpha " . $folderPath . "temp.tif " . $folderFilePath . "_convert.tif");
    
  //  echo "gdalwarp -t_srs '+proj=longlat +datum=WGS84 + no_defs' -ot UInt16 -tps -srcnodata '0' -dstnodata '0' -dstalpha " . $folderPath . "temp.tif " . $folderFilePath . "_convert.tif";
  
    // convert .tif to .png
    exec("gdal_translate -of PNG -a_nodata '0' " . $folderFilePath . "_convert.tif" . " " . $folderFilePath . "_convert.png");

    // create thumbnail from _convert.png
    exec("gdal_translate -of PNG -outsize 500 450 -a_nodata '0' " . $folderFilePath . "_convert.png" . " " . $folderFilePath . "_thumbnail.png");
		
    if (file_exists($folderPath . "temp.tif"))
    {
       unlink($folderPath . "temp.tif");
    }
    else
    {
       echo "cannot create image thumbnail," .  $fileInput . ",1 <br/>";
       ob_flush();
       flush(); 	
       //return 1; // file is error then return 1
    }

  

        // *** remove file .xml from gdal_translate output (trashed)
        foreach (glob($folderPath . "*.xml") as $filename) {
            unlink($filename);
        }

        // Check that output thumbnail is done or error		
        if (file_exists($folderFilePath . "_thumbnail.png")) {
            $this->log[] = time() . "," . "Create thumbnail image" . "," . $fileInput . ",0" . "\n";
	    //echo time() . "," . "Create thumbnail image" . "," . $fileInput . ",0" . "<br/>";
        } else {
	    // out put error file
            echo "cannot create image thumbnail," .  $fileInput . ",1 \n";
	    ob_flush();
	    flush(); 	
	    return 1;
            //exit(1); // error because cannot create thumbnail for $fileInput
        }
	return 0; // not error image is succesful
    } // end function createImageThumbnail


   /**
     * [writeCornerFile description]
     * @param  [array string]  $data [array string]
     * @param  [string] $dataFile [meta data file.txt]
     * @param  [string] $cornerFile [corner data.txt]
     * @return [null]     
     */
    public function writeCornerFile($data, $dataFile, $cornerFile) {

        // Open datafile to write data   
        $fh = fopen($dataFile, 'w') or die("can't open file metadata");

        $fhCorner = fopen($cornerFile, 'w') or die("can't open file corner file");

        //print_r($data);
        foreach ($data as $line) {
            // Ghi dữ liệu metadata to $dataFile
            fwrite($fh, $line . "\n");

            // Ghi dữ liệu vào file _corner.txt; (thông tin tọa độ 4 điểm upperleft, lower left, upper right, lower right)
            $str = ""; // parse each line to get the value
            $isLowerRight = false;
            if (strpos($line, 'Upper Left') !== false) {
                $str = str_replace(' ', '', $line) . "\n";
            } else if (strpos($line, 'Lower Left') !== false) {
                $str = str_replace(' ', '', $line) . "\n";
            } else if (strpos($line, 'Upper Right') !== false) {
                $str = str_replace(' ', '', $line) . "\n";
            } else if (strpos($line, 'Lower Right') !== false) {
                $str = str_replace(' ', '', $line) . "\n";
                $isLowerRight = true;
            }

            // If str is one of corner then parse to get Lat, Long value and write to _corner.txt
            if ($str != "") {
                // Write corner to each line _corner.txt
                preg_match('/\((.*?)\)/', $str, $output);
                $value = explode(",", $output[1]);

                // Longtitude (-180, 180), Latitude (90 - 90)
                fwrite($fhCorner, $value[0] . " ");
                if ($isLowerRight == false) {
                    // if not lowerRight then print ","
                    fwrite($fhCorner, $value[1] . ",");
                } else {
                    // if is lowerRight then not print ","
                    fwrite($fhCorner, $value[1]);
                }
            }
        }// end read each line of $data
        fclose($fh); //close file metadata
        fclose($fhCorner); // close file corner
        // echo $dataFile . " write successful! <br/>";
        // Check if metadata file and corner file has value
        if (filesize($dataFile) != 0 && filesize($cornerFile) != 0) {
            $this->log[] = time() . "," . "Write metadata corner file" . "," . $dataFile . ",0" . "\n";
	    //echo time() . "," . "Write metadata corner file" . "," . $dataFile . ",0" . "\n";
        } else {
	    // error file
            $this->log[] = time() . "," . "Write metadata corner file" . "," . $dataFile . ",1" . "\n";
	    echo time() . "," . "Write metadata corner file" . "," . $dataFile . ",1" . "\n";
            //exit(1);
        }
    } // end function write corner file	

     /**
     * [insertImageInfoToDatabase description]
     * @param  [string] $satType [image sat type]     
     * @param  [string] $folderFilePath [full folder file path]     
     * @param  [string] $fileName       [ten file]
     * @return [type]                 [description]
     */
    public function insertImageInfoToDatabase($tableName, $satType, $folderPath, $fileName, $collection, $sourceid) {
        // fileName = $fileName,
        // Path = $folderPath,
        // Cornder = $folderPath . $fileName . "_corner.txt"
        // polygon = POLYGON((upper left, lower left, upper right, lower right));
        // SourceID = 0 // Default is NASA
        // AQSTime = '01-01-2011' (only have 1 in this year)  

        // Get corner content
        $corner = file_get_contents($folderPath . $fileName . "_corner.txt");

        // Create string Polygon from corner.txt
        // upper left, lower left, upper right, lower right
        $array = explode(",", $corner);

	// uppler left, lower left, lower right, upper right
        $polygon = "POLYGON((" . $array[0] . "," . $array[1] . ","
                . $array[3] . "," . $array[2] . "," . $array[0] . "))";
        // echo $polygon;

        $aqstime = "2011-01-01"; // default aqstime is DEM time in 2011
        // If sat is modis then get accquire time
  
            //MOD07_L2.A2013001.0330.006.2013001132534 this is modis name
            //get only A2013001 (2013: year, 001:jDay)
        $str = explode(".", $fileName);
        $year = substr($str[1], 1, 4);
        $jDay = substr($str[1], 5);

        $hour = substr($str[2], 0, 2);
	    $minute = substr($str[2], 2, 3);

        $aqstime = $this->convertJDayToDate($year, $jDay);

	    $aqstime = $aqstime . " " . $hour . ":" . $minute . ":00"; // year-month-day hour:minute

	   // folder path not get the folder before fimo
	    // *** Explode $folderPath to get only the path from fimo folder ***
	    $temp = explode($this->home_folder, $folderPath); // data to store
	    $folderPath = $temp[1];// . "<br/>"; // fimo path folder

	// NOTE: INSERT FILENAME WITH EXTENSION TO DATABASE
	    $fileName = $fileName . ".hdf"; // DEFAULT MODIS FILE NAME IS HDF

        $data = array(
            //"id" => '', // mysql mới cần ghi rõ tên cột
            "filename" => $fileName,
            "path" => $folderPath,
            "corner" => $polygon,
            "sourceid" => $sourceid,
            "aqstime" => $aqstime,
	    "collection" => $collection,
	    "sourceid" => $sourceid
        );

	//print_r($data);

	$result = 0;

        $result = $this->insertInfoImage($tableName, $data); // check if insert is success or fail

	//echo "RESAMPLE HERE! \n ";
	
	//echo $satType . "<br/>";
	//exit(1);

	$fileResample = ""; // file Resample (from resampleMODIS function)
	
	// Ảnh MODIS MOD07 và MYD07 resample 
	if($satType == "MOD07_L2")
	{
	   /*$satType = "MOD07_L2_P";
	    echo "----------------------------------------RESAMPLE MOD07_L2_P--------------------------------------------------<br/>";
	    echo "--------RESAMPLE 3 km -------- <br/>";
            $this->resampleMODIS($satType, $folderPath, $fileName, $polygon, $year, $aqstime, 3, $sourceid);
	    echo "--------RESAMPLE 6 km -------- <br/>";
            $this->resampleMODIS($satType, $folderPath, $fileName, $polygon, $year, $aqstime, 6, $sourceid);
	    echo "--------RESAMPLE 10 km -------- <br/>";
            $this->resampleMODIS($satType, $folderPath, $fileName, $polygon, $year, $aqstime, 10, $sourceid);
   	    echo "-------------------------------------------------------------------------------------------------------------<br/>";
	   */

    	    $satType = "MOD07_L2_T";
	    echo "----------------------------------------RESAMPLE MOD07_L2_T--------------------------------------------------<br/>";
            //echo "--------RESAMPLE 3 km -------- <br/>";
            //$fileResample = $this->resampleMODIS($satType, $folderPath, $fileName, $polygon, $year, $aqstime, 3, $sourceid);

	    //echo "--------RESAMPLE 6 km -------- <br/>";
           // $fileResample = $this->resampleMODIS($satType, $folderPath, $fileName, $polygon, $year, $aqstime, 6, $sourceid);

            echo "--------RESAMPLE 10 km -------- <br/>";
    	    $fileResample = $this->resampleMODIS($satType, $folderPath, $fileName, $polygon, $year, $aqstime, 10, $sourceid);

	    echo "-------------------------------------------------------------------------------------------------------------<br/>";
	}
	else if($satType == "MYD07_L2")
	{
	    /*$satType = "MYD07_L2_P";
	    echo "----------------------------------------RESAMPLE MYD07_L2_P--------------------------------------------------<br/>";
	    echo "--------RESAMPLE 3 km -------- <br/>";
            $this->resampleMODIS($satType, $folderPath, $fileName, $polygon, $year, $aqstime, 3, $sourceid);
            echo "--------RESAMPLE 6 km -------- <br/>";
            $this->resampleMODIS($satType, $folderPath, $fileName, $polygon, $year, $aqstime, 6, $sourceid);
            echo "--------RESAMPLE 10 km -------- <br/>";
            $this->resampleMODIS($satType, $folderPath, $fileName, $polygon, $year, $aqstime, 10, $sourceid);
	    echo "-------------------------------------------------------------------------------------------------------------<br/>";
	   */
	
    	    $satType = "MYD07_L2_T";
	    echo "----------------------------------------RESAMPLE MYD07_L2_T--------------------------------------------------<br/>";
          //  echo "--------RESAMPLE 3 km -------- <br/>";
           // $fileResample = $this->resampleMODIS($satType, $folderPath, $fileName, $polygon, $year, $aqstime, 3, $sourceid);

          // echo "--------RESAMPLE 6 km -------- <br/>";
          // $fileResample = $this->resampleMODIS($satType, $folderPath, $fileName, $polygon, $year, $aqstime, 6, $sourceid);

           echo "--------RESAMPLE 10 km -------- <br/>";
           $fileResample =  $this->resampleMODIS($satType, $folderPath, $fileName, $polygon, $year, $aqstime, 10, $sourceid);

	    echo "-------------------------------------------------------------------------------------------------------------<br/>";
	}
	else if($satType == "MOD04_L2")
        {
	    $satType = "MOD04_L2_DT"; // Dark Target
            echo "----------------------------------------RESAMPLE MOD04_L2 Dark Target--------------------------------------------------<br/>";
	    echo "--------RESAMPLE 10 km -------- <br/>";

            $fileResample = $this->resampleMODIS($satType, $folderPath, $fileName, $polygon, $year, $aqstime, 10, $sourceid);
	    //echo "-------------------------------------------------------------------------------------------------------------<br/>";

	   /* $satType = "MOD04_L2_AT"; // Aerosol Type
            echo "----------------------------------------RESAMPLE MOD04_L2 Aerosol Type--------------------------------------------------<br/>";
	    echo "--------RESAMPLE 10 km -------- <br/>";
            $this->resampleMODIS($satType, $folderPath, $fileName, $polygon, $year, $aqstime, 10, $sourceid);
	    echo "-------------------------------------------------------------------------------------------------------------<br/>";*/
	}
	else if($satType == "MYD04_L2")
	{
	    $satType = "MYD04_L2_DT";
            echo "----------------------------------------RESAMPLE MYD04_L2 Dark Target--------------------------------------------------<br/>";
	    echo "--------RESAMPLE 10 km -------- <br/>";
            $fileResample = $this->resampleMODIS($satType, $folderPath, $fileName, $polygon, $year, $aqstime, 10, $sourceid);
	    echo "-------------------------------------------------------------------------------------------------------------<br/>";

	    //$satType = "MYD04_L2_AT";
            //echo "----------------------------------------RESAMPLE MYD04_L2 Aerosol Type--------------------------------------------------<br/>";
	    //echo "--------RESAMPLE 10 km -------- <br/>";
            //$fileResample = $this->resampleMODIS($satType, $folderPath, $fileName, $polygon, $year, $aqstime, 10, $sourceid);
	    echo "-------------------------------------------------------------------------------------------------------------<br/>";
	}
      

        // check result if insert successful (cannot save log because update and insert is executed same time so row effect is 0)
        if ($result != false) { // remove row effect in imagelist model
            $this->log[] = time() . "," . "Insert image" . "," . $tableName . ",0" . "\n";
	    //echo time() . "," . "Insert image" . "," . $tableName . ",0" . "\n";
        } else {
            $this->log[] = time() . "," . "Insert image" . "," . $tableName . ",1" . "\n";
	    echo time() . "," . "Insert image" . "," . $tableName . ",1" . "\n";
        }

	#print log file
	/*echo "<pre>";
	print_r($this->log);
	echo "</pre>";*/		

        ob_flush();
	flush(); 

	//echo "Insert image " . $fileResample; // know the file which is resampled	
	//exit(1);
	return $fileResample; 

	
    } // end function insertImageInfoToDatabase

    // Get the lastest day from tableName
    function getLastDay($tableName)
    {
	//echo $tableName;
	//exit(1);
	
	//var_dump($tableName);


	$query = "select to_char(aqstime, 'YYYY-MM-DD') as aqstime from $tableName ";
	$query .= "order by aqstime desc ";
	$query .= "limit 1 offset 0"; // offset 0 to get the top value
	
	$db = $this->connect();
	$result = pg_exec($db, $query); // fetch the array value to $result	
	
	if(pg_fetch_assoc($result)["aqstime"] == "") // no element at array
	{
	   echo "Table is empty, please choose the startDate to download file from THIS DATE! <br/>";
	   return 0;
	}
	// if result["aqstime"] is valid then start
	return pg_fetch_result($result, 0, 0); // row 0, field 0
    }// end function getLastDay




    // Insert info Image to Sat table 
    function insertInfoImage($tableName, $data) {
        /*
          UPDATE apom.test SET username='Bang' WHERE id=2;
          INSERT INTO apom.test (id, username)
          SELECT 2, 'Trang'
          WHERE NOT EXISTS (SELECT 1 FROM apom.test WHERE id=2); */
        $query = "UPDATE " . $tableName . " SET filename = '" . $data['filename'] . "',";
        $query .= "path = '" . $data['path'] . "',";
        $query .= "corner = '" . $data['corner'] . "',";
	$query .= "updatetime = '" . date('Y/m/d H:i:s') . "',";
	$query .= "collection = " . $data['collection'] . ",";
	$query .= "sourceid = " . $data['sourceid'] . ",";
        $query .= "aqstime = '" . $data['aqstime'] . "' WHERE filename = '" . $data['filename'] . "';";
        $query .= "insert into " . $tableName;
        $query .= '("filename", "path", "corner", "aqstime", "collection", "sourceid", "updatetime")';
        $query .= "SELECT '" . $data['filename'] . "','";
        $query .= $data['path'] . "','";
        $query .= $data['corner'] . "','";
        $query .= $data['aqstime'] . "','";
        $query .= $data['collection'] . "','";
        $query .= $data['sourceid'] . "','";
        $query .= date('Y/m/d H:i:s') . "'";
        $query .= " WHERE NOT EXISTS (SELECT 1 FROM " . $tableName . " WHERE filename = '" . $data['filename'] . "');";

        //   $this->db->insert($tableName, $data);
        // echo "Insert sucessful!";
        $db = $this->connect();
	$result = pg_exec($db, $query); // exec query to insert to database

        return $result;
    } // end function insertInfoImage


	   # satType là loại ảnh (MOD04, MYD04,...)
	# folderPath là đường dẫn đến thư mục ảnh đã download
	# fileName là tên file hdf đã download
	# polygon là tọa độ 4 góc của ảnh
	# year là khoảng thời gian ảnh chụp
	# version là resample rasref to version (10, 6, 3)
	# sourceid la thong tin du lieu nguon cung cap (0:NASA, 1:UET)
	public function resampleMODIS($imageType, $inputFolderPath, $fileName, $imageBound, $year, $aqstime, $version, $sourceID)
	{

	  	//$exePath = "raster2pgsql"; # link to raster2pgsql
        $exePath = "/usr/bin/raster2pgsql"; # link to raster2pgsql
        

		$prefixDataset = ""; # vd MOD04: HDF4_EOS:EOS_SWATH:"
		$postfixDataset = ""; # vd MOD04: ":mod04:Optical_Depth_Land_And_Ocean;

		$folderPath = ""; # FROM FOLDER PATH SAT RESAMPLE

		$tableName = "";

		#$hdfFolder = "/apom_data/apom/"; // ******************* input Folder Prefix to Resample (MUST HAVE)
   
        #
		 $hdfFolder = $this->home_folder;
        //$hdfFolder = "/home/apom/Share/EOS/";

		$hostIP = ""; # folder to store the image

		$hostIP = $hostIP . $hdfFolder ;  // IT IS REALLY LIKE hdfFolder, expect it can handle from another IP

		$outputFile = "TEST123_10km.tif"; # outputFile tiff from gdalwarp (ex: MOD04: MOD04_L2.A2014001.0300.051.2014001135220.hdf_10km.tif)

		$temp = explode(".hdf", $fileName); // get the folderName from file .hdf
		$folderName = $temp[0]; // folder with out /varr/www/

	
		// 1. CHECK SAT TYPE TO OUTPUT TO FOLDER RESAMPLE
		// MOD04
		if ($imageType == "MOD04_L2_DT") // Use this
		{
			$prefixDataset = 'HDF4_EOS:EOS_SWATH:"';

			$postfixDataset = "";

			// CHECK SOURCE ID
			if($sourceID == 0) // NASA
			{
				$postfixDataset = '":mod04:Optical_Depth_Land_And_Ocean'; // Download anh tu NASA
			}
			else // UET, IMAPP 2.3
			{
				$postfixDataset = '":Swath00:Optical_Depth_Land_And_Ocean'; // # Anh thu tu tram thu
			}
			$tableName = "res.satresampmod04";
			$folderPath = $hostIP . "apom/res/SatResampMOD04/" . $year . "/" . $folderName . "/"; # NEED TO KNOW WHAT YEAR	
			$outputFile = $fileName . "_DT_" . $version . "km.tif";	
		}
		else if ($imageType == "MOD04_L2_AT")
		{
			$prefixDataset = 'HDF4_EOS:EOS_SWATH:"';
			$postfixDataset = '":mod04:Aerosol_Type_Land';
			$tableName = "res.satresampmod04aerosoltype";
			$folderPath = $hostIP . "apom/res/SatResampMOD04/" . $year . "/" . $folderName . "/"; # NEED TO KNOW WHAT YEAR	
			$outputFile = $fileName . "_AT_" . $version . "km.tif";	
		}

		// MYD04
		else if ($imageType == "MYD04_L2_DT") // Dark Target Deep Blue Combined
		{	
			$prefixDataset = 'HDF4_EOS:EOS_SWATH:"';

			$postfixDataset = "";

			// CHECK SOURCE ID
			if($sourceID == 0)
			{
				$postfixDataset = '":mod04:AOD_550_Dark_Target_Deep_Blue_Combined';  // Download anh tu NASA
			}
			else // UET IMAPP3.1
			{
				$postfixDataset = '":mod04:AOD_550_Dark_Target_Deep_Blue_Combined';  // # Anh thu tu tram thu (NEED TO CHANGE TO IMAPP 3.1)
			}
			$tableName = "res.satresampmyd04";
			$folderPath = $hostIP . "apom/res/SatResampMYD04/" . $year . "/" . $folderName . "/"; # NEED TO KNOW WHAT YEAR
			$outputFile = $fileName . "_DT_" . $version . "km.tif";
		}	
		else if ($imageType == "MYD04_L2_AT")
		{
			$prefixDataset = 'HDF4_EOS:EOS_SWATH:"';
			$postfixDataset = '":mod04:Aerosol_Type_Land';
			$tableName = "res.satresampmyd04aerosoltype";
			$folderPath = $hostIP . "apom/res/SatResampMYD04/" . $year . "/" . $folderName . "/"; # NEED TO KNOW WHAT YEAR	
			$outputFile = $fileName . "_AT_" . $version . "km.tif";	
		}

		// MOD07
		else if ($imageType == "MOD07_L2_P") 
		{	
			$prefixDataset = 'HDF4_EOS:EOS_SWATH:"';
			$postfixDataset = '":mod07:Surface_Pressure';
			$tableName = "res.satresampmod07pressure";
			$folderPath = $hostIP . "apom/res/SatResampMOD07/" . $year . "/" . $folderName . "/"; # NEED TO KNOW WHAT YEAR
			$outputFile = $fileName . "_P_". $version . "km.tif";
		}
		else if ($imageType == "MOD07_L2_T")	
		{
			#print "THIS IS MOD07";
			$prefixDataset = 'HDF4_EOS:EOS_SWATH:"';
			// NOTE: IF collection is 51 then surface_temperature, if collection is 6 then skin_temperature

			if($this->collection == "51")
			{
			    // collection 51
			    $postfixDataset = '":mod07:Surface_Temperature'; # Surface -> Skin (moi cap nhat)
			}
			else
			{	
			    // collection 6, // CHECK SOURCE ID	
			    if($sourceID == 0)
			    {			
			    	$postfixDataset = '":mod07:Skin_Temperature'; # Surface -> Skin (moi cap nhat) # Download Tu NASA
			    }
			    else // Tram thu MOD07 IMMAP v2.3
			    {
				$postfixDataset = '":Swath00:Skin_Temperature'; # Surface -> Skin (moi cap nhat) # Tu Tram thu
			    }
			}

			$tableName = "res.satresampmod07temperature";
			$folderPath = $hostIP . "apom/res/SatResampMOD07/" . $year . "/" . $folderName . "/"; # NEED TO KNOW WHAT YEAR
			$outputFile = $fileName . "_T_". $version ."km.tif";
		}

		// MYD07
		else if ($imageType == "MYD07_L2_P") 
		{
			$prefixDataset = 'HDF4_EOS:EOS_SWATH:"';
			$postfixDataset = '":mod07:Surface_Pressure';
			$tableName = "res.satresampmyd07pressure";
			$folderPath = $hostIP . "apom/res/SatResampMYD07/" . $year . "/" . $folderName . "/"; # NEED TO KNOW WHAT YEAR
			$outputFile = $fileName . "_P_" . $version . "km.tif";
		}
		else if ($imageType == "MYD07_L2_T")
		{	
			$prefixDataset = 'HDF4_EOS:EOS_SWATH:"';
			
			// CHECK SOURCE ID
			if($sourceID == 0)
			{			
				$postfixDataset = '":mod07:Skin_Temperature'; # Surface -> Skin (moi cap nhat), download tu NASA
			}
			else // Tram thu IMAPP v3.1
			{
				$postfixDataset = '":mod07:Skin_Temperature'; # Surface -> Skin (moi cap nhat), Thu tu tram thu
			}
			$tableName = "res.satresampmyd07temperature";
			$folderPath = $hostIP . "apom/res/SatResampMYD07/" . $year . "/" . $folderName . "/"; # NEED TO KNOW WHAT YEAR
			$outputFile = $fileName . "_T_" . $version . "km.tif";
		}

		// output file is file to resample;

		// $version resample to 10, 6, 3 km
		if ($version == 6)
		{
		  $resX = 0.07037547957;
		  $resY = -0.07037547957; 
		}
		else if ($version == 3)
		{
		  $resX = 0.03518773978;
		  $resY = -0.03518773978;
		}
		else if ($version == 10)
		{		
		   $resX = "0.117292465957718";
		   $resY = "-0.117292465957718";
		}

		//echo $folderName;
	
		// 1.1 CHECK FOLDER RESAMPLE OUTPUT IS EXIST OR NOT, IF NOT THEN CREATE FOLDER
		// Here is fullpath
		// echo 'FOLDER: ' . $folderPath . " Folder exist: " . file_exists($hdfFolder . $folderPath);
		// exit(1);
		


		if (!file_exists($folderPath)) {
		    mkdir($folderPath, 0777, true);
		    $this->log[] = time() . "," . "Create folder resample" . "," . $folderPath . ",0" . "\n";  
		}

		//echo $prefixDataset . " " . $hdfFolder . " " . $inputFolderPath;
		//exit(1);

		// 1.2 EXEC GDALWARP TO RESAMPLE TO OUTPUT FOLDER
		$warp = "gdalwarp -t_srs '+proj=longlat +datum=WGS84' -tps -ot Float32 -wt Float32 -te 100.1 6.4 111.8 25.6 -tr " . $resX . " " . $resY . " -r cubic -srcnodata -9999 -dstnodata -9999 -overwrite -multi " . $prefixDataset . $hdfFolder . $inputFolderPath . $fileName . $postfixDataset . " " . $folderPath . $outputFile; 
		
		echo "warp = " . $warp . "\n";		

		/*if($this->collection == "6")
		{
		    echo "warp: " . $warp;
		    exit(1);
		}*/		


		shell_exec($warp);
		$this->log[] = time() . "," . "Resample warp" . "," . $folderPath . $outputFile . ",0". "\n";

		// 2. RASTER2PGSQL to get the raster
		$output = shell_exec($exePath . " -a -f rasref -F " . $folderPath . $outputFile . " " . $tableName);

		//print $output;

		$firstIndex =  strpos($output, "('");
		$lastIndex = strpos($output, ",'");

		//print $firstIndex . " " . $lastIndex . "\n";

		$rasref = substr($output, $firstIndex + 1, $lastIndex - $firstIndex - 1 ); # get only the raster value (remove ('
		//print $rasref;

		// 3. INSERT TO DATABASE
		//$filepath = "fimo/" . $filepath.split("fimo/")[1];
		//$temp = explode("fimo/", $folderPath);
		//$filePath = "fimo/" . $temp[1];
		
		// *******************
		$temp = explode($this->home_folder, $folderPath);
		$filePath = $temp[1];

		//echo $folderPath;
		//exit(1);

		// Because MOD07/MYD07 only have 3 raster resolution so filename is same .hdf and 3 columns raster
		/*if ($imageType == "MOD07_L2_P" || $imageType == "MOD07_L2_T" || $imageType == "MYD07_L2_T" || $imageType == "MYD07_L2_P")
		{
			$outputFile = $fileName; // only set the filename is .HDF and update another raster column
		}*/

		$temp1 = explode(".tif", $outputFile);
		$outputFileName = $temp1[0] . ".tif"; // cut ".tif" extension. (outputFileName is just file name)

		$gridid = "1";	
		$orgid = "1"; // tham chieu toi bang mod04org hoac mod07org

		$query = "UPDATE " . $tableName . " SET gridid = " . $gridid . ", ";
		$query .= "aqstime = '" . $aqstime . "', ";
		$query .= "rasref" . " = " . $rasref . ", ";
		$query .= "filepath = '" . $filePath . "', " . "projection = '" . "1" . "', ";
		$query .= "sourceid = '" . $sourceID . "', ";
		$query .= "updatetime = '" . date('Y-m-d H:i:s') . "'";
		$query .= "WHERE filename = '" . $outputFileName . "';";

		$query .= "INSERT INTO " . $tableName . " (gridid, orgid, aqstime,";
		$query .= " rasref" . ",";
		$query .= " filename, filepath, projection, sourceid, updatetime) ";
		$query .= "SELECT " . $gridid . ", " . $orgid . ", '" . $aqstime . "', ";
		$query .= $rasref . ", '";
		$query .= $outputFileName . "', '" . $filePath . "', '";
		$query .= "1" . "', '" . $sourceID . "', '" . date('Y-m-d H:i:s') . "'"; // projection, sourceid, updatetime
		$query .= "WHERE NOT EXISTS (SELECT 1 FROM " . $tableName . " WHERE filename =  '" . $outputFileName . "')";
	
		//echo $query;
		//exit(1);

		$db = $this->connect();

		echo "<br/>" . $imageType . " is resampled succesfull! <br/>";

		$result = pg_query($db, $query); // exec query to insert to database
	
		$this->log[] = time() . "," . "Insert Resample " . $version . " km," . $fileName . "," . "0" . "\n";

		// check result if insert successful (cannot save log because update and insert is executed same time so row effect is 0)
		if ($result == true) { // remove row effect in imagelist model
		    $this->log[] = time() . "," . "Insert image and resample" . "," . $tableName . ",0" . "\n";
		} else {
		    $this->log[] = time() . "," . "Insert image and resample" . "," . $tableName . ",1" . "\n";
		}

		echo "<pre>";
		print_r($this->log);
		echo "</pre>";

		//echo $outputFile;
		//exit(1);

		return $folderPath . $outputFile;  // get the full path to resample images link to groundstation
	
	}


    // **** Check file UET is exist or not to download (only check file mod04 or myd04 no need to check mod07 or myd07)
    public function checkFileUETIsExist($tableName, $checkDate, $startCheckDate, $endCheckDate)
    {
	$query = "select id from $tableName where aqstime >= '$startCheckDate' and aqstime <= '$endCheckDate'";
	
	$db = $this->connect();
	$result = pg_exec($db, $query); // fetch the array value to $result	
	
	if(pg_fetch_assoc($result)["id"] == "") // no element at array then file is not exist
	{	   
	   return 0; // need to download
	}
	// if result["aqstime"] is valid then start
	return 1; // file is exist, no need  to download
    }

   
    // Convert Julian day to Date (only MODIS)
    public function convertJDayToDate($year, $jDay) {
        // this is leap year
        $date = "1-1"; // date and month;
        $day = array();
        if ($this->is_leap_year($year)) {
            $day = array(1, 32, 61, 92, 122, 153, 183, 214, 245, 275, 306, 336);
        } else { // no leap year
            $day = array(1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335);
        }

        // check if $JDay - $d >= 0 then it in this month and get the day of this month
        for ($i = 11; $i >= 0; $i--) {
            if ($jDay - $day[$i] >= 0) {
                $date = $year . "-" . ($i + 1) . "-" . ($jDay + 1 - $day[$i]);
                break;
            }
        }
        // date = month - day in month
        return $date;
    }

// end function convertJDayToDate

    function is_leap_year($year) {
        return ((($year % 4) == 0) && ((($year % 100) != 0) || (($year % 400) == 0)));
    }

} // end class ModisHandle

