import pymongo
from . import ModuleStore, Location
from .exceptions import ItemNotFoundError, InsufficientSpecificationError
from xmodule.x_module import XModuleDescriptor, DescriptorSystem


class MongoModuleStore(ModuleStore):
    """
    A Mongodb backed ModuleStore
    """
    def __init__(self, host, db, collection, port=27017):
        self.collection = pymongo.connection.Connection(
            host=host,
            port=port
        )[db][collection]

        # Force mongo to report errors, at the expense of performance
        self.collection.safe = True

    def get_item(self, location):
        """
        Returns an XModuleDescriptor instance for the item at location.
        If location.revision is None, returns the most item with the most
        recent revision

        If any segment of the location is None except revision, raises
            keystore.exceptions.InsufficientSpecificationError
        If no object is found at that location, raises keystore.exceptions.ItemNotFoundError

        location: Something that can be passed to Location
        """

        query = {}
        for key, val in Location(location).dict().iteritems():
            if key != 'revision' and val is None:
                raise InsufficientSpecificationError(location)

            if val is not None:
                query['location.{key}'.format(key=key)] = val

        item = self.collection.find_one(
            query,
            sort=[('revision', pymongo.ASCENDING)],
        )
        if item is None:
            raise ItemNotFoundError(location)

        return XModuleDescriptor.load_from_json(item, DescriptorSystem(self.get_item))

    def create_item(self, location, editor):
        """
        Create an empty item at the specified location with the supplied editor

        location: Something that can be passed to Location
        """
        self.collection.insert({
            'location': Location(location).dict(),
            'editor': editor
        })

    def update_item(self, location, data):
        """
        Set the data in the item specified by the location to
        data

        location: Something that can be passed to Location
        data: A nested dictionary of problem data
        """

        # See http://www.mongodb.org/display/DOCS/Updating for
        # atomic update syntax
        self.collection.update(
            {'location': Location(location).dict()},
            {'$set': {'definition.data': data}}
        )

    def update_children(self, location, children):
        """
        Set the children for the item specified by the location to
        data

        location: Something that can be passed to Location
        children: A list of child item identifiers
        """

        # See http://www.mongodb.org/display/DOCS/Updating for
        # atomic update syntax
        self.collection.update(
            {'location': Location(location).dict()},
            {'$set': {'definition.children': children}}
        )