import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import QtGui, QtCore
import sys, os
import numpy as np
import matplotlib.pyplot as plt
from osgeo import gdal, ogr, osr
import mgdal

from imgshow import *


#######
mcurrenttabindex = 0
sidebaritems = {}
all_layers = {}		#all_layers[base_name]=path
AHP_result = {}		#AHP_result["CI"], AHP_result["wheights"]
headers = []
layer_reclasses={}

user_changed_ahp_weights = 0

#data_dic = {'name':{'weight','classes','np_','np_reclassed'}}
#data_dic.setdefault("a", {})['weight'] = 122
data_dic = {}

#######


class dockdemo(QMainWindow):
   def __init__(self, parent = None):
      super(dockdemo, self).__init__(parent)


      self.allpages = {0:["layers",base_Tab()], 1:["AHP",AHP_Tab()], 2:["Results",AHP_Result()], 3:["reclass",reclass_w()], 4:["output setting",Output_Setting()], 5:["output results",Output_results()]}
   ### globals
      global tabWidget, files_items,user_changed_ahp_weights
	
   ### toolbar
      self.layout = QHBoxLayout()
      self.bar = self.menuBar()
      self.file = self.bar.addMenu("File")

      self.testAct = QAction('&Test', self)
      self.testAct.setShortcut('Ctrl+O')
      self.testAct.setStatusTip('Open Directory')
      self.testAct.triggered.connect(test)
      self.file.addAction(self.testAct)

      self.testAct = QAction('E&xit', self)
      self.testAct.setShortcut('Ctrl+Q')
      self.testAct.setStatusTip('Exit the application')
      self.testAct.triggered.connect(self.close)
      self.file.addAction(self.testAct)



      self.view_menu = self.bar.addMenu('&Tools')
      self.viewAct = QAction('&ROC plot', self)
      self.viewAct.setShortcut('Ctrl+R')
      self.viewAct.setStatusTip('draw ROC curve')
      self.viewAct.triggered.connect(test)
      self.view_menu.addAction(self.viewAct)


   #right dock list
      self.items = QDockWidget("Steps", self)

      dockwidget_action = self.items.toggleViewAction()
      self.view_menu = self.bar.addMenu('&View')
      self.view_menu.addAction(dockwidget_action)


      self.listWidget = QListWidget()
      for x in xrange(len(self.allpages)):
	self.listWidget.addItem(self.allpages[x][0])

      for index in xrange(self.listWidget.count()):
	mtext = str(self.listWidget.item(index).text())
	sidebaritems[index] = self.listWidget.item(index)
	self.listWidget.item(index).setBackground(QtGui.QColor(239,165,184))
	self.listWidget.item(index).mindex = index


      self.items.setWidget(self.listWidget)
      self.items.setFloating(False)
      self.items.setMinimumWidth(60)
      self.items.setMaximumWidth(150)

      self.listWidget.itemClicked.connect(self.item_click)

   ### add tabs
      self.tabWidget = QtGui.QTabWidget()
      self.myBoxLayout = QtGui.QVBoxLayout()
      self.tabWidget.setLayout(self.myBoxLayout)


      self.tabs = {}
      for x in xrange(len(self.allpages)):
	self.tabs[self.allpages[x][0]] = self.allpages[x][1]
	self.tabWidget.addTab(self.tabs[self.allpages[x][0]], self.allpages[x][0])
      self.tabWidget.tabBar().hide()


      self.tabWidget.connect(self.tabWidget, SIGNAL('currentChanged(int)'), self.ontabchanged)


   ### do
      self.setCentralWidget(self.tabWidget)
      self.addDockWidget(Qt.RightDockWidgetArea, self.items)
      self.setLayout(self.layout)
      self.setWindowTitle("GEO_AHP")


   def ontabchanged(self,e):
	return

   def item_click(self, item):
	return







def extract_value_to_point(rast,fc):
    import struct
    ds=gdal.Open(rast)
    prj=ds.GetProjection()
    srs1=osr.SpatialReference(wkt=prj)


    driver = ogr.GetDriverByName('ESRI Shapefile')
    dataset = driver.Open(fc)
    layer = dataset.GetLayer()
    spatialRef = layer.GetSpatialRef()

    IsSame = spatialRef.IsSame(srs1) 

    if IsSame !=1:
	print 'Spatial Reference of two Shapefile and Result raster is not same'
	#####return 3



    values = []
    coords = []

    #open vector layer
    drv=ogr.GetDriverByName('ESRI Shapefile') #assuming shapefile?
    ds=drv.Open(fc,True) #open for editing
    lyr=ds.GetLayer(0)

    #open raster layer
    src_ds=gdal.Open(rast) 
    gt=src_ds.GetGeoTransform()
    rb=src_ds.GetRasterBand(1)
    gdal.UseExceptions() #so it doesn't print to screen everytime point is outside grid

    for feat in lyr:
        geom=feat.GetGeometryRef()
        mx=geom.Centroid().GetX()
        my=geom.Centroid().GetY()

        px = int((mx - gt[0]) / gt[1]) #x pixel
        py = int((my - gt[3]) / gt[5]) #y pixel

        structval=rb.ReadRaster(px,py,1,1,buf_type=gdal.GDT_Float32) #Assumes 32 bit int- 'float'
        intval = struct.unpack('f' , structval) #assume float
        val=intval[0]

        try: #in case raster isnt full extent
            structval=rb.ReadRaster(px,py,1,1,buf_type=gdal.GDT_Float32) #Assumes 32 bit int- 'float'
            intval = struct.unpack('f' , structval) #assume float
            val=intval[0]
        except:
            val=-9999 #or some value to indicate a fail
	#print val

	values.append(val)
	coords.append([px,py])

	feat.SetField('YOURFIELD',val)
	lyr.SetFeature(feat)

    src_ds=None
    ds=None
    return values,coords





