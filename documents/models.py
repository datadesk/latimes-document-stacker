# GAE biz
from google.appengine.ext import db
from google.appengine.api import urlfetch

# URLs
import urllib

# Date and time
from datetime import datetime


class Project(db.Model):
    """
    A project hosted on DocumentCloud.
    """
    title = db.StringProperty(required=True)
    slug = db.StringProperty(required=True)
    document_cloud_id = db.IntegerProperty(required=True)
    short_url = db.LinkProperty(required=False)
    related_url = db.TextProperty(required=False)
    description = db.TextProperty(required=False)
    byline = db.TextProperty(required=False)
    is_published = db.BooleanProperty(required=True)
    tags = db.StringListProperty(required=True)
    
    def __unicode__(self):
        return self.title
    
    def __repr__(self):
        return '<Project: %s>' % self.title.encode("utf-8")
    
    def get_absolute_url(self):
        return u'/%s/' % self.slug
    
    def get_rss_url(self):
        return u'/feeds/projects/%s/' % self.slug
    
    def extended_description(self):
        """
        Returns the path to the object's extended description, if it exists.
        """
        from django.template.loader import get_template, TemplateDoesNotExist
        path = 'documents/extended_descriptions/projects/%s.html' % self.slug
        try:
            template = get_template(path)
            return path
        except TemplateDoesNotExist:
            return None


class Document(db.Model):
    """
    A document hosted on DocumentCloud.
    """
    title = db.StringProperty(required=True)
    slug = db.StringProperty(required=True)
    document_cloud_id = db.StringProperty(required=True)
    related_url = db.TextProperty(required=False)
    byline = db.TextProperty(required=False)
    publication_date = db.DateProperty(required=True)
    order_in_project = db.IntegerProperty(required=False)
    description = db.TextProperty(required=False)
    is_published = db.BooleanProperty(required=True)
    footer = db.TextProperty(required=False)
    sources = db.TextProperty(required=False)
    credits = db.TextProperty(required=False)
    show_pdf_link = db.BooleanProperty(required=True, default=True)
    show_document_cloud_rail = db.BooleanProperty(required=True, default=True)
    similar_documents = db.ListProperty(db.Key, default=None)
    tags = db.ListProperty(db.Key, default=None)
    project = db.ReferenceProperty(Project)
    
    def __unicode__(self):
        if self.project:
            return '%s: %s' % (self.project.title, self.title)
        else:
            return self.title
    
    def __repr__(self):
        return '<Document: %s>' % self.title.encode("utf-8")
    
    def get_absolute_url(self):
        return u'/%s/' % self.slug

    def extended_description(self):
        """
        Returns the path to the object's extended description, if it exists.
        """
        from django.template.loader import get_template, TemplateDoesNotExist
        path = 'documents/extended_descriptions/documents/%s.html' % self.slug
        try:
            template = get_template(path)
            return path
        except TemplateDoesNotExist:
            return None

    def get_thumbnail_url(self):
        url = 'http://s3.documentcloud.org/documents/%(id)s/pages/%(slug)s-p1-thumbnail.gif'
        id, slug = self.document_cloud_id.split("-")[0], "-".join(self.document_cloud_id.split("-")[1:])
        return url % dict(id=id, slug=slug)
    
    def get_small_url(self):
        url = 'http://s3.documentcloud.org/documents/%(id)s/pages/%(slug)s-p1-small.gif'
        id, slug = self.document_cloud_id.split("-")[0], "-".join(self.document_cloud_id.split("-")[1:])
        return url % dict(id=id, slug=slug)
    
    def get_pdf_url(self):
        url = 'http://s3.documentcloud.org/documents/%(id)s/%(slug)s.pdf'
        id, slug = self.document_cloud_id.split("-")[0], "-".join(self.document_cloud_id.split("-")[1:])
        return url % dict(id=id, slug=slug)
    
    def get_tag_list(self):
        """
        Return all the Tag objects connected to this object.
        """
        return db.get(self.tags)
    
    def get_rendered_tag_list(self, html=True, conjunction='and'):
        """
        Return a rendered list of tags.
        
        By default a HTML link list that's ready for the table detail page.
        """
        from django.utils.text import get_text_list
        tag_list = self.get_tag_list()
        tag_list.sort(key=lambda x: x.title)
        if html:
            tag_list = ['<a href="%s">%s</a>' % (i.get_absolute_url(), i.title)
                for i in tag_list]
        else:
            tag_list = [i.title for i in tag_list]
        return get_text_list(tag_list, conjunction)
    
    def get_html_tag_list(self):
        """
        Returns an HTML link list that's ready for the table detail page.
        """
        return self.get_rendered_tag_list(html=True, conjunction='and')
    
    def get_keywords_list(self):
        """
        Returns a list of tags that ready for the META keywords tag on
        the table_detail page.
        """
        tag_list = tag_list = self.get_tag_list()
        tag_list.sort(key=lambda x: x.title)
        return ", ".join([i.title.lower() for i in tag_list])
    
    def get_similar_documents(self):
        """
        Returns a list of Keys for the documents that share tags with this object,
        ordered by the number of similar tags.
        """
        self_key = self.key()
        related_dict = {}
        # Loop through all of the tags
        for tag in self.get_tag_list():
            # Get each table that shares this tag
            doc_set = Document.all().filter('tags =', tag.key())
            for doc in doc_set:
                # Exclude this doc from the list
                this_key = doc.key()
                if this_key == self_key:
                    continue
                # If it's a different doc, increase the related count by 1
                try:
                    related_dict[this_key] += 1
                except KeyError:
                    related_dict[this_key] = 1
        # Sort it into a list ranked by the count
        related_list = related_dict.items()
        related_list.sort(key=lambda x: x[1], reverse=True)
        # Return just the keys
        return [i[0] for i in related_list]
    
    def get_similar_documents_list(self):
        """
        Get a list of the related table objects, not keys.
        """
        return db.get(self.similar_documents)


class Tag(db.Model):
    """
    A descriptive label connected to a document.
    """
    title = db.StringProperty(required=True)
    slug = db.StringProperty(required=True)
    
    def __unicode__(self):
        return self.title
    
    def __repr__(self):
        return '<Tag: %s>' % self.title.encode("utf-8")
    
    def get_absolute_url(self):
        return u'/tag/%s/page/1/' % self.slug
    





