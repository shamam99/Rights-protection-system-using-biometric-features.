from flask import Flask, render_template, request
import matplotlib.pyplot as plt
import webview
import pickle
import face_recognition
import cvzone
from datetime import datetime
import numpy as np
import os
import cv2
from PIL import Image
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage
from firebase_admin import auth
from werkzeug.utils import secure_filename


app = Flask(__name__, static_folder='static')


cred = credentials.Certificate("verifyingofpatients.json")

firebase_admin.initialize_app(cred, {
    'databaseURL':"https://verifyingofpatients-default-rtdb.firebaseio.com/",
    'storageBucket':"verifyingofpatients.appspot.com"
})
bucket = storage.bucket()

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db_ref = db.reference('patients')

                                                                  #start camera coding here


camera_active = False  # Global variable to track camera activation status
camera = None  # Initialize camera object

def get_camera():
    global camera
    if camera is None:
        camera = cv2.VideoCapture(1)
        camera.set(3, 640)
        camera.set(4, 480)
    return camera
@app.route('/')
def index():
    return render_template('index.html')
    
    
@app.route('/activate_camera', methods=['GET'])
def activate_camera():
    
    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)


    imgBackground = cv2.imread('Resources/background.png')

    success, img = cap.read()



    folderModePath = 'Resources/Modes'
    modePathList = os.listdir(folderModePath)
    imgModeList = []
    for path in modePathList:
        imgModeList.append(cv2.imread(os.path.join(folderModePath, path)))
    # print(len(imgModeList))

    # Load the encoding file
    print("Loading Encode File ...")
    file = open('EncodeFile.p', 'rb')
    encodeListKnownWithIds = pickle.load(file)
    file.close()
    encodeListKnown, patientIds = encodeListKnownWithIds
    # print(patientIds)
    print("Encode File Loaded")

    #change the mods
    modeType = 0
    counter = 0
    id = -1
    imgpatient = []

    while True:
        success, img = cap.read()
        if not success or img is None:
            print("Failed to capture frame")
            continue

        imgS = cv2.resize(img, (0,0), None, 0.25, 0.25) #ensure the size of the image
        imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

        faceCurFrame = face_recognition.face_locations(imgS)
        encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)

        imgBackground[162:162 + 480, 55:55 + 640] = img
        imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]
        
        
        
        
    
                     #start to detect here to match the face on the camera with the face in the database (the codes should be the same)
        match_found = False
        if faceCurFrame:
            for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
                matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
                faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
                # print("matches", matches)
                # print("faceDis", faceDis)

                matchIndex = np.argmin(faceDis)
                # print("Match Index", matchIndex)

                if matches[matchIndex]:
                    if counter == 0:
                        cvzone.putTextRect(imgBackground, "Loading", (275, 400))
                        cv2.imshow("Face Attendance", imgBackground)
                        cv2.waitKey(1)
                        counter = 1
                        modeType = 1
                    match_found = True
                    id = patientIds[matchIndex]
                    matched_patient = db_ref.child(id).get()
                    response_text = f"Name: {matched_patient['name']}\n" \
                                f"Last Name: {matched_patient['Lname']}\n" \
                                f"Age: {matched_patient['Age']}\n" \
                                f"Blood Type: {matched_patient['bloodtype']}\n" \
                                f"Insurance Year: {matched_patient['insurance_year']}\n" \
                                f"Total Visits: {matched_patient['total_visit']}\n" \
                                f"Last Verification Time: {matched_patient['last_verify_time']}"
                    return response_text

            if counter != 0:
    
                if counter == 1:
                    # Get the Data/downolad data starte here
                    patientInfo = db.reference(f'patients/{id}').get()
                    print(patientInfo)
                    # Get the Image from the storage    
                    blob = bucket.get_blob(f'Images/{id}.png')
                    array = np.frombuffer(blob.download_as_string(), np.uint8)
                    imgpatient = cv2.imdecode(array, cv2.COLOR_BGRA2BGR)
                    # Update data of attendance
                    datetimeObject = datetime.strptime(patientInfo['last_verify_time'],
                                                   "%Y-%m-%d %H:%M:%S")
                    secondsElapsed = (datetime.now() - datetimeObject).total_seconds()
                    
                    if secondsElapsed > 180:
                        
                        modeType = 3
                        
                        
                    print(secondsElapsed)
                    if secondsElapsed > 30:
                        ref = db.reference(f'patients/{id}')
                        patientInfo['total_visit'] += 1
                        ref.child('total_visit').set(patientInfo['total_visit'])
                        ref.child('last_verify_time').set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    else:
                        modeType = 3
                        counter = 0
                        imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]
                    
        else:
            modeType = 0
            counter = 0
        # cv2.imshow("Webcam", img)
        cv2.imshow("insurance camera", imgBackground)
        if cv2.waitKey(1) == ord('q'):
                break
            
                                        #start to detect fingerprint here
                                        
    
