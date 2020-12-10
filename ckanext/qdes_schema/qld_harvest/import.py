import csv
import os
import json
import re

from ckanext.qdes_schema.logic.helpers import harvest_helpers as helpers
from datetime import datetime
from ckanapi import RemoteCKAN
from pprint import pformat

owner_org = os.environ['OWNER_ORG']
apiKey = os.environ['HARVEST_API_KEY']
dataservice_name = 'queensland-government-open-data-portal'

DEBUG = False
SOURCE_FILENAME = 'DES_Datasets_Open_data_V1.csv'


def convert_size_to_bytes(size_str):
    """
    Convert human file-sizes to bytes.
    """
    multipliers = {
        'kib': 1024,
        'mib': 1024 ** 2,
        'gib': 1024 ** 3,
    }

    # Some Nones observed during migration
    if not size_str:
        return 0

    # Some Int values observed for size
    if isinstance(size_str, int):
        return size_str

    try:
        for suffix in multipliers:
            size_str = size_str.replace(',', '')
            size_str = size_str.lower().strip().strip('s')
            if size_str.lower().endswith(suffix):
                return int(float(size_str[0:-len(suffix)]) * multipliers[suffix])
        else:
            if size_str.endswith('b'):
                size_str = size_str[0:-1]
            elif size_str.endswith('byte'):
                size_str = size_str[0:-4]
        return int(size_str)
    except Exception as e:
        print('Exception raised in convert_size_to_bytes')
        print(f'>>> Input: {size_str}')
        print('Exception: {}'.format(str(e)))
        raise e


def get_dataset_schema_fields():
    """
    Get all fields available on QDES dataset.
    """
    with open('../qdes_ckan_dataset.json') as f:
        return json.load(f)


def dataset_mapping(dataset, source_dict):
    """
    Map QLD dataset to QDES dataset.
    """
    mapped_dataset = {}
    schema = get_dataset_schema_fields()

    try:
        # Added default fields specific to the QDES dataset.
        mapped_dataset['type'] = 'dataset'
        mapped_dataset['owner_org'] = owner_org
        today = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
        mapped_dataset['dataset_creation_date'] = today
        mapped_dataset['dataset_release_date'] = today
        mapped_dataset['dataset_last_modified_date'] = today

        # Manual field mapping.
        manual_fields = [
            'owner_org',
            'license_id',
            'url',
            'update_schedule',
            'classification_and_access_restrictions',
            'classification',
            'topic',
            'contact_point',
            'contact_publisher',
            'publication_status',
            'format',
            'tag_string',
        ]

        # Keeping track of license_id and license_url values
        license_id = dataset.get('license_id', None)
        if license_id not in unique_license_ids:
            unique_license_ids.append(license_id)
        license_url = dataset.get('license_url', None)
        if license_url not in unique_license_urls:
            unique_license_urls.append(license_url)

        # Map license, license_id on QLD only a fraction of the vocab data that controlled QDES field.
        # @todo: fix this.
        mapped_dataset['license_id'] = 'http://registry.it.csiro.au/licence/cc-by-4.0'

        # Map URL, if the URL is not available on source, give it default value.
        mapped_dataset['url'] = source_dict.get('URL', '') or 'http://data.qld.gov.au'

        mapped_dataset['update_schedule'] = helpers.get_mapped_update_frequency(dataset.get('update_frequency'))

        # Map keyword (tag_string).
        mapped_dataset['tag_string'] = []

        # Classification vocabulary service lookup
        classification = helpers.get_vocabulary_service_term(
            destination,
            source_dict.get('General classification of dataset type', 'Dataset').lower(),
            'classification')

        if classification:
            mapped_dataset['classification'] = json.dumps([classification['value']])

        # Classification and access restrictions vocabulary service lookup
        class_and_access = helpers.get_vocabulary_service_term(
            destination,
            source_dict.get('classification_and_access_restrictions', 'Dataset').lower(),
            'classification_and_access_restrictions')

        if class_and_access:
            mapped_dataset['classification_and_access_restrictions'] = json.dumps([class_and_access['value']])

        # Topic/theme vocabulary service lookup
        source_topic = source_dict.get('Topic or theme', None) or None

        if source_topic:
            topic = helpers.get_vocabulary_service_term(
                destination,
                source_topic.lower().strip(),
                'topic')

            if topic:
                mapped_dataset['topic'] = json.dumps([topic['value']])
            else:
                print('>>> No matching topic found for:')
                print('>>> source: {}'.format(pformat(source_dict)))
        else:
            print('>>> No source topic set for:')
            print('>>> source: {}'.format(pformat(source_dict)))

        # Point of Contact "secure" vocabulary look-up
        point_of_contact = helpers.get_point_of_contact_id(
            destination,
            source_dict.get('Point of contact'),
            'point-of-contact')

        if point_of_contact:
            mapped_dataset['contact_point'] = point_of_contact['value']

        # Publication status vocabulary service lookup
        publication_status = helpers.get_vocabulary_service_term(
            destination,
            source_dict.get('Publication status', '').lower(),
            'publication_status')

        # @TODO: Set this to COMPLETED
        if publication_status:
            mapped_dataset['publication_status'] = 'http://registry.it.csiro.au/def/isotc211/MD_ProgressCode/completed'

        # @TODO: This CV is not currently implemented
        mapped_dataset['contact_publisher'] = 'http://linked.data.gov.au/def/organisation-type/family-partnership'

        # @TODO: Should this be set in here??? i.e. Dataset schema does not have a `format` field
        #mapped_dataset['format'] = 'https://www.iana.org/assignments/media-types/application/1d-interleaved-parityfec'

        # Build the rest of the values.
        for field in schema.get('dataset_fields'):
            field_name = field.get('field_name')

            # Do not process if the field already added via manual mapping or empty.
            if field_name not in manual_fields and dataset.get(field_name, None):
                mapped_dataset[field_name] = dataset.get(field_name, '')

        return mapped_dataset
    except Exception as e:
        print('>>> Exception raised in dataset_mapping')
        print(str(e))
        raise


