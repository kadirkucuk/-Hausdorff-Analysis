import numpy as np
import math
import arcpy
import os
arcpy.env.overwriteOutput = True
# ------------------------------------------------------------------------------------------------
TOPOVT_LargeBuilding_Layer = arcpy.GetParameterAsText(0) #TOPOVT Large Building Layer
TOPOVT_SmallBuilding_Layer = arcpy.GetParameterAsText(1) #TOPOVT Small Building Layer
OSM_Layer = arcpy.GetParameterAsText(2) #OSM Building Layer
Folder = arcpy.GetParameterAsText(3) # File location to save outputs
Method = arcpy.GetParameterAsText(4) # Method to Use
SmallBuilding_Threshold = arcpy.GetParameterAsText(5) # Small Building Threshold
Optional_Threshold = arcpy.GetParameterAsText(6) # Large Building Threshold
dsc_topovt = arcpy.Describe(TOPOVT_LargeBuilding_Layer) # Define the coordinate system of TOPOVT
coord_system_topovt = dsc_topovt.spatialReference 
# ------------------------------------------------------------------------------------------------
if Optional_Threshold: # Use if a threshold value is also given for large building analysis
    LargeBuilding_Threshold = Optional_Threshold
else: # Use the threshold value of small building analysis if a threshold value is not given for large building analysis
    LargeBuilding_Threshold = SmallBuilding_Threshold

# ------------------------------------------------------------------------------------------------
# The names of layers and attributes and data types are defined here
Hausdorff_Distance = "hausdorff" 
topodetaya = "TOPODETAYA"
name = "name"
m_distance = "distance"
overlap_ratio = "Overlap"
field_type = "Double"
field_type2 = "String"
feature_type = "POLYGON"
Matching_Buildings = os.path.join(Folder,"Matching_Buildings.shp")
Unmatched_Buildings = os.path.join(Folder,"Unmatched_Buildings.shp")
Matching_SmallBuildings = os.path.join(Folder,"Matching_SmallBuildings.shp")
Unmatched_SmallBuildings = os.path.join(Folder,"Unmatched_SmallBuildings.shp")
# ------------------------------------------------------------------------------------------------
# This function calculates the Hausdorff distance
def Hausdorff_dist(poly_a,poly_b):
    distance_list = [] # An empty list opens
    distance_list_a = []
    distance_list_b = []
    for i in range(len(poly_a)): # from each corner of the polygon a
        minimum_distance = 1000.0 # Minimum distance set as initial.
        for j in range(len(poly_b)): # to each corner of the polygon a
            distance = math.sqrt((poly_a[i].X - poly_b[j].X)**2+(poly_a[i].Y - poly_b[j].Y)**2) # The distance between corners is calculated
            if minimum_distance > distance: # If the calculated distance is greater than the minimum distance
                minimum_distance = distance # minimum distance is calculated distance
        distance_list_a.append(minimum_distance) # the minimum distance is added to the list
    distance_list.append(np.max(distance_list_a)) # The greatest value between the smallest distances becomes the Hausdorff distance
    for k in range(len(poly_b)): # from each corner of the polygon a
        minimum_distance = 1000.0 # Minimum distance set as initial.
        for l in range(len(poly_a)): # to each corner of the polygon a
            distance = math.sqrt((poly_a[l].X - poly_b[k].X)**2+(poly_a[l].Y - poly_b[k].Y)**2) # The distance between corners is calculated
            if minimum_distance > distance: #  If the calculated distance is greater than the minimum distance
                minimum_distance = distance # minimum distance is calculated distance
        distance_list_b.append(minimum_distance) # the minimum distance is added to the list
    distance_list.append(np.max(distance_list_b)) # The greatest value between the smallest distances becomes the Hausdorff distance
    return (np.min(distance_list))
# ------------------------------------------------------------------------------------------------
# This function finds corner points
def polygon_vertices(p1):
    for point in p1:
        return point
