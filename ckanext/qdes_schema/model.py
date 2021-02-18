import ckanext.qdes_schema.constants as constants
import datetime
import logging

from ckan.model import meta
from ckan.model import types as _types
from sqlalchemy import types, Column, Table
from ckan.model.domain_object import DomainObject
from sqlalchemy import desc
from pprint import pformat

log = logging.getLogger(__name__)

# Define publish_log table structure.
publish_log_table = Table(
    'publish_log', meta.metadata,
    Column('id', types.UnicodeText, primary_key=True, default=_types.make_uuid),
    Column('dataset_id', types.UnicodeText, nullable=False),
    Column('resource_id', types.UnicodeText),
    Column('trigger', types.UnicodeText, nullable=False),
    Column('destination', types.UnicodeText),
    Column('destination_identifier', types.UnicodeText),
    Column('action', types.UnicodeText),
    Column('date_created', types.DateTime, default=datetime.datetime.utcnow()),
    Column('date_processed', types.DateTime),
    Column('status', types.UnicodeText, nullable=False),
    Column('details', types.UnicodeText),
)


class PublishLog(DomainObject):
    u"""
    An PublishLog object.
    """

    # Available destination.
    destinations = [
        constants.PUBLISH_EXTERNAL_IDENTIFIER_DATA_QLD_SCHEMA,
        constants.PUBLISH_EXTERNAL_IDENTIFIER_QSPATIAL_SCHEMA,
        constants.PUBLISH_EXTERNAL_IDENTIFIER_SIR_SCHEMA
    ]

    def __init__(self, dataset_id=None, resource_id=None, trigger=None, destination=None, destination_identifier=None,
                 action=None, status=None, details=None):
        self.dataset_id = dataset_id
        self.resource_id = resource_id
        self.trigger = trigger
        self.destination = destination
        self.destination_identifier = destination_identifier
        self.action = action
        self.status = status
        self.details = details

    @classmethod
    def get(cls, id):
        query = meta.Session.query(cls).filter(cls.id == id)
        return query.first()

    @classmethod
    def get_recent_resource_log(cls, resource_id, status=False, action=[]):
        query = meta.Session.query(cls) \
            .filter(cls.resource_id == resource_id) \
            .order_by(desc(cls.date_processed))

        if status:
            query = query.filter(cls.status == status)

        if action:
            query = query.filter(cls.action.in_(tuple(action)))

        return query.first()

    @classmethod
    def has_published(cls, id, type='dataset'):
        published_log = {}
        for destination in cls.destinations:
            query = meta.Session.query(cls) \
                .filter(cls.action.in_(tuple([constants.PUBLISH_ACTION_UPDATE, constants.PUBLISH_ACTION_CREATE]))) \
                .filter(cls.status == constants.PUBLISH_STATUS_SUCCESS) \
                .filter(cls.destination == destination) \
                .order_by(desc(cls.date_processed))

            if type == 'dataset':
                query = query.filter(cls.dataset_id == id)
            elif type == 'resource':
                query = query.filter(cls.resource_id == id)

            publish_log = query.first()

            if publish_log and not cls.has_unpublished(publish_log, destination):
                # Check if this resource already unpublished.
                published_log[destination] = publish_log

        return published_log

    @classmethod
    def has_unpublished(cls, publish_log, destination):
        query = meta.Session.query(cls) \
            .filter(cls.resource_id == publish_log.resource_id) \
            .filter(cls.action == constants.PUBLISH_ACTION_DELETE) \
            .filter(cls.status == constants.PUBLISH_STATUS_SUCCESS) \
            .filter(cls.destination == destination) \
            .filter(cls.date_processed > publish_log.date_processed)

        return query.first()

    @classmethod
    def get_published_distributions(cls, pkg):
        published_log = {}
        for destination in cls.destinations:
            published_log[destination] = []

        for resource in pkg.get('resources'):
            published_distributions = cls.has_published(resource.get('id'), 'resource')
            for destination in published_distributions:
                published_log[destination].append(published_distributions[destination])


        return published_log


meta.mapper(PublishLog, publish_log_table)
