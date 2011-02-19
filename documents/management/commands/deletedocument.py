from documents.models import Document
from documents.management.commands import *
from google.appengine.api.labs import taskqueue
from django.core.management.base import CommandError


class Command(GAECommand):
    help = 'Deletes the specified document from the datastore'
    args = '<document_key_name>'
    
    def handle(self, *args, **options):
        # Make sure they provided a table name
        try:
            key_name = args[0]
        except:
            raise CommandError("You must provide the key_name of a document as the first argument.")
        
        # Login
        self.authorize(options)
        
        # Get it
        obj = Document.get_by_key_name(key_name)
        # Drop it
        if obj:
            print "Deleting %s" % obj
            obj.delete()
        else:
            print "'%s' does not exist" % key_name
        # Update the related list of all the related documents
        taskqueue.add(
            url='/_/document/update-similar/',
            params=dict(key=obj.key()),
            method='GET'
        )



