import glob
import json
import os

from ckanapi import RemoteCKAN
from sir_object import SirObject
from pprint import pformat, pprint
from datetime import datetime as dt


def get_remote_ckan():
    remoteCKAN = RemoteCKAN(
        os.environ['LAGOON_ROUTE'],
        os.environ['HARVEST_API_KEY']
    )
    return remoteCKAN


def get_ckan_packages():
    ckan_packages = []

    files = glob.glob('xml_files/*.xml')
    log_file = 'logs/{0}.txt'.format(dt.now().strftime("%Y%m%d-%H%M%S"))
    count = 0
    with get_remote_ckan() as remoteCKAN:
        for file in files:
            count += 1
            if count > 1000:
                break
            obj = SirObject(file, remoteCKAN, log_file, True)
            ckan_packages.append(obj.get_ckan_package_dict())

    return ckan_packages


def create_package(remoteCKAN, package):
    # print(pformat(package))

    try:
        result = remoteCKAN.action.package_create(**package)
        package['id'] = result.get('id')
    except Exception as e:
        append_error(package.get('title'),  str(e))


def append_error(dataset_title, error):
    # log =  {'error': str(error)}
    # error_log.append(log) if log not in error_log else error_log
    log = '{0}: {1}'.format(dataset_title, error)
    error_log.append(log) if log not in error_log else error_log


def main():
    if not os.path.exists('logs'):
        os.makedirs('logs')
    packages = get_ckan_packages()

    with get_remote_ckan() as remoteCKAN:
        distinct_package_fields = {}
        package_fields = [
            'parent_identifier',
            'classification',
            'topic',
            'contact_point',
            'contact_publisher',
            'contact_other_party',
            'publication_status',
            'classification_and_access_restrictions',
            'license_id',
            'owner_org',
            'dataset_language',
            'temporal_start',
            'temporal_end',
            'tag_string',
            'spatial_lower_left',
            'spatial_upper_right',
            'spatial_content_resolution',
            'spatial_representation',
            'spatial_datum_crs',
            'dataset_release_date',
            'update_schedule',
            'quality_description',
            'url',
            'lineage_description',
            'rights_statement'
        ]

        distinct_resource_fields = {}
        resource_fields = [
            'format',
            'size',
            'service_api_endpoint',
            'rights_statement',
            'license'
        ]
        for check_field in package_fields:
            distinct_package_fields[check_field] = []

        for check_field in resource_fields:
            distinct_resource_fields[check_field] = []

        parent_packages = [package for package in packages if package.get('parent_identifier', None) == None] or []
        child_packages = [package for package in packages if package.get('parent_identifier', None) != None] or []
        # Create parent packages first to get package id
        for package in parent_packages:
            for field in package:
                if field in distinct_package_fields:
                    distinct_package_fields[field].append(package.get(field)) if package.get(field) not in distinct_package_fields[field] else distinct_package_fields[field]

            for resource in package.get('resources', []):
                for field in resource:
                    if field in distinct_resource_fields:
                        distinct_resource_fields[field].append(resource.get(field)) if resource.get(field) not in distinct_resource_fields[field] else distinct_resource_fields[field]

            # pprint('parent_package')
            # pprint(package)
            create_package(remoteCKAN, package)

        # Create child packages with parent package id
        for package in child_packages:
            for field in package:
                if field in distinct_package_fields:
                    distinct_package_fields[field].append(package.get(field)) if package.get(field) not in distinct_package_fields[field] else distinct_package_fields[field]

            for resource in package.get('resources', []):
                for field in resource:
                    if field in distinct_resource_fields:
                        distinct_resource_fields[field].append(resource.get(field)) if resource.get(field) not in distinct_resource_fields[field] else distinct_resource_fields[field]

            # pprint('package')
            # pprint(package)
            parent_package = next((parent_package for parent_package in parent_packages if package.get('parent_identifier', None)
                                   in [parent_package.get('identifiers') if parent_package.get('identifiers') else []]), None)
            if parent_package:
                print('parent package found {0} for {1}'.format(parent_package.get('title'), package.get('title')))
                package['series_or_collection'] = json.dumps([{"id": parent_package.get('id'), "text": parent_package.get('title')}])

            create_package(remoteCKAN, package)

        # pprint(distinct_package_fields)
        # pprint(distinct_resource_fields)

    if error_log:
        print(json.dumps(error_log, indent=2))


error_log = []

if __name__ == '__main__':
    main()