class ROCdialog(QDialog):
    def __init__(self):
        super(ROCdialog, self).__init__()

	self.setGeometry(50,50,600,600)
	layout = QVBoxLayout(self)
	self.viewer = PhotoViewer(self)
	layout.addWidget(self.viewer)

	self.True_shp = fileItem(mlabel='True point file',filetypes=['shp'])
	#True_shp.setTitle("filesItem")
	layout.addWidget(self.True_shp)
   
	self.False_shp = fileItem(mlabel='False point file',filetypes=['shp'])
	layout.addWidget(self.False_shp)

	button_1 = QtGui.QPushButton()
	button_1.setText('Run')
	button_1.clicked.connect(self.myfunc)
	layout.addWidget(button_1)

	self.viewer.fitInView()
	self.setWindowTitle("Dialog")
	self.setWindowModality(Qt.ApplicationModal)
	self.exec_()

    def myfunc(self):

		self.True_shp_path = self.True_shp.path
		self.False_shp_path = self.False_shp.path

		#self.viewer.setPhoto(QtGui.QPixmap('a.png'))
		raster_filename='dem1.tif'
		print "------------------"
		print type(self.False_shp_path)
		print self.True_shp_path
		print "------------------"
		raster_filename = str(ex.tabs['output setting'].folderitem.get_dirpath()) + "/result.tif"
		true_p = extract_value_to_point(raster_filename,self.True_shp_path.replace('/','\\'))
		false_p = extract_value_to_point(raster_filename,self.False_shp_path.replace('/','\\'))

		print true_p
		print type(true_p[0])
		true_ = [1]*len(true_p[0])
		print true_

		false_ = [-1]*len(false_p[0])
		data = zip(true_,true_p[0]) + zip(false_,false_p[0])
		print data

		from pyroc import ROCCalc
		roc = ROCCalc(data,linestyle='bo-') #linestyle='bo-'
		roc.plot('ROC_t.png',title='ROC curve (in training step)') # create a plot of the ROC curve
		auc_t = roc.auc()
		self.viewer.setPhoto(QtGui.QPixmap('ROC_t.png'))



class base_Tab(QtGui.QWidget):
    def __init__(self, parent=None):
        super(base_Tab, self).__init__(parent)
        self.layout = QVBoxLayout(self)


        self.files_items = filesItem()
        self.files_items.setTitle("filesItem")

        self.scroll = QtGui.QScrollArea()
        self.scroll.setWidget(self.files_items)
        self.scroll.setWidgetResizable(True)
        #scroll.setFixedHeight(400)
        self.layout.addWidget(self.scroll)

        self.setLayout(self.layout)






	self.mybox = createGroupBox(self.layout, "Run box")
	self.mybox.addWidget(createButton("Cancel", self.cancel))
	self.mybox.addWidget(createButton("Next", self.run))

    def print_row(self, item):
	return

    def run(self):
	mindex = 0
	is_completed = check_this_page(mindex)
	if is_completed != 1:
		return
	else:
		update_AHP()
		ex.tabWidget.setCurrentIndex(1)


    def cancel(self):
	ex.close()


class AHP_Tab(QtGui.QWidget):
    def __init__(self, parent=None):
        super(AHP_Tab, self).__init__(parent)
        self.layout = QVBoxLayout(self)


	self.update_table(6, 6)
    def update_table(self,rows, columns,Hlables=[],Vlables=[]):
	for i in reversed(range(self.layout.count())): 
		self.layout.itemAt(i).widget().setParent(None)

        #rows, columns = 6,6
        #self.table = QTableWidget(3, 1)
        self.table = QtGui.QTableWidget(rows, columns)
        self.table.setHorizontalHeaderLabels(Hlables)
        self.table.setVerticalHeaderLabels(Vlables)
        for column in range(columns):
            for row in range(rows):
		if row == column:
			mvalue = 1
                	item = QtGui.QTableWidgetItem()
			item.setData(QtCore.Qt.DisplayRole, "%s" %(mvalue) )
			item.setData(QtCore.Qt.EditRole, mvalue)

                	#item.setFlags(QtCore.Qt.ItemIsEnabled)
			item.setFlags(QtCore.Qt.ItemIsEnabled)
                	item.setBackground(QtGui.QColor(183,183,183))
                	self.table.setItem(row, column, item)
			continue
		elif row > column:
			mvalue = 1
                	item = QtGui.QTableWidgetItem()
			item.setData(QtCore.Qt.DisplayRole, "%s" %(mvalue) )
			item.setData(QtCore.Qt.EditRole, mvalue)

                	#item.setFlags(QtCore.Qt.ItemIsEnabled)
			item.setFlags(QtCore.Qt.ItemIsEnabled)
                	item.setBackground(QtGui.QColor(183,183,183))
                	self.table.setItem(row, column, item)
			continue
		else:
			mvalue = 1
                	item = QtGui.QTableWidgetItem()
			item.setData(QtCore.Qt.DisplayRole, "Row: %s" %(mvalue) )
			item.setData(QtCore.Qt.EditRole, mvalue)

                	#item.setFlags(QtCore.Qt.ItemIsEnabled)
			item.setFlags(QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled)
                	item.setBackground(QtGui.QColor(240,240,240))
                	#self.table.setItem(row, column, item)

                	combo = QtGui.QComboBox()
			combo.activated[str].connect(self.onActivated)        
         
                	combo_box_options = ['1','2','3','4','5','6','7','8','9','1/2','1/3','1/4','1/5','1/6','1/7','1/8','1/9']
                	for t in combo_box_options:
                		combo.addItem(t)
                	self.table.setCellWidget(row, column,combo)

			mvalue = 1
                	item = QtGui.QTableWidgetItem()
			item.setData(QtCore.Qt.DisplayRole, "%s" %(mvalue) )
			item.setData(QtCore.Qt.EditRole, mvalue)

                	#item.setFlags(QtCore.Qt.ItemIsEnabled)
			item.setFlags(QtCore.Qt.ItemIsEnabled)
                	item.setBackground(QtGui.QColor(183,183,183))
                	self.table.setItem(row, column, item)




			continue


        self.layout.addWidget(self.table)

        self.statusLabel = QtGui.QLabel("info:")
        self.layout.addWidget(self.statusLabel)

        self.setLayout(self.layout)

	self.mybox = createGroupBox(self.layout, "Run box")
	self.mybox.addWidget(createButton("Back", self.back))
	self.mybox.addWidget(createButton("Next", self.run))

    def onActivated(self, text):
	global user_changed_ahp_weights
	user_changed_ahp_weights = 1
	text = str(text)
        print (text)
        button = QtGui.qApp.focusWidget()
        # or button = self.sender()
        index = self.table.indexAt(button.pos())
	mrow=index.row()
	mcol=index.column()

	##### set table item not combo
	mvalue = str(text)
        item = QtGui.QTableWidgetItem()
	item.setData(QtCore.Qt.DisplayRole, "%s" %(mvalue) )
	item.setData(QtCore.Qt.EditRole, mvalue)

        item.setFlags(QtCore.Qt.ItemIsEnabled)
        item.setBackground(QtGui.QColor(183,183,183))
        self.table.setItem(mrow, mcol, item)

        if index.isValid():
        	print(index.row(), index.column())
        	print(index.row(), index.column())
		#item = self.table.item(index.row(), index.column())
		#print str(item.text())
		mydic = {'1/7': '7', '1/6': '6', '1/5': '5', '1/4': '4', '1/3': '3', '1/2': '2', '1/9':'9', '1/8': '8', '1': '1', '3': '1/3', '2': '1/2', '5': '1/5', '4': '1/4', '7':'1/7', '6': '1/6', '9': '1/9', '8': '1/8'}
