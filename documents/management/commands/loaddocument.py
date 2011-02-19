from documents.management.commands import *
from django.core.management.base import CommandError


class Command(GAECommand):
    help = 'Loads the specified document into the datastore'
    args = '<document_slug>'
    
    def handle(self, *args, **options):
        # Make sure they provided a document slug
        try:
            doc_slug = args[0]
        except:
            raise CommandError("You must provide a document slug")
        
        # Login
        self.authorize(options)
        
        # Try to find the document in our the YAML files
        doc = get_document(doc_slug)
        
        # Create the object
        obj, created = update_or_create_document(doc)
        if created:
            print "Created: %s" % obj
        else:
            print "Updated: %s" % obj







