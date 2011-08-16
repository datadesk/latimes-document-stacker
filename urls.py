# Copyright 2008 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django.conf.urls.defaults import *
from django.contrib.syndication.views import feed
from documents.feeds import LatestDocuments, ProjectDocumentsFeed

urlpatterns = patterns('documents.views',
    
    # The homepage
    url(r'^$', 'document_list', name='document-index'),
    
    # Pagination 
    url(r'^page/(?P<page>[0-9]+)/$', 'document_list', name='document-page'),
    
    # Tag pages
    url(r'^tag/(?P<tag>.*)/page/(?P<page>[0-9]+)/$', 'tag_page', name='tag-page'),

    # The document/project detail page
    url(r'^(?P<slug>[-\w]+)/$', 'object_detail', name='object-detail'),
    
    # RSS feeds
    url(r'^feeds/(?P<url>.*)/$', feed,
        {'feed_dict': dict(
            latest=LatestDocuments,
            projects=ProjectDocumentsFeed
            )},
        name='feeds'),
    
    # Sitemap
    url(r'^sitemap.xml$', 'sitemap', name='sitemap')
    
)