# ------------------------------------------------------------------------------------------------
# This function calculates overlap ratio between two polygons
def overlap_percent(poligon1, poligon2):
    overlapping_area = poligon1.intersect(poligon2, 4)
    total_area = poligon1.area + poligon2.area - overlapping_area.area
    rate = overlapping_area.area/total_area
    return (rate*100)
# This function adds polygons to the layer
def insert_cursor(base_polygon,polygon):
    cursor = arcpy.da.InsertCursor(base_polygon, ['SHAPE@'])
    for i in polygon:
        cursor.insertRow([i])
# ------------------------------------------------------------------------------------------------
# This function adds attributes to the attribute table in the layer.
def update_cursor(base_polygon,polygon_field,list):
    pointer = 0
    with arcpy.da.UpdateCursor(base_polygon, polygon_field) as cursor:
        for a in cursor:
            a[0] = list[pointer]
            pointer += 1
            cursor.updateRow(a)
# ------------------------------------------------------------------------------------------------
# This function analyzes Small Building
def SmallBuilding_Analysis(Input1,Input2,Threshold):
    OSM_Attributes = ["OID@", "SHAPE@",  "name","SHAPE@TRUECENTROID"] # List of features to be used in analysis
    cursor_osm = [ cursor for cursor in arcpy.da.SearchCursor(Input2, OSM_Attributes)] # Queries the properties of OSM data
    cursor_osm2 = cursor_osm[:]
    TOPOVT_Attributes = ["OID@", "SHAPE@", "TOPODETAYA","SHAPE@TRUECENTROID"] # List of features to be used in analysis
    cursor_topovt = [cursor for cursor in arcpy.da.SearchCursor(Input1,TOPOVT_Attributes )] # Queries the properties of TOPOVT data
    errors = 0
    # ----------------------------------------------------------
    # Blank lists pop up
    poly_list = []
    Point_TOPODETAY = []
    Point_TOPODETAY2 = []
    Point_name = []
    Point_name2 = []
    distance_list = []
    for topovt in cursor_topovt: # From each TOPOVT building
        try:
            poly_list2 = []
            number_of_matches = 0
            Matching = False
            for osm in cursor_osm: # To each OSM building
                distance = math.sqrt((topovt[3][0] - osm[3][0]) ** 2 + (topovt[3][1] - osm[3][1]) ** 2) # Distance between the centers of the buildings
                if distance < int(Threshold): # If the distance between the centers is less than the threshold value
                    Matching = True # There is a match
                    centroid_distance = distance
                    Point_TOPODETAY2 = topovt[2] # Topodetay number
                    Point_name2 = osm[2] # Name of the OSM polygon
                    poly_list2 = osm[1] # Matching OSM polygon
                    number_of_matches = number_of_matches+1 # Increase the number of matches by 1
                    cursor_osm2.remove(osm) # Add matching OSM polygon
            if Matching is True:
                if number_of_matches == 1: # If TOPOVT polygon only matches 1 OSM polygon
                    distance_list.append(centroid_distance)
                    Point_TOPODETAY.append(Point_TOPODETAY2) # Add topodetay number to list
                    poly_list.append(poly_list2) # Add OSM polygon to list 
                    Point_name.append(Point_name2) # Add the name of the OSM polygon to the list
        except:
            errors = +1
    insert_cursor(Matching_SmallBuildings, poly_list) # Add matching OSM polygon to layer
    update_cursor(Matching_SmallBuildings, topodetaya, Point_TOPODETAY) # Add Topodetay number
    update_cursor(Matching_SmallBuildings, name, Point_name) # Add the name of the OSM polygon to the attribute table
    update_cursor(Matching_SmallBuildings, m_distance, distance_list)
    Unmatched_Attributes = []
    Unmatched_Buildings = []

    for i in cursor_osm2: # Add remaining OSM polygons to unmatched buildings
        try:
            Unmatched_Buildings.append(i[1])
            Unmatched_Attributes.append(i[2])
        except:
            errors +=1
    insert_cursor(Unmatched_SmallBuildings, Unmatched_Buildings) # Add unmatched OSM polygon to layer
    update_cursor(Unmatched_SmallBuildings, name, Unmatched_Attributes) # Add the name of the OSM polygon to the attribute table
