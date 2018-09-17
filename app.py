from flask import Flask, render_template, request
from fhirclient import client
import fhirclient.models.patient as p
import fhirclient.models.observation as o
import fhirclient.models.list as l
import fhirclient.models.medication as m
import fhirclient.models.condition as c
import fhirclient.models.practitioner as pr
import datetime

# create the application object
APP = Flask(__name__, static_folder='static')
settings = {
    'app_id': 'my_web_app',
    'api_base': 'http://fhirtest.uhn.ca/baseDstu3/'
}
#Initialize a global smart token to use as the server
smart = client.FHIRClient(settings=settings)

def getPatient(pID):
    """
        Extract basic demographic information from the Patient FHIR resource
    """

    patient = p.Patient.read(pID, smart.server).as_json()
    name = patient['name'][0]['given'][0] + " " + patient['name'][0]['family']
    age = datetime.date.today().year - int(patient['birthDate'].split('-')[0])
    return name,patient['gender'],age

def getMedications(pID):
    medications = ""
    search = l.List.where(struct={'subject': pID})
    lists = search.perform_resources(smart.server)
    for list in lists:
        list_json = list.as_json()
        if list_json['title'] == 'Medications':
            for entry in list_json['entry']:
                mID = entry['item']['reference'].split('/')[1]
                search = m.Medication.where(struct={'_id': mID})
                meds = search.perform_resources(smart.server)
                for med in meds:
                    med_json = med.as_json()
                    medications = medications + med_json['code']['coding'][0]['display'] + ", "
    return medications

def getCondition(pID):
    problem_list = ""
    practitioner = ""
    search = c.Condition.where(struct={'subject': pID})
    conditions = search.perform_resources(smart.server)
    for con in conditions:
        problem_list = problem_list + con.as_json()['code']['coding'][0]['display']
        search = pr.Practitioner.where(struct={'_id': con.as_json()['asserter']['reference'].split('/')[1]})
        practitioners = search.perform_resources(smart.server)
        for practs in practitioners:
            practitioner = practitioner + practs.as_json()['name'][0]['given'][0] + ' ' + \
                           practs.as_json()['name'][0]['family'] + ', ' + \
                           practs.as_json()['qualification'][0]['code']['text'] + ', ' + \
                           practs.as_json()['telecom'][0]['value']
    return practitioner,problem_list

def getObservations():
    """
        Extract data from the Observation FHIR resource
    """
    search = o.Observation.where(struct={'subject': patID})
    observations = search.perform_resources(smart.server)
    for obs in observations:
        o_out = obs.as_json()
    return 'Reason for visit: ' + o_out['code']['coding'][0]['display']

@APP.route('/get-patient', methods=['GET'])
def getPatientID():
    if 'file' not in request.files:
        return ""
    file = request.files['file']


@APP.route('/', methods=['GET', 'POST'])
def home():
    """
        Landing page for the app, displays patient and observation data by default
    """
    if request.method == 'POST':
        name = request.form['patients']

        if name == 'Michael':
            pID = 'cf-1537060831781'

        name,gender,age = getPatient(pID)
        medications = getMedications(pID)[:-2]
        practitioner,problem_list = getCondition(pID)
        return render_template('index.html', name=name, gender=gender, age=age, meds=medications, prob=problem_list, practitioner=practitioner)
    else:
        return render_template('test_patients.html')

# start the server with the 'run()' method
if __name__ == '__main__':
    APP.run(debug=True, host="0.0.0.0", port=8000)
