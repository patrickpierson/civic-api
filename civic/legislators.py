import boto3
import csv
from io import StringIO
import os
import requests
import googlemaps
import logging
from datetime import datetime
from pprint import pprint

bucket = 'civic.patrickpierson.us'
upload_prefix = '/upload/'
s3 = boto3.resource('s3')

app = Chalice(app_name='civic-api')
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class Legislators(object):

    def __init__(self):
        self.google_api_key = os.environ.get('google_api_key')
        self.civic_api_key = os.environ.get('civic_api_key')

    def geocode(self, address):
        results = []
        logger.info('Geocode hit: %s' % address)
        gmaps = googlemaps.Client(key=os.environ.get('google_api_key'))
        geocode_result = gmaps.geocode(address=address.replace('%20', ' '))
        for result in geocode_result:
            if result.get('geometry').get('location_type') == 'ROOFTOP':
                lat = result.get('geometry').get('location').get('lat')
                long = result.get('geometry').get('location').get('lng')
                results.append(
                    {'geocode': {
                        'lat': lat,
                        'long': long
                                },
                     'accuracy': 'EXCELLENT'})
            elif result.get('geometry').get('location_type') == 'RANGE_INTERPOLATED':
                lat = result.get('geometry').get('location').get('lat')
                long = result.get('geometry').get('location').get('lng')
                results.append(
                    {'geocode': {
                        'lat': lat,
                        'long': long
                                },
                     'accuracy': 'HIGH'})
            elif result.get('geometry').get('location_type') == 'GEOMETRIC_CENTER':
                lat = result.get('geometry').get('location').get('lat')
                long = result.get('geometry').get('location').get('lng')
                results.append(
                    {'geocode': {
                        'lat': lat,
                        'long': long
                                },
                     'accuracy': 'MEDIUM'})
            elif result.get('geometry').get('location_type') == 'APPROXIMATE':
                lat = result.get('geometry').get('location').get('lat')
                long = result.get('geometry').get('location').get('lng')
                results.append(
                    {'geocode': {
                        'lat': lat,
                        'long': long
                                },
                     'accuracy': 'LOW'})
            else:
                lat = result.get('geometry').get('location').get('lat')
                long = result.get('geometry').get('location').get('lng')
                results.append(
                    {'geocode': {
                        'lat': lat,
                        'long': long
                                },
                     'accuracy': 'UNKNOWN'})

        matching = [s for s in results if "EXCELLENT" in s.get('accuracy')]
        if matching:
            return matching[0]
        else:
            matching = [s for s in results if "HIGH" in s.get('accuracy')]
            if matching:
                return matching[0]
            else:
                matching = [s for s in results if "MEDIUM" in s.get('accuracy')]
                if matching:
                    return matching[0]
                else:
                    matching = [s for s in results if "LOW" in s.get('accuracy')]
                    if matching:
                        return matching[0]
                    else:
                        matching = [s for s in results if "UNKNOWN" in s.get('accuracy')]
                        if matching:
                            return matching[0]
                        else:
                            return results[0]

    def google_civic_api(self, address):
        logger.info('Google Civic Api hit: %s' % address)
        individuals = []
        google_civic_url = 'https://www.googleapis.com/civicinfo/v2/representatives?address={}&includeOffices=true' \
                           '&levels=administrativeArea1&levels=country&levels=administrativeArea2&levels=internati' \
                           'onal&levels=locality&levels=regional&levels=special&levels=subLocality1&levels=subLoca' \
                           'lity2&roles=deputyHeadOfGovernment&roles=executiveCouncil&roles=governmentOfficer&role' \
                           's=headOfGovernment&roles=headOfState&roles=highestCourtJudge&roles=judge&roles=legisla' \
                           'torLowerBody&roles=legislatorUpperBody&roles=schoolBoard&roles=specialPurposeOfficer&k' \
                           'ey={}'.format(address, self.google_api_key)
        res = requests.get(google_civic_url).json()
        for official in res.get('officials'):
            if official.get('emails'):
                data = {
                    'full_name': official.get('name'),
                    'phone': official.get('phones')[0],
                    'email': official.get('emails')[0],
                    'data_source': 'google_civic_api'
                }
            else:
                data = {
                    'full_name': official.get('name'),
                    'phone': official.get('phones')[0],
                    'email': 'None Found',
                    'data_source': 'google_civic_api'
                }
            individuals.append(data)
        return individuals

    def lookup_openstates(self, lat, long):
        logger.info('Lookup OpenStates hit: %s, %s' % (lat, long))
        individuals = []
        civic_url = 'https://openstates.org/api/v1/legislators/geo/?lat={}&long={}&apikey={}'.format(
            lat,
            long,
            self.civic_api_key)
        logger.info('Getting: %s' % civic_url)
        res = requests.get(civic_url)
        if res.status_code == 500:
            return [{
                'status': 'openstates is down'
            }]
        else:
            for individual in res.json():
                data = {
                    'full_name': individual.get('full_name'),
                    'phone': individual.get('offices')[0].get('phone'),
                    'email': individual.get('email'),
                    'data_source': 'openstates'
                }
                individuals.append(data)
            return individuals

    def lookup_balt_data(self, lat, long):
        individuals = []
        url = 'https://epsg.io/trans?data={0},{1}&s_srs=4326&t_srs=102685'.format(
            long,
            lat)
        json_coordinates = requests.get(url)
        md_coordinates = []
        for json_coordinate in json_coordinates.json():
            md_coordinates.append(json_coordinate['x'])
            md_coordinates.append(json_coordinate['y'])
        balt_url = 'https://gis.baltimorecity.gov/egis/rest/services/opengisdata/CouncilDistrict/MapServer/0/query?' \
                   'where=1%3D1&text=&objectIds=&time=&geometry={}%2C+{}%2C&geometryType=esriGeometryPoint&inSR=' \
                   '&spatialRel=esriSpatialRelIntersects&relationParam=&outFields=*&returnGeometry=true&returnTrueC' \
                   'urves=false&maxAllowableOffset=&geometryPrecision=&outSR=&having=&returnIdsOnly=false&returnCou' \
                   'ntOnly=false&orderByFields=&groupByFieldsForStatistics=&outStatistics=&returnZ=false&returnM=fa' \
                   'lse&gdbVersion=&historicMoment=&returnDistinctValues=false&resultOffset=&resultRecordCount=&que' \
                   'ryByDistance=&returnExtentOnly=false&datumTransformation=&parameterValues=&rangeValues=&quantiz' \
                   'ationParameters=&f=json'.format(md_coordinates[0], md_coordinates[1])
        #logger.info('Balt Data hit: %s' % balt_url )
        res = requests.get(balt_url).json()
        if len(res.get('features')) >= 1:
            for individual in res.get('features'):
                data = {
                    'full_name': individual.get('attributes').get('CNTCT_NME'),
                    'phone': individual.get('attributes').get('CNTCT_PHN').replace(' \r\n', ''),
                    'email': individual.get('attributes').get('CNTCT_EML'),
                    'data_source': 'baltimore_city_gis'
                }
                individuals.append(data)
            return individuals
        else:
            return []


