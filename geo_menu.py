'''
NOTES:  This is a script for an assignment I did at university. It opens a Tkinter menu in order to set the layer, field, suburbs and filter
and then displays a count of features, a density of features and a ratio of features between 2 suburbs (if the parameters are correct)
'''
# Created by:  Liam Robinson
#              17727260
# Created on:  17/10/2015
# Updated on:  07/11/2016   Liam Robinson


# ==== IMPORTS ====
import ttk
import Tkinter
from Tkinter import Tk
from Tkinter import StringVar
from Tkinter import IntVar
import os
import arcpy
import sys
import time

# ==== GLOBALS ====
''' Gets the map path from the user, as well as the geodatabase path'''

map_path = raw_input("Please enter the map path ")
workspace_path = raw_input("Please enter the workspace path ")

''' Tries to use these user-specified paths, if it fails the program exits'''
try:
    mxd = arcpy.mapping.MapDocument(str(map_path))
    arcpy.env.workspace = str(workspace_path)
except AssertionError:
    print "Please enter valid path names."
    sys.exit()

''' Creates a list of layers in order for the Tkinter window to have an initial list of layers'''
list_layers = arcpy.mapping.ListLayers(mxd)
layerList = []
i=0
while i < len(list_layers):
    layerList.append(str(list_layers[i]))
    i = i+1

