import cv2
import face_recognition
import pickle
import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import  storage

cred = credentials.Certificate("verifyingofpatients.json")

firebase_admin.initialize_app(cred, {
   'databaseURL':"https://verifyingofpatients-default-rtdb.firebaseio.com/",
    'storageBucket':"verifyingofpatients.appspot.com"
})



# Importing patient images
folderPath = 'fingers'
pathList = os.listdir(folderPath)
print(pathList)
imgList = []
patientIds = [] #to call the name of the image with path
for path in pathList:
    imgList.append(cv2.imread(os.path.join(folderPath, path))) # to split the path from the name to extract the value
    patientIds.append(os.path.splitext(path)[0])
    
    fileName = f'{folderPath}/{path}'
    bucket = storage.bucket()
    blob = bucket.blob(fileName)
    blob.upload_from_filename(fileName)

#---------------------------------------------------------------------------------------#
    # print(path)
    # print(os.path.splitext(path)[0])
    
print(patientIds)

#start to encode the images so can store it in DB
def findEncodings(imagesList):
    encodeList = []
    for img in imagesList:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodeList.append(encode) #put it in a loop

    return encodeList

#to give us the instruction of loading
print("Encoding Started ...")
encodeListKnown = findEncodings(imgList) #store the ecoding data with the names
encodeListKnownWithIds = [encodeListKnown, patientIds]
print("Encoding Complete")

file = open("EncodeFile.p", 'wb') #to give permition
pickle.dump(encodeListKnownWithIds, file)
file.close() #close the file and save
print("File Saved")