# ------------------------------------------------------------------------------------------------
# This function makes Hausdorff analysis according to the threshold method
def Threshold_Method(Input1,Input2,Threshold):
    OSM_Attribute = ["OID@", "SHAPE@",  "name","SHAPE@TRUECENTROID"] # List of features to be used in analysis
    cursors1 = [ cursor for cursor in arcpy.da.SearchCursor(Input2, OSM_Attribute)] # Queries the properties of OSM data
    cursors3 = cursors1[:]
    TOPOVT_Attribute = ["OID@", "SHAPE@", "TOPODETAYA","SHAPE@TRUECENTROID"] # List of features to be used in analysis
    cursors2 = [cursor for cursor in arcpy.da.SearchCursor(Input1,TOPOVT_Attribute )] # Queries the properties of TOPOVT data
    errors = 0
    # ----------------------------------------------------------
    # Blank lists pop up
    hausdorff_list = []
    TOPODETAY_list = []
    OSM_list = []
    Unmatched_Attributes = []
    Unmatched_list = []
    polygon_list = []
    overlap_ratio_list = []
    for topovt in cursors2: # From each TOPOVT building
        try:
            number_of_matches = 0
            Matching = False
            for osm in cursors1: # To each OSM building
                distance = math.sqrt((osm[3][0] - topovt[3][0]) ** 2 + (osm[3][1] - topovt[3][1]) ** 2) # Distance between the centers of the buildings
                if distance < int(Threshold): # If the distance between the centers is less than the threshold value
                    Matching = True # There is a match
                    overlap_percentage = overlap_percent(topovt[1], osm[1])
                    Hausdorff = Hausdorff_dist(polygon_vertices(osm[1]), polygon_vertices(topovt[1])) # Calculate  Hausdorff distance
                    topodetay = topovt[2] # Topodetay number
                    osm_name = osm[2] # Name of the OSM polygon
                    number_of_matches = number_of_matches + 1 # Increase the number of matches by 1
                    cursors3.remove(osm) # Remove matching OSM polygon
            if Matching is True:
                if number_of_matches == 1: # If there are only 1-1 matches
                    overlap_ratio_list.append(overlap_percentage)
                    hausdorff_list.append(Hausdorff) # Add Hausdorff distance to list
                    polygon_list.append(topovt[1]) # Add TOPOVT polygon to list
                    TOPODETAY_list.append(topodetay) # Add topodetay number to list
                    OSM_list.append(osm_name) # Add the name of the OSM polygon to the list
        except:
            errors += 1
    insert_cursor(Matching_Buildings, polygon_list) # Add matching TOPOVT polygons to Matching_Buildings layer
    update_cursor(Matching_Buildings, Hausdorff_Distance, hausdorff_list) # Add Hausdorff distances from the list to the attribute table of the Matching_Buildings layer
    update_cursor(Matching_Buildings, topodetaya, TOPODETAY_list) # Add topodetay numbers from the list to the attribute table of the Matching_Buildings layer
    update_cursor(Matching_Buildings, name, OSM_list) # Add the names of the OSM polygons in the list to the attribute table of the Matching_Buildings layer
    update_cursor(Matching_Buildings, overlap_ratio, overlap_ratio_list)
    for i in cursors3:
        try:
            Unmatched_list.append(i[1]) # Add unmatched OSM polygon to list
            Unmatched_Attributes.append(i[2]) # Add the name of the unmatched OSM polygon to the list
        except:
            errors +=1
    insert_cursor(Unmatched_Buildings, Unmatched_list) # Add unmatched OS0M polygons to the Unmatched_Buildings layer
    update_cursor(Unmatched_Buildings, name, Unmatched_Attributes) # Add the names of unmatched OSM polygons to the Unmatched_Buildings layer's attribute table