#########
		mvalue = mydic[text]
                item = QtGui.QTableWidgetItem()
		item.setData(QtCore.Qt.DisplayRole, "Row: %s" %(mvalue) )
		item.setData(QtCore.Qt.EditRole, mvalue)

                item.setFlags(QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled)
                item.setBackground(QtGui.QColor(240,240,240))
                self.table.setItem(mcol,mrow,item)

	self.cancel()


    def run(self):
	myindex = 1
	isok = check_this_page(myindex)
	if isok == 0:
		return
	else:
		table = self.table
		aaa = table2list(table)
		names = ex.tabs['layers'].files_items.getall(1)
		for i,x in enumerate(names):
			aaa[i].insert(0,x)
		aaa.insert(0,names)
		aaa[0].insert(0,'')

		f=open('www.csv','w')
		for r in aaa:
			for col in r:
				f.write('"%r",'%col)
			f.write('\n')

		f.close()

		ex.tabWidget.setCurrentIndex(2)
		ex.tabs['Results'].update_table()

    def back(self):
	ex.tabWidget.setCurrentIndex(0)

    def cancel(self):
	table_data = []
	for row in range(ex.tabs['AHP'].table.rowCount()):
		rowdata = []
		for column in range(ex.tabs['AHP'].table.columnCount()):
			item = ex.tabs['AHP'].table.item(row, column)
			mydic = {'0':1,'2': 2, '9': 9, '8': 8, '1': 1, '3': 3, '1/3': 0.3333333333333333, '1/2': 0.5, '1/5': 0.2, '1/4': 0.25, '1/7': 0.14285714285714285, '1/6': 0.16666666666666666, '1/9': 0.1111111111111111, '1/8': 0.125, '7': 7, '6': 6, '5': 5,'4': 4}
			print '0000',str(item.text()),mydic[str(item.text())]
			item = mydic[str(item.text())]
			rowdata.append(float(str(item)))
		print rowdata
		table_data.append(rowdata )
	headers = []
	for column in range(ex.tabs['AHP'].table.columnCount()):
                    header = ex.tabs['AHP'].table.horizontalHeaderItem(column)
                    if header is not None:
                         headers.append(str(header.text()))
	print headers

	table_data = np.array(table_data)
	calc_AHP(table_data,headers)

	ex.tabs['AHP'].statusLabel.setText("C.I is: %s"%AHP_result['CI'])


class AHP_Result(QtGui.QWidget):
    def __init__(self, parent=None):
        super(AHP_Result, self).__init__(parent)
        self.layout = QVBoxLayout(self)


    def update_table(self):
	Vlables=["layer name","weight"]
	for i in reversed(range(self.layout.count())): 
		self.layout.itemAt(i).widget().setParent(None)


	Hlables = AHP_result["wheights"].keys()
	wheights = AHP_result["wheights"].values()
	print 111,Hlables,wheights
        self.table = QtGui.QTableWidget(2, len(Hlables))
        #self.table.setHorizontalHeaderLabels(Hlables)
        self.table.setVerticalHeaderLabels(Vlables)
        for column in range(len(wheights)):
			mvalue = str(wheights[column])
                	item = QtGui.QTableWidgetItem()
			item.setData(QtCore.Qt.DisplayRole, "%s" %(mvalue) )
			item.setData(QtCore.Qt.EditRole, mvalue)

                	#item.setFlags(QtCore.Qt.ItemIsEnabled)
			item.setFlags(QtCore.Qt.ItemIsEnabled)
                	item.setBackground(QtGui.QColor(183,183,183))
                	self.table.setItem(1, column, item)

        for column in range(len(Hlables)):
			mvalue = Hlables[column]
                	item = QtGui.QTableWidgetItem()
			item.setData(QtCore.Qt.DisplayRole, "%s" %(mvalue) )
			item.setData(QtCore.Qt.EditRole, mvalue)

                	#item.setFlags(QtCore.Qt.ItemIsEnabled)
			item.setFlags(QtCore.Qt.ItemIsEnabled)
                	item.setBackground(QtGui.QColor(183,183,183))
                	self.table.setItem(0, column, item)

        self.layout.addWidget(self.table)
        self.setLayout(self.layout)

	self.mybox = createGroupBox(self.layout, "Run box")
	self.mybox.addWidget(createButton("Back", self.back))
	self.mybox.addWidget(createButton("Next", self.run))

    def run(self):
	sidebaritems[2].setBackground(QtGui.QColor(0,255,0))
	ex.tabWidget.setCurrentIndex(3)
	ex.tabs['reclass'].update_table()

    def back(self):
	ex.tabWidget.setCurrentIndex(1)


