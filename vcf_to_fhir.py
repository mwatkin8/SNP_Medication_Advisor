import json, requests, argparse, sqlite3, re, datetime

def parse_VCF(filename):
    with open(filename, 'r') as file:
        var_list = []
        for line in file:
            line_list = line.split('\t')
            if len(line_list) < 3:
                continue
            elif line_list[2][0] != 'r':
                continue
            else:
                rsID = line_list[2]
                geno = extract_genotype(line_list)
                if geno != 'no call':
                    var_list.append((rsID, geno))
        return var_list

def extract_genotype(line_list):
    gt = line_list[9]
    ref = line_list[3]
    alt = line_list[4]
    geno_list = ['$','$']

    if gt[0] == '.':
        return 'no call'
    elif gt[0] == '0':
        geno_list[0] = ref
    elif gt[0] == '1':
        geno_list[0] = alt
    else:
        print('Non-decomposed VCF at POS = ' + str(line_list[1]))

    if gt[2] == '.':
        return 'no call'
    elif gt[2] == '0':
        geno_list[1] = ref
    elif gt[2] == '1':
        geno_list[1] = alt
    else:
        print('Non-decomposed VCF at POS = ' + str(line_list[1]))

    geno = "".join(geno_list)
    return geno

def query_pharmGKB_web(rsID):
    url = 'https://api.pharmgkb.org/v1/data/clinicalAnnotation?location.fingerprint=' + rsID + '&view=base'
    print(url)
    response = requests.get(url)
    print(response.status_code)
    if response != None:
        json_data = json.loads(response.text)
        if response.status_code == '404':
            return 'No pharmGKB annotations found'
        else:
            return json_data

def query_pharmGKB_db(rsID):
    with sqlite3.connect('db/pharmGKB_ann.sqlite') as db:
        cursor = db.cursor()
        try:
            cursor.execute("SELECT * FROM clinical_ann_metadata WHERE Location='" + rsID + "'")
            rows = cursor.fetchall()
            val = str(rows)
            if val == '[]':
                return 'No pharmGKB clinical annotations found'
            else:
                return val
        except: return "database error"

def parse_annotations(annotation, geno):
    annotation.strip('\\')
    pattern = geno + ":[\w\s.\,\\\:\+\-\(\)']+"
    ann = re.search(pattern, annotation)
    return ann.group()


def create_obs(patient, rsID, geno, annotation):

    if annotation != 'No pharmGKB clinical annotations found':
        ann = parse_annotations(annotation, geno)
    else:
        ann = annotation

    #Since only SNPs are being queried for annqotations, each variant is stored as a "Simple variant" as defined in LOINC (https://s.details.loinc.org/LOINC/81252-9.html?sections=Comprehensive)
    obs = {
      "resourceType": "Observation",
      "text": {
        "status": "generated",
        "div": "<div xmlns='http://www.w3.org/1999/xhtml'><a name='mm'/></div>"
      },
      "id": "",
      "subject": {
        "reference": patient
      },
      "status": "final",
      "code": {
        "coding": [
          {
            "code": "LP212295-2",
            "system": "http://loinc.org",
            "display": "Simple variant"
          }
        ]
      },
      "identifier": [
        {
          "value": rsID,
          "system": "dbSNP"
        }
      ],
      "valueString": geno,
      "comment": ann
    }
    return json.dumps(obs, indent=4)

def create_list(obs_ids, patient, file_name):

    list = {
        "resourceType": "List",
        "text": {
        "status": "generated",
        "div": "<div xmlns='http://www.w3.org/1999/xhtml'>test VCF<a name='mm'/></div>"
        },
        "id": "",
        "subject": {
            "reference": patient
        }
    }
    entries = []
    for id in obs_ids:
        entry = {
                "item": {
                    "reference": "Observation/" + id
                }
            }
        entries.append(entry)

    list['entry'] = entries
    list['status'] = 'current'
    list['mode'] = 'working'
    list['title'] = file_name
    list['note'] = [
        {
            "text": "ftp://ftp-trace.ncbi.nih.gov/1000genomes/ftp/pilot_data/release/2010_07/exon/snps/CEU.exon.2010_03.genotypes.vcf.gz",
            "time": datetime.datetime.now().isoformat()
        }
    ]
    return json.dumps(list, indent=4)


if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", "-f", type=str, required=True)
    parser.add_argument("--server", "-s", type=str, required=True)
    parser.add_argument("--patientID", "-p", type=str, required=True)
    args = parser.parse_args()

    #FHIR Patient resource ID to link the List of variant observations to
    patient = 'Patient/' + args.patientID

    #Parse the VCF file to extract the rsID and Genotype for each variant
    var_list = parse_VCF(args.file)

    #Make a FHIR Observation resource for each variant with a Genotype (not for no-calls)
    obs_list = []
    for var in var_list:
        rsID = var[0]
        geno = var[1]
        obs_list.append(create_obs(patient, rsID, geno, query_pharmGKB_db(rsID)))

    #POST the Observation resources to the appropriate FHIR server
    obs_ids = []
    for obs in obs_list:
        r = requests.post(args.server + 'Observation', data=obs)
        if r.status_code != 201:
            print(r.status_code)
            print(obs)
        obs_ids.append(r.headers['Content-Location'].split('Observation/')[1].split('/')[0])

    #Create a FHIR List resource from the list of created Observation resources
    list = create_list(obs_ids, patient, args.file)

    #POST the List resource to the appropriate FHIR server
    r = requests.post(args.server + 'List', data=list)
    print('FHIR List Resource logical identifier: ' + r.headers['Content-Location'].split('List/')[1].split('/')[0])