# ------------------------------------------------------------------------------------------------
# This function makes Hausdorff analysis according to centroid method
def Centroid_Method(Input1,Input2):
    OSM_Attribute = ["OID@","SHAPE@", "SHAPE@TRUECENTROID", "name"] # Attributes to be used in analysis
    cursors1 = [cursor for cursor in arcpy.da.SearchCursor(Input2, OSM_Attribute)] # Queries the properties of OSM data
    TOPOVT_Attribute = ["OID@","SHAPE@", "TOPODETAYA","SHAPE@TRUECENTROID"] # Attributes to be used in analysis
    cursors2 = [cursor for cursor in arcpy.da.SearchCursor(Input1,TOPOVT_Attribute )] #  Queries the properties of TOPOVT data
    errors = 0
    # Blank lists pop up
    hausdorff_list = []
    TOPODETAY_list = []
    OSM_list = []
    Unmatched_OSM_Attribute = []
    polygon_list = []
    Unmatched_list = []
    overlap_ratio_list = []
    for topovt in cursors2: # From each TOPOVT building
        for osm in cursors1: # To each OSM building
            try:
                OSM_Centroid = arcpy.Point(osm[2][0], osm[2][1]) # Define the center of the OSM polygon
                if topovt[1].contains(OSM_Centroid): # If the center of the OSM polygon is inside the TOPOVT polygon, there is a match
                    Hausdorff = Hausdorff_dist(polygon_vertices(osm[1]), polygon_vertices(topovt[1])) # Calculate  Hausdorff distance
                    overlap_ratio_percentage = overlap_percent(topovt[1],osm[1])
                    overlap_ratio_list.append(overlap_ratio_percentage)
                    hausdorff_list.append(Hausdorff) # Add Hausdorff distance to list
                    TOPODETAY_list.append(topovt[2]) # Add topodetay number to list
                    OSM_list.append(osm[3]) # Add the name of the OSM polygon to the list
                    polygon_list.append(topovt[1]) # Add matching TOPOVT polygon to list 
                    cursors1.remove(osm) # Remove matching OSM polygon
                    break
            except:
                errors +=1
    insert_cursor(Matching_Buildings, polygon_list) # Add TOPOVT polygons in the list to the Matching_Buildings layer
    update_cursor(Matching_Buildings, Hausdorff_Distance, hausdorff_list) # Add Hausdorff distances from the list to the attribute table of the Matching_Buildings layer
    update_cursor(Matching_Buildings, topodetaya, TOPODETAY_list) # Add topodetay numbers from the list to the attribute table of the Matching_Buildings layer
    update_cursor(Matching_Buildings, name, OSM_list) # Add the names of OSM polygons in the list to the Matching_Buildings layer
    update_cursor(Matching_Buildings, overlap_ratio, overlap_ratio_list)
    for i in cursors1:
        try:
            Unmatched_list.append(i[1]) # Add unmatched OSM polygons to the list
            Unmatched_OSM_Attribute.append(i[3]) # Add names of unmatched OSM polygons to list
        except:
            errors +=1
    insert_cursor(Unmatched_Buildings, Unmatched_list) # Add polygons in the list to the Unmatched_Buildings layer
    update_cursor(Unmatched_Buildings, name, Unmatched_OSM_Attribute) # Add the names of OSM polygons in the list to the attribute table of the Unmatched_Buildings layer