class myListWidget(QListWidget):
   def Clicked(self,item):
      QMessageBox.information(self, "ListWidget", "You clicked: "+item.text())

class reclass_w(QtGui.QWidget):
    def __init__(self, parent=None):
        super(reclass_w, self).__init__(parent)
        self.layout = QVBoxLayout(self)


    def update_table(self):
	Vlables=["layer name","weight"]
	for i in reversed(range(self.layout.count())): 
		self.layout.itemAt(i).widget().setParent(None)


	Hlables = AHP_result["wheights"].keys()
	wheights = AHP_result["wheights"].values()
	layers = AHP_result["wheights"].keys()

        self.table = QtGui.QTableWidget(len(layers), 3)
        self.table.setHorizontalHeaderLabels(['layer','number of class','reclass'])
        #self.table.setVerticalHeaderLabels(Vlables)


        for index in range(len(layers)):

			mvalue = str(layers[index])
                	item = QtGui.QTableWidgetItem()
			item.setData(QtCore.Qt.DisplayRole, "%s" %(mvalue) )
			item.setData(QtCore.Qt.EditRole, mvalue)

			item.setFlags(QtCore.Qt.ItemIsEnabled)
                	item.setBackground(QtGui.QColor(183,183,183))
                	self.table.setItem(index, 0, item)

                	item = QtGui.QTableWidgetItem(str(0))
			item.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled)
                	item.setBackground(QtGui.QColor(255,0,0))
                	self.table.setItem(index, 1, item)


			self.button = QtGui.QPushButton('Reclass')
			self.button.x = 3
			self.button.clicked.connect(self.Reclass)
			self.table.setCellWidget(index,2,self.button)

                	item = QtGui.QTableWidgetItem(str(1))
                	self.table.setItem(index, 2, item)


        self.layout.addWidget(self.table)
        self.setLayout(self.layout)

	self.mybox = createGroupBox(self.layout, "Run box")
	self.mybox.addWidget(createButton("Back", self.back))
	self.mybox.addWidget(createButton("Next", self.run))

    def run(self):
	#7788
	isok = check_this_page(3)
	if isok == 0:
		return
	else:
		ex.tabWidget.setCurrentIndex(4)



	get_all_data()
	for x in layer_reclasses:
		table = layer_reclasses[x].table
		#print x,table2list(table)
		#id,w,min,max
		classes = reclass_maker(table2list(table),x)
		#print AHP_result["wheights"][x]

		'''classes =[[0,500,1.0],[2500,3000,2.0],[3000,4000,3.0]]
		a = mgdal.reclassify(file,classes)
		mgdal.array2raster(file,"rrr.tif",a)
		mgdal.write_info("rrr.tif")'''


	#ok()
    def back(self):
	ex.tabWidget.setCurrentIndex(2)

    def Reclass(self):
        button = QtGui.qApp.focusWidget()
        # or button = self.sender()
        index = self.table.indexAt(button.pos())
        if index.isValid():
        	print(index.row(), index.column())
        	print(index.row(), index.column())
		item = self.table.item(index.row(), 0)
		print str(item.text())

		if layer_reclasses.has_key(str(item.text())):
			layer_reclasses[str(item.text())].show()

		else:
			a = Reclass_Window(str(item.text()))
			layer_reclasses[str(item.text())] = a
			#print 999
			#a.show()





class Output_Setting(QtGui.QWidget):
    #778812
    def __init__(self, parent=None):
        super(Output_Setting, self).__init__(parent)
        self.layout = QVBoxLayout(self)


        self.folderitem = dirItem()
        self.folderitem.setTitle("DirItem")
        self.layout.addWidget(self.folderitem)


	self.mybox = createGroupBox(self.layout, "Run box")
	self.mybox.addWidget(createButton("Back", self.back))
	self.mybox.addWidget(createButton("Run", self.run))

    def run(self):
	#7788
	isok = check_this_page(4)
	if isok == 0:
		return
	else:
		ok(str(ex.tabs['output setting'].folderitem.get_dirpath()))
		ex.tabWidget.setCurrentIndex(5)
		#show_Message(title='!',message='result created')
		ex.tabs['output results'].run_Preview()
	
    def back(self):
	ex.tabWidget.setCurrentIndex(3)