def address_lookup(address):
    address = address.replace('%20', ' ')
    logger.info('Address hit: %s' % address)
    representatives = []
    job = Legislators()
    geocode = job.geocode(address)
    lat = geocode.get('geocode').get('lat')
    long = geocode.get('geocode').get('long')
    accuracy = geocode.get('accuracy')
    logger.info('Accuracy: %s' % accuracy)
    representatives = representatives + job.lookup_balt_data(lat, long) + job.google_civic_api(address) + job.lookup_openstates(lat, long)
    return {
        'representatives': representatives,
        'metadata': {
            'query_address': address,
            'geocord': {
                'lat': lat,
                'long': long,
                'latlongstring': '%s,%s' % (lat, long)
            },
            'accuracy': accuracy
        }
    }


def upload_to_s3():
    # object = s3.Object(bucket, upload_prefix + )
    # data = []
    # rows = app.current_request.raw_body.decode("utf-8").split('\n')
    # for row in rows:
    #     data.append(row.split(','))

    return {
        'data': datetime.now()
    }


# if __name__ == "__main__":
#     with open('data/test.csv', 'r') as csvfile:
#         reader = csv.reader(csvfile, delimiter=',', quotechar='|')
#
#         for row in reader:
#             print(row)

    # test = Legislators()
    # geo = test.geocode('***REMOVED***')
    # pprint(test.lookup_openstates(geo.get('geocode').get('lat'), geo.get('geocode').get('long')))