def resource_mapping(res):
    """
    Clean up resource.
    """
    try:
        # Keeping track of unique formats from Data.Qld to map to DES controlled vocab
        source_format = res.get('format', None)
        if source_format not in unique_formats:
            unique_formats.append(source_format)

        mapped_resource = {
            'data_services': json.dumps([os.environ['LAGOON_ROUTE'] + '/dataservice/' + dataservice_name]),
            'size': convert_size_to_bytes(res.get('size', 0)),
            # @TODO: fix this. issue example: on source there is "JSON" as value, but the format has many JSON types.
            'format': 'https://www.iana.org/assignments/media-types/application/alto-directory+json'
        }

        # Manual field mapping.
        manual_fields = [
            'size',
            'format',
        ]

        # Get all fields available on QDES dataset.
        schema = get_dataset_schema_fields()

        # Build the rest of the value.
        for field in schema.get('resource_fields'):
            field_name = field.get('field_name')

            # Do not process if field value is empty.
            if (res.get(field_name, None)) and (not field_name in manual_fields):
                mapped_resource[field_name] = res.get(field_name, '')

        # Encode url if exist.
        if mapped_resource['url']:
            mapped_resource['url'] = helpers.fix_url(mapped_resource['url'])

        return mapped_resource
    except Exception as e:
        print('>>> Exception raised in resource_mapping')
        print(f'>>> Input: {res}')
        print(str(e))
        raise e


