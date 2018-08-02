<?php
require "modishandle.php";
ini_set("display_errors", true);
error_reporting(E_ALL);
// sudo service cron start, chuong trinh tu dong chay vao 23h tối
// sudo service cron stop 



# php /var/www/MODIS/download_2015_01_20/modisdownload.php



$obj = new ModisDownload();
$obj->index();


class ModisDownload
{
    public $dateMile; // From here is date 0
    
    public $collection = array(); // Version image download
    public $default_Folder = "/home/apom/apom/org/";
    public $date_start = "2018/02/01";
    public $create_pm_cmd = "Rscript /var/www/html/MODIS_Quytrinh/AodToPm.R ";
        
    
    function __construct()
    {
        // Call the Model constructor
        // parent::__construct();
        date_default_timezone_set('Asia/Ho_Chi_Minh'); // need set default timezone
        $this->dateMile = new DateTime("2013-01-14");
    }
    
    public function index()
    {
        
        header('Content-type: text/html; charset=utf-8');
        
        
        # các biến khởi tạo
        $dateStart = new DateTime("2013-01-14"); // (JUST INIT, NOT CHANGE IN HERE)
        $dateEnd = new DateTime("2013-12-26"); //  (JUST INIT, NOT CHANGE IN HERE)
        
        // get date yesterday
        $date = date("Y-m-d", strtotime("-3 days")); // 3 day is good

        $jDay = intval($this->convertDateToJDay($date)); // get the int value of $jDay, tính  từ 1/1/xxxx năm đó tới ngày xét
        $jDay = $this->getjDay($jDay);#thêm 00
        $defaultFolder = $this->default_Folder;
        
        #khai báo biến
        $temp = explode("-", $date);
        $year = $temp[0]; // get current year
        
        #gán giá trị cho biến. Nếu có dữ liệu Mod, Myd04=> có dứ liệu myd, mod 07. Nhưng có dữ liệu 07 thì chưa chắc có dữ liệu 04
        // download mod04 to folderPath
        // Create associative array to download
        // 1. DOWNLOAD MOD04
        $imageType  = array(
            "MOD04_L2",
            "MOD07_L2"
        ); //MOD03, MOD04_L2, MOD07_L2
        $folderName = array(
            "SatOrgMOD04",
            "SatOrgMOD07"
        ); // folder Name
        $tableName  = array(
            "org.satorgmod04",
            "org.satorgmod07"
        ); // table Name
        
        $outputFolder = array(
            $defaultFolder . $folderName[0],#combine defaultFolder + folderName
            $defaultFolder . $folderName[1]
        ); // folder to SatOrgMOD04
        
        $dateStart = $this->date_start; // if table is empty then download from this date, Khai báo ngày mặc định
        
        $dateDownload = array( #thứ tự  các phiên ảnh có chứa lãnh thổ VN theo thời gian GMT0+. Theo chu kì 16 ngày lặp lại 1 lần
            "0300-0305",
            "0345",
            "0250-0425",
            "0330-0335",
            "0240-0415",
            "0320-0325",
            "0405",
            "0310",
            "0350-0355",
            "0255-0300",
            "0340",
            "0245-0420",
            "0325-0330",
            "0410",
            "0315",
            "0355-0400"
        ); // 0 - 15 (day 97 is same to day 1)
        echo "<br/> Time: " . date('Y-m-d H:i:s') . "---------------------------------------------------------------------Download MOD04_L2 and MOD07_L2-------------------------------------------------------------------- <br/>";
        #gọi tới hàm startDownload
        $this->startDownload($imageType, $folderName, $tableName, $outputFolder, $dateDownload, $dateStart); 
        // foreach from lastest date in DB to current date to download
        
        // 2. DOWNLOAD MYD04
        $imageType  = array(
            "MYD04_L2",
            "MYD07_L2"
        ); //MOD03, MOD04_L2, MOD07_L2
        $folderName = array(
            "SatOrgMYD04",
            "SatOrgMYD07"
        ); // folder Name
        $tableName  = array(
            "org.satorgmyd04",
            "org.satorgmyd07"
        ); // table Name
        
        $outputFolder = array(
            $defaultFolder . $folderName[0],
            $defaultFolder . $folderName[1]
        ); // folder to SatOrgMOD04
        
        $dateStart = "2018/02/01"; // if table is empty then download from this date
        
        $dateDownload = array(
            "0605-0610",
            "0650-0655",
            "0555-0600",
            "0640",
            "0545",
            "0625-0630",
            "0530-0535-0710-0715",
            "0615",
            "0655-0700",
            "0600-0605",
            "0645-0650",
            "0550",
            "0630-0635",
            "0535-0540",
            "0620-0625",
            "0700-0705"
        ); // 0 - 15 (day 97 is same to day 1)
        $this->startDownload($imageType, $folderName, $tableName, $outputFolder, $dateDownload, $dateStart); // download myd04
      echo "<br/> Time: " . date('Y-m-d H:i:s') . "---------------------------------------------------------------------Download MYD04_L2 and MYD07_L2-------------------------------------------------------------------- <br/>";
        
        
        // 3. DOWNLOAD MOD07
        $imageType = "MOD07_L2"; //MOD03, MOD04_L2, MOD07_L2
        
        $folderName = "SatOrgMOD07"; // folder Name
        $tableName  = "org.satorgmod07"; // table Name
        
        $outputFolder = $defaultFolder . $folderName; // folder to SatOrgMOD04
        
        $dateStart = "2018/02/01"; // if table is empty then download from this date
        
        // new download mod07
        $dateDownload = array(
            "0300-0305",
            "0345",
            "0250-0425",
            "0330-0335",
            "0240-0415",
            "0320-0325",
            "0405",
            "0310",
            "0350-0355",
            "0255-0300",
            "0340",
            "0245-0420",
            "0325-0330",
            "0410",
            "0315",
            "0355-0400"
        ); // 0 - 15 (day 97 is same to day 1)
                
        // 4. DOWNLOAD MYD07
        $imageType = "MYD07_L2"; //MOD03, MOD04_L2, MOD07_L2
        
        $folderName = "SatOrgMYD07"; // folder Name
        $tableName  = "org.satorgmyd07"; // table Name
        
        $outputFolder = $defaultFolder . $folderName; // folder to SatOrgMOD04
        
        $dateStart = "2018/02/01"; // if table is empty then download from this date
        
        $dateDownload = array(
            "0605-0610",
            "0650-0655",
            "0555-0600",
            "0640",
            "0545",
            "0625-0630",
            "0530-0535-0710-0715",
            "0615",
            "0655-0700",
            "0600-0605",
            "0645-0650",
            "0550",
            "0630-0635",
            "0535-0540",
            "0620-0625",
            "0700-0705"
        ); // 0 - 15 (day 97 is same to day 1)
        // 5. DOWNLOAD MOD03
        $imageType    = "MOD03"; //MOD03, MOD04_L2, MOD07_L2
        $dateDownload = array(
            "0300-0305-1530-1535",
            "0345-0350-1435-1440",
            "0250-0255-0425-0430-1520-1525",
            "0330-0335-1425-1430-1605",
            "0240-0415-1505-1510",
            "0320-0325-1550-1555",
            "0405-1455-1500",
            "0310-1540",
            "0350-0355-1445",
            "0255-0300-1525-1530",
            "0340-1430-1435",
            "0245-0420-1515",
            "0325-0330-1420-1555-1600",
            "0410-1500-1505",
            "0315-1545-1550",
            "0355-0400-1450-1455"
        ); // 0 - 15 (day 97 is same to day 1)
        
        // 6. DOWNLOAD MYD03
        $imageType    = "MYD03"; //MOD03, MOD04_L2, MOD07_L2
        $dateDownload = array(
            "0605-0610-1820-1825",
            "0650-0655-1905",
            "0555-0600-1810",
            "0640-1850-1855",
            "0545-1755-1800-1935",
            "0625-0630-1840",
            "0530-0535-0710-0715-1745-1920",
            "0615-1825-1830",
            "0655-0700-1910",
            "0600-0605-1815",
            "0645-0650-1855-1900",
            "0550-0555-1800-1805",
            "0630-0635-1845-1850",
            "0535-0540-1750-1755-1925-1930",
            "0620-0625-1830-1835",
            "0700-0705-1915-1920"
        ); // 0 - 15 (day 97 is same to day 1)
        
        // 7. Download MOD02HKM
        $imageType    = "MOD02HKM";
        $dateDownload = array(
            "0300-0305",
            "0345-0350",
            "0250-0255-0425-0430",
            "0330-0335",
            "0240-0415",
            "0320-0325",
            "0345",
            "0310",
            "0350-0355",
            "0255-0300",
            "0340",
            "0245-0420",
            "0325-0330",
            "0410",
            "0315",
            "0355-0400"
        ); // 0 - 15 (day 97 is same to day 1)
        // 8. Download MYD02HKM
        $imageType    = "MYD02HKM";
        $dateDownload = array(
            "0605-0610",
            "0650-0655",
            "0555-0600",
            "0640",
            "0545",
            "0625-0630",
            "0530-0535-0710-0715",
            "0615",
            "0655-0700",
            "0600-0605",
            "0645-0650",
            "0550",
            "0630-0635",
            "0535-0540",
            "0620-0625",
            "0700-0705"
        ); // 0 - 15 (day 97 is same to day 1)
        
        // 9. Download MOD021KM
        $imageType = "MOD021KM";
        array(
            "0300-0305-1530-1535",
            "0345-0350-1435-1440",
            "0250-0255-0425-0430-1520-1525",
            "0330-0335-1425-1430-1605",
            "0240-0415-1505-1510",
            "0320-0325-1550-1555",
            "0405-1455-1500",
            "0310-1540",
            "0350-0355-1445",
            "0255-0300-1525-1530",
            "0340-1430-1435",
            "0245-0420-1515",
            "0325-0330-1555-1600",
            "0410-1500-1505",
            "0315-1545-1550",
            "0355-0400-1450-1455"
        ); // 0 - 15 (day 97 is same to day 1)
        
        // 10. Download MYD021KM
        $imageType    = "MYD021KM";
        $dateDownload = array(
            "0605-0610-1820-1825",
            "0650-0655-1905",
            "0555-0600-1810",
            "0640-1850-1855",
            "0545-1755-1800-1935",
            "0625-0630-1840",
            "0530-0535-0710-0715-1745-1920",
            "0615-1825-1830",
            "0655-0700-1910",
            "0600-0605-1815",
            "0645-0650-1855-1900",
            "0550-0555-1800-1805",
            "0630-0635-1845-1850",
            "0535-0540-1750-1755-1925-1930",
            "0620-0625-1830-1835",
            "0700-0705-1915-1920"
        ); // 0 - 15 (day 97 is same to day 1)
        
        // 11. Download MOD13A1  ftp://ladsweb.nascom.nasa.gov/allData/5/MOD13A1/2014/
        $imageType    = "MOD13A1";
        $dateDownload = array(
            "h28v07",
            "h27v06"
        );
        
        // 12. Download MYD13A1
        $imageType    = "MYD13A1";
        $dateDownload = array(
            "h28v07",
            "h27v06"
        );
        
        // 13. Download MCD64A1 (link from ftp://fire:burnt@fuoco.geog.umd.edu/db/MCD64A1/ University of Maryland not as other 
        // have to change download function
        $imageType    = "MCD64A1";
        $dateDownload = array(
            "h28v07",
            "h27v06"
        );
        
    }
    
