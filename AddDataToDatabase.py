import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

cred = credentials.Certificate("verifyingofpatients.json")

firebase_admin.initialize_app(cred, {
    'databaseURL': "https://verifyingofpatients-default-rtdb.firebaseio.com/",
    'storageBucket':"verifyingofpatients.appspot.com"
})

ref = db.reference('test')

data = {
    "32165": {
        "name": "Mohammed",
        "Lname": "alkafri",
        "insurance_year": 2020,
        "total_visit": 7,
        "bloodtype": "O",
        "Age": 23,
        "last_verify_time": "2022-12-11 00:54:34",
        "fingerprint_reference": "fingers/32165.bmp"  # Reference to fingerprint images in Firebase Storage
    },
    "85274": {
        "name": "Emy",
        "Lname": "lanston",
        "insurance_year": 2019,
        "total_visit": 10,
        "bloodtype": "A",
        "Age": 30,
        "last_verify_time": "2020-10-12 00:30:20",
        "fingerprint_reference": "fingers/85274.bmp"  # Reference to fingerprint images in Firebase Storage
    },
    "96385": {
        "name": "Elon",
        "Lname": "mask",
        "insurance_year": 2015,
        "total_visit": 25,
        "bloodtype": "AB",
        "Age": 36,
        "last_verify_time": "2023-10-11 00:02:20",
        "fingerprint_reference": "fingers/96385.bmp"  # Reference to fingerprint images in Firebase Storage
    }
}

try:
    for key, value in data.items():
        ref.child(key).set(value)
    print("Data successfully updated.")
except Exception as e:
    print("Error:", e)
    
    
