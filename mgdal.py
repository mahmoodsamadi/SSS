from osgeo import gdal, ogr, osr
import sys,time
import numpy as np

class read_raster():
	def __init__(self, raster):
		self.raster = raster
		self.graster = gdal.Open(self.raster)
		self.band = self.graster.GetRasterBand(1)
		self.stats = self.band.GetStatistics( True, True )
	def stat(self):
		return {'min':self.stats[0],'max':self.stats[1],'mean':self.stats[2],'std':self.stats[3]}

	def tonp(self):
		return self.band.ReadAsArray().astype('float32')

	def getnodata(self):
		ds = gdal.Open(self.raster)
		band = ds.GetRasterBand(1)
		nodata = band.GetNoDataValue()
		myarray1 = np.array(band.ReadAsArray()).astype('float32')
		myarray1[myarray1 == nodata] = np.nan 
		return myarray1

	def array2raster(self, rasterfn,newRasterfn,array,nodata):

		raster = gdal.Open(rasterfn)
		geotransform = raster.GetGeoTransform()
		originX = geotransform[0]
		originY = geotransform[3]
		pixelWidth = geotransform[1]
		pixelHeight = geotransform[5]
		cols = raster.RasterXSize
		rows = raster.RasterYSize

		driver = gdal.GetDriverByName('GTiff')
		outRaster = driver.Create(newRasterfn, cols, rows, 1, gdal.GDT_Float32)	#gdal.GDT_Byte or gdal.GDT_Float32
		outRaster.SetGeoTransform((originX, pixelWidth, 0, originY, 0, pixelHeight))
		outband = outRaster.GetRasterBand(1)
		outband.SetNoDataValue(nodata)
		outband.WriteArray(array)
		outRasterSRS = osr.SpatialReference()
		outRasterSRS.ImportFromWkt(raster.GetProjectionRef())
		outRaster.SetProjection(outRasterSRS.ExportToWkt())
		outband.FlushCache()

def raster2array(raster):
	return myraster_to_array(raster)
def myraster_to_array(raster_path1):
	ds = gdal.Open(raster_path1)
	band = ds.GetRasterBand(1)
	nodata = band.GetNoDataValue()
	myarray1 = np.array(band.ReadAsArray()).astype('float32')
	myarray1[myarray1 == nodata] = np.nan 
	return myarray1


def array2raster(rasterfn,newRasterfn,array):

		raster = gdal.Open(rasterfn)
		band = raster.GetRasterBand(1)
		nodata = band.GetNoDataValue()

		geotransform = raster.GetGeoTransform()
		originX = geotransform[0]
		originY = geotransform[3]
		pixelWidth = geotransform[1]
		pixelHeight = geotransform[5]
		cols = raster.RasterXSize
		rows = raster.RasterYSize

		driver = gdal.GetDriverByName('GTiff')
		outRaster = driver.Create(newRasterfn, cols, rows, 1, gdal.GDT_Float32)	#gdal.GDT_Byte or gdal.GDT_Float32
		outRaster.SetGeoTransform((originX, pixelWidth, 0, originY, 0, pixelHeight))
		outband = outRaster.GetRasterBand(1)
		outband.SetNoDataValue(nodata)
		outband.WriteArray(array)
		outRasterSRS = osr.SpatialReference()
		outRasterSRS.ImportFromWkt(raster.GetProjectionRef())
		outRaster.SetProjection(outRasterSRS.ExportToWkt())
		outband.FlushCache()


def write_info(file):
	import gdalinfo2
	gdalinfo2.main(file)

def reclassify(file,classes):
	rArray = myraster_to_array(file)
	a = rArray
	classes[-1] = [classes[-1][0],classes[-1][1] + 1,classes[-1][2]]
	for x in classes:
		#a[np.where((a >= x[0]) & (a < x[1]))] =x[2]
		a[((a >= x[0]) & (a < x[1]))] = x[2]
	return a




if __name__ == '__main__':

	file = r"bb.tif"
	classes =[[0,500,1.0],[2500,3000,2.0],[3000,4000,3.0]]
	a = reclassify(file,classes)
	array2raster(file,"rrr.tif",a)
	write_info("rrr.tif")

	input()
	greader = read_raster('a.tif')
	min = greader.stat()['min']
	max = greader.stat()['max']

	print min,max

	m='''
	rasterfn = 'Slope.tif'
	newValue = 0
	newRasterfn = 'SlopeNew.tif'

	# Convert Raster to array
	rasterArray = raster2array(rasterfn)

	# Get no data value of array
	noDataValue = getNoDataValue(rasterfn)

	# Updata no data value in array with new value
	rasterArray[rasterArray == noDataValue] = newValue

	# Write updated array to new raster
	array2raster(rasterfn,newRasterfn,rasterArray)
	'''
	input()