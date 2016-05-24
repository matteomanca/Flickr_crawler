import urllib, json, csv, datetime,sys
import pyproj as pyproj
import unicodedata

import codecs

reload(sys)
sys.setdefaultencoding('utf-8')
if sys.stdout.encoding is None:
	sys.stdout = codecs.open("/dev/stdout", "w", 'utf-8')

# I need to convert the photo coordinates also in UTMZ31N_ETRS89 format. for this I will use pyproj
"""
INSTALL pyproj:

- Download pyproj from https://github.com/jswhit/pyproj
- python setup.py build
- python setup.py install (with sudo if necessary).

SOME CHECK:

-  SEE http://all-geo.org/volcan01010/2012/11/change-coordinates-with-pyproj/ for more info
- results are ok if compared with those of http://spatialreference.org/ref/epsg/wgs-84-utm-zone-31n/
## and to http://tool-online.com/en/coordinate-converter.php

"""

"""Convert lat and long coordinate in UTMZ31N_ETRS89 format """
def wgsToUTM(long, lat):
	wgs84=pyproj.Proj("+init=EPSG:4326")
	UTMZ31N_ETRS89=pyproj.Proj("+init=EPSG:25831")
	x, y = pyproj.transform(wgs84, UTMZ31N_ETRS89, float(long), float(lat))
	return [x,y]


def get_photo_info(photo_id):
#    print "photo_id ", photo_id
    global locationsToCheck
    try:
        url_info_api = "https://api.flickr.com/services/rest/?method=flickr.photos.getInfo&api_key="+str(apiKey)+"&photo_id="+photo_id+"&format=json&nojsoncallback=1"
	print url_info_api
	response_info = urllib.urlopen(url_info_api)
        photo_info = json.loads(response_info.read())
        createdAt = ""
	userId = photo_info["photo"]["owner"]["nsid"]
	if "taken" in photo_info["photo"]["dates"]:
		createdAt = datetime.datetime.strptime(photo_info["photo"]["dates"]["taken"],"%Y-%m-%d %H:%M:%S").strftime('%Y-%m-%dT%H:%M:%S')
        lat = photo_info["photo"]["location"]["latitude"]
        lon = photo_info["photo"]["location"]["longitude"]
        UTMZ31N = wgsToUTM(lon,lat)
	user_location = "NOT-AVAILABLE"
	if "location" in photo_info["photo"]["owner"]:
		if photo_info["photo"]["owner"]["location"] != "":
			user_location = photo_info["photo"]["owner"]["location"]

#################################
##Initially a user is defined a tourist if her location is not in locationsToCheck list
## Then, the field tourist has been re-computed with a new algorithm implemented in the setTouristUser.py script
 	if any(location.lower() in user_location.lower() for location in locationsToCheck) :
		tourist=0 ## NO TOURIST
	else:
		tourist=1
#################################
#################################
 	return [photo_id, createdAt.encode('utf-8'),UTMZ31N[0], UTMZ31N[1], lat,lon, userId, user_location.encode('utf-8'), tourist]
    except:
        print "Error photo info ", sys.exc_info()[0]
        pass



locationsToCheck = ["bcn", "barcelona", "badalona", "hospitalet"]

"""CREATE YOUR FLICKR API KEY: 
https://www.flickr.com/services/api/misc.api_keys.html """

apiKey = "YOUR-FLICKR-API-KEY"

# Barcelona bounding box
min_lon =2.069526
min_lat =41.320004
max_lon =2.228010
max_lat = 41.469576
page=1

outfile = "flickr_data.csv"
csvfile = open(outfile, 'wb')

bkpPhotoFileName = "flickrDataOriginal.json" # 11 and 12 are months
bkpPhotoFile = open(bkpPhotoFileName, 'wb')

filewriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
filewriter.writerow(["photoid", "createdAt", "utmz31n_1", "utmz31n_2" , "lat", "long", "userId", "userLocation", "tourist"])    #change the column labels here

days_per_month = {"1":31,"2":28,"3":31,"4":30,"5":31,"6":30,"7":31,"8":31,"9":30,"10":31,"11":30,"12":31,}

##set starting and end months
for month in range(11,13):
	for day in range(1,days_per_month[str(month)]):
		min_taken_date = "2015-" + str(month) + "-" + str(day)
		max_taken_date = "2015-" + str(month) + "-" + str(day+1)
		try:
			url = "https://api.flickr.com/services/rest/?method=flickr.photos.search&api_key="+str(apiKey)+"&min_taken_date=" + str(min_taken_date) + "&max_taken_date=" + str(max_taken_date) + "&bbox="+ str(min_lon) + ","+ str(min_lat) + ","+ str(max_lon) + "," + str(max_lat)+ "&per_page=250&format=json&nojsoncallback=1&page="+str(page)
			print url
			response = urllib.urlopen(url)
			data = json.loads(response.read())
			print "Pages: ", data["photos"]["pages"]
			pages = data["photos"]["pages"]
		except:
			print "Error ", sys.exc_info()[0]
		for current_page in range(1,pages+1):
			print str(current_page) + " of " + str(pages)
			try:
				url = "https://api.flickr.com/services/rest/?method=flickr.photos.search&api_key="+str(apiKey)+"&min_taken_date=" + str(min_taken_date) + "&max_taken_date=" + str(max_taken_date) + "&bbox="+ str(min_lon) + ","+ str(min_lat) + ","+ str(max_lon) + "," + str(max_lat)+ "&per_page=250&format=json&nojsoncallback=1&page="+str(current_page)
				print "\n\n" + url
				response = urllib.urlopen(url)
				data = json.loads(response.read())
				json.dump(data, bkpPhotoFile)
				bkpPhotoFile.flush()
				numOfPhotos = len(data["photos"]["photo"])
				for i in range(1, numOfPhotos):
				    photo_id = data["photos"]["photo"][i]["id"]
				    record = get_photo_info(photo_id)
				    filewriter.writerow(record)
				    csvfile.flush()
			except:
				print "Error main ",  sys.exc_info()[0]
				pass
csvfile.close()
bkpPhotoFile.close()
