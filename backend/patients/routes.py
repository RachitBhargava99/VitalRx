from flask import Blueprint, request, current_app
from backend.models import Patient, User
from backend import db, mail
import json
import random
import requests
from datetime import datetime
from flask_mail import Message

patients = Blueprint('patients', __name__)


# Checker to see whether or not is the server running
@patients.route('/patients/add', methods=['POST'])
def add_patient():
    request_json = request.get_json()

    auth_token = request_json['auth_token']
    user = User.verify_auth_token(auth_token)

    pat = Patient(name=request_json['name'], doctor_id=user.id, nurse_id=request_json['nurse_id'], is_male=request_json['is_male'], age=request_json['age'])

    db.session.add(pat)
    db.session.commit()

    return json.dumps({'message': "Patient Added Successfully", 'status': 0})


@patients.route('/patients/view/<patient_id>', methods=['POST'])
def get_patient_info(patient_id):
    request_json = request.get_json()

    pat = Patient.query.filter_by(id=patient_id).first()

    if pat is None:
        return json.dumps({'message': "Incorrect Patient ID Provided", 'status': 1})
    else:
        if request_json.get('past_info') is None:
            bp_sys = random.randint(80, 200)
            bp_dias = bp_sys * int((1 + random.random() * 0.25))
            final_dict = {
                'patient_name': pat.name,
                'doctor_name': User.query.filter_by(id=pat.doctor_id).first().name,
                'nurse_name': User.query.filter_by(id=pat.nurse_id).first().name,
                'bp_sys': bp_sys,
                'bp_dias': bp_dias,
                'heart_rate': random.randint(40, 200),
                'gender': 'Male' if pat.is_male else 'Female',
                'age': pat.age,
                'temperature': round(98.7 + 4 * (random.random() - 0.5), 1),
                'o2_sat': 95 + int(10 * (random.random() - 0.5)),
                'resp_rate': 16 + int(20 * (random.random() - 0.5))
            }
        else:
            bp_sys = int(10 * (random.random() - 0.5)) + request_json['past_info']['bp_sys']
            bp_dias = bp_sys * int((1 + random.random() * 0.25))
            final_dict = {
                'patient_name': pat.name,
                'doctor_name': User.query.filter_by(id=pat.doctor_id).first().name,
                'nurse_name': User.query.filter_by(id=pat.nurse_id).first().name,
                'bp_sys': bp_sys,
                'bp_dias': bp_dias,
                'heart_rate': int(10 * (random.random() - 0.5)) + request_json['past_info']['heart_rate'],
                'gender': 'Male' if pat.is_male else 'Female',
                'age': pat.age,
                'temperature': request_json['past_info']['temperature'],
                'o2_sat': request_json['past_info']['o2_sat'] + int(2 * (random.random() - 0.5)),
                'resp_rate': request_json['past_info']['resp_rate'] + int(2 * (random.random() - 0.5))
            }

        apikey = 'egPh5UOh9KSnPryHPC5289APk7z3QCURTCHQNUEba_Vr'

        url = "https://iam.bluemix.net/oidc/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = "apikey=" + apikey + "&grant_type=urn:ibm:params:oauth:grant-type:apikey"
        IBM_cloud_IAM_uid = "bx"
        IBM_cloud_IAM_pwd = "bx"
        response = requests.post(url, headers=headers, data=data, auth=(IBM_cloud_IAM_uid, IBM_cloud_IAM_pwd))
        iam_token = response.json()["access_token"]

        header = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + iam_token,
                  'ML-Instance-ID': 'f0e1f0f2-1f07-47ef-baaf-82019f1ff85e'}

        payload_scoring = {"input_data": [{"fields": ["gender", "Age", "Non-Invasive BP Systolic",
                                                      "Non-Invasive BP Diastolic", "Temperature (F)",
                                                      "O2 Saturation", "Heart Rate", "Respiratory Rate",
                                                      "Pain Score"], "values": [[final_dict['gender'], final_dict['age'],
                                                                                 final_dict['bp_sys'], final_dict['bp_dias'],
                                                                                 final_dict['temperature'], final_dict['o2_sat'],
                                                                                 final_dict['heart_rate'], final_dict['resp_rate'],
                                                                                 None]]}]}

        response_scoring = json.loads(requests.post(
            'https://us-south.ml.cloud.ibm.com/v4/deployments/5549218c-486c-4634-8876-9c222be57f19/predictions',
            json=payload_scoring, headers=header).text)

        final_dict['pain_score'] = response_scoring
        return json.dumps(final_dict)


@patients.route('/patients/all', methods=['POST'])
def get_all_patients():
    request_json = request.get_json()

    auth_token = request_json['auth_token']
    user = User.verify_auth_token(auth_token)

    if user.isDoctor:
        all_pats = Patient.query.filter_by(doctor_id=user.id)
    else:
        all_pats = Patient.query.filter_by(nurse_id=user.id)

    patient_data = [{'name': curr_pat.name, 'doctor_name': User.query.filter_by(id=curr_pat.doctor_id).first().name,
                     'nurse_name': User.query.filter_by(id=curr_pat.nurse_id).first().name, 'age': curr_pat.age,
                     'gender': "Male" if curr_pat.is_male else "Female"} for curr_pat in all_pats]

    return json.dumps({'patients': patient_data, 'status': 0})