# ------------------------------------------------------------------------------------------------
# This function makes Hausdorff analysis according to the overlap method.
def Overlap_Method(Input1,Input2):
    OSM_Attribute = ["OID@", "SHAPE@",  "name","SHAPE@TRUECENTROID"] # Attributes to be used in analysis
    cursors1 = [ cursor for cursor in arcpy.da.SearchCursor(Input2, OSM_Attribute)] # Queries the properties of OSM data
    TOPOVT_Attribute = ["OID@", "SHAPE@", "TOPODETAYA","SHAPE@TRUECENTROID"] # Attributes to be used in analysis
    cursors2 = [cursor for cursor in arcpy.da.SearchCursor(Input1,TOPOVT_Attribute)] #  Queries the properties of TOPOVT data
    errors = 0
    # Blank lists pop up
    hausdorff_list = []
    TOPODETAY_list = []
    OSM_list = []
    Unmatched_OSM_Attribute = []
    Unmatched_list = []
    polygon_list = []
    overlap_ratio_list = []
    for topovt in cursors2: # From each TOPOVT building
        try:
            number_of_matches = 0
            Matching = False
            for osm in cursors1: # To each OSM building
                if osm[1].overlaps(topovt[1]): # If TOPOVT and OSM polygons overlap
                    Matching = True # There is a match
                    distance = Hausdorff_dist(polygon_vertices(osm[1]), polygon_vertices(topovt[1])) # Calculate  Hausdorff distance
                    Hausdorff = distance
                    overlap_ratio_percentage = overlap_percent(topovt[1],osm[1])
                    topodetay = topovt[2] # Topodetay number
                    osm_name = osm[2] # Name of the OSM polygon
                    number_of_matches = number_of_matches + 1  # Increase the number of matches by 1
                    cursors1.remove(osm) # Remove matching OSM polygon
            if Matching is True:
                if number_of_matches == 1: # If there are only 1-1 matches
                    overlap_ratio_list.append(overlap_ratio_percentage)
                    hausdorff_list.append(Hausdorff) # Add Hausdorff distance to list
                    polygon_list.append(topovt[1]) # Add TOPOVT polygon to list
                    TOPODETAY_list.append(topodetay) # Add topodetay number to list
                    OSM_list.append(osm_name) # Add the name of the OSM polygon to the list
        except:
            errors +=1
    insert_cursor(Matching_Buildings, polygon_list) # Add polygons from the list to the Matching_Buildings layer
    update_cursor(Matching_Buildings, Hausdorff_Distance, hausdorff_list) # Add Hausdorff distances from the list to the attribute table of the Matching_Buildings layer
    update_cursor(Matching_Buildings, topodetaya, TOPODETAY_list) # Add topodetay numbers from the list to the attribute table of the Matching_Buildings layer
    update_cursor(Matching_Buildings, name, OSM_list) # Add the names of OSM polygons in the list to the attribute table of the Eslesen_Binlar layer
    update_cursor(Matching_Buildings, overlap_ratio, overlap_ratio_list)
    for i in cursors1:
        try:
            Unmatched_list.append(i[1]) # Add unmatched OSM polygons to the list
            Unmatched_OSM_Attribute.append(i[2]) # Add names of unmatched OSM polygons to list
        except:
            errors +=1
    insert_cursor(Unmatched_Buildings, Unmatched_list) # Add polygons in the list to the Unmatched_Buildings layer
    update_cursor(Unmatched_Buildings, name, Unmatched_OSM_Attribute) # Add the names of OSM polygons in the list to the attribute table of the Unmatched_Buildings layer