def compare_uploaded_image_with_storage(uploaded_image_path, unique_identifier):
    
    uploaded_image = cv2.imread(uploaded_image_path)
    uploaded_image_gray = cv2.cvtColor(uploaded_image, cv2.COLOR_BGR2GRAY)
    
    try:

        patient_image_name =f"fingers/{unique_identifier}.BMP"
        blob = bucket.blob(patient_image_name)
        local_patient_image_path = f"temp_patient_images/{unique_identifier}.BMP"
        blob.download_to_filename(local_patient_image_path)

        patient_image = cv2.imread(local_patient_image_path)
        patient_image_gray = cv2.cvtColor(patient_image, cv2.COLOR_BGR2GRAY)

        # Create a SIFT detector
        sift = cv2.SIFT_create()

        # Detect keypoints and compute descriptors for the uploaded and patient images
        keypoints_1, des1 = sift.detectAndCompute(uploaded_image_gray, None)
        keypoints_2, des2 = sift.detectAndCompute(patient_image_gray, None)

        if keypoints_1 is None or keypoints_2 is None:
            return "Keypoint detection failed"

                                                                   # Create a FLANN-based matcher for keypoint matching
        matcher = cv2.FlannBasedMatcher({"algorithm": 1, "trees": 10}, {})
        matches = matcher.knnMatch(des1, des2, k=2)

        # Filter good matches based on Lowe's ratio test
        match_points = [p for p, q in matches if p.distance < 0.1 * q.distance]

        # Calculate a matching score as the ratio of good matches to total keypoints
        keypoints = min(len(keypoints_1), len(keypoints_2))
        score = len(match_points) / keypoints * 100

        # Set a threshold for considering a match
        threshold = 50  # You can adjust this threshold based on your requirement

        # Return the result based on the comparison score
        if score >= threshold:
            return f"Match found for {unique_identifier}"
        else:
            return "No match found"
        
    except Exception as e:
        print(f"Error occurred: {e}")
        return "No matching fingerprint file found"
    
    
                                                     #routing for all files
                                                     
                                                     
@app.route('/deactivate_camera', methods=['GET'])
def deactivate_camera():
    global camera_active
    global camera
    
    # Check if the camera is not active
    if not camera_active:
        return 'Camera is already inactive', 200
    
    # Set camera_active to False to indicate camera deactivation
    camera_active = False
    
    # Release the camera object if it's not None
    if camera is not None:
        camera.release()
    
    return 'Camera Deactivated', 200
    
@app.route('/result/<patient_id>')
def display_result(patient_id):
    patient_info = db_ref.child(patient_id).get()
    return render_template('patient_info.html', patient_info=patient_info)

# Route for rendering the HTML page with the fingerprint upload button
@app.route('/', methods=['GET'])
def upload_fingerprint_page():
    return render_template('index.html')


def get_patient_data(unique_identifier):
    ref = db.reference('/patients')
    patient_ref = ref.child(unique_identifier)
    return patient_ref.get()


# Route for handling the uploaded fingerprint and performing matching
@app.route('/upload_fingerprint', methods=['POST'])
def upload_fingerprint():
    if 'fingerprint' not in request.files:
        return "No file part"

    fingerprint_file = request.files['fingerprint']

    if fingerprint_file.filename == '':
        return "No selected file"

    if fingerprint_file:
        unique_identifier = fingerprint_file.filename.split('.')[0]

        filename = secure_filename(fingerprint_file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        fingerprint_file.save(filepath)

        result = compare_uploaded_image_with_storage(filepath, unique_identifier)
        # If the result indicates no match found, return a specific message to the result page
        if result == "No match found":
            return "Not matching"
        else:
            # Fetch patient data based on the unique identifier
            patient_data = get_patient_data(unique_identifier)
            response_text = f"Name: {patient_data['name']}\n" \
                                f"Last Name: {patient_data['Lname']}\n" \
                                f"Age: {patient_data['Age']}\n" \
                                f"Blood Type: {patient_data['bloodtype']}\n" \
                                f"Insurance Year: {patient_data['insurance_year']}\n" \
                                f"Total Visits: {patient_data['total_visit']}\n" \
                                f"Last Verification Time: {patient_data['last_verify_time']}"
            # Increment total_visit for the matched patient
            if 'total_visit' in patient_data:
                patient_data['total_visit'] += 1
            else:
                patient_data['total_visit'] = 1
            
            # Update total_visit in the database
            ref = db.reference('/patients')
            ref.child(unique_identifier).update({'total_visit': patient_data['total_visit']})
            
            return response_text
        
        
        
# Create a new user and assign the "insurance" role
@app.route('/create_user_and_assign_role', methods=['GET'])
def create_user_and_assign_role():
    try:
        # Create a new user
        user = auth.create_user(
            email='fayrouzasiri@gmail.com',
            email_verified=False,
            password='fay1234',
            display_name='insurance',
        )

        # Assign the "insurance" role to the newly created user
        auth.set_custom_user_claims(user.uid, {'insurance': True})

        return "New user created and 'insurance' role assigned successfully", 200

    except Exception as e:
        return f"Error creating user and assigning role: {e}", 500
    
       
@app.route('/assign_role', methods=['POST'])
def assign_role():
    # Assuming you receive user ID and role in the request
    user_id = request.json.get('CZRgfUrQA1NLm83a9bvFG8DByRA2', None)
    role = request.json.get('insurance', None)

    if not user_id or not role:
        return "User ID or role not provided", 400

    try:
        # Set custom claims based on role
        auth.set_custom_user_claims(user_id, {role: True})
        return f"Role '{role}' assigned to user '{user_id}'", 200
    except Exception as e:
        return f"Error assigning role: {e}", 500
    
    
    
@app.route('/verify_access', methods=['POST'])
def verify_access():
    data = request.get_json()  # Get the JSON data from the request
    id_token = data.get('idToken')  # Access the 'idToken' field from the JSON

    if not id_token:
        return "No token provided", 400

    try:
        decoded_token = auth.verify_id_token(id_token)
        user_id = decoded_token['uid']
        
        # Check for custom claims to determine access
        user = auth.get_user(user_id)
        user_custom_claims = user.custom_claims
        
        if user_custom_claims.get('hospital'):
            # Logic for hospital user access (user validation)
            return "Hospital user: Allowed to validate users", 200
        elif user_custom_claims.get('insurance'):
            # Logic for insurance user access (database updates)
            return "Insurance user: Allowed to update database", 200
        else:
            return "Unauthorized user", 403

    except Exception as e:
        return f"Error: {e}", 500

if __name__ == '__main__':
    app.run(debug=True)
