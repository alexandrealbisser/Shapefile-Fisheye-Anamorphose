# pip install pyshp
# pip install matplotlib
import inspect
import shapefile
from math import*
import matplotlib.pyplot as plt

# sets the x and y constants for readability
global x, y
x, y = 0, 1


def switchList(list):
    xList, yList = [list[i][x] for i in range(len(list))], [list[i][y] for i in range(len(list))]

    return xList, yList


def plotShapes(shapes, points = True):
    for shape in shapes:
        if points:
            list = switchList(shape.points)
        else:
            list = switchList(shape)
        plt.plot(list[0], list[1])
    plt.show()


def changeTransformScale(function, newAtOrigin, newAtBound):
    oldAtOrigin, oldAtBound = function(0), function(1)
    ratio = (newAtOrigin - newAtBound) / (oldAtOrigin - oldAtBound)
    return lambda x: (function(x) - oldAtBound) * ratio + newAtBound


def plotTransform(function, ax1, n=100):
    t = [i/(n - 1) for i in range(n)]
    deform = [function(ti) for ti in t]
    tdeform = [t[i] * deform[i] for i in range(n)]
    ax1.plot(t, deform, color='blue', label='transform function')
    ax2 = ax1.twinx()
    ax2.plot(t, tdeform, color='red', label='applied transformation')
    ax1.legend()
    ax2.legend()


def getVector(pointA, pointB):
    return [(pointB[x] - pointA[x]), (pointB[y] - pointA[y])]


def computeDistance(pointA, pointB, returnVector=False):
    vector = getVector(pointA, pointB)
    distance = sqrt(vector[x] ** 2 + vector[y] ** 2)
    if returnVector:
        return distance, vector
    else:
        return distance


def transformShape(origin, maxDistance, points, function):
    newPoints = []

    for point in points:
        # gets the current point distance to origin
        distance, vector = computeDistance(origin, point, True)
        if type(maxDistance)==list:
            normalized = [0, 0]
            if vector[x] > 0:
                normalized[x] = distance / maxDistance[0]
            else:
                normalized[x] = distance / maxDistance[1]
            if vector[y] > 0:
                normalized[y] = distance / maxDistance[2]
            else:
                normalized[y] = distance / maxDistance[3]
            transform = [function(normalized[x]), function(normalized[y])]
            vector = [transform[x] * vector[x], transform[y] * vector[y]]
        else:
            # normalizes distance
            normalized = distance / maxDistance
            if normalized > 1:
                normalized = 1
            # computes the transform value for the point
            transform = function(normalized)
            # scales the vector
            vector = [transform * vector[x], transform * vector[y]]

        # computes the new point position
        newPoint = [origin[x] + vector[x], origin[y] + vector[y]]
        newPoints.append(newPoint)

    return newPoints


