from documents.models import Project
from documents.management.commands import *
from django.core.management.base import CommandError


class Command(GAECommand):
    help = 'Deletes the specified project from the datastore'
    args = '<project_key_name>'
    
    def handle(self, *args, **options):
        # Make sure they provided a table name
        try:
            key_name = args[0]
        except:
            raise CommandError("You must provide the key_name of a project as the first argument.")
        
        # Login
        self.authorize(options)
        
        # Drop it, if it exists.
        obj = Project.get_by_key_name(key_name)
        if obj:
            print "Deleting %s" % obj
            obj.delete()
        else:
            print "'%s' does not exist" % key_name




