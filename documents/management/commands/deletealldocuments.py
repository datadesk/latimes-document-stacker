from documents.models import Document
from documents.management.commands import *


class Command(GAECommand):
    help = 'Delete all documents in the datastore'
    
    def handle(self, *args, **options):
        
        # Login
        self.authorize(options)
        
        # Loop through them...
        for obj in Document.all():
            # ... and do the deed.
            print "Deleted %s" % obj
            obj.delete()

