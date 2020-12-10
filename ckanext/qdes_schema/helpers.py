import re
import datetime
import logging

from ckan.model import Session
from ckan.model.package_relationship import PackageRelationship
from ckan.lib import helpers as core_helper
from ckan.plugins.toolkit import config, h, get_action, get_converter, get_validator, Invalid, request
from ckanext.qdes_schema.logic.helpers import relationship_helpers
from ckanext.invalid_uris.model import InvalidUri
from pprint import pformat

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


def qdes_relationship_types_choices(field):
    """
    Return choices for dataset relationship types.
    """
    choices = []

    try:
        # Remove the duplicate `unspecified relationship` type
        # as it has the same value for forward and reverse
        unique_relationship_types = []

        types = PackageRelationship.get_forward_types()

        for relationship_type in h.get_relationship_types():
            if relationship_type not in types:
                continue

            if relationship_type not in unique_relationship_types:
                unique_relationship_types.append(relationship_type)

        for data in unique_relationship_types:
            choices.append({
                'value': data,
                'label': data
            })
    except Exception as e:
        log.error(str(e))

    return choices


def update_related_resources(context, pkg_dict, reconcile_relationships=False):
    if reconcile_relationships:
        # Combine existing related_resources and new related_resources together
        existing_related_resources = get_converter('json_or_string')(request.form.get('existing_related_resources', '')) or []
        new_related_resources = get_converter('json_or_string')(pkg_dict.get('related_resources', '')) or []
        combined_related_resources = existing_related_resources + new_related_resources
        pkg_dict['related_resources'] = h.dump_json(combined_related_resources)

        remove_duplicate_related_resources(pkg_dict)
        reconcile_package_relationships(context, pkg_dict['id'], pkg_dict.get('related_resources', None))

    if pkg_dict.get('type') == 'dataset':
        create_related_relationships(context, pkg_dict, 'series_or_collection', 'isPartOf')
        create_related_relationships(context, pkg_dict, 'related_datasets', 'unspecified relationship')
    elif pkg_dict.get('type') == 'dataservice':
        create_related_relationships(context, pkg_dict, 'related_services', 'unspecified relationship')

    create_related_resource_relationships(context, pkg_dict)
    get_action('update_related_resources')(context, {"id": pkg_dict.get('id')})


# @TODO: This should be renamed to something more appropriate to what it does, i.e. "stage|build|add_related_resources"
# and could probably just be absorbed into the `set_pkg_related_resources` function below
def create_related_relationships(context, pkg_dict, metadata_field, relationship_type):
    resources = get_converter('json_or_string')(pkg_dict.get(metadata_field, []))
    set_pkg_related_resources(pkg_dict, resources, relationship_type)


def set_pkg_related_resources(pkg_dict, resources, relationship_type):
    if resources and isinstance(resources, list):
        pkg_related_resources = get_converter('json_or_string')(pkg_dict.get('related_resources', []))
        if not pkg_related_resources:
            pkg_related_resources = []

        for resource in resources:
            # Only add `resource` to `related_resources` if it does not already exist
            if not any(x for x in pkg_related_resources
                       if x.get('resource', {}).get('id', '') == resource.get('id', '')
                       and x.get('relationship', '') == relationship_type):
                pkg_related_resources.append({
                    'resource': resource,
                    'relationship': relationship_type
                })

        pkg_dict['related_resources'] = h.dump_json(pkg_related_resources)


def create_related_resource_relationships(context, pkg_dict):
    remove_duplicate_related_resources(pkg_dict)
    pkg_related_resources = get_converter('json_or_string')(pkg_dict.get('related_resources', []))
    if pkg_related_resources and isinstance(pkg_related_resources, list):
        create_package_relationship_records(context, pkg_dict.get('id'), pkg_related_resources)


def create_package_relationship_records(context, pkg_id, pkg_related_resources):
    try:
        for resource in pkg_related_resources:
            relationship_type = resource.get('relationship')
            object_package_id, url = get_related_object_or_url(context, resource.get('resource'))

            if object_package_id or url:
                # Pre-check to see if a `package_relationship` already exists for this `subject_package_id`,
                # `object_package_id` and `type`, because it's possible that a sysadmin user added a
                # relationship to a package that an admin or editor user does not have `package_update` permission
                if object_package_id and \
                        relationship_helpers.get_existing_relationship(pkg_id, object_package_id, relationship_type):
                    continue

                # Upsert the `package_relationship`
                get_action('package_relationship_create')(context, {
                    'subject': pkg_id,
                    'object': object_package_id,
                    'type': relationship_type,
                    'comment': url,
                })
    except Exception as e:
        log.error('create_package_relationship_records error: {0}'.format(e), exc_info=True)
        raise


def get_related_object_or_url(context, resource):
    object_package_id = None
    url = None
    resource_id = resource.get('id', '')
    try:
        get_validator('package_id_exists')(resource_id, context)
        object_package_id = resource_id
    except Invalid:
        # Dataset does not exist so must be an external dataset URL
        # Validation should have already happened in validator 'qdes_validate_related_dataset'
        # so the `resource` should be a URL to external dataset
        url = resource_id

    return object_package_id, url