class Reclass_Window(QtGui.QDialog):
    def __init__(self,basename):
        super(Reclass_Window,self).__init__()
        self.layout = QVBoxLayout(self)
        self.setGeometry(50,50,600,400)
	mybox = createGroupBox(self.layout, "Run box")
	mybox.addWidget(createButton("Next", self.run))

	self.basename = basename
	self.file_path = get_path()[self.basename]


        self.e1 = QLineEdit()
        self.e1.setValidator(QIntValidator(1,99))
        self.e1.setMaxLength(3)
	self.e1.setText(str(1))
        self.layout.addWidget(self.e1)

        self.setWindowTitle(basename)
	self.update_table(1)
        self.exec_()

    
    def update_table(self,number_of_class=1):
	
	Vlables=["class","weight",'min','max']
	for i in reversed(range(self.layout.count())): 
		self.layout.itemAt(i).widget().setParent(None)

        self.e1 = QLineEdit()
        self.e1.setValidator(QIntValidator(1,99))
        self.e1.setMaxLength(3)
        #self.e1.textChanged.connect(self.input_onChanged)
        self.layout.addWidget(self.e1)

	self.e1.setText(str(1))
	mybox = createGroupBox(self.layout, "Run box")
	mybox.addWidget(createButton("Apply", self.run))

	#number_of_class = 1
	greader = mgdal.read_raster(self.file_path)

	#self.file_path
	band = greader.band
	min = band.GetMinimum()
	max = band.GetMaximum()

	#this is ok method
	(min,max) = band.ComputeRasterMinMax(0)
	print "*"*33
	print min,max
	print "*"*33


        self.table = QtGui.QTableWidget(number_of_class, 4)
        self.table.setHorizontalHeaderLabels(["class","weight",'min','max'])
        #self.table.setVerticalHeaderLabels(Vlables)
	self.table.itemChanged.connect(self.table_event)

        for index in range(number_of_class):

			mvalue = str(index)
                	item = QtGui.QTableWidgetItem()
			item.setData(QtCore.Qt.DisplayRole, "%s" %(mvalue) )
			item.setData(QtCore.Qt.EditRole, mvalue)

			item.setFlags(QtCore.Qt.ItemIsEnabled)
                	item.setBackground(QtGui.QColor(183,183,183))
                	self.table.setItem(index, 0, item)


			mvalue = str('')
                	item = QtGui.QTableWidgetItem()
			item.setData(QtCore.Qt.DisplayRole, "%s" %(mvalue) )
			item.setData(QtCore.Qt.EditRole, mvalue)

			item.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled)
                	item.setBackground(QtGui.QColor(183,183,183))
                	self.table.setItem(index, 2, item)



	print 778,number_of_class
        if number_of_class ==1:
                	item = QtGui.QTableWidgetItem(str(1))
			item.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled)
                	self.table.setItem(0, 1, item)

                	item = QtGui.QTableWidgetItem(str(min))
			item.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled)
                	item.setBackground(QtGui.QColor(183,183,183))
                	self.table.setItem(0, 2, item)

                	item = QtGui.QTableWidgetItem(str(max))
			item.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled)
                	item.setBackground(QtGui.QColor(183,183,183))
                	self.table.setItem(0, 3, item)
	else:
                	item = QtGui.QTableWidgetItem(str(min))
			item.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled)

                	item.setBackground(QtGui.QColor(183,183,183))
                	self.table.setItem(0, 2, item)

                	item = QtGui.QTableWidgetItem(str(max))
			item.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled)
                	item.setBackground(QtGui.QColor(183,183,183))
                	self.table.setItem(number_of_class - 1, 3, item)




        self.layout.addWidget(self.table)
        self.setLayout(self.layout)




    def run(self):
	x = int(self.e1.text())
	self.update_table(x)
	self.e1.setText(str(x))


    def table_event(self, item):
	mrow = int(item.row())
	mcol = int(item.column())
	mtxt = str(item.text())
	if mcol == 3:
			mvalue = mtxt
                	item = QtGui.QTableWidgetItem()
			item.setData(QtCore.Qt.DisplayRole, "Row: %s" %(mvalue) )
			item.setData(QtCore.Qt.EditRole, mvalue)

                	#item.setFlags(QtCore.Qt.ItemIsEnabled)
			item.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled)
                	item.setBackground(QtGui.QColor(240,240,240))
                	self.table.setItem(mrow + 1, mcol -1, item)

    def set_color(self,isok=0):
	if isok == 1:
		color = [0,255,0]
		layer_reclasses[self.basename] = self
		class_no = str(layer_reclasses[self.basename].e1.text())
		class_no = str(self.e1.text())
	else:
		color = [255,0,0]
		layer_reclasses[self.basename] = self
		class_no = '0'
	for row in xrange(ex.tabs['reclass'].table.rowCount()):
		widget = ex.tabs['reclass'].table.item(row, 0).text()
		if str(widget) == self.basename:
			#ex.tabs['reclass'].table.item(row, 1).setBackground(QtGui.QColor(color[0],color[1],color[2]))
			mvalue = class_no
                	item = QtGui.QTableWidgetItem()
			item.setData(QtCore.Qt.DisplayRole, "%s" %(mvalue) )
			item.setData(QtCore.Qt.EditRole, mvalue)

                	#item.setFlags(QtCore.Qt.ItemIsEnabled)
			item.setFlags(QtCore.Qt.ItemIsEnabled)
                	item.setBackground(QtGui.QColor(color[0],color[1],color[2]))
                	ex.tabs['reclass'].table.setItem(row, 1, item)



    def closeEvent(self, event):
	empty_fined = 0
        for row in xrange(self.table.rowCount()):
		for col in xrange(self.table.columnCount()):
			widget = self.table.item(row, col)
			if widget is None:
				empty_fined = 1
	print empty_fined
	if empty_fined == 0:
		event.accept()
		
	reply = empty_fined
        if reply == 0:
            event.accept()
	    self.set_color(1)
        else:
	    rreply = QtGui.QMessageBox.warning(self, 'Message',
            "Some of cells are empty. Are you sure to quit?", QtGui.QMessageBox.Yes | 
            QtGui.QMessageBox.No, QtGui.QMessageBox.No)
            if rreply == QtGui.QMessageBox.Yes:
                event.accept()
		self.set_color(0)
            else:
                event.ignore()        



#################################
#####################################
##########################################
################################################


class dirItem(QtGui.QGroupBox):
    def __init__(self):
        super(dirItem, self).__init__()
	self.type = "file"
        self.v_layout = QtGui.QHBoxLayout(self)

        directoryLabel = QtGui.QLabel("In directory:")
	self.v_layout.addWidget(directoryLabel)
	self.filepath = createTextbox(text="")
	self.v_layout.addWidget(self.filepath)
	self.v_layout.addWidget(createButton("&Browse...", self.browse))

	self.value = self.filepath.text()

    def browse(self):
	self.direc = str(QtGui.QFileDialog.getExistingDirectory(self, "Select Directory"))
        if self.direc:
		print self.direc
		self.filepath.setText(self.direc)
		self.value = self.filepath.text()

    def get_dirpath(self):
	return self.filepath.text()

