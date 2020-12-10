import logging

from ckan.plugins.toolkit import get_converter, h

log = logging.getLogger(__name__)


def get_collection_ids(pkg):
    ids = []
    series_relationships = h.get_series_relationship(pkg)

    for relationship in series_relationships.get('isPartOf'):
        ids.append(relationship.get('pkg_id'))

    return ids


def get_resource_format_labels(dataset_type, resource_formats):
    resource_format_labels = []

    # Only perform this step if the package type is "dataset" (and we have some resources)
    if dataset_type in ['dataset'] and resource_formats:
        schema = h.scheming_get_dataset_schema('dataset')
        schema_field = h.scheming_field_by_name(schema['resource_fields'], 'format') if schema else []
        schema_field_choices = h.scheming_field_choices(schema_field) or []

        for format in resource_formats:
            # The `scheming_choices_label` helper returns the
            # original value if no matching choice found
            resource_format_labels.append(h.scheming_choices_label(schema_field_choices, format))

    return resource_format_labels


def convert_vocabulary_terms_json_to_labels(dataset_type, field_name, terms_json):
    """
    Generic helper function to convert a JSON string list of vocabulary terms into their respective labels
    For indexing in Solr to allow keyword querying on the vocabulary term / label
    """
    labels = []

    schema = h.scheming_get_dataset_schema(dataset_type)
    schema_field = h.scheming_field_by_name(schema['dataset_fields'], field_name) if schema else []

    schema_field_choices = []
    if schema_field:
        schema_field_choices = h.scheming_field_choices(schema_field) or []

    terms_list = []
    if terms_json:
        terms_list = get_converter('json_or_string')(terms_json)

    if schema_field_choices and terms_list:
        for term in terms_list:
            labels.append(h.scheming_choices_label(schema_field_choices, term))

    return labels


def convert_license_uri_to_label(dataset_type, license_uri):
    """
    License is currently stored as a URI in both:
    - license_id
    - license_title
    """
    if license_uri:
        try:
            schema = h.scheming_get_dataset_schema(dataset_type)

            # The `license` field in the Dataset metadata schema is named `license_id`
            # But in the Data Service metadata schema it is named `license`
            schema_field = h.scheming_field_by_name(schema['dataset_fields'], 'license_id') if schema else []

            if not schema_field:
                # Try the `license` field
                schema_field = h.scheming_field_by_name(schema['dataset_fields'], 'license') if schema else []

            if schema_field:
                schema_field_choices = h.scheming_field_choices(schema_field) or []

                return h.scheming_choices_label(schema_field_choices, license_uri)
        except Exception as e:
            log.error(str(e))

    return None


def convert_term_uri_to_label(dataset_type, field_name, uri):
    """
    Generic helper function to convert uri to term label.
    """
    try:
        schema = h.scheming_get_dataset_schema(dataset_type)
        schema_field = h.scheming_field_by_name(schema['dataset_fields'], field_name) if schema else []

        if schema_field:
            schema_field_choices = h.scheming_field_choices(schema_field) or []

            return h.scheming_choices_label(schema_field_choices, uri)
    except Exception as e:
        log.error(str(e))

    return None