# ------------------------------------------------------------------------------------------------
if Method == "Threshold Method": # If the threshold method is selected
    arcpy.CreateFeatureclass_management(Folder, "Matching_SmallBuildings.shp", feature_type) # Create Matching_SmallBuildings.shp file
    arcpy.CreateFeatureclass_management(Folder, "Unmatched_SmallBuildings.shp", feature_type) # Create Unmatched_SmallBuildings.shp file
    arcpy.AddField_management(Matching_SmallBuildings, topodetaya, field_type2) # Add column named topodetaya to the attribute table of the Matching_SmallBuildings layer
    arcpy.AddField_management(Matching_SmallBuildings, name, field_type2) # Add the name column to the attribute table of the Matching_SmallBuildings layer
    arcpy.AddField_management(Matching_SmallBuildings, m_distance, field_type)
    arcpy.AddField_management(Unmatched_SmallBuildings, name, field_type2) # Add the name column to the attribute table of the Unmatched_SmallBuildings layer
    SmallBuilding_Analysis(TOPOVT_SmallBuilding_Layer,OSM_Layer,SmallBuilding_Threshold) # Do small building analysis
    arcpy.CreateFeatureclass_management(Folder, "Matching_Buildings.shp", feature_type) # Create Matching_Buildings.shp file
    arcpy.CreateFeatureclass_management(Folder, "Unmatched_Buildings.shp", feature_type) # Create Unmatched_Buildings.shp file
    arcpy.AddField_management(Matching_Buildings, Hausdorff_Distance, field_type) # Add the Hausdorff column to the attribute table of the Matching_Buildings layer
    arcpy.AddField_management(Matching_Buildings, topodetaya, field_type2) # Add column named topodetaya to attribute table of Matching_Buildings layer
    arcpy.AddField_management(Matching_Buildings, name, field_type2) # Add name column to attribute table of Matching_Buildings layer
    arcpy.AddField_management(Matching_Buildings, overlap_ratio, field_type)
    arcpy.AddField_management(Unmatched_Buildings, name, field_type2) # Add name column to attribute table of Unmatched_Buildings layer
    # The next 4 lines define coordinate systems
    arcpy.DefineProjection_management(Matching_SmallBuildings, coord_system_topovt)
    arcpy.DefineProjection_management(Unmatched_SmallBuildings, coord_system_topovt)
    arcpy.DefineProjection_management(Matching_Buildings, coord_system_topovt)
    arcpy.DefineProjection_management(Unmatched_Buildings, coord_system_topovt)
    Threshold_Method(TOPOVT_LargeBuilding_Layer,Unmatched_SmallBuildings,LargeBuilding_Threshold) # Run the function of the threshold method
elif Method == "Overlap Method":
    arcpy.CreateFeatureclass_management(Folder, "Matching_SmallBuildings.shp", feature_type) # Create Matching_SmallBuildings.shp file
    arcpy.CreateFeatureclass_management(Folder, "Unmatched_SmallBuildings.shp", feature_type) # Create Unmatched_SmallBuildings.shp file
    arcpy.AddField_management(Matching_SmallBuildings, topodetaya, field_type2) # Add column named topodetaya to the attribute table of the Matching_SmallBuildings layer
    arcpy.AddField_management(Matching_SmallBuildings, name, field_type2) # Add the name column to the attribute table of the Matching_SmallBuildings layer
    arcpy.AddField_management(Matching_SmallBuildings, m_distance, field_type)
    arcpy.AddField_management(Unmatched_SmallBuildings, name, field_type2) # Add the name column to the attribute table of the Unmatched_SmallBuildings layer
    SmallBuilding_Analysis(TOPOVT_SmallBuilding_Layer,OSM_Layer,SmallBuilding_Threshold) # Do small building analysis
    arcpy.CreateFeatureclass_management(Folder, "Matching_Buildings.shp", feature_type) # Create Matching_Buildings.shp file
    arcpy.CreateFeatureclass_management(Folder, "Unmatched_Buildings.shp", feature_type) # Create Unmatched_Buildings.shp file
    arcpy.AddField_management(Matching_Buildings, Hausdorff_Distance, field_type) # Add the Hausdorff column to the attribute table of the Matching_Buildings layer
    arcpy.AddField_management(Matching_Buildings, topodetaya, field_type2) # Add column named topodetaya to attribute table of Matching_Buildings layer
    arcpy.AddField_management(Matching_Buildings, name, field_type2) # Add name column to attribute table of Matching_Buildings layer
    arcpy.AddField_management(Matching_Buildings, overlap_ratio, field_type)
    arcpy.AddField_management(Unmatched_Buildings, name, field_type2) # Add name column to attribute table of Unmatched_Buildings layer
    # The next 4 lines define coordinate systems
    arcpy.DefineProjection_management(Matching_SmallBuildings, coord_system_topovt)
    arcpy.DefineProjection_management(Unmatched_SmallBuildings, coord_system_topovt)
    arcpy.DefineProjection_management(Matching_Buildings, coord_system_topovt)
    arcpy.DefineProjection_management(Unmatched_Buildings, coord_system_topovt)
    Overlap_Method(TOPOVT_LargeBuilding_Layer,Unmatched_SmallBuildings) # Run function of overlap method