    // end function index
    
    // NOTE: This is start function to download by foreach data in tableName to get lastest date (compare with -2 days left) to download
    public function startDownload($imageType, $folderName, $tableName, $outputFolder, $dateDownload, $dateStartDefault) // Start to download MODIS
    {
    $modisHandle = new ModisHandle();
        
	echo "LASTEST TIME NOW IS: " . $modisHandle->getLastDay("org.satorgmyd04"); // get the time of table
        #gọi tới hàm getLastDay trong ModisHandle. Hàm này truy ván trả về giá trị cuối cùng của ngày, Nếu Bảng rỗng hay ko có bản ghi nào thì sẽ thực hiện với dateStartDefault
        $result      = $modisHandle->getLastDay($tableName[0]); // default is index 0 (same MOD04 - MOD07)
        $dateStart   = null;
        
        if ($result == 0) // table is empty
            {
            $dateStart = new DateTime($dateStartDefault); // default date start
        } else {
            // **********************************************
		
	    // FAKE DATE START: 
             $dateStart = new DateTime($modisHandle->getLastDay($tableName[0])); // the lastes date in DB by table name #lấy giá trị ngày cuối cùng trong bảng
            //echo date_format($dateStart, 'Y-m-d') . "\n";
            
	     # DO WE NEED TO DOWNLOAD FROM NEXT DAY, OR FROM THE LATEST DAY AND CHECK THAT IT IS OK TO DOWNLOAD OR NOT
             $dateStart = date_add($dateStart, date_interval_create_from_date_string("1 days")); // download from the next day #+1 để dơn dữ liệu ngày kế tiếp, là dữ liệu chưa có trong CSDL
            
        } // end check if table is empty or not
        
        $dateEnd = date("Y-m-d", strtotime("-1 days")); // 3 days ago (change to 1 day) #dữ liệu theo SATE NASA có sau 3 ngày so với thực tế vì vậy lấy ngày hiện tại trên hệ thống -1 hoặc -3,-2
        
        // TEST FOR 2015-01-29
        $dateEnd = new DateTime($dateEnd); // old is current day -1 DateTime($dateEnd)+ Chuyển về định dạng DATETIME
        // $dateEnd = new DateTime('2015-02-02'); // ************ NOTE: Change date end in here

        while ($dateStart <= $dateEnd) {#duyệt từng ngày
            $dateString = date_format($dateStart, 'Y-m-d'); #format date
            
            $jDay = intval($this->convertDateToJDay($dateString)); // get the int value of $jDay
            $jDay = $this->getjDay($jDay);#thêm 00
            
            $diffDay = date_diff($this->dateMile, $dateStart)->days + 1; 
            #diffDay: đếm số ngày trong khoảng dateMile, dateStart
            // calculate dateMile and dateStart to get the real JDay #tính jday theo mốc của a Bằng hay mốc chu kì 16 ngày
            #từ đó xác định được giờ phiên ảnh tương ứng với ngày dơnload
            $diffDay = $this->getjDay($diffDay);
            
            $dateIndex = $diffDay % 16 - 1; // get the devide of jDay - 1 for the index of array $dateDownload
            $dateIndex = $dateIndex >= 0 ? $dateIndex : 15; // (day % 16 - 1) is = 15 #xác định vị trí index của ngày trong mảng dateDownload=> tính được time phiên ảnh cần down
                        
            $temp = explode("-", $dateString);
            $year = $temp[0]; // get current year      
            // increate $dateStart by 1 day to download next day  in range
	    #gọi tới hàm download 
	    $result = $this->download($dateIndex, $dateDownload, $imageType, $jDay, $year, $outputFolder, $tableName, $dateStart); // download mod04 and mod07

	    // Increase 1 day to download the next day, tăng ngày lên 1 đơn vị và duyệt tiếp
            $dateStart = date_add($dateStart, date_interval_create_from_date_string("1 days"));
            // Start to download image files
            if ($result == 1) {
                return; // because this image type day cannot download then stop (continue to download next imageType), almost is by host doesnot update to current date
            }
	    else if ($result == 2 || $result == 3)	
	    {		
		return; // new images are not exist then stop and download next MYD04
	    }            
        } // end for download
        
    } // end start download
    
