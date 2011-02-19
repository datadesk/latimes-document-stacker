# -*- coding: utf-8 -*-
# Response helpers
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.views.generic.simple import direct_to_template

# Models
from models import Document, Project, Tag

# Cache
from google.appengine.api import memcache

# Pagination
from django.core.paginator import Paginator
from django.core.paginator import  InvalidPage, EmptyPage

# Pinging
import logging
import random
from google.appengine.api import urlfetch
from google.appengine.api.labs import taskqueue

# Etc.
import datetime

#
# Caching, grouping and the like
#

def get_cached_response(request, cache_key):
    """
    Returns a cached response, if one exists. Returns None if it doesn't.
    
    Provide your request object and the cache_key.
    """
    # Hit the cache and see if it already has this key
    cached_data = memcache.get(cache_key)
    # If it does, return the cached data (unless we force a reload with the qs)
    if cached_data is not None and not request.GET.get('force', None):
        return cached_data

#
# List pages
#

def document_list(request, page=1):
    """
    Displays document lists, 10 at a time.
    """
    cache_key = 'document_page:%s' % page
    cached_response = get_cached_response(request, cache_key)
    if cached_response:
        return cached_response
    else:
        # Pull the documents
        object_list = Document.all().filter(
                "is_published =", True
            ).order("-publication_date")
        # Cut it first 10
        paginator = Paginator(object_list, 10)
        try:
            page = paginator.page(page)
        except (EmptyPage, InvalidPage):
            raise Http404
        # Create the response
        context = {
            'headline': 'Latest Documents',
            'object_list': page.object_list,
            'page_number': page.number,
            'has_next': page.has_next(),
            'next_page_number': page.next_page_number(),
        }
        response = direct_to_template(request, 'document_list.html', context)
        # Add it to the cache
        memcache.add(cache_key, response, 60)
        # Pass it back
        return response

#
# Detail pages
#

def object_detail(request, slug):
    """
    Serves the detail page for both project and document detail pages.
    
    Tries to find the slug among projects first, and then fallsback to 
    documents.
    """
    # First see if a project exists for this slug
    project_response = project_detail(request, slug)
    if project_response:
        return project_response
    else:
        return document_detail(request, slug)


def project_detail(request, slug):
    """
    A project detail page with a list of documents.
    """
    cache_key = 'project_detail:%s' % slug
    cached_response = get_cached_response(request, cache_key)
    if cached_response:
        return cached_response
    else:
        # Pull the object
        obj = Project.get_by_key_name(slug)
        if not obj:
            # Return None so it can move along and look for matching document
            return None
        context = {
            'object': obj,
            'document_list': obj.document_set.filter("is_published =", True).order("-publication_date").order("order_in_project"),
        }
        response = direct_to_template(request, 'documents/project_detail.html', context)
        memcache.add(cache_key, response, 60)
        return response


def document_detail(request, slug):
    """
    The detail page laying out one of our Document objects.
    """
    cache_key = 'document_detail:%s' % slug
    cached_response = get_cached_response(request, cache_key)
    if cached_response:
        return cached_response
    else:
        # Pull the object
        obj = Document.get_by_key_name(slug)
        if not obj or not obj.is_published:
            # Drop out if it doesn't
            raise Http404
        context = {
            'object': obj,
        }
        response = direct_to_template(request, 'documents/document_detail.html', context)
        memcache.add(cache_key, response, 60)
        return response


def tag_page(request, tag, page):
    """
    Lists documents with a certain tag.
    """
    # Check if the page is cached
    cache_key = 'tag_page:%s-%s' % (tag, page)
    cached_response = get_cached_response(request, cache_key)
    if cached_response:
        return cached_response
    # Get the data
    tag = Tag.get_by_key_name(tag)
    if not tag:
        raise Http404
    object_list = Document.all().filter('tags =', tag.key()).filter("is_published =", True)
    paginator = Paginator(object_list, 15)
    # Limit it to thise page
    try:
        page = paginator.page(page)
    except (EmptyPage, InvalidPage):
        raise Http404
    # Create a response and pass it back
    context = {
        'headline': 'Documents tagged &lsquo;%s&rsquo;' % tag.title,
        'object_list': group_objects_by_number(page.object_list),
        'page_number': page.number,
        'has_next': page.has_next(),
        'next_page_number': page.next_page_number(),
    }
    return direct_to_template(request, 'documents/tag_detail.html', context)


def sitemap(request):
    """
    A sitemap for Google.
    """
    document_list = Document.all().filter("is_published =", True).order("-publication_date")
    project_list = Project.all().filter("is_published =", True)
    context = {
        'document_list': document_list,
        'project_list': project_list,
    }
    return direct_to_template(request, 'sitemap.xml', context, mimetype='text/xml')


