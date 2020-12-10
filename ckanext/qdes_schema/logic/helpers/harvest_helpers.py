import urllib as urllib


def get_mapped_update_frequency(update_frequency):
    # Map Update frequency, we can't use get_vocab_value because some of the values are custom (can't be matched 1:1).
    # The below frequency value to filter based on this value, use below
    # https://www.data.qld.gov.au/organization/a3cdcdcb-201c-4360-9fa6-98e361c89279?update_frequency=not-updated.
    # @todo: fix this.
    frequency_map = {
        'near-real-time': 'http://registry.it.csiro.au/def/isotc211/MD_MaintenanceFrequencyCode/continual',
        'hourly': '',
        'daily': 'http://registry.it.csiro.au/def/isotc211/MD_MaintenanceFrequencyCode/daily',
        'weekly': 'http://registry.it.csiro.au/def/isotc211/MD_MaintenanceFrequencyCode/weekly',
        'fortnightly': 'http://registry.it.csiro.au/def/isotc211/MD_MaintenanceFrequencyCode/fortnightly',
        'monthly': 'http://registry.it.csiro.au/def/isotc211/MD_MaintenanceFrequencyCode/monthly',
        'quarterly': 'http://registry.it.csiro.au/def/isotc211/MD_MaintenanceFrequencyCode/quarterly',
        'half-yearly': 'http://registry.it.csiro.au/def/isotc211/MD_MaintenanceFrequencyCode/biannually',
        'annually': 'http://registry.it.csiro.au/def/isotc211/MD_MaintenanceFrequencyCode/annually',
        'non-regular': 'http://registry.it.csiro.au/def/isotc211/MD_MaintenanceFrequencyCode/irregular',
        'not-updated': 'http://registry.it.csiro.au/def/isotc211/MD_MaintenanceFrequencyCode/notPlanned'
    }
    return frequency_map.get(update_frequency, '')


def get_secure_vocabulary_record(destination, query, vocabulary_name, debug=False):
    try:
        data_dict = {
            'query': query,
            'vocabulary_name': vocabulary_name
        }
        result = destination.action.get_secure_vocabulary_search(**data_dict)

        # If action fails it will return something like this {'success': False, 'msg': 'Not authorised'}, instead of a list of results.
        if result and 'success' in result and result.get('success') == False:
            print(result.get('msg'))
        # Only return the first result, as presumably the data in the CSV file will be a unique name
        if result and isinstance(result, list) and len(result) >= 1:
            return result[0].get('value', None)

        if debug:
            print('>>>')
            print('No secure vocabulary record found: {0} for query: {1}'.format(vocabulary_name, query))
            print('>>>')
    except Exception as e:
        print(str(e))


def get_vocabulary_service_term(destination, query, vocabulary_service_name, debug=False):
    try:
        data_dict = {
            'q': query,
            'term_name': vocabulary_service_name,
            'limit': 1,
        }
        result = destination.action.vocabulary_service_term_search(**data_dict)

        # Only return the first result, as presumably the data in the CSV file will be a unique name
        if result and len(result) >= 1:
            return result[0].get('value', None)

        if debug:
            print('>>>')
            print('No term found in vocabulary_service: {0} for query: {1}'.format(vocabulary_service_name, query))
            print('>>>')
    except Exception as e:
        print(str(e))


def fix_url(url):
    parsed_url = urllib.parse.urlparse(url)

    if parsed_url.query:
        parsed_query_params = urllib.parse.parse_qs(parsed_url.query)
        query = urllib.parse.urlencode(parsed_query_params, doseq=True)

        return urllib.parse.urlunparse((
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            parsed_url.params,
            query,
            parsed_url.fragment,
        ))

    return None
