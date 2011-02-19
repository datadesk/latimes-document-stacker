import logging
from google.appengine.ext import db
from google.appengine.ext import webapp
from documents.models import Document, Tag
from google.appengine.api.labs import taskqueue


def get_key_or_none(request):
    """
    Gets the key param from the db, or returns None.
    """
    # Is the key is in the GET params?
    key = request.get('key', None)
    if not key:
        return None
    # Is the key is valid?
    try:
        key = db.Key(key)
    except:
        return None
    # Is the key in the database?
    obj = db.get(key)
    if not obj:
        return None
    # If all of the above are yes...
    return obj


class UpdateSimilarDocuments(webapp.RequestHandler):
    """
    Update the similarity lists for all documents that share tags with the
    submitted key.
    """
    def get(self):
        # Check if the key exists as an object in the db
        obj = get_key_or_none(self.request)
        # If it does...
        if obj:
            # ..update connected docs
            obj.similar_documents = obj.get_similar_documents()
            obj.put()
            # And then grab them all
            similar_documents = db.get(obj.similar_documents)
        # Otherwise just grab the ones currently linked to them
        else:
            key = db.Key(self.request.get('key', None))
            similar_documents = Document.all().filter("similar_documents =", key)
        # Then loop through and update all of them.
        for doc in similar_documents:
            doc.similar_documents = doc.get_similar_documents()
            logging.debug("Updated similar documents for %s" % doc)
            doc.put()
        # Close out
        self.response.out.write('OK')