def resource_to_dataset_mapping(res, parent_dataset, parent_dataset_id, source_url=None):
    """
    Map resource to dataset for series.
    """
    mapped_dataset = {}
    schema = get_dataset_schema_fields()

    try:
        # Loop the parent, get the data from resource first and if none, use the parent data.
        for field in schema.get('dataset_fields'):
            field_name = field.get('field_name')
            value = res.get(field_name)

            if field_name == 'name':
                value = re.sub('[^0-9a-zA-Z]+', '-', value.lower())
                # No value longer than 100 chars, we will add the last 8 chars with current uuid,
                # otherwise it will have possibility conflict with other series.
                value = (value[:92] + res.get('id')[:8]) if len(value) > 100 else value

            if not value:
                value = parent_dataset.get(field_name)

            if value:
                mapped_dataset[field_name] = value

        # Set title.
        mapped_dataset['title'] = res.get('name')

        # Set the new dataset's notes (description) field to the resource description
        resource_description = res.get('description', None) or None
        mapped_dataset['notes'] = resource_description if resource_description else parent_dataset.get('notes', '')

        # Set isPartOf relationship.
        mapped_dataset['series_or_collection'] = json.dumps([{"id": parent_dataset_id.get('id'), "text": parent_dataset_id.get('title')}])

        # Create a resource for the dataset based on the resource we are working with
        # AND connect it to the data service
        mapped_dataset['resources'] = [resource_mapping(res)]

        # Encode url if exist.
        if mapped_dataset['url']:
            mapped_dataset['url'] = helpers.fix_url(mapped_dataset['url'])

        return mapped_dataset

    except Exception as e:
        print('>>> Exception raised in resource_to_dataset_mapping')
        print(str(e))
        raise


def append_error(dataset_name, errors, source_url):
    error_log.append({
        'package_id': dataset_name,
        'errors': errors,
        'source_url': source_url,
    })


# Set the import source and destination.
source = RemoteCKAN('https://www.data.qld.gov.au')
destination = RemoteCKAN(os.environ['LAGOON_ROUTE'], apikey=apiKey)

error_log = []
success_log = []
unique_formats = []
unique_license_ids = []
unique_license_urls = []

# Open CSV file.
with open(SOURCE_FILENAME, "rt") as file:
    data = file.read().split('\n')

csv_reader = csv.DictReader(data)

count = 0
limit = 5

for row in csv_reader:
    count += 1

    if DEBUG and count > limit:
        break

    # Get dataset name.
    source_url = row.get('URL', None)

    if not source_url:
        append_error('Row {}'.format(count), 'URL not set (URL is case sensitive)', None)
        continue

    dataset_name = source_url.split('/')[-1]

    # Fetch package from Data.Qld.
    package_dict = []
    try:
        package_dict = source.action.package_show(id=dataset_name)
    except Exception as e:
        print(f'Error fetching package {dataset_name}')
        append_error(dataset_name, str(e), source_url)
        continue

    # Map dataset.
    new_package_dict = dataset_mapping(package_dict, row)

    if DEBUG:
        print('Got package_dict: {}'.format(pformat(package_dict)))
        print('Mapped to package_dict: {}'.format(pformat(new_package_dict)))

    if 'series' in package_dict['title'].lower():
        # This will be resource-less package.
        new_package_dict['resources'] = []
        error = False
        new_package_dict_id = {}

        # Create the parent of series dataset.
        try:
            new_package_dict_id = destination.action.package_create(**new_package_dict)
        except Exception as e:
            append_error(dataset_name, str(e), source_url)
            continue

        # Create individual package for each resource that belong to above series dataset.
        if ('resources' in package_dict) and not error:
            for resource in package_dict.get('resources'):
                new_series_package_dict = resource_to_dataset_mapping(resource, new_package_dict, new_package_dict_id)

                try:
                    new_series_package_dict_id = destination.action.package_create(**new_series_package_dict)
                except Exception as e:
                    append_error(new_series_package_dict.get('name'), str(e), source_url)
    else:
        # Map Resources.
        new_package_dict['resources'] = []

        try:
            if 'resources' in package_dict:
                for resource in package_dict.get('resources'):
                    new_package_dict['resources'].append(resource_mapping(resource))

            new_package_dict_id = destination.action.package_create(**new_package_dict)
            success_log.append({
                'package_id': dataset_name,
                'message': 'Successfully migrated.'
            })
        except Exception as e:
            append_error(dataset_name, str(e), source_url)

if success_log:
    print(pformat(success_log))

if error_log:
    print(pformat(error_log))

print('>>> Unique formats from Data.Qld:')
print(pformat(unique_formats))

print('>>> Unique license_id values from Data.Qld:')
print(pformat(unique_license_ids))

print('>>> Unique license_url values from Data.Qld:')
print(pformat(unique_license_urls))

print(f'\nRows in CSV: {count}')