# ==== MAIN SCRIPT ====
#   This is where the statistics are calculated.
def main(allFeaturesVar, filteredFeaturesVar):
    ''' Runs a check on what features should be used, checks if a full filter is used or not.'''
    if allFeaturesVar == 1:
        allFeaturesVar = 1
        filteredFeaturesVar = 0
    elif entryFilter.get() == "" or dropDownFilter.get() == "":
        print "You did not enter a complete filter, all features will be used."
        allFeaturesVar = 1
        filteredFeaturesVar = 0
    else:
        allFeaturesVar = 0
        filteredFeaturesVar = 1

    ''' Creates an initial string for the full filter, and compiles the filter based upon the drop down options entered'''
    fullFilter = ""
    if filteredFeaturesVar == 1:
        if dropDownFilter.get() == "LESS THAN":
            fullFilter = str(fieldsVar.get()) + " < " + str(entryFilter.get())
        if dropDownFilter.get() == "GREATER THAN":
            fullFilter = str(fieldsVar.get()) + " > " + str(entryFilter.get())
        if dropDownFilter.get() == "EQUAL TO":
            fullFilter = str(fieldsVar.get()) + " = " + str(entryFilter.get())
        if dropDownFilter.get() == "EQUALS":
            fullFilter = str(fieldsVar.get()) + " = " + str(entryFilter.get())
    # print layerVar.get() #DEBUG
    # print "All features: " + str(allFeaturesVar) #DEBUG
    # print "Filtered Features: " + str(filteredFeaturesVar) #DEBUG

    ''' Sets the count of features (filtered or all) to zero'''
    countFilteredFeatures = 0
    countAllFeatures = 0

    ''' If the filtered features were specified to be used, the cursor uses the full filter generated'''
    if filteredFeaturesVar == 1:
        cursor = arcpy.da.SearchCursor(layerVar.get(), (str(fieldsVar.get())), str(fullFilter))
        for row in cursor:
            countFilteredFeatures = countFilteredFeatures + 1
        print "Count of Filtered Features: " + str(countFilteredFeatures)
        del cursor

        ''' If all features were specified to be used, the cursor doesn't have a filter applied'''
    else:
        cursor = arcpy.da.SearchCursor(layerVar.get(), (str(fieldsVar.get())))
        for row in cursor:
            countAllFeatures = countAllFeatures + 1
        print "Count of All Features: " + str(countAllFeatures)
        del cursor
    # print "Suburb Chosen: " + str(suburbVar.get()) #DEBUG

    ''' Creates a serarch cursor and loops through the rows, recording the area of the suburb chosen'''
    cursor = arcpy.da.SearchCursor("WAMethodOfTransport", ["SSC_NAME","SQKM"])
    for row in cursor:
        if str(row[0]) == str(suburbVar.get()):
            areaOfSelectedSuburb = row[1]

    ''' If the temp feature layers created below exist, they are deleted'''
    if arcpy.Exists("suburb_chosen"):
        arcpy.Delete_management("suburb_chosen")
    if arcpy.Exists("chosen_layer"):
        arcpy.Delete_management("chosen_layer")

    '''Makes feature layers in order for them to be selectable'''
    arcpy.MakeFeatureLayer_management("WAMethodOfTransport", "suburb_chosen", "SSC_NAME = " +  '\'' + suburbVar.get() + '\'')
    arcpy.MakeFeatureLayer_management(layerVar.get(), "chosen_layer", fullFilter)

    ''' The chosen layer is then completely selected as the filter has already been applied, and these features
    remain in the selection only if they are also in the suburb chosen'''
    arcpy.SelectLayerByAttribute_management("chosen_layer", "NEW_SELECTION")
    arcpy.SelectLayerByLocation_management("chosen_layer", "INTERSECT", "suburb_chosen", '', "SUBSET_SELECTION")

    '''Creates a search cursor on the chosen layer, because features are selected, the cursor will only look at these'''
    cursor = arcpy.da.SearchCursor("chosen_layer", '*')

    ''' Sets an initial count and then loops through the cursor, incrementing the count by one for each row'''
    countInsideSuburb = 0
    for row in cursor:
        countInsideSuburb = countInsideSuburb + 1
    # print countInsideSuburb #DEBUG
    del cursor

    '''If the count doesn't equal zero, the density is calculated, otherwise, a message is produced'''
    if countInsideSuburb != 0:
        density = countInsideSuburb/areaOfSelectedSuburb
        print "Density of Features: " + str(density)
    else:
        print "The count of features inside the suburb selected is 0, the density cannot be calculated."

    '''Checks if the layer chosen is WAMethodOfTransport, the field chosen is a transport field, and the suburbs chosen
    are not the same or blank, the else statements are at the bottom of this process, that provide error messages
    if a parameter is incorrect to calculate the ratio'''
    if layerVar.get() == "WAMethodOfTransport":
        if fieldsVar.get() == "Train" or fieldsVar.get() == "Bus" or fieldsVar.get() == "Car__as_driver" or fieldsVar.get() == "Bicycle" or fieldsVar.get() == "Motorbike_scooter":
            if suburbVar.get() != suburbSecondVar.get() and suburbVar.get() != "" and suburbSecondVar.get() != "":

                '''Creates a string for the filter and an initial list'''
                filterForCursor = "SSC_NAME = " + '\'' + suburbVar.get() + '\'' + " or SSC_NAME = " + '\'' + suburbSecondVar.get() + '\''
                listOfData = []

                '''Creates a Search Cursor based on the layer chosen, the method of transport chosen and the suburbs chosen
                it then loops through each row and appends the number of people that use the selected mode of transport.
                The list will have two records, the first being the first suburb chosen, and the second being the second
                suburb chosen.'''
                cursor = arcpy.da.SearchCursor(layerVar.get(), fieldsVar.get(), filterForCursor)
                for row in cursor:
                    for info in row:
                        listOfData.append(info)
                # print listOfData #DEBUG
                del cursor

                ''' Checks if the number of people that use the selected mode of transport is 0. If it is the ratio
                is not calculated. If the numbers are different then the ratio is calculated, but if they are equal
                a message comes up saying that they have the same number of people that use the selected mode of
                transport '''
                if listOfData[0] == 0 or listOfData[1] == 0:
                    print "One suburb has a count of 0 for the mode of transport you selected." + '\n' + \
                    "Please try again with a different suburb, or a different mode of transport."
                elif listOfData[0] > listOfData[1]:
                    ratio = listOfData[0] / listOfData[1]
                    print str(suburbVar.get()) + " has " + str(ratio) + " times more people who use the selected mode of transport than " + str(suburbSecondVar.get()) + "."
                elif listOfData[0] < listOfData[1]:
                    ratio = listOfData[1] / listOfData[0]
                    print str(suburbSecondVar.get()) + " has " + str(ratio) + " time more people who use the selected mode of transport than " + str(suburbVar.get()) + "."
                elif listOfData[0] == listOfData[1]:
                    print "Equal"
                    print str(suburbVar.get()) + " and " + str(suburbSecondVar.get()) + " have the same number of people who use the selected mode of transport."
                else:
                    print "An error has occured with the ratio between 2 suburbs statistic, please try again."
            else:
                print "You didn't select two different suburbs, the ratio statistic will not be calculated."
        else:
            print "The ratio cannot be calculated between two suburbs, please select a mode of transport as your field."
    else:
        print "The ratio cannot be calculated between two suburbs, please select WAMethodOfTransport as your layer."
    time.sleep(7)
    root.destroy()

# Checks if one of the boxes are ticked to use filtered or all features. If not the program does not execute until
# the user has checked one.
def tickBoxCheck():
    allFeatures = allFeaturesVar.get()
    filteredFeatures = filteredFeaturesVar.get()
    if allFeatures == 1 and filteredFeatures == 0:
        main(allFeatures, filteredFeatures)
    elif filteredFeatures == 1 and allFeatures == 0:
        main(allFeatures, filteredFeatures)
    elif allFeatures == 1 and filteredFeatures == 1:
        print "Please only tick one box"
    else:
        print "Please specify what features you want to use."

# Function to open the helpfile
def openHelpFile():
    os.system("home.html")

# Runs when the layers or fields combobox is selected, the dropdown boxes for fields or the filter are updated.
# [Performed across validateFields and validateFilters].
def validateFields(layers):
    fieldsVar = StringVar()
    for fc in arcpy.ListFeatureClasses(mxd):
        if str(layerVar.get()) == str(fc):
            fc_chosen = fc
    fields_list = arcpy.ListFields(fc_chosen)
    fieldOptions = []
    for field in fields_list:
        fieldOptions.append(field.name)
        fields['values'] = fieldOptions
    fields.pack()
    validateFilters(fields.get())