    public function getjDay($jDay)
    {
        if ($jDay >= 10 && $jDay < 100) {
            $jDay = "0" . $jDay;
        }
        //009
        else if ($jDay < 10) {
            $jDay = "00" . $jDay;
        }
        return $jDay;
    }
    
    public function echoValue()
    {
        echo "abc";
    }
    
    
    // Download MOD04 and MOD07, MYD04 and MYD07
    public function download($dateIndex, $dateDownload, $imageType, $jDay, $year, $outputFolder, $tableName, $dateStart)
    {
  
	$folderPath = array();
        for ($i = 0; $i < 2; $i++) {# i<2 là MOD04 and MOD07 Hoặc MYD04 and MYD07, trong mảng đã khai báo bên trên
            
            // download images by day and put to folder year      
            $folderYear = $outputFolder[$i] . "/" . $year . "/"; // folder year save download image

            if (!file_exists($folderYear)) {
                mkdir($folderYear, 0777, true);
            }
            
            
            $folderPath[$i] = $folderYear; // . $jDay . "/"; // no need jDay

            // each day create a folder then download all files to this folder
            if (!file_exists($folderPath[$i])) {
                mkdir($folderPath[$i], 0777, true);
            }
        } // end mod04_l2, mod07_l2

        
        // MOD04_L2.A2014135.0210.051.2014135115549.hdf
        // connect to ftp server
        $ftp = ftp_connect("ladsweb.nascom.nasa.gov");
        //ftp://ladsweb.nascom.nasa.gov/allData/51/MOD04_L2/
        
        if (!$ftp) {
            die('could not connect.');
        }
        
        // login
        $r = ftp_login($ftp, "anonymous", "");
        if (!$r) {
            die('could not login.');
        }
        
        // enter passive mode
        $r = ftp_pasv($ftp, true);
        if (!$r) {
            die('could not enable passive mode.');
        }
        
        
        // Get the collection
        
        $ftpPath = array();

	// MOD04_L2    #0: Index đàu tiên trong mảng    
        if ($imageType[0] == "MOD04_L2") { // Note: MYD04_L2 download by collection 6
            $this->collection[0] = "6";
            $ftpPath[0]          = "allData/" . $this->collection[0] . "/$imageType[0]/$year/" . ($jDay) . "/";

            $data = ftp_rawlist($ftp, $ftpPath[0]); // wtf
	    //$data = ftp_nlist($ftp, '.');

	    if ($data == false) {
                echo "$imageType[0]  $ftpPath[0] is not exist! Problem with FPT from ladsweb or This day is not exist, Try another Image type!<br/>";   
		ftp_close($ftp); // close the connection
		return;
		//exit(1);
	    }	
        }
	
	// MYD04_L2
	if ($imageType[0] == "MYD04_L2") { // Note: MYD04_L2 download by collection 6
            $this->collection[0] = "6";
            $ftpPath[0]          = "allData/" . $this->collection[0] . "/$imageType[0]/$year/" . ($jDay) . "/";
        }

	// Neu MOD04, MYD04 ton tai, can check xem MOD07, MYD07 co ton tai khong
	// MOD07_L2, MYD07_L2
        if ($imageType[1] == "MOD07_L2" || $imageType[1] == "MYD07_L2" || $imageType[0] == "MYD04_L2") {		
            $this->collection[1] = "6";
            $ftpPath[1]          = "allData/" . $this->collection[1] . "/$imageType[1]/$year/" . ($jDay) . "/";
	             
            // Only MOD07 have to check first (collection 51 or collection 6)
            $data = ftp_rawlist($ftp, $ftpPath[1]);
            
	          
            if ($data == false) {#nếu ko có dưc liệu collection 6 thì tải dữ liệu collection 51
                echo "$imageType[1] collection 6 is not exist! Try collection 51.....<br/>";
                $this->collection[1] = "51";
                $ftpPath[1]          = "allData/" . $this->collection[1] . "/$imageType[1]/$year/" . ($jDay) . "/";
            } // end try collection 51
        }
        

        $arrTime = explode("-", $dateDownload[$dateIndex]); // time to download of this day # lấy time phiên ảnh cần donload từ index trong mảng dateDownload

        $arrResult = array(); //file result in day to download by $time        

	$modisHandle = new ModisHandle();		
        
        foreach ($arrTime as $time) { #vói mỗi thời gian - phiên ảnh
            
            // FIX Here

	    // Improve: If the images from UET not have then need to download from NASA (only check from MOD04 or MYD04)	
	     $hour = substr($time, 0, 2);#tách giờ + phút
	     $minute = substr($time, 2, 4); 
	   #check date sẽ download từ NASA
	     $checkDate = new DateTime(date_format($dateStart, 'Y-m-d') . ' ' . $hour . ':' . $minute . ':00'); // CHECK THAT DATE WILL BE DOWNLOADED FROM NASA IS INSERT INTO DB FROM GROUND STATION OR NOT, IF NOT THEN DOWNLOAD FROM NASA, NOTE: The time is +- 30 minutes to make sure that file inserted.

	     // TEST Check Date (check file is exist or not in Database)

	     // CHECK DATE RANGE IS EXIT IN DATABASE - SOURCEID = 0 (DATA FROM GROUNDSTATION)
	     $endCheckDate =  new DateTime(date_format($checkDate, 'Y-m-d') . ' ' . $hour . ':' . $minute . ':00');      	   
	     $endCheckDate = $endCheckDate->add(new DateInterval('PT' . '30' . 'M')); // VD: 2015-04-29 03:30:00 -> 2015-04-29 04:00:00
		
	     $startCheckDate =  new DateTime(date_format($checkDate, 'Y-m-d') . ' ' . $hour . ':' . $minute . ':00');
	     $startCheckDate = $startCheckDate->sub(new DateInterval('PT' . '30' . 'M')); // VD: 2015-04-29 03:30:00 -> 2015-04-29 03:00:00	

	     // ******  CHECK THAT IMAGE FROM UET IS RECEIVED OR NOT, IF NOT THEN DO NOTHING BY checkDate is in RANGE from startCheckDate to endCheckDate  **** 

	     $checkFileUETIsExist = 0; // check file UET is exist or not
	     // check is valid
	     if($imageType[0] == 'MOD04_L2' || $imageType[0] == 'MYD04_L2')# chỉ càn check mod,myd 04. Không cần check mod, myd 07
	     {
		 // table name is mod04/myd04, checkdate is datetime need to check is exist or not, startcheckdate is < 30 minute, endcheckdate is < 30 minute from checkDate
		 $checkFileUETIsExist = $modisHandle->checkFileUETIsExist($tableName[0], date_format($checkDate, 'Y-m-d H:i:s'), date_format($startCheckDate, 'Y-m-d H:i:s'), date_format($endCheckDate, 'Y-m-d H:i:s')); // convert date object to string

	     }	    
	
	     if ($checkFileUETIsExist == 1) // = 0 then need to download
	     {
		echo 'EXIST_' . date_format($checkDate, 'Y-m-d H:i:s') . ' is exist on Storage, then not need to download from NASA <br/>';
		continue; // no need to download this file which is already received from UET
	     }
	     
	     echo 'NOT_EXIST_' . date_format($checkDate, 'Y-m-d H:i:s') . ' is not exist on Storage, then need to download from NASA <br/>';

            for ($i = 0; $i < 2; $i++) // mod04_l2, mod07_l2 (only need to check mod04 or myd04 no need to check mod07/myd07)
            {

		// Notice collection of MOD07 (6 sometime don't have it)		
                $data = ftp_rawlist($ftp, $ftpPath[$i]); // get all list image data then filter by $dateDownload

		$check = is_array($data) ? 0 : 1; // 0 is good: array, 1 is bad: not array
		if($check == 1) // day is not exist then return and download MYD04
		{
		    echo $ftpPath[$i] . " is not exist! Then not download MOD07!....<br/>";
		    return 2; // return 2 mean it stop at this day
		}
        
	        foreach ($data as $item) {
                    
                    // ***************************************************************
                    // Because this day may not be existed so quit
                    if (!is_array($data)) // check if data ftp file need to download
                        {
                       
                        echo "-------------------------------------------------------------------- $jDay is not downloadable day! -------------------------------------------------------------------- <br/>"; 
                        return 1; // error no need to continue to download
                        
                    } // end is array    
                    // iterate time of day to download
                    $array    = preg_split("/\s+/", $item, 9);
                    $fileName = $array[8];
                    // Get the file name time
                    $temp     = explode(".", $fileName);
                    $fileTime = $temp[2]; // get file time to compare with input time array
                    // compare file time and time to download
                    if (strpos($fileTime, $time) !== false) {
                        //push file item to $arrResult
                        $arrResult[] = $item;
                    }
                } //end foreach $data
            } // end foreach mod04_mod07
        } // end foreach arrTime
        
        //-----------------------------------------------
        
        $errorArray = array();
        
        // successArray to store success link
        $successArray = array();
        
        $fileNameNoExtension = ""; // fileNameNoExtension
        
        
        // NOTE: ****************************************************
        // Check if $arrResult is no value then this day has files to download but current now file is not exist
        /*if (count($arrResult) == 0) {
            echo "$jDay is exist in Ladsweb FTP but file need to download not exist!";
            return 3; // 3 mean that JDay is exist but file need to download not exist
        } // end check if this day has file need to download
        */
        
        
        // iterate arrayResult to download to output folder $folderPath
        
        echo "-------------------------------------------------------------------- JDAY: " . $jDay . " is downloading ---------------------------------------------------------------------------- <br/>";
        
	$j = 0; // count that it is even than download MOD04, odd download MOD07
        // MOD04_L2
        $index = 0; // choose to download mod04 or mod07
	foreach ($arrResult as $result) {
     	  
	    if($j % 2 == 0)
	    {
		$index = 0; // download mod04	
	    }
	    else
	    {
		$index = 1; // download mod07
	    }

	    $j++; // increase j to next mod04 or mod07
		
            // ob_start();  // start buffer
            $array = preg_split("/\s+/", $result, 9);
            
            $fileName = $array[8];
           
            // get file name without extension
            
            $fileNameNoExtension = basename($fileName, ".hdf");
            
            // default is collection 51
            
            // collection get from above when choose the ftp folder to download
            $downloadFile = "ftp://ladsweb.nascom.nasa.gov/allData/" . $this->collection[$index] . "/" . $imageType[$index] . "/" . $year . "/" . $jDay . "/" . $fileName; // no need jDay . $jDay . "/"
   
	    $outputValue = "";
	    $returnValue = "";   
           
 	        echo $downloadFile . "<br/>"; 

                $output = shell_exec('wget -q -N -P ' . $folderPath[$index] . $fileNameNoExtension . ' ' . $downloadFile . ' && echo $?');

		

		// Default is sucess (i don't care if error)

		echo date('h-i-s:d-m-Y') . "," . $fileName . ",0" . "<br/>";
                $successArray[] = $folderPath[$index] . $fileNameNoExtension . '/' . $fileName; // push success download file to handle
            
            // print output to view the data download
	    
            ob_flush();
            flush();
            
            // flush the output to screen
            // ob_end_flush(); 
        } // end result
        
        
        // *****        
        
        ftp_close($ftp); // download success all then close ftp connection
	echo "download successful!";

        // Download image type is finish
     
        
        // It is ok now, then now to sat_handle file (only need to create output files and insert to database)
        // NOTE: because all variable is changed, only filePath is not changed so need to remake it again
        // NOTE: DOWNLOAD ALL IMAGES ON DAY THEN HANDLE LATTER

	$j = 0; // check if download mod04 or download mod07 successful!
	$index = 0;

	$fileResample = array();
        foreach ($successArray as $filePath) {
	    if ($j % 2 == 0)
	    {	
		$index = 0; // download mod04
	    }				
	    else
	    { 
		$index = 1;  // download mod07
	    }
	    

            $modisHandle         = new ModisHandle();
            $folderPath          = dirname($filePath) . "/";
            // filePath is path to file success download
            // folderPatth is path to folder file
            // imageType is MOD04, MYD04....
            // hdf: default extension
            $fileName            = basename($folderPath);
            $fileNameNoExtension = basename($fileName, ".hdf"); // get satType from fileName

	    $array = [$fileNameNoExtension, $filePath, $folderPath, $imageType[$index], ".hdf", $tableName[$index], $this->collection[$index]];
	    echo "<pre>";
	    echo "</pre>";
	    $sourceid = 0; // NOTE: Default is 0: NASA (source image)
			
            if ($index == 0)
	    {	
            	// NOTE: Class MODISHandle to hanlde downloaded image	    
            	$fileResample[0] = $modisHandle->index($fileNameNoExtension, $filePath, $folderPath, $imageType[$index], ".hdf", $tableName[$index], $this->collection[$index], $sourceid); // default is ".hdf"
	    }
	    else
	    {
		// MOD07
		$fileResample[1] = $modisHandle->index($fileNameNoExtension, $filePath, $folderPath, $imageType[$index], ".hdf", $tableName[$index], $this->collection[$index], $sourceid); // default is ".hdf"
	    }	 
		
	    if($j % 2 == 1)  // it finished resample mod04, mod07 then print
	    {
	        echo "Interpolation " . $fileResample[0] . " " . $fileResample[1] . "<br/>"; // fileResampe[0]: mod04, fileResample[1]: mod07
	
		// CHECK that MODIS04 is exist in table prodpm.prodmodispm_vn_collection0, if not then run HAPV script AodToPm.R

		// Check fileResamp[0] is exist	
		

		// 0: mod/myd, 1: file mod04/myd04, 2: file mod07/myd07 <---------------- NOTE: 2015/03/20 (MUST DO)
		$type = $imageType[0]; // check if type is contain mod or myd
		if (strpos($type,'MOD') !== false) {
			$type = "mod";
		}
		else
		{
			$type = "myd";
		}
		
		$sourceid = 0; // # NOTE: download from NASA, 1 mean copy file from Ground Station

		$out = shell_exec($this->create_pm_cmd . $type . " "  . $fileResample[0] . " " . $fileResample[1] . " " . $sourceid);
	
		echo $this->create_pm_cmd . $type . " "  . $fileResample[0] . " " . $fileResample[1] . " " . $sourceid;

		//run script with parameter
		/*Rscript /var/www/html/MODIS/HaPV/AodToPm.R /var/www/fimo/apom/Resample/SatResampMOD04/2013/MOD04_L2.A2013360.0340.051.2013360151630/MOD04_L2.A2013360.0340.051.2013360151630.hdf_DT_10km.tif /var/www/fimo/apom/Resample/SatResampMOD07/2013/MOD07_L2.A2013360.0340.005.2013360151010/MOD07_L2.A2013360.0340.005.2013360151010.hdf_T_10km.tif	
		*/


		echo "<br/> GOOD: Create successful PM Image!" . "<br/>";		
	    }
	
	     $j++; // increase index


	    // need file resample?	
	    
        } // end foreach successArray
        
        return 0; // not error
        
    } // end function download file
    