#######################################

def update_AHP():
	print 'updating AHP'
	items = ex.tabs['layers'].files_items.getall(1)

	mlen = len(ex.tabs['layers'].files_items.getall(1))
	ex.tabs['AHP'].update_table(mlen,mlen,items,items)






def createGroupBox(layout, text):
        ButtonsGroupBox = QtGui.QGroupBox(text)
        ButtonsLayout = QtGui.QHBoxLayout()
        ButtonsGroupBox.setLayout(ButtonsLayout)
        layout.addWidget(ButtonsGroupBox)


        return ButtonsLayout

def createButton(text, member):
        button = QtGui.QPushButton(text)
        button.clicked.connect(member)
        return button

def createTextbox(text=""):
        textbox = QtGui.QLineEdit()
        textbox.setText(text)
        return textbox

def createComboBox(self, text=""):
        comboBox = QtGui.QComboBox()
        comboBox.setEditable(True)
        comboBox.addItem(text)
        comboBox.setSizePolicy(QtGui.QSizePolicy.Expanding,
                QtGui.QSizePolicy.Preferred)
        return comboBox

#################################################################################################################################################################

class fileItem(QtGui.QGroupBox):
    def __init__(self,mlabel="In file:",filetypes=['*']):
        super(fileItem, self).__init__()
	self.filetypes = filetypes
	self.type = "file"
        self.v_layout = QtGui.QHBoxLayout(self)

        directoryLabel = QtGui.QLabel(mlabel)
	self.v_layout.addWidget(directoryLabel)
	self.filepath = createTextbox(text="")
	self.v_layout.addWidget(self.filepath)
	self.v_layout.addWidget(createButton("&Browse...", self.browse))

	self.value = self.filepath.text()
	self.path = None
    def browse(self):
	filetype_pat = ''
	for x in self.filetypes:
		filetype_pat +='(*.%s);;'%x
	#'All Files(*.*)'
	filename = QtGui.QFileDialog.getOpenFileName(None, 'Test Dialog', os.getcwd(), filetype_pat)
        if filename:
		print filename
		self.filepath.setText(filename)
		self.value = self.filepath.text()
		self.path = str(self.filepath.text())
		print self.path
class textItem(QtGui.QGroupBox):

    def __init__(self):
        super(textItem, self).__init__()
	self.type = "text"
        self.v_layout = QtGui.QVBoxLayout(self)
	self.item = createTextbox(text="aaxx")
        self.v_layout.addWidget(self.item)

	self.value = self.item.text()

class filesItem(QtGui.QGroupBox):
    def __init__(self):
        super(filesItem, self).__init__()
        self.v_layout = QtGui.QVBoxLayout(self)
	self.type = "files"
        myQWidget = QtGui.QWidget()
        myBoxLayout = QtGui.QVBoxLayout()
        myQWidget.setLayout(myBoxLayout)   

        # Bottom GroupBox
        BottomGroupBox = QtGui.QGroupBox('BottomGroupBox')
        BottomGroupBox = QtGui.QGroupBox()
        BottomGroupBox.setFlat(True)

        BottomLayout = QtGui.QHBoxLayout()
        BottomGroupBox.setLayout(BottomLayout)
        myBoxLayout.addWidget(BottomGroupBox)

        # Left Bottom Horizontal GroupBox


################################################
        #LeftHorGroupBox = QtGui.QGroupBox('Left Horizontal')
        LeftHorGroupBox = QtGui.QGroupBox()
        LeftHorGroupBox.setFlat(True)
        LeftHorLayout = QtGui.QHBoxLayout()
        LeftHorGroupBox.setLayout(LeftHorLayout)




        self.listA=QtGui.QTreeWidget()
        self.listA.setColumnCount(2)
        self.listA.setHeaderLabels(['No','Name','Path'])
        for i in range(0):
            item=QtGui.QTreeWidgetItem()
            #item.setCheckState(0,QtCore.Qt.Checked)
            item.setText(0, str(i + 1))
            item.setText(1, 'Item '+str(i + 1))
            #item.setData(2, QtCore.Qt.UserRole, id(item) )
            #item.setText(2, str(id(item) ) )
            self.listA.addTopLevelItem(item)

        self.listA.resizeColumnToContents(0)
        self.listA.resizeColumnToContents(1)
        self.listA.resizeColumnToContents(2)

        self.listA.sortByColumn(0, 0)

        LeftHorLayout.addWidget(self.listA)
 
        #self.v_layout.addWidget(self.listA)
        self.v_layout.addWidget(BottomGroupBox)
        #self.v_layout.addWidget(BottomLayout)



########################################
##############################################
        # Left Bottom Vertical GroupBox
        #RightVertGroupBox = QtGui.QGroupBox('Right Vertical')
        RightVertGroupBox = QtGui.QGroupBox()
        RightVertGroupBox.setFlat(True)
        RightVertLayout = QtGui.QVBoxLayout()
        RightVertGroupBox.setLayout(RightVertLayout)

        BottomLayout.addWidget(LeftHorGroupBox)
        BottomLayout.addWidget(RightVertGroupBox)

        viewA=QtGui.QListWidget()
        viewB=QtGui.QListWidget()
        viewC=QtGui.QListWidget()

###
        RightVertLayout.addWidget(createButton("openfiles", self.openfiles))

        RightVertLayout.addWidget(createButton("Remove all", self.removeall))

        RightVertLayout.addWidget(createButton("Remove Selected", self.removeSel))