def validateFilters(fields):
    fcList = arcpy.ListFeatureClasses(mxd)
    for fc in fcList:
        if str(fc) == str(layerVar.get()):
            chosenFeatureClass = fc
    cursor = arcpy.da.SearchCursor(chosenFeatureClass, (str(fieldsVar.get())))
    for row in cursor:
        for info in row:
            try:
                info = float(info)
                dropDownFilter['values'] = ["LESS THAN", "GREATER THAN", "EQUAL TO"]
            except ValueError:
                dropDownFilter['values'] = ["EQUALS"]
    del cursor

# Creates an initial window
root = Tk()

# Creates the layer label
layerLabel = ttk.Label(root, text="Choose a Layer: ")
layerLabel.pack()

# Creates the layer drop down box, and creates an event for when the combobox is selected to update the fields
# The layer drop down box is populated based on the layer list calculated in the global variables.
layerVar = StringVar()
layers = ttk.Combobox(root, textvariable=layerVar)
layers['values'] = layerList
layers.current(0)
layers.bind("<<ComboboxSelected>>", validateFields)
layers.pack()

# Creates the fields label
fieldsLabel = ttk.Label(root, text="Choose A Field: ")
fieldsLabel.pack()

# Creates the fields drop down box, and creates an event for when the combobox is selected to update the filters
# The fields drop down box is populated by creating a list of feature classes and looping through until it is the
# same as the layer chosen, and then the list fields function is used. This list is then looped through and the
# string of each record is appended to a separate list.
fieldsVar = StringVar()
fields = ttk.Combobox(root, textvariable=fieldsVar)
for fc in arcpy.ListFeatureClasses(mxd):
    if str(layerVar.get()) == str(fc):
        fc_chosen = fc
field_list = arcpy.ListFields(fc_chosen)
fieldOptions = []
for field in field_list:
    fieldOptions.append(field.name)
    fields['values'] = fieldOptions
fields.current(0)
fields.bind("<<ComboboxSelected>>", validateFilters)
fields.pack()

# Creates the label for the first suburb combobox
suburbOneLabel = ttk.Label(root, text="Enter a suburb: ")
suburbOneLabel.pack()

# Creates an initial suburb list, and creates a search cursor that appends all the suburb names to a list. The
# combobox is then created and populated using this list.
suburb_list = []
cursor = arcpy.da.SearchCursor("WAMethodOfTransport", "SSC_NAME")
for row in cursor:
    for info in row:
        suburb_list.append(str(info))
del cursor
# print suburb_list #DEBUG
suburbVar = StringVar()
suburbChoice = ttk.Combobox(root, textvariable=suburbVar)
suburbChoice['values'] = suburb_list
suburbChoice.pack()

# Creates the label for choosing the second suburb
suburbTwoLabel = ttk.Label(root, text="Please enter the second suburb: ")
suburbTwoLabel.pack()

# Creates the second suburb choice combobox, and populates it from the list created before.
suburbSecondVar = StringVar()
suburbSecondChoice = ttk.Combobox(root, textvariable=suburbSecondVar)
suburbSecondChoice['values'] = suburb_list
suburbSecondChoice.pack()

# Creates a filter label for the combobox
filterLabel = ttk.Label(root, text="Enter a Filter Option: ")
filterLabel.pack()

# Creates a drop down box for the filter options
dropDownVar = StringVar()
dropDownFilter = ttk.Combobox(root, textvariable=dropDownVar)
dropDownFilter['values'] = ("LESS THAN", "GREATER THAN", "EQUAL TO")
dropDownFilter.pack()

# Creates the label for the entry box for the filter
filterSecondLabel = ttk.Label(root, text="Enter a Value for the Filter: ")
filterSecondLabel.pack()

# Creates the entry box for the filter
filter = StringVar()
entryFilter = ttk.Entry(root, textvariable=filter)
entryFilter.pack()

# Creates the checkbox to use all features
allFeaturesVar = IntVar()
allFeatures = Tkinter.Checkbutton(root, text="Use All Features", variable=allFeaturesVar)
allFeatures.pack()
allFeatures.deselect()

# Creates the checkbox to use all the filtered features
filteredFeaturesVar = IntVar()
filteredFeatures = Tkinter.Checkbutton(root, text="Use Filtered Features", variable=filteredFeaturesVar)
filteredFeatures.pack()
filteredFeatures.deselect()

# Executes the statistics processes based on the parameters set
okButton = ttk.Button(root, text="OK", command=tickBoxCheck)
okButton.pack(side="left")

#Creates a button to open the help file
helpButton = ttk.Button(root, text="Help File", command=openHelpFile)
helpButton.pack(side="right")

# Creates the Tkinter window
root.mainloop()
