from documents.management.commands import *


class Command(GAECommand):
    help = 'Loads more than one project into the datastore. All projects by default. Specify a yaml file name if you\'d like to limit it.'
    args = '<project_file_name>'
    
    def handle(self, *args, **options):
        # Figure out if the user provided a yaml_name
        try:
            filename = args[0]
        except:
            filename = None
        
        # Login
        self.authorize(options)
        
        # If they did, pull that one.
        if filename:
            proj_list = open_project_yaml('%s.yaml' % filename)
        # Otherwise pull everything
        else:
            proj_list = get_all_projects()
        
        # Loop through all the documents
        for proj in proj_list:
            try:
                obj, created = update_or_create_project(proj)
                if created:
                    print "Created: %s" % obj
                else:
                    print "Updated: %s" % obj
            except:
                raise
                print "Failed: %s" % proj
            
            # Update all the documents linked with this project
            doc_list = get_documents_in_project(proj.get("slug"))
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
