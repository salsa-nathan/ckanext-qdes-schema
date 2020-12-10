import ckan.lib.munge as munge
import json
import re
from datetime import datetime

import xml.etree.ElementTree as ET
from pprint import pformat, pprint
from ckanext.qdes_schema.logic.helpers import harvest_helpers as helpers


class QSpatialObject:
    """
    This class will do mapping from QSpatial XML to CKAN package dictionary.
    """

    def __init__(self, xml_filename, remoteCKAN, log_file, debug=False):
        self.root = ET.parse(xml_filename).getroot()
        # self.ns={"gts":"http://www.isotc211.org/2005/gts","gml":"http://www.opengis.net/gml","gml32":"http://www.opengis.net/gml/3.2","gmx":"http://www.isotc211.org/2005/gmx","gsr":"http://www.isotc211.org/2005/gsr","gss":"http://www.isotc211.org/2005/gss","gco":"http://www.isotc211.org/2005/gco","gmd":"http://www.isotc211.org/2005/gmd","srv":"http://www.isotc211.org/2005/srv","xlink":"http://www.w3.org/1999/xlink","xsi":"http://www.w3.org/2001/XMLSchema-instance"}
        self.ns = {
            "gts": "http://www.isotc211.org/2005/gts",
            "gml": "http://www.opengis.net/gml",
            "gml32": "http://www.opengis.net/gml/3.2",
            "gmx": "http://www.isotc211.org/2005/gmx",
            "gsr": "http://www.isotc211.org/2005/gsr",
            "gss": "http://www.isotc211.org/2005/gss",
            "gco": "http://www.isotc211.org/2005/gco",
            "gmd": "http://www.isotc211.org/2005/gmd",
            "srv": "http://www.isotc211.org/2005/srv",
            "xlink": "http://www.w3.org/1999/xlink",
            "xsi": "http://www.w3.org/2001/XMLSchema-instance"
        }
        self.package = {}
        self.resource = {}
        # Set the import source and destination.
        self.remoteCKAN = remoteCKAN
        self.debug = debug
        self.log_file = open(log_file, 'a')

    def log(self, message):
        if self.debug:
            self.log_file.write(message+"\n")
            # file.close()
            # print(message)

    def get_ckan_package_dict(self):
        
        # Populate some of the other fields that throw errors from scheming validation
        self.package['type'] = 'dataset'
        today = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
        self.package['dataset_last_modified_date'] = today
        self.package['metadata_review_date'] = today

        self.package.update(self.get_title())
        self.log('<----------------------------------------------------------------------------------------------------------------------------------------------------------->')
        self.log(self.package.get('title'))
        self.log('<----------------------------------------------------------------------------------------------------------------------------------------------------------->')
        self.package.update(self.get_parent_identifier())
        self.package.update(self.get_identifiers())
        self.package.update(self.get_classification())
        self.package.update(self.get_notes())
        self.package.update(self.get_topic())
        self.package.update(self.get_contact_point())
        self.package.update(self.get_contact_publisher())
        self.package.update(self.get_contact_other_party())
        self.package.update(self.get_publication_status())
        self.package.update(self.get_classification_and_access_restrictions())
        self.package.update(self.get_license_id())
        self.package.update(self.get_owner_org())
        self.package.update(self.get_name())
        self.package.update(self.get_additional_info())
        self.package.update(self.get_dataset_language())
        self.package.update(self.get_keywords())
        self.package.update(self.get_temporal_start())
        self.package.update(self.get_temporal_end())
        self.package.update(self.get_spatial_lower_left())
        self.package.update(self.get_spatial_upper_right())
        self.package.update(self.get_spatial_content_resolution())
        self.package.update(self.get_spatial_representation())
        self.package.update(self.get_spatial_datum_crs())
        self.package.update(self.get_dataset_release_date(today))
        self.package.update(self.get_update_schedule())
        self.package.update(self.get_quality_description())
        self.package.update(self.get_url())
        self.package.update(self.get_lineage_description())
        self.package.update(self.get_rights_statement())

        # # @TODO: These ones should probably have the ignore_missing validator added to themx
        # for field in [
        #     'qdes_iso_8601_durations',
        #     'parameter',
        #     'contact_other_party',
        #     'lineage_inputs',
        #     'lineage_sensor',
        #     'url',
        # ]:
        #     self.package[field] = None

        # # Create resource
        self.resource.update(self.get_resource_name())
        self.resource.update(self.get_resource_format())
        self.resource.update(self.get_resource_size())
        self.resource.update(self.get_resource_service_api_endpoint())
        self.resource.update(self.get_resource_rights_statement())
        self.resource.update(self.get_resource_license())
        self.package['resources'] = [self.resource]

        return self.package

    def get_parent_identifier(self):
        parent_identifier = None
        # /MD_Metadata/fileIdentifier/gco:CharacterString
        parentIdentifier = self.root.find('gmd:parentIdentifier/gco:CharacterString', self.ns)
        if parentIdentifier != None:
            parent_identifier = parentIdentifier.text

        # if parent_identifier == None:
            # Set default value
            # self.log('parent_identifier: No value')

        # self.log('parent_identifier: {}'.format(parent_identifier))
        return {'parent_identifier': parent_identifier}

    def get_identifiers(self):
        identifiers = None
        # /MD_Metadata/fileIdentifier/gco:CharacterString
        fileIdentifier = self.root.find('gmd:fileIdentifier/gco:CharacterString', self.ns)
        if fileIdentifier != None:
            identifiers = fileIdentifier.text

        if identifiers == None:
            # Set default value
            self.log('identifiers: {0}'.format(fileIdentifier.text if fileIdentifier != None else "No value"))
            # identifiers = 'value'

        # self.log('identifiers: {}'.format(identifiers))
        # Multi value
        return {'identifiers': json.dumps([identifiers]) if identifiers else None}

    def get_title(self):
        title = None
        # /MD_Metadata/identificationInfo/MD_DataIdentification/citation/CI_Citation/title/gco:CharacterString
        titleElement = self.root.find('gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:title/gco:CharacterString', self.ns)
        if titleElement != None:
            title = titleElement.text or None

        if title == None:
            # Set default value
            self.log('title: {0}'.format(titleElement.text if titleElement != None else "No value"))
            # title = 'Default title - {}'.format(self.xml_filename)

        # self.log('title: {}'.format(title))
        return {'title': title}

    def get_name(self):
        name = None
        title = self.get_title().get('title')
        if title != None:
            name = munge.munge_title_to_name(title) or None

        if name == None:
            # Set default value
            self.log('name: {0}'.format(title if title != None else "No value"))
            # title = 'Default name - {}'.format(self.xml_filename)

        # self.log('name: {}'.format(name))
        return {'name': name}

    def get_classification(self):
        classification_term = None
        presentationFormCode = self.root.find('gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:presentationForm/gmd:CI_PresentationFormCode', self.ns)
        if presentationFormCode != None:
            classification_term = helpers.get_vocabulary_service_term(self.remoteCKAN, presentationFormCode.text, 'classification')

        if classification_term == None:
            # Set default value
            self.log('classification: {0}'.format(presentationFormCode.text if presentationFormCode != None else "No value"))
            # Grabbed the last value from https://ckan-qdes-ckan-develop.au.amazee.io/ckan-admin/vocabulary-service/terms/940c52b1-bb97-47d7-a515-2d42c068ab53
            classification_term = 'http://registry.it.csiro.au/def/datacite/resourceType/Workflow'

        # self.log('classification: {}'.format(classification_term))
        # Multi value
        return {'classification': json.dumps([classification_term]) if classification_term else None}

    def get_notes(self):
        notes = None
        # /MD_Metadata/identificationInfo/MD_DataIdentification/abstract/gco:CharacterString
        abstract = self.root.find('gmd:identificationInfo/gmd:MD_DataIdentification/gmd:abstract/gco:CharacterString', self.ns)
        if abstract != None:
            notes = abstract.text

        if notes == None:
            # Set default value
            self.log('notes: {0}'.format(abstract.text if abstract else "No value"))
            # notes = 'Default notes - {}'.format(self.get_title().get('title'))

        # self.log('notes: {}'.format(notes))
        return {'notes': notes}

    def get_topic(self):
        topic_term = ''
        # /MD_Metadata/identificationInfo/MD_DataIdentification/topicCategory/MD_TopicCategoryCode
        topicCategoryCode = self.root.find('gmd:identificationInfo/gmd:MD_DataIdentification/gmd:topicCategory/gmd:MD_TopicCategoryCode', self.ns)
        if topicCategoryCode != None:
            topic_term = helpers.get_vocabulary_service_term(self.remoteCKAN, topicCategoryCode.text, 'topic')

        if topic_term == None:
            # Set default value
            self.log('topic_term: {0}'.format(topicCategoryCode.text if topicCategoryCode != None else "No value"))
            # Grabbed the last value from https://ckan-qdes-ckan-develop.au.amazee.io/ckan-admin/vocabulary-service/terms/67cb4107-9b8b-4dfd-a688-6c3e76e02239
            topic_term = 'https://gcmdservices.gsfc.nasa.gov/kms/concept/14625f2a-4186-4377-a0d9-88998bb6b775'

        # self.log('topic: {}'.format(topic_term))
        # Multi value
        return {'topic': json.dumps([topic_term]) if topic_term else None}

    def get_contact_point(self):
        contact_point_term = None
        # /MD_Metadata/contact/CI_ResponsibleParty/contactInfo/CI_Contact/address/CI_Address/electronicMailAddress/gco:CharacterString
        # /MD_Metadata/identificationInfo/MD_DataIdentification/pointOfContact/CI_ResponsibleParty/contactInfo/CI_Contact/address/CI_Address/electronicMailAddress/gco:CharacterString
        electronicMailAddress = self.root.find(
            'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:pointOfContact/gmd:CI_ResponsibleParty/gmd:contactInfo/gmd:CI_Contact/gmd:address/gmd:CI_Address/gmd:electronicMailAddress/gco:CharacterString', self.ns)
        if electronicMailAddress != None:
            contact_point_term = helpers.get_secure_vocabulary_record(self.remoteCKAN, electronicMailAddress.text, 'point-of-contact')

        if contact_point_term == None:
            # Set default value
            self.log('contact_point: {0}'.format(electronicMailAddress.text if electronicMailAddress != None else "No value"))
            # Get 'Kelly Bryant' as the default
            contact_point_term = helpers.get_secure_vocabulary_record(self.remoteCKAN, 'Kelly Bryant', 'point-of-contact')

        # self.log('contact_point: {}'.format(contact_point_term))
        return {'contact_point': contact_point_term}

    def get_contact_publisher(self):
        contact_publisher_term = None
        # /MD_Metadata/identificationInfo/MD_DataIdentification/citation/CI_Citation/citedResponsibleParty[5]/CI_ResponsibleParty/positionName/gco:CharacterString
        positionName = self.root.find(
            'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:citedResponsibleParty/gmd:CI_ResponsibleParty[@id="resourceOwner"]/gmd:positionName/gco:CharacterString', self.ns)
        if positionName != None:
            contact_publisher_term = helpers.get_vocabulary_service_term(self.remoteCKAN, positionName.text, 'contact_publisher')

        if contact_publisher_term == None:
            # Set default value
            self.log('contact_publisher: {0}'.format(positionName.text if positionName != None else "No value"))
            # Grabbed the last value from https://ckan-qdes-ckan-develop.au.amazee.io/ckan-admin/vocabulary-service/terms/e763c23d-2fd9-4e73-b186-ce121ea75791
            contact_publisher_term = 'http://linked.data.gov.au/def/organisation-type/trust-regarded-as-corporations'

        # self.log('contact_publisher: {}'.format(contact_publisher_term))
        return {'contact_publisher': contact_publisher_term}

    def get_contact_other_party(self):
        the_party_term = None
        # "<identificationInfo>
        # <MD_DataIdentification>
        # <citation>
        # <CI_Citation>
        # <citedResponsibleParty>
        # <CI_ResponsibleParty id=""resourceCustodian"">
        # <organisationName> - ?
        # <positionName> - ?
        # <contactInfo>
        # <CI_Contact>
        # <onlineResource>
        # <CI_OnlineResource>
        # <linkage>
        # <URL> - ?

        # where <CI_RoleCode codeListValue=""custodian"" codeList=""http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml#CI_RoleCode"">"
        # TODO: Need to find out which element to use?
        # /MD_Metadata/identificationInfo/MD_DataIdentification/citation/CI_Citation/citedResponsibleParty/CI_ResponsibleParty/contactInfo/CI_Contact/onlineResource/CI_OnlineResource/linkage/URL
        # /MD_Metadata/identificationInfo/MD_DataIdentification/citation/CI_Citation/citedResponsibleParty[4]/CI_ResponsibleParty/positionName/gco:CharacterString
        URL = self.root.find('gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:citedResponsibleParty/gmd:CI_ResponsibleParty[@id="resourceCustodian"]/gmd:positionName/gco:CharacterString', self.ns)
        # /MD_Metadata/identificationInfo/MD_DataIdentification/citation/CI_Citation/citedResponsibleParty[4]/CI_ResponsibleParty/role/CI_RoleCode/@codeListValue
        # URL = self.root.find('gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:citedResponsibleParty/gmd:CI_ResponsibleParty/gmd:role/gmd:CI_RoleCode[@codeListValue="custodian"]', self.ns)
        if URL != None:
            the_party_term = helpers.get_secure_vocabulary_record(self.remoteCKAN, URL.text, 'the-party')

        if the_party_term == None:
            # Set default value
            self.log('contact_other_party: {0}'.format(URL.text if URL != None else "No value"))
            # Get 'Kelly Bryant' as the default
            the_party_term = helpers.get_secure_vocabulary_record(self.remoteCKAN, 'Kelly Bryant', 'the-party')

        contact_other_party = [{"the-party": the_party_term, "nature-of-their-responsibility": "http://linked.data.gov.au/def/dataciteroles/DataCurator"}]
        # self.log('contact_other_party: {}'.format(contact_other_party))
        return {'contact_other_party': json.dumps(contact_other_party) if the_party_term else None}

    def get_publication_status(self):
        publication_status = None
        progressCode = self.root.find('gmd:identificationInfo/gmd:MD_DataIdentification/gmd:status/gmd:MD_ProgressCode', self.ns)
        if progressCode != None:
            publication_status = helpers.get_vocabulary_service_term(self.remoteCKAN, progressCode.text, 'publication_status')

        if publication_status == None:
            # Set default value
            self.log('publication_status: {0}'.format(progressCode.text if progressCode != None else "No value"))
            # Grabbed the last value from https://ckan-qdes-ckan-develop.au.amazee.io/ckan-admin/vocabulary-service/terms/462ae48e-9509-46e7-b001-857f78c1a7ab
            publication_status = 'http://registry.it.csiro.au/def/isotc211/MD_ProgressCode/withdrawn'

        # self.log('publication_status: {}'.format(publication_status))
        return {'publication_status': publication_status}

    def get_classification_and_access_restrictions(self):
        classification_and_access_restrictions = None
        # /MD_Metadata/identificationInfo/MD_DataIdentification/resourceConstraints[10]/MD_SecurityConstraints/classification/MD_ClassificationCode/@codeListValue
        classificationCode = self.root.find('gmd:identificationInfo/gmd:MD_DataIdentification/gmd:resourceConstraints/gmd:MD_SecurityConstraints/gmd:classification/gmd:MD_ClassificationCode', self.ns)
        if classificationCode != None:
            classification_and_access_restrictions = helpers.get_vocabulary_service_term(self.remoteCKAN, classificationCode.text, 'classification_and_access_restrictions')

        if classification_and_access_restrictions == None:
            # Set default value
            self.log('classification_and_access_restrictions: {0}'.format(classificationCode.text if classificationCode != None else "No value"))
            # Grabbed the send to last   value from https://ckan-qdes-ckan-develop.au.amazee.io/ckan-admin/vocabulary-service/terms/940c52b1-bb97-47d7-a515-2d42c068ab53
            classification_and_access_restrictions = 'http://registry.it.csiro.au/def/isotc211/MD_ClassificationCode/topSecret'

        # self.log('classification_and_access_restrictions: {}'.format(classification_and_access_restrictions))
        # REQUIRED Multi value
        return {'classification_and_access_restrictions': json.dumps([classification_and_access_restrictions])}

    def get_license_id(self):
        license_id = 'http://registry.it.csiro.au/licence/cc-by-4.0'
        # TODO: Verify this XPath as it returns the value 'license' which is not correct
        # restrictionCode = self.root.find(
        #     'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:resourceConstraints/gmd:MD_LegalConstraints/gmd:useConstraints/gmd:MD_RestrictionCode[@codeListValue="license"]', self.ns)
        # if restrictionCode != None:
        #     license_id = helpers.get_vocabulary_service_term(self.remoteCKAN, restrictionCode.text, 'license')

        # self.log('license_id: {}'.format(license_id))
        # Set default value to Creative Commons Attribution 4.0 International https://ckan-qdes-ckan-develop.au.amazee.io/ckan-admin/vocabulary-service/terms/6290f167-9105-49e7-9c0b-d1ca05881525
        return {'license_id': license_id}

    def get_owner_org(self):
        # # TODO: REQUIRED What should be the default owner_org
        return {'owner_org': 'qspatial'}

    def get_additional_info(self):
        additional_info = None
        supplementalInformation = self.root.find('gmd:identificationInfo/gmd:MD_DataIdentification/gmd:supplementalInformation/gco:CharacterString', self.ns)
        if supplementalInformation != None:
            additional_info = supplementalInformation.text

        if additional_info == None:
            # Set default value?
            self.log('additional_info: {0}'.format(supplementalInformation.text if supplementalInformation != None else "No value"))

        # self.log('additional_info: {}'.format(additional_info))
        # Multi value
        return {'additional_info': json.dumps([additional_info]) if additional_info else None}

    def get_dataset_language(self):
        dataset_language = None
        language = self.root.find('gmd:identificationInfo/gmd:MD_DataIdentification/gmd:language/gco:CharacterString', self.ns)
        if language != None:
            dataset_language = helpers.get_vocabulary_service_term(self.remoteCKAN, language.text, 'dataset_language')

        if dataset_language == None:
            # Set default value
            self.log('dataset_language: {0}'.format(language.text if language != None else "No value"))
            # Grabbed the last value from https://ckan-qdes-ckan-develop.au.amazee.io/ckan-admin/vocabulary-service/terms/79209863-6432-4810-b614-d95e048affe5
            dataset_language = 'http://id.loc.gov/vocabulary/iso639-1/zu'

        # self.log('dataset_language: {}'.format(dataset_language))
        # Multi value
        return {'dataset_language': json.dumps([dataset_language]) if dataset_language else None}

    def get_keywords(self):
        tag_string = None
        tag_strings = []
        keywords = self.root.findall('gmd:identificationInfo/gmd:MD_DataIdentification/gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:keyword/gco:CharacterString', self.ns)
        if keywords != None:
            for keyword in keywords:
                # There is 1 record with a list of keywords seperated by a ';' Lets split these out as individual keywords to stop the tag validation error 'length is more than maximum 100'
                if keyword.text.count(';') > 1:
                    tag_strings.extend([word.strip() for word in keyword.text.split(';')])
                else:
                    tag_strings.append(keyword.text.strip())

        if len(tag_strings) == 0:
            # Set default value?
            self.log('tag_string: {0}'.format(keywords.text if keywords != None else "No value"))
        else:
            # Strip out invalid characters
            # Remove any character that is not alphanumeric, underscore, space, hyphen, fullstop
            tag_string = ','.join([re.sub('[^\w \-.]', '', str(tag)) for tag in tag_strings])

        # self.log('tag_string: {}'.format(tag_string))
        return {'tag_string': tag_string}

    def get_temporal_start(self):
        temporal_start = None
        beginPosition = self.root.find(
            'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent/gml:TimePeriod/gml:beginPosition', self.ns)
        if beginPosition != None:
            temporal_start = beginPosition.text

        if temporal_start == None:
            # Set default value?
            self.log('temporal_start: {0}'.format(beginPosition.text if beginPosition != None else "No value"))

        # self.log('temporal_start: {}'.format(temporal_start))
        return {'temporal_start': temporal_start}

    def get_temporal_end(self):
        temporal_end = None
        endPosition = self.root.find(
            'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent/gml:TimePeriod/gml:endPosition', self.ns)
        if endPosition != None:
            temporal_end = endPosition.text

        if temporal_end == None:
            # Set default value?
            self.log('temporal_end: {0}'.format(endPosition.text if endPosition != None else "No value"))

        # self.log('temporal_end: {}'.format(temporal_end))
        return {'temporal_end': temporal_end}

    def get_spatial_lower_left(self):
        coordinates = []

        westBoundLongitude = self.root.find(
            'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox/gmd:westBoundLongitude/gco:Decimal', self.ns)
        if westBoundLongitude != None:
            coordinates.append(float(westBoundLongitude.text))
        else:
            # Set default value?
            self.log('westBoundLongitude: No value')

        southBoundLatitude = self.root.find(
            'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox/gmd:southBoundLatitude/gco:Decimal', self.ns)
        if southBoundLatitude != None:
            coordinates.append(float(southBoundLatitude.text))
        else:
            # Set default value?
            self.log('southBoundLatitude: No value')

        # self.log('spatial_lower_left: {}'.format(coordinates))
        # Set default value? Only set value if there are 2 coordinates
        return {'spatial_lower_left': json.dumps({"type": "Point", "coordinates": coordinates}) if len(coordinates) == 2 else None}

    def get_spatial_upper_right(self):
        coordinates = []
        eastBoundLongitude = self.root.find(
            'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox/gmd:eastBoundLongitude/gco:Decimal', self.ns)
        if eastBoundLongitude != None:
            coordinates.append(float(eastBoundLongitude.text))
        else:
            # Set default value?
            self.log('eastBoundLongitude: No value')

        northBoundLatitude = self.root.find(
            'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox/gmd:northBoundLatitude/gco:Decimal', self.ns)
        if northBoundLatitude != None:
            coordinates.append(float(northBoundLatitude.text))
        else:
            # Set default value?
            self.log('northBoundLatitude: No value')

        # self.log('spatial_upper_right: {}'.format(coordinates))
        # Set default value? Only set value if there are 2 coordinates
        return {'spatial_upper_right': json.dumps({"type": "Point", "coordinates": coordinates}) if len(coordinates) == 2 else None}

    def get_spatial_content_resolution(self):
        spatial_content_resolution = None
        distance = self.root.find('gmd:identificationInfo/gmd:MD_DataIdentification/gmd:spatialResolution/gmd:MD_Resolution/gmd:distance/gco:Distance', self.ns)
        if distance != None:
            spatial_content_resolution = distance.text
        else:
            # Set default value?
            self.log('spatial_content_resolution: No value')

        # self.log('spatial_content_resolution: {}'.format(spatial_content_resolution))
        return {'spatial_content_resolution': spatial_content_resolution}

    def get_spatial_representation(self):
        spatial_representation = None
        spatialRepresentationTypeCode = self.root.find('gmd:identificationInfo/gmd:MD_DataIdentification/gmd:spatialRepresentationType/gmd:MD_SpatialRepresentationTypeCode', self.ns)
        if spatialRepresentationTypeCode != None:
            spatial_representation = helpers.get_vocabulary_service_term(self.remoteCKAN, spatialRepresentationTypeCode.text, 'spatial_representation')

        if spatial_representation == None:
            # Set default value
            self.log('spatial_representation: {0}'.format(spatialRepresentationTypeCode.text if spatialRepresentationTypeCode != None else "No value"))
            # Grabbed the last value from https://ckan-qdes-ckan-develop.au.amazee.io/ckan-admin/vocabulary-service/terms/1a4a638c-b6c0-43cd-aef1-413a1d99bd4b
            spatial_representation = 'http://registry.it.csiro.au/def/isotc211/MD_SpatialRepresentationTypeCode/video'

        # self.log('spatial_representation: {}'.format(spatial_representation))
        return {'spatial_representation': spatial_representation}

    def get_spatial_datum_crs(self):
        spatial_datum_crs = None
        # /MD_Metadata/referenceSystemInfo/MD_ReferenceSystem/referenceSystemIdentifier/RS_Identifier/code/gco:CharacterString
        code = self.root.find('gmd:referenceSystemInfo/gmd:MD_ReferenceSystem[@id="coordRefSystem"]/gmd:referenceSystemIdentifier/gmd:RS_Identifier/gmd:code/gco:CharacterString', self.ns)
        if code != None:
            spatial_datum_crs = helpers.get_vocabulary_service_term(self.remoteCKAN, code.text, 'spatial_datum_crs')
            # TODO: Map to  vocab service manually eg. EPSG:4283 = ?

        if spatial_datum_crs == None:
            # Set default value
            self.log('spatial_datum_crs: {0}'.format(code.text if code != None else "No value"))
            # Grabbed the last value from https://ckan-qdes-ckan-develop.au.amazee.io/ckan-admin/vocabulary-service/terms/d112d2c1-9f93-40f3-9ac0-0a829aaf4090
            spatial_datum_crs = 'http://linked.data.gov.au/def/queensland-crs/wgs1984'

        # self.log('spatial_datum_crs: {}'.format(spatial_datum_crs))
        return {'spatial_datum_crs': spatial_datum_crs}

    def get_dataset_release_date(self, default_date):
        dataset_release_date = None
        date = self.root.find('gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:date/gmd:CI_Date/gmd:date/gco:Date', self.ns)
        if date != None:
            dataset_release_date = date.text + "T14:00:00"  # Australia/Brisbane timezone in UTC
        else:
            # Set default value?
            self.log('dataset_release_date: No value')
            dataset_release_date = default_date

        # self.log('dataset_release_date: {}'.format(dataset_release_date))
        return {'dataset_release_date': dataset_release_date, 'dataset_creation_date': dataset_release_date}

    def get_update_schedule(self):
        update_schedule = None
        maintenanceFrequencyCode = self.root.find(
            'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:resourceMaintenance/gmd:MD_MaintenanceInformation/gmd:maintenanceAndUpdateFrequency/gmd:MD_MaintenanceFrequencyCode', self.ns)
        if maintenanceFrequencyCode != None:
            # update_schedule = helpers.get_mapped_update_frequency(maintenanceFrequencyCode.get('codeListValue', None))
            update_schedule = helpers.get_vocabulary_service_term(self.remoteCKAN, maintenanceFrequencyCode.get('codeListValue', None), 'update_schedule')
            # TODO: Map to vocab service manually eg notPlanned = ?

        if update_schedule == None:
            # Set default value
            self.log('update_schedule: {0}'.format(maintenanceFrequencyCode.get('codeListValue', None) if maintenanceFrequencyCode != None else "No value"))
            # Grabbed the last value from https://ckan-qdes-ckan-develop.au.amazee.io/ckan-admin/vocabulary-service/terms/54ca21ca-fa3b-4574-b2de-86d9986f18ab
            update_schedule = 'http://registry.it.csiro.au/def/isotc211/MD_MaintenanceFrequencyCode/unknown'

        # self.log('update_schedule: {}'.format(update_schedule))
        return {'update_schedule': update_schedule}

    def get_quality_description(self):
        quality_description = []

        # TODO: Verify this is the correct XPath

        # "<dataQualityInfo>
        # <DQ_DataQuality>
        # <report>"
        # "dqv:hasQualityAnnotation
        #  ⤷/dqv:inDimension"
        # <DQ_CompletenessOmission>
        # <DQ_ConceptualConsistency>
        # <DQ_AbsoluteExternalPositionalAccuracy>
        # <DQ_NonQuantitativeAttributeAccuracy>
        # /MD_Metadata/dataQualityInfo/DQ_DataQuality/report[2]/DQ_CompletenessOmission/result/DQ_ConformanceResult/explanation/gco:CharacterString
        # explanations = self.root.findall('gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:report/gmd:DQ_CompletenessOmission/gmd:result/gmd:DQ_ConformanceResult/gmd:explanation/gco:CharacterString', self.ns)
        # if explanations != None:
        #     dimensions = []
        #     for explanation in explanations:
        #         dimension = helpers.get_vocabulary_service_term(self.remoteCKAN, explanation, 'dimension')
        #         dimensions.append(dimension) if dimension else dimensions

        # "<dataQualityInfo>
        # <DQ_DataQuality>
        # <result>
        # <DQ_ConformanceResult>
        # <explanation>"
        # /MD_Metadata/dataQualityInfo/DQ_DataQuality/report[5]/DQ_NonQuantitativeAttributeAccuracy/result/DQ_ConformanceResult/explanation/gco:CharacterString
        # explanations = self.root.findall('gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:report/gmd:DQ_CompletenessOmission/gmd:result/gmd:DQ_ConformanceResult/gmd:explanation/gco:CharacterString', self.ns)
        # if explanations != None:
        #     values = []
        #     for explanation in explanations:
        #         values.append(explanation)

        # self.log('quality_description: {}'.format(quality_description))
        # Multi value
        return {'quality_description': json.dumps([quality_description]) if quality_description else None}

    def get_url(self):
        url = None
        # "<dataQualityInfo>
        # <DQ_DataQuality>
        # <lineage>
        # <LI_Lineage>
        # <source>
        # <LI_Source>
        # <description>"
        # /MD_Metadata/dataQualityInfo/DQ_DataQuality/lineage/LI_Lineage/source/LI_Source/description/gco:CharacterString

        # description = self.root.find('gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:source/gmd:LI_Source/gmd:description/gco:CharacterString', self.ns)
        # if description != None:
        #     url = description.text

        # TODO: Verify this is the correct XPath
        # /MD_Metadata/distributionInfo/MD_Distribution/distributor/MD_Distributor/distributorTransferOptions/MD_DigitalTransferOptions/onLine/CI_OnlineResource/linkage/URL ??
        linkage = self.root.find(
            'gmd:distributionInfo/gmd:MD_Distribution/gmd:distributor/gmd:MD_Distributor/gmd:distributorTransferOptions/gmd:MD_DigitalTransferOptions/gmd:onLine/gmd:CI_OnlineResource/gmd:linkage/gmd:URL', self.ns)
        if linkage != None:
            url = helpers.fix_url(linkage.text)
        else:
            # Set default value?
            self.log('url: No value')

        # self.log('url: {}'.format(url))
        return {'url': url}

    def get_lineage_description(self):
        lineage_description = None
        statement = self.root.find('gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:statement/gco:CharacterString', self.ns)
        if statement != None:
            lineage_description = statement.text
        else:
            # Set default value?
            self.log('lineage_description: No value')

        # self.log('lineage_description: {}'.format(lineage_description))
        return {'lineage_description': lineage_description}

    def get_rights_statement(self):
        rights_statement = None
        useLimitation = self.root.find(
            'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:resourceConstraints/gmd:MD_LegalConstraints/gmd:useConstraints/gmd:MD_RestrictionCode/../../gmd:useLimitation/gco:CharacterString', self.ns)
        if useLimitation != None:
            rights_statement = useLimitation.text
            # Rights statement is not displayed in a HTML markup textbox so the below copyright statement '&copy;' needs to be replaced with '©'
            rights_statement = rights_statement.replace('&copy;', '©').replace('&copy', '©')
        else:
            # Set default value?
            self.log('rights_statement: No value')

        # self.log('rights_statement: {}'.format(rights_statement))
        return {'rights_statement': rights_statement}

    def get_resource_name(self):
        resource_name = None
        # TODO: Confirm XPath, it is the same as the title
        title = self.root.find('gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:title/gco:CharacterString', self.ns)
        if title != None:
            resource_name = title.text
        else:
            # Set default value?
            self.log('resource_name: No value')

        # self.log('resource_name: {}'.format(resource_name))
        return {'name': resource_name}

    def get_resource_format(self):
        resource_format = None
        # TODO: Verify if should be using this XPATH It also has multiple formats?
        # /MD_Metadata/identificationInfo/MD_DataIdentification/resourceFormat/MD_Format/name/gco:CharacterString
        # /MD_Metadata/identificationInfo/MD_DataIdentification/resourceFormat/MD_Format/name/gco:CharacterString
        name = self.root.find('gmd:identificationInfo/gmd:MD_DataIdentification/gmd:resourceFormat/gmd:MD_Format/gmd:name/gco:CharacterString', self.ns)
        if name != None:
            # TODO: Map string format to vocab
            resource_format = helpers.get_vocabulary_service_term(self.remoteCKAN, name.text, 'format')

        if resource_format == None:
            # Set default value
            self.log('resource_format: {0}'.format(name.text if name != None else "No value"))
            # Grabbed the last value from https://ckan-qdes-ckan-develop.au.amazee.io/ckan-admin/vocabulary-service/terms/035d3c4b-f503-496e-ab4b-820deee6c5cd
            resource_format = 'https://www.iana.org/assignments/media-types/application/zstd'

        # self.log('resource_format: {}'.format(resource_format))
        return {'format': resource_format}

    def get_resource_size(self):
        resource_size = None
        transferSize = self.root.find(
            'gmd:distributionInfo/gmd:MD_Distribution/gmd:distributor/gmd:MD_Distributor/gmd:distributorTransferOptions/gmd:MD_DigitalTransferOptions/gmd:transferSize/gco:Real', self.ns)
        if transferSize != None:
            resource_size = int(float(transferSize.text)) * 1024  # convert megabytes into bytes
        else:
            self.log('resource_size: No value')

        # self.log('resource_size: {}'.format(resource_size))
        return {'size': resource_size}

    def get_resource_service_api_endpoint(self):
        resource_service_api_endpoint = None
        url = self.root.find(
            'gmd:distributionInfo/gmd:MD_Distribution/gmd:distributor/gmd:MD_Distributor/gmd:distributorTransferOptions/gmd:MD_DigitalTransferOptions/gmd:onLine/gmd:CI_OnlineResource/gmd:linkage/gmd:URL', self.ns)
        if url != None:
            resource_service_api_endpoint = helpers.fix_url(url.text)
        else:
            self.log('resource_service_api_endpoint: No value')

        # self.log('resource_service_api_endpoint: {}'.format(resource_service_api_endpoint))
        # MULTI
        return {'service_api_endpoint': json.dumps([resource_service_api_endpoint]) if resource_service_api_endpoint else None}

    def get_resource_rights_statement(self):
        resource_rights_statement = None
        useLimitation = self.root.find('gmd:identificationInfo/gmd:MD_DataIdentification/gmd:resourceConstraints/gmd:MD_LegalConstraints/gmd:useLimitation/gco:CharacterString', self.ns)
        if useLimitation != None:
            resource_rights_statement = useLimitation.text
            # Rights statement is not displayed in a HTML markup textbox so the below copyright statement '&copy;' needs to be replaced with '©'
            resource_rights_statement = resource_rights_statement.replace('&copy;', '©').replace('&copy', '©')
        else:
            self.log('resource_rights_statement: No value')

        # self.log('resource_rights_statement: {}'.format(resource_rights_statement))
        return {'rights_statement': resource_rights_statement}

    def get_resource_license(self):
        resource_license = 'http://registry.it.csiro.au/licence/cc-by-4.0'

        # TODO: Verify this XPath as it returns the value 'license' which is not correct
        # restrictionCode = self.root.find(
        #     'gmd:identificationInfo/gmd:MD_DataIdentification/gmd:resourceConstraints/gmd:MD_LegalConstraints/gmd:useConstraints/gmd:MD_RestrictionCode[@codeListValue="license"]', self.ns)
        # if restrictionCode != None:
        #     license_id = helpers.get_vocabulary_service_term(self.remoteCKAN, restrictionCode.text, 'license')

        # self.log('license_id: {}'.format(license_id))
        # Set default value to Creative Commons Attribution 4.0 International https://ckan-qdes-ckan-develop.au.amazee.io/ckan-admin/vocabulary-service/terms/6290f167-9105-49e7-9c0b-d1ca05881525

        # self.log('resource_license: {}'.format(resource_license))
        return {'license': resource_license}
