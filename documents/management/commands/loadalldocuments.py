from documents.management.commands import *


class Command(GAECommand):
    help = 'Loads more than one document into the datastore. All documents by default. Specify a yaml file name if you\'d like to limit it.'
    args = '<document_file_name>'
    
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
            doc_list = open_document_yaml('%s.yaml' % filename)
        # Otherwise pull everything
        else:
            doc_list = get_all_documents()
        
        # Loop through all the documents
        for doc in doc_list:
            try:
                # and make it happen
                obj, created = update_or_create_document(doc)
                if created:
                    print "Created: %s" % obj
                else:
                    print "Updated: %s" % obj
            except:
                print "Failed: %s" % doc