    public function printValue($data)
    {
        echo "<pre>";
        print_r($data);
        echo "</pre>";
        
        //exit(1);
    }
    
    public function convertDateToJDay($date)
    {
        $array = explode("-", $date);
        
        $year  = $array[0];
        $month = $array[1];
        $day   = $array[2];
        
        $d = array();
        
        if ($this->is_leap_year($year)) {
            $d = array(
                31,
                29,
                31,
                30,
                31,
                30,
                31,
                31,
                30,
                31,
                30,
                31,
                30
            );
        } else {
            $d = array(
                31,
                28,
                31,
                30,
                31,
                30,
                31,
                31,
                30,
                31,
                30,
                31,
                30
            );
        }
        
        $jDay = 0;
        
        $count    = 1;
        $monthDay = 0;
        for ($i = 0; $i < 12; $i++) {
            if ($count >= $month) {
                break;
            } else {
                // Sum total month from January to current $month
                $monthDay = $monthDay + $d[$i];          
                $count++;
            }
        }
        
        // after all sum $monthDay with $day
        $jDay = $monthDay + $day;
        
        return $jDay;
    }
    
    // end function convert date to jDay
    
    function is_leap_year($year)
    {
        return ((($year % 4) == 0) && ((($year % 100) != 0) || (($year % 400) == 0)));
    }
    
}
?>

