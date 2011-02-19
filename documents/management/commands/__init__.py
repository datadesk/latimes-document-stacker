import os
import yaml
import getpass
import itertools
from django.conf import settings
from optparse import make_option
from toolbox.slugify import slugify
from toolbox.FileIterator import FileIterator

# GAE biz
from google.appengine.ext import db
from google.appengine.api.labs import taskqueue
from documents.models import Document, Project, Tag
from django.core.management.base import BaseCommand, CommandError
from google.appengine.ext.remote_api import remote_api_stub

#
# Building blocks
#

class YAMLDoesNotExistError(Exception):
    """
    Called when you try to open a YAML that doesn't exist.
    """
    def __init__(self, value):
        self.parameter = value
    
    def __str__(self):
        return repr(self.parameter)


class GAECommand(BaseCommand):
    """
    A Django custom management command tailored for our way of using Google
    App engine.
    """
    custom_options = (
        make_option(
            "--host",
            action="store",
            dest="host",
            default=None,
            help="specify the host to update, defaults to <app_id>.appspot.com"
        ),
    )
    option_list = BaseCommand.option_list + custom_options
    
    def authorize(self, options):
        """
        Setup all the GAE remote API bizness.
        """
        # Pull the app id
        app_id = self.get_app_id()
        # Figure out the URL to hit
        if options.get('host'):
            host = options.get('host')
        else:
            host = '%s.appspot.com' % app_id
        # Connect
        remote_api_stub.ConfigureRemoteDatastore(app_id, '/remote_api', self.login, host)
    
    def get_app_id(self):
        """
        Retrieves the id of the current app.
        """
        path = os.path.join(settings.ROOT_PATH, 'app.yaml')
        yaml_data = yaml.load(open(path))
        return yaml_data['application']
    
    def login(self):
        """
        Quickie method for logging in to the remote api. From GAE docs.
        """
        return raw_input('Username:'), getpass.getpass('Password:')

#
# Documents
#

def open_document_yaml(filename):
    """
    Open a YAML file return a list of all the document configs.
    """
    path = os.path.join(settings.DOCUMENT_DIR, filename)
    return yaml.load(open(path))['documents']


def get_all_documents():
    """
    Returns a list of all the documents configured in the DOCUMENT_DIR
    in dictionary form.
    """
    file_list = FileIterator(settings.DOCUMENT_DIR)
    yaml_list = [i for i in file_list if i.endswith('.yaml')]
    doc_iter = itertools.chain(*[open_document_yaml(i) for i in yaml_list])
    return list(doc_iter)


def get_document(slug):
    """
    Retrieves the yaml obj of particular document specified by the slug.
    """
    hits = [i for i in get_all_documents() if i.get('slug') == slug]
    if len(hits) > 1:
        raise ValueError("More than one YAML config slugged: %s" % slug)
    elif len(hits) == 0:
        raise YAMLDoesNotExistError("Slug %s could not be found" % slug)
    else:
        return hits[0]


def update_or_create_document(yaml_obj):
    """
    Submit an object read from our YAML files and it will update it in the
    database, creating it if it doesn't already exist. 
    
    Returns the database object, and a boolean that is true if a new object 
    was created.
    """
    # Check if the table already exists in the datastore
    obj = Document.get_by_key_name(yaml_obj.get('slug'))
    # Update the obj if it exists
    if obj:
        # Loop through the keys and update the object one by one.
        for key in yaml_obj.keys():
            # With some special casing for projects...
            if key == 'project_slug':
                proj = Project.get_by_key_name(yaml_obj.get('project_slug'))
                obj.project = proj
            # ...and for tags.
            elif key == 'tags':
                obj.tags = get_tag_keys(yaml_obj.get("tags"))
            else:
                setattr(obj, key, yaml_obj.get(key))
        # Save it out
        obj.put()
        created = False
    # Create it if it doesn't
    else:
        # If it has tags....
        if yaml_obj.has_key('tags'):
            # Convert to database keys
            tags = get_tag_keys(yaml_obj.pop("tags"))
            # Load the data
            obj = Document(key_name=yaml_obj.get('slug'), **yaml_obj)
            # Set the tags
            obj.tags = tags
        # Otherwise....
        else:
            # Update the basic values
            obj = Document(key_name=yaml_obj.get('slug'), **yaml_obj)
            # And clear out the tag data
            obj.tags = []
            obj.similar_documents = []
        # Connected it to a project, if it exists
        if yaml_obj.has_key('project_slug'):
            proj = Project.get_by_key_name(yaml_obj.get('project_slug'))
            obj.project = proj
        # Save it out
        obj.put()
        created = True
    
    # Update the similarity lists of documents with the same tags
    taskqueue.add(
        url='/_/document/update-similar/',
        params=dict(key=obj.key()),
        method='GET'
    )
    
    # Pass it out
    return obj, created

#
# Projects
#

def open_project_yaml(filename):
    """
    Open a YAML file return a list of all the project configs.
    """
    path = os.path.join(settings.PROJECT_DIR, filename)
    return yaml.load(open(path))['projects']


def get_all_projects():
    """
    Returns a list of all the projects configured in the PROJECT_DIR
    in dictionary form.
    """
    file_list = FileIterator(settings.PROJECT_DIR)
    yaml_list = [i for i in file_list if i.endswith('.yaml')]
    proj_iter = itertools.chain(*[open_project_yaml(i) for i in yaml_list])
    return list(proj_iter)


def get_project(slug):
    """
    Retrieves the yaml obj of particular project specified by the slug.
    """
    hits = [i for i in get_all_projects() if i.get('slug') == slug]
    if len(hits) > 1:
        raise ValueError("More than one YAML config slugged: %s" % slug)
    elif len(hits) == 0:
        raise YAMLDoesNotExistError("Slug %s could not be found" % slug)
    else:
        return hits[0]


def get_documents_in_project(slug):
    """
    Retrieves a list of the yaml objects for all of the documents linked
    to the provided project slug.
    
    Returns an empty list if nothing matches.
    """
    return [i for i in get_all_documents() if i.get('project_slug', '') == slug]


def update_or_create_project(yaml_obj):
    """
    Submit an object read from our YAML files and it will update it in the
    database, creating it if it doesn't already exist. 
    
    Returns the database object, and a boolean that is true if a new object 
    was created.
    """
    obj = Project.get_by_key_name(yaml_obj.get('slug'))
    # Update the obj if it exists
    if obj:
        for key in yaml_obj.keys():
            setattr(obj, key, yaml_obj.get(key))
        obj.put()
        return obj, False
    # Create it if it doesn't
    else:
        obj = Project(key_name=yaml_obj.get('slug'), **yaml_obj)
        obj.put()
        return obj, True

#
# Tags
#

def get_tag_keys(tag_list):
    """
    Accepts a list of humanized tag names and returns a list of the db.Key's
    for the corresponding Tag model entries.
    """
    if not tag_list:
        return []
    key_list = []
    for tag_name in tag_list:
        obj = Tag.get_by_key_name(slugify(tag_name))
        if obj:
            key_list.append(obj.key())
        else:
            slug = slugify(tag_name)
            obj = Tag(title=tag_name, slug=slug, key_name=slug)
            obj.put()
            key_list.append(obj.key())
    return key_list