###
	self.value = self.setvalue()

    def setvalue(self):

	mylist = []
        for item in self.listA.findItems("", QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive):
		mylist.append(str(item.text(1)))
	return mylist


    def removeSel(self):
        listItems=self.listA.selectedItems()
        if not listItems: return   
        for item in listItems:
            itemIndex=self.listA.indexOfTopLevelItem(item)
            self.listA.takeTopLevelItem(itemIndex)
	self.value = self.setvalue()
    def removeall(self):
	self.listA.clear()
	self.value = self.setvalue()

    def getall(self,col):
	self.mylist = []
        for item in self.listA.findItems("", QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive):
		self.mylist.append(str(item.text(col)))
	return self.mylist

    def get_path(self):
	col = 2
	self.mylist = []
        for item in self.listA.findItems("", QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive):
		self.mylist.append(str(item.text(col)))
	return self.mylist

    def get_basename(self):
	col = 1
	self.mylist = []
        for item in self.listA.findItems("", QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive):
		self.mylist.append(str(item.text(col)))
	return self.mylist

    def openfiles(self):

	#filter = "TXT (*.py);;PDF (*.pdf)"
	#filter = 'All Files(*.*)'
	filter = 'TIFF Files(*.tif)'
	file_name = QtGui.QFileDialog()
	file_name.setFileMode(QtGui.QFileDialog.ExistingFiles)
	names = file_name.getOpenFileNamesAndFilter(None, "Open files", os.getcwd(), filter)
	# getOpenFileNamesAndFilter  , getOpenFileNameAndFilter

	for x in names[0]:
	    print x


            item=QtGui.QTreeWidgetItem()
            #item.setCheckState(0,QtCore.Qt.Checked)
            item.setText(0, str(len(self.getall(1)) + 1))
	    base_name = os.path.splitext(os.path.basename(str(x)))[0]
            item.setText(1, base_name)
            item.setText(2, x)
            #item.setData(2, QtCore.Qt.UserRole, id(item) )
            #item.setText(2, str(id(item) ) )
            self.listA.addTopLevelItem(item)
            self.listA.resizeColumnToContents(1)
	    all_layers[base_name]=str(x)

	self.value = self.setvalue()


def calc_AHP(data,headers):
	a = data
	asum = a.sum(axis=0)

	normal= a/asum
	norm_mean = normal.mean(axis=1)
	norm_mean_X_a = norm_mean*a

	norm_mean_X_a_sum = norm_mean_X_a.sum(axis=1)
	wheights = norm_mean_X_a_sum.copy()
	#print wheights

	wheights_norm = wheights/wheights.sum()
	print wheights_norm

	lambeda_max = norm_mean_X_a_sum/norm_mean
	lambeda_max = lambeda_max.mean()
	#print lambeda_max
	CI =(lambeda_max-a.shape[0])/(a.shape[0]-1)
	print CI
	AHP_result["CI"] = CI
	temp = {}
	for index,header in enumerate(headers):
		temp[header] = wheights_norm[index]
	AHP_result["wheights"] = temp


	for index,header in enumerate(headers):
		temp[header] = wheights_norm[index]
		data_dic.setdefault(header, {})['weight'] = wheights_norm[index]


def get_all_data():
	headers = get_path().keys()
	for header in headers:
		data_dic.setdefault(header, {})['path'] = get_path()[header]

	table = ex.tabs['Results'].table
	table_l = table2list(table)
	for index, header in enumerate(table_l[0]):
		data_dic.setdefault(header, {})['weight'] = float(table_l[1][index])

	print data_dic

	for header in headers:
		try:
			re_data = layer_reclasses[header]
			print 666666
			print table2list(re_data.table)
		except:
			print "set reclass data"



def check_this_page(myindex):

	if myindex == 0:
	  if len(ex.tabs['layers'].files_items.get_basename()) <=2:
		show_error(title='Error',message='Please select three or more layers')
		ex.tabWidget.setCurrentIndex(0)
		sidebaritems[0].setBackground(QtGui.QColor(239,165,184))
		return 0
	  elif len(ex.tabs['layers'].files_items.get_basename()) != len(list(set(ex.tabs['layers'].files_items.get_basename()))):
		show_error(title='Error',message='basename of two or more layers is same')
		ex.tabWidget.setCurrentIndex(0)
		sidebaritems[0].setBackground(QtGui.QColor(239,165,184))
		return 0
	  else:
		row_col = {}
		for file in ex.tabs['layers'].files_items.get_path():
			r2r = mgdal.raster2array(file)
			print r2r.shape
			row_col[file]=r2r.shape
		if len(list(set(list(row_col.values())))) !=1:
			mymessage = ""
			for path in row_col:
				mymessage += '%s:%s\n'%(path,row_col[path])
			show_error(title='Error',message=mymessage,desc="row and col of all raster is not same")
			ex.tabWidget.setCurrentIndex(0)
			sidebaritems[0].setBackground(QtGui.QColor(239,165,184))
			return 0

		sidebaritems[0].setBackground(QtGui.QColor(0,255,0))
		return 1


	if myindex == 1:
	   if user_changed_ahp_weights == 0:
		show_error(title='Error',message='please set AHP table')
		sidebaritems[1].setBackground(QtGui.QColor(239,165,184))
		return 0
	   else:
		sidebaritems[1].setBackground(QtGui.QColor(0,255,0))
		return 1
	if myindex == 3:

		tlist = table2list(ex.tabs['reclass'].table)
		isok = 0
		for x in tlist:
			if x[1] == '0':
				isok += 1
		if isok > 0:
			show_error(title='Error',message='please set class of layers')
			sidebaritems[3].setBackground(QtGui.QColor(239,165,184))
			return 0
		else:
			sidebaritems[3].setBackground(QtGui.QColor(0,255,0))
			return 1


	if myindex == 4:
		dire = ex.tabs['output setting'].folderitem.get_dirpath()

		if dire == "":
			show_error(title='Error',message='please select output path dir')
			sidebaritems[4].setBackground(QtGui.QColor(239,165,184))
			return 0
		else:
			sidebaritems[4].setBackground(QtGui.QColor(0,255,0))
			return 1


	return 0