def reconcile_package_relationships(context, pkg_id, related_resources):
    """
    Only delete package relationships for the dataset when the relationship
    no longer exists in the `related_resources` field

    Called on IPackageController `after_update`

    :param context:
    :param pkg_id: package/dataset ID
    :return:
    """
    model = context.get('model')
    existing_relationships = get_action('subject_package_relationship_objects')(context, {'id': pkg_id})

    # `related_resources` might be an empty string
    related_resources = related_resources or None

    # If `related_resources` is empty - it indicates that all related resources have been removed from the dataset
    if not related_resources:
        # Delete ALL existing relationships for this dataset
        log.debug('Deleting ALL package_relationship records for dataset id {0}'.format(pkg_id))
        get_action('package_relationship_delete_all')(context, {'id': pkg_id})
    else:
        # Convert the `related_resources` JSON string into a more usable structure
        related_resources = get_converter('json_or_string')(related_resources)
        # Check each existing relationship to see if it still exists in the dataset's related_resources
        # if not, delete it.
        for relationship in existing_relationships:
            matching_related_resource = None

            # If it's an external URI we can process straight away
            if not relationship.object_package_id:
                matching_related_resource = [resource for resource in related_resources
                                             if resource.get('relationship', None) == relationship.type
                                             and resource.get('resource', {}).get('id', None) == relationship.comment]
            else:
                try:
                    matching_related_resource = [resource for resource in related_resources
                                                 if resource.get('relationship', None) == relationship.type
                                                 and resource.get('resource', {}).get('id', None) == relationship.object_package_id]
                except Exception as e:
                    log.error(str(e))

            if not matching_related_resource:
                # Delete the existing relationship from `package_relationships` as it no longer exists in the dataset
                log.debug('Purging relationship: Subject {0} - Object {1} - Type {2} - Comment {3}'
                          .format(relationship.subject_package_id, relationship.object_package_id, relationship.type, relationship.comment))
                relationship.purge()
                model.meta.Session.commit()


def remove_duplicate_related_resources(pkg_dict):
    related_resources = get_converter('json_or_string')(pkg_dict.get('related_resources', []))
    if related_resources and isinstance(related_resources, list):
        distinct_list = []
        for related_resource in related_resources:
            dataset_id = related_resource.get('resource', {}).get('id', '')
            relationship_type = related_resource.get('relationship', '')

            if not any(distinct_dataset for distinct_dataset in distinct_list
                       if distinct_dataset.get('resource', {}).get('id', '') == dataset_id
                       and distinct_dataset.get('relationship', '') == relationship_type):
                distinct_list.append(related_resource)

        pkg_dict['related_resources'] = h.dump_json(distinct_list)


def get_related_versions(id):
    """
    Get related versions of dataset, index 0 is the current version.
    """
    successors = get_action('get_all_successor_versions')({}, {'id': id})
    predecessors = get_action('get_all_predecessor_versions')({}, {'id': id})

    versions = []
    try:
        # Load provided version.
        package_dict = get_action('package_show')({}, {'id': id})

        # Build versions list.
        versions = successors + [package_dict] + predecessors
    except Exception as e:
        log.error(str(e))

    return list(version for version in versions if version.get('state') != 'deleted')


def get_all_relationships(id):
    return get_action('get_all_relationships')({}, id)


def convert_relationships_to_related_resources(relationships):
    related_resources = []
    for relationship in relationships:
        id = relationship.get('object', None) or relationship.get('comment', None)
        related_resources.append({"resource": {"id": id}, "relationship": relationship.get('type', None)})

    return h.dump_json(related_resources) if related_resources and len(related_resources) > 0 else ''


def get_qld_bounding_box_config():
    return config.get('ckanext.qdes_schema.qld_bounding_box', None)


def get_package_dict(id):
    return get_action('package_show')({}, {'id': id})


def get_invalid_uris(entity_id, pkg_dict):
    u"""
    Get invalid uris for the current package.
    """
    uris = Session.query(InvalidUri).filter(InvalidUri.entity_id == entity_id).all()

    return [uri.as_dict() for uri in uris]


def wrap_url_within_text_as_link(value):
    urlfinder = re.compile("(https?:[;\/?\\@&=+$,\[\]A-Za-z0-9\-_\.\!\~\*\'\(\)%][\;\/\?\:\@\&\=\+\$\,\[\]A-Za-z0-9\-_\.\!\~\*\'\(\)%#\{\}]*|[KZ]:\\*.*\w+)")

    return urlfinder.sub(r'<a href="\1">\1</a>', value)


def get_series_relationship(package):
    """
    Return package series relationship.
    """
    # Get all relationship.
    relationships = get_all_relationships(package.get('id'))

    # Group hasPart/isPartOf relationship.
    has_part = []
    is_part_of = []
    for relationship in relationships:
        type = relationship.get('type')
        if type == 'hasPart':
            has_part.append(relationship)
        elif type == 'isPartOf':
            is_part_of.append(relationship)

    return {'hasPart': has_part, 'isPartOf': is_part_of}


def is_collection(series_relationship):
    if series_relationship.get('hasPart'):
        return True

    return False


def is_part_of_collection(series_relationship):
    if series_relationship.get('isPartOf'):
        return True

    return False
