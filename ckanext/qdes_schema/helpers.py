import datetime
import logging

from ckan.common import config
from ckan.plugins.toolkit import h
from ckan.plugins.toolkit import get_action

log = logging.getLogger(__name__)


def is_legacy_ckan():
    return False if h.ckan_version() > '2.9' else True


def set_first_option(options, first_option):
    """Find the option (case insensitive) from the options text property and move it to the start of the list at index 0"""
    option = next((option for option in options if option.get('text').lower() == first_option.lower()), None)
    if option:
        old_index = options.index(option)
        options.insert(0, options.pop(old_index))
    return options


def get_current_datetime():
    """
    Returns current datetime.
    """
    return datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')


def qdes_dataservice_choices(field):
    """
    Return choices for dataservice dropdown.
    """
    choices = []

    try:
        for data in get_action('get_dataservice')({}):
            choices.append({
                'value': config.get('ckan.site_url', None) + '/dataservice/' + data.name,
                'label': data.title
            })
    except Exception as e:
        log.error(str(e))

    return choices


def qdes_process_json_facets(facet_items):
    log.debug(facet_items)
    processed_facet_items = []
    import json
    for item in facet_items:
        try:
            display_name = json.loads(item['display_name'])
            item['display_name'] = display_name[0].split('/')[-1]
            #processed_facet_items.append({
            # })
        except Exception as e:
            log.error(str(e))
    return facet_items