def show_error(title='Error',message='please complete all required fields',desc="An error occurred"):
   msg = QMessageBox()
   msg.setIcon(QMessageBox.Information)

   msg.setText(desc)
   msg.setInformativeText(message)
   msg.setWindowTitle(title)
   msg.setStandardButtons(QMessageBox.Ok)
   #msg.buttonClicked.connect(msgbtn)
	
   retval = msg.exec_()


def show_Message(title='!',message='ok'):
   msg = QMessageBox()
   msg.setIcon(QMessageBox.Information)

   msg.setInformativeText(message)
   msg.setWindowTitle(title)
   msg.setStandardButtons(QMessageBox.Ok)
   #msg.buttonClicked.connect(msgbtn)
	
   retval = msg.exec_()


def table2list(table):
	table_data = []
	for row in range(table.rowCount()):
		rowdata = []
		for column in range(table.columnCount()):
			item = table.item(row, column)
                        rowdata.append(str(item.text()))
		table_data.append(rowdata )
	return table_data
def reclass_maker(mlist, layer):#id,w,min,max

	classes =[]
	sum_of_class_wight = 0.0
	for x in mlist:
		sum_of_class_wight += float(x[1])

	for x in mlist[:-1]:
		classes.append([float(x[2]),float(x[3]),float(x[1])/sum_of_class_wight])
	classes.append([float(mlist[-1][2]),float(mlist[-1][3]) + 1,float(mlist[-1][1])/sum_of_class_wight])

	print layer,classes
	print "="*22
	data_dic.setdefault(layer, {})['classes'] = classes

	
	return classes

def ok(outdir=""):
	tlist = []
	for layer in data_dic:
		file = data_dic[layer]['path']
		classes = data_dic[layer]['classes']
		layer_reclassed_array = mgdal.reclassify(file,classes)
		#########data_dic.setdefault(layer, {})['np_reclassed'] = layer_reclassed_array
		out_rec_name = outdir + "/recl_%s.tif"%layer
		mgdal.array2raster(file,out_rec_name,layer_reclassed_array)
		mgdal.write_info(out_rec_name)

		layer_array = mgdal.raster2array(file)
		#########data_dic.setdefault(layer, {})['np_'] = layer_array



		#layer_array = data_dic[layer]['np_']
		layer_weight = data_dic[layer]['weight']
		#layer_reclassed_array = data_dic[layer]['np_reclassed']
		ww = layer_reclassed_array * float(layer_weight)
		tlist.append(ww)
		####data_dic.setdefault(layer, {})['out'] = ww

	#The actual calculation
	#Out_array = np.sum(tlist)
	Out_array = np.zeros_like(tlist[0])

	for xz in tlist:
		print xz
		print '------------'
		Out_array += xz

	print '55555555555555555555555555555555555'
	print Out_array
	print data_dic[data_dic.keys()[0]]['path']
	print '55555555555555555555555555555555555'
	
	outname = outdir + "/result.tif"

	mgdal.array2raster(data_dic[data_dic.keys()[0]]['path'],outname,Out_array)
	import gdalinfo2
	gdalinfo2.main(outname)



def test():
	print ex.tabs['layers'].files_items.get_basename()
	print ex.tabs['layers'].files_items.get_path()
	sidebaritems[0].setBackground(QtGui.QColor(0,255,0))
	ROCdialog()
def get_path():
	basen = ex.tabs['layers'].files_items.get_basename()
	path = ex.tabs['layers'].files_items.get_path()
	mydic = zip(basen , path)
	return dict(mydic)

def preview(tif_dir):
	tifffile = tif_dir + "\\result.tif"
	dem = mgdal.myraster_to_array(tifffile)
	plt.close('all')
	plt.imshow(dem, origin="lower", cmap='seismic', interpolation='nearest')
	plt.colorbar()
	plt.xticks([])
	plt.yticks([])
	#plt.show()
	plt.tight_layout()
	plt.savefig(tif_dir + "\\preview.png", format='png', dpi=300)
	plt.close('all')
	return tif_dir + "\\preview.png"


def showimage(mimage):
   from ImageViewer import ImageViewer
   d = QDialog()
   d.setGeometry(50,50,700,700)
   layout = QVBoxLayout(d)
   viewer = ImageViewer(mimage)
   layout.addWidget(viewer)
   d.setWindowTitle("Dialog")
   d.setWindowModality(Qt.ApplicationModal)
   d.exec_()

class Output_results(QtGui.QWidget):
    #778812
    def __init__(self, parent=None):
        super(Output_results, self).__init__(parent)
        self.layout = QVBoxLayout(self)

	self.viewer = PhotoViewer(self)
	self.layout.addWidget(self.viewer)

	self.mybox = createGroupBox(self.layout, "Run box")
	self.mybox.addWidget(createButton("Reload", self.run_Preview))

	self.mybox.addWidget(createButton("Create ROC plot", test))

	self.mybox.addWidget(createButton("Back", self.back))

    def run_Preview(self):
	print str(ex.tabs['output setting'].folderitem.get_dirpath())
	preview_png = preview(str(ex.tabs['output setting'].folderitem.get_dirpath()))
	#ex.tabWidget.setCurrentIndex(5)

	self.viewer.setPhoto(QtGui.QPixmap(preview_png))
	####showimage(preview_png)
	return preview_png
    def back(self):
	ex.tabWidget.setCurrentIndex(4)



if __name__ == '__main__':
   app = QApplication(sys.argv)
   ex = dockdemo()
   ex.setGeometry(20,40,1000, 500)
   ex.show()
   sys.exit(app.exec_())