elif Method == "Centroid Method":
    arcpy.CreateFeatureclass_management(Folder, "Matching_SmallBuildings.shp", feature_type) # Create Matching_SmallBuildings.shp file
    arcpy.CreateFeatureclass_management(Folder, "Unmatched_SmallBuildings.shp", feature_type) # Create Unmatched_SmallBuildings.shp file
    arcpy.AddField_management(Matching_SmallBuildings, topodetaya, field_type2) # Add column named topodetaya to the attribute table of the Matching_SmallBuildings layer
    arcpy.AddField_management(Matching_SmallBuildings, name, field_type2) # Add the name column to the attribute table of the Matching_SmallBuildings layer
    arcpy.AddField_management(Matching_SmallBuildings, m_distance, field_type)
    arcpy.AddField_management(Unmatched_SmallBuildings, name, field_type2) # Add the name column to the attribute table of the Unmatched_SmallBuildings layer
    SmallBuilding_Analysis(TOPOVT_SmallBuilding_Layer,OSM_Layer,SmallBuilding_Threshold) # Do small building analysis
    arcpy.CreateFeatureclass_management(Folder, "Matching_Buildings.shp", feature_type) # Create Matching_Buildings.shp file
    arcpy.CreateFeatureclass_management(Folder, "Unmatched_Buildings.shp", feature_type) # Create Unmatched_Buildings.shp file
    arcpy.AddField_management(Matching_Buildings, Hausdorff_Distance, field_type) # Add the Hausdorff column to the attribute table of the Matching_Buildings layer
    arcpy.AddField_management(Matching_Buildings, topodetaya, field_type2) # Add column named topodetaya to attribute table of Matching_Buildings layer
    arcpy.AddField_management(Matching_Buildings, name, field_type2) # Add name column to attribute table of Matching_Buildings layer
    arcpy.AddField_management(Matching_Buildings, overlap_ratio, field_type)
    arcpy.AddField_management(Unmatched_Buildings, name, field_type2) # Add name column to attribute table of Unmatched_Buildings layer
    # The next 4 lines define coordinate systems
    arcpy.DefineProjection_management(Matching_SmallBuildings, coord_system_topovt)
    arcpy.DefineProjection_management(Unmatched_SmallBuildings, coord_system_topovt)
    arcpy.DefineProjection_management(Matching_Buildings, coord_system_topovt)
    arcpy.DefineProjection_management(Unmatched_Buildings, coord_system_topovt)
    Centroid_Method(TOPOVT_LargeBuilding_Layer,Unmatched_SmallBuildings) # Run the function of the centroid method
# The following lines allow layers to be displayed in ArcMap software
mxd = arcpy.mapping.MapDocument("CURRENT")
df = arcpy.mapping.ListDataFrames(mxd, "*")[0]
newlayer1 = arcpy.mapping.Layer(Matching_SmallBuildings)
newlayer2 = arcpy.mapping.Layer(Unmatched_SmallBuildings)
newlayer3 = arcpy.mapping.Layer(Matching_Buildings)
newlayer4 = arcpy.mapping.Layer(Unmatched_Buildings)
arcpy.mapping.AddLayer(df, newlayer1, "BOTTOM")
arcpy.mapping.AddLayer(df, newlayer2,"BOTTOM")
arcpy.mapping.AddLayer(df, newlayer3, "BOTTOM")
arcpy.mapping.AddLayer(df, newlayer4, "BOTTOM")