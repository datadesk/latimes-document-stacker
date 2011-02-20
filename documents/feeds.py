from datetime import datetime
from toolbox.mrss import MediaRSSFeed
from documents.models import Document, Project
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.syndication.feeds import Feed, FeedDoesNotExist


class LatestDocuments(Feed):
    """
    The latest documents published on the site.
    """
    feed_type = MediaRSSFeed
    title_template = "feeds/document_title.html"
    description_template = "feeds/document_description.html"
    
    def items(self):
        return Document.all().filter("is_published =", True).order("-publication_date")[:10]
    
    def item_pubdate(self, item):
        return datetime(*(item.publication_date.timetuple()[:6]))
    
    def item_extra_kwargs(self, obj):
        return {
            'thumbnail_url': obj.get_small_url(),
            'content_url': obj.get_pdf_url()
        }


class ProjectDocumentsFeed(Feed):
    """
    The latest documents published in a particular project.
    """
    feed_type = MediaRSSFeed
    title_template = "feeds/project_documents_title.html"
    description_template = "feeds/project_documents_description.html"
    
    def get_object(self, bits):
        if len(bits) != 1:
            raise ObjectDoesNotExist
        obj = Project.get_by_key_name(bits[0])
        if obj:
            return obj
        else:
            raise ObjectDoesNotExist
    
    def title(self, obj):
        return "Recent documents about %s" % obj.title
    
    def description(self, obj):
        return "The latest documents about %s from the Los Angeles Times" % obj.title
    
    def link(self, obj):
        if not obj:
            raise FeedDoesNotExist
        return obj.get_absolute_url()
        
    def items(self, obj):
        return obj.document_set.filter("is_published =", True).order("-publication_date")[:10]
    
    def item_pubdate(self, item):
        return datetime(*(item.publication_date.timetuple()[:6]))
    
    def item_extra_kwargs(self, obj):
        return {
            'thumbnail_url': obj.get_small_url(),
            'content_url': obj.get_pdf_url()
        }

