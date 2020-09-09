import ast
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import json
import logging

from ckan.lib.navl.dictization_functions import MissingNullEncoder
from ckanext.qdes_schema import helpers, validators
from ckanext.qdes_schema.logic.action import get

log = logging.getLogger(__name__)


class QDESSchemaPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IFacets)
    plugins.implements(plugins.IPackageController, inherit=True)

    # IValidators
    def get_validators(self):
        return {
            'qdes_temporal_start_end_date': validators.qdes_temporal_start_end_date,
            'qdes_dataset_current_date_later_than_creation': validators.qdes_dataset_current_date_later_than_creation,
            'qdes_uri_validator': validators.qdes_uri_validator,
            'qdes_validate_decimal': validators.qdes_validate_decimal,
            'qdes_validate_geojson': validators.qdes_validate_geojson,
            'qdes_validate_geojson_point': validators.qdes_validate_geojson_point,
            'qdes_validate_geojson_polygon': validators.qdes_validate_geojson_polygon,
            'qdes_within_au_bounding_box': validators.qdes_within_au_bounding_box,
            'qdes_validate_geojson_spatial': validators.qdes_validate_geojson_spatial,
            'qdes_spatial_points_pair': validators.qdes_spatial_points_pair,
            'qdes_iso_8601_durations': validators.qdes_iso_8601_durations,
            'qdes_validate_multi_groups': validators.qdes_validate_multi_groups
        }

    # IConfigurer
    def update_config_schema(self, schema):
        ignore_missing = toolkit.get_validator('ignore_missing')
        qdes_validate_geojson = toolkit.get_validator('qdes_validate_geojson')

        schema.update({
            'ckanext.qdes_schema.au_bounding_box': [ignore_missing, qdes_validate_geojson],
        })

        return schema

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'qdes_schema')

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'get_multi_textarea_values': self.get_multi_textarea_values,
            'set_first_option': helpers.set_first_option,
            'get_current_datetime': helpers.get_current_datetime,
            'qdes_dataservice_choices': helpers.qdes_dataservice_choices,
            'qdes_process_json_facets': helpers.qdes_process_json_facets,
        }

    def get_multi_textarea_values(self, value):
        try:
            if len(value) > 0:
                return json.loads(value)
        except:
            pass

        return ['']

    # IActions
    def get_actions(self):
        return {
            'get_dataservice': get.dataservice
        }

    # IFacets
    def dataset_facets(self, facets_dict, package_type):
        facets_dict['type'] = plugins.toolkit._('Resource type')
        facets_dict['classification'] = plugins.toolkit._('General classification of dataset type')
        facets_dict['topic'] = plugins.toolkit._('Topic or theme')
        return facets_dict

    # IPackageController
    def before_index(self, pkg_dict):
        from pprint import pprint
        log.debug('>>>> QDES before_index <<<<')
        validated_data_dict = None

        #log.debug(pprint(validated_data_dict))
        #log.debug(type(validated_data_dict))
        #log.debug(pprint(ast.literal_eval(validated_data_dict)))

        try:
            # 'validated_data_dict' is actually a string representation of a dict
            # we need to convert it back to a dict in order to process it
            # and then convert it back to a string when we're finished
            validated_data_dict = json.loads(pkg_dict['validated_data_dict'])
            log.debug(pprint(validated_data_dict))
        except Exception as e:
            log.error(str(e))

        # PoC remove some things
        qdes_facets = ['classification', 'topic']

        for facet in qdes_facets:
            if pkg_dict.get('extras_' + facet, None):
                pkg_dict.pop('extras_' + facet)

            field_value = pkg_dict.get(facet, None)

            if field_value:
                try:
                    items = json.loads(field_value)
                    if items:
                        pkg_dict[facet] = [item.split('/')[-1] for item in items]

                        # We don't want to do this because when you load the dataset
                        # for editing it comes from solr and the URIs have been lost
                        # to re-populate the fields :(
                        # if facet in validated_data_dict:
                        #     validated_data_dict[facet] = pkg_dict[facet]
                        #     print('ok')
                except Exception as e:
                    log.error(str(e))

        # pkg_dict['validated_data_dict'] = json.dumps(validated_data_dict,
        #                                              cls=MissingNullEncoder)

        return pkg_dict