def computeTransform(origin, boundBox, function, maxDistance, shapeFileR, shapeFileW):
    # newShapes = []
    shapeFileType = shapeFileR.shapeType

    # computes max bound distance
    if type(maxDistance) != float:
        distXp = abs(boundBox[1][x] - origin[x])
        distXn = abs(boundBox[0][x] - origin[x])
        distYp = abs(boundBox[1][y] - origin[y])
        distYn = abs(boundBox[0][y] - origin[y])
        if maxDistance == "bounds":
            maxDistance = [distXp, distXn, distYp, distYn]
        elif maxDistance == "min":
            maxDistance = min([distXn, distXp, distYn, distYp])

    for shapeRec in shapeFileR.iterShapeRecords():
        newShape = transformShape(origin, maxDistance, shapeRec.shape.points, function)

        shapeFileW.record(*shapeRec.record)

        if shapeRec.shape.shapeType == shapefile.POINT:
            shapeFileW.point(newShape[0][x],newShape[0][y])
        elif shapeRec.shape.shapeType == shapefile.POLYLINE:
            shapeFileW.line([newShape])
        elif shapeRec.shape.shapeType == shapefile.POLYGON:
            shapeFileW.poly([newShape])
        elif shapeRec.shape.shapeType == shapefile.MULTIPOINT:
            shapeFileW.multipoint([newShape])
        elif shapeRec.shape.shapeType == shapefile.POINTZ:
            shapeFileW.pointz([newShape])
        elif shapeRec.shape.shapeType == shapefile.POLYLINEZ:
            shapeFileW.linez([newShape])
        elif shapeRec.shape.shapeType == shapefile.POLYGONZ:
            shapeFileW.polyz([newShape])
        elif shapeRec.shape.shapeType == shapefile.MULTIPOINTZ:
            shapeFileW.multipointz([newShape])
        elif shapeRec.shape.shapeType == shapefile.POINTM:
            shapeFileW.pointm([newShape])
        elif shapeRec.shape.shapeType == shapefile.POLYLINEM:
            shapeFileW.linem([newShape])
        elif shapeRec.shape.shapeType == shapefile.POLYGONM:
            shapeFileW.polym([newShape])
        elif shapeRec.shape.shapeType == shapefile.MULTIPOINTM:
            shapeFileW.multipointm([newShape])
        elif shapeRec.shape.shapeType == shapefile.MULTIPATCH:
            shapeFileW.multipatch([newShape])


def editShapefiles(origin, filenames, inpath, outpath, transform, maxDistance):
    inPaths = [inpath + filename for filename in filenames]
    outPaths = [outpath + filename for filename in filenames]
    boundBox = []

    for i in range(len(inPaths)):
        # create shapefile reader
        shapeFileR = shapefile.Reader(inPaths[i])
        # create shapefile writer using same type as reader
        shapeFileType = shapeFileR.shapeType
        shapeFileW = shapefile.Writer(outPaths[i], shapeType=shapeFileType)
        shapeFileW.autoBalance = 1
        # copy the existing fields
        shapeFileW.fields = shapeFileR.fields[1:]

        if i == 0:
            # gets the bounding box of the first shapefile and format it to a two points list
            boundBox = shapeFileR.bbox
            boundBox = [[boundBox[0], boundBox[1]], [boundBox[2], boundBox[3]]]


        # compute shapes transform
        computeTransform(origin, boundBox, transform, maxDistance, shapeFileR, shapeFileW)

        # save the new shapefile
        shapeFileW.close()


# center coordinates of the "fisheye" transform
# X=45.75757 Y=4.83197
origin = [842440, 6519200]

# transform function, assumes it is defined and monotonously decreasing on [0; 1]
# note: x*transform(x) should also be monotonous on [0; 1]
transform = lambda x : -log(0.2*x+0.1)

# transform factors/zoom at origin and bound
transformOrigin = 1.5
transformBound = 1

# shapefile path - .shp/.dbf/... library does not care about file extensions
#path = "base_shapes_Lyon/"
#filenames = ["bati_aroundLyon.shp", "bridges.shp", "cimetiere_aroundLyon.shp", "hydro_Lyon.shp", "metro_lines.shp",
#             "metro_stations.shp", "parcs_aroundLyon.shp", "places_aroundLyon.shp", "railway_lines_aroundLyon.shp", "streets_name.shp",
 #           "terrain_sport_aroundLyon.shp", "tram_lines.shp", "tram_stations.shp", "veget_aroundLyon.shp"]

path = "test/"
filenames = ["grid.shp"]

fig, ax1 = plt.subplots()

fstring = str(inspect.getsourcelines(transform)[0])
fstring = fstring.strip("['\\n']").split(" = ")
plt.title(str(fstring) + " zoom from " + str(transformOrigin) + " to " + str(transformBound))

transform = changeTransformScale(transform, transformOrigin, transformBound)
plotTransform(transform, ax1)
fig.tight_layout()
plt.show()

#editShapefiles(origin, filenames, path, path+"transformed_", transform, 2500.0)



