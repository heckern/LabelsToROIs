#@ File (label="Select Original Image File") imagefile
#@ File (label="Select Labeled Image File") labelfile

from ij import IJ
from ij.plugin.frame import RoiManager
from ij.plugin import RoiEnlarger
from ij.process import ImageProcessor
from ij.measure import ResultsTable, Measurements
from ij.plugin.filter import ParticleAnalyzer
from datetime import time, tzinfo
from ij.gui import Wand
from javax.swing import SwingWorker, SwingUtilities
import time
import datetime
import math
import os
import re

###########################################################
####################  Before we begin #####################
###########################################################
gvars = {} # Create dictionary to store variables created within functions
gvars['eroded_pixels'] = 0 # initialize
print(imagefile.name)
gvars['path_original_image'] = imagefile.getAbsolutePath()
print(labelfile.name)
gvars['path_label_image'] = labelfile.getAbsolutePath()



###########################################################
####################  Define SwingWorker ##################
###########################################################

class LabelToRoi_Task(SwingWorker):

    def __init__(self, imp):
        SwingWorker.__init__(self)
        self.imp = imp

    def doInBackground(self):
        imp = self.imp
        print "started"

        ts = time.time()
        st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        print st

        RM = RoiManager()        # we create an instance of the RoiManager class
        rm = RM.getRoiManager()  # "activate" the RoiManager otherwise it can behave strangely
        rm.reset()
        rm.runCommand(imp,"Show All without labels") # we make sure we see the ROIs as they are loading


        imp2 = imp.duplicate()
        ip = imp2.getProcessor()
        width = imp2.getWidth()
        height = imp2.getHeight() - 1

        max_label = int(imp2.getStatistics().max)
        max_digits = int(math.ceil(math.log(max_label,10))) # Calculate the number of digits for the name of the ROI (padding with zeros)
        IJ.setForegroundColor(0, 0, 0) # We pick black color to delete the label already computed

        for j in range(height):
           for i in range(width):
              current_pixel_value = ip.getValue(i,j)
              if current_pixel_value > 0:
                 IJ.doWand(imp2, i, j, 0.0, "Legacy smooth");

                 # We add this ROI to the ROI manager
                 roi = imp2.getRoi()
                 roi.setName(str(int(current_pixel_value)).zfill(max_digits))
                 rm.addRoi(roi)

                 ip.fill(roi) # Much faster than IJ.run(imp2, "Fill", ....


        rm.runCommand(imp,"Sort") # Sort the ROIs in the ROI manager
        rm.runCommand(imp,"Show All without labels")

        ts = time.time()
        st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        print st

        print "Finished"


# Definition of function RoiEroder
def RoiEroder(pixels):
   RM = RoiManager()        # we create an instance of the RoiManager class
   rm = RM.getRoiManager()  # "activate" the RoiManager otherwise it can behave strangely

   rm.reset()

   # Re-open temporary original ROIs
   temp_roi_path = gvars['tempFile']
   rm.runCommand("Open", temp_roi_path)
   print "Temp ROIs OPENED"

   for i in range(0, rm.getCount()):
      roi = rm.getRoi(i)
      new_roi = RoiEnlarger.enlarge(roi, -pixels) # Key to use this instead of the IJ.run("Enlarge... much faster!!
      rm.setRoi(new_roi,i)

   gvars['eroded_pixels'] = pixels # Store globally the amount of pixels used to later save them in the ROI file name


   
### main
imp = IJ.openImage(imagefile.getAbsolutePath())

RM = RoiManager()        # we create an instance of the RoiManager class
rm = RM.getRoiManager()

gvars["workingImage"] = imp
imp.show()
IJ.run(imp, "Enhance Contrast", "saturated=0.35");

imp2 = IJ.openImage(labelfile.getAbsolutePath())
task = LabelToRoi_Task(imp2) # Executes the LabelToRoi function defined on top of this script. It is wrapped into a SwingWorker in order for the windows not to freeze

task.execute()

rm.runCommand(imp,"Show All without labels")
