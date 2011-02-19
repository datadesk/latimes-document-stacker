from documents.models import Document
from documents.management.commands import *
from django.core.management.base import CommandError


class Command(GAECommand):
    help = 'Loads the specified project into the datastore'
    args = '<project_slug>'
    
    def handle(self, *args, **options):
        # Make sure they provided a document slug
        try:
            proj_slug = args[0]
        except:
            e = "You must provide a valid project slug as the first argument."
            raise CommandError(e)
        
        # Login
        self.authorize(options)
        
        # Pull the project config
        proj = get_project(proj_slug)
        
        # Create the object
        obj, created = update_or_create_project(proj)
        if created:
            print "Created: %s" % obj
        else:
            print "Updated: %s" % obj
        
        # Update all the documents linked with this project
        doc_list = get_documents_in_project(proj_slug)
        for doc in doc_list:
            doc_obj, created = update_or_create_document(doc)
            if created:
                print "Created: %s" % doc_obj
            else:
                print "Updated: %s" % doc_obj
        
        # Find any linked documents in the database who are not in the yaml list
        linked_slugs = [i.get('slug') for i in doc_list]
        for doc in obj.document_set:
            if doc.slug not in linked_slugs:
                # And disconnect them from the project
                doc.project = None
                doc.put()








