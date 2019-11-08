
from bs4 import BeautifulSoup
from canvasapi import Canvas
from collections import namedtuple
from pprint import pprint
import re
import requests

# Canvas API Key
api_key = '1158~CElid5nGPo5n2kgLujNn8NQaO8XaR35Zb2ZQvaJX9UaArbIGaEYqF5Mc44X3JvcN'
# Canvas URL e.g. https://example.instructure.com
api_url = 'https://webcourses2c.test.instructure.com'

course_id = 1346257
canvas = Canvas(api_url, api_key)
course = canvas.get_course(course_id)

youtube_playlist_pattern = r'[?&]list=([^#\&\?\s]+)'  # noqa
youtube_pattern = r'(?:https?:\/\/)?(?:[0-9A-Z-]+\.)?(?:youtube|youtu|youtube-nocookie)\.(?:com|be)\/(?:watch\?v=|watch\?.+&v=|embed\/|v\/|.+\?v=)?([^&=\n%\?]{11})'  # noqa
vimeo_pattern = r'(http|https)?:\/\/(www\.|player\.)?vimeo.com\/(?:channels\/(?:\w+\/)?|video\/(?:\w+\/)?|groups\/([^\/]*)\/videos\/|)(\d+)(?:|\/\?)'  # noqa
lib_media_urls = ['fod.infobase.com', 'search.alexanderstreet.com', 'kanopystreaming-com']


class ResourceProvider:
    def __init__(self, enabled=True):
        self.enabled = enabled
        
    def fetch(self):
        if not self.enabled:
            return
        
        resources = self.get_resources()
        return resources

    def get_resources(self):
        if not hasattr(self, 'function'):
            raise NotImplementedError(
                "{} requires either a definition of 'function' or an "
                "implementation of 'get_resources()'".format(self.__class__)
            )

        if hasattr(self, 'options'):
            items = self.function(**self.options)
        else:
            items = self.function()

        retrieved_data = {
            'info': [],
            'is_flat': True
        }

        for item in items:
            retrieved_data['info'].append((
                getattr(item, self.field),
                item.html_url,
            ))

        return retrieved_data


class SyllabusService(ResourceProvider):
    def get_resources(self):
        syllabus = canvas.get_course(course_id, include='syllabus_body')
        url = '{}/courses/{}/assignments/syllabus'.format(api_url, course_id)
        return {
            'info': [(syllabus.syllabus_body, url)],
            'is_flat': True
        }


class AnnouncementService(ResourceProvider):
    function = course.get_discussion_topics
    field = "message"
    options = {'only_announcements': 'True'}


class ModuleService(ResourceProvider):
    def get_resources(self):
        retrieved_data = {
            'info': [],
            'is_flat': False
        }

        modules = course.get_modules()
        for module in modules:
            for item in module.get_module_items(include='content_details'):
                if item.type == 'ExternalUrl':
                    retrieved_data['info'].append((
                        item.external_url,
                        item.html_url
                    ))
        return retrieved_data

class AssignmentService(ResourceProvider):
    function = course.get_assignments
    field = "description"


class DiscussionService(ResourceProvider):
    function = course.get_discussion_topics
    field = "message"
    

class PageService(ResourceProvider):
    def get_resources(self):
        retrieved_data = {
            'info': [],
            'is_flat': True
        }

        pages = course.get_pages()
        for page in pages:
            p = course.get_page(page.url)
            retrieved_data['info'].append((p.body, page.html_url))
        return retrieved_data

class Parser:
    def parse_content(self, content_pair, flat):
        # Check all links
        if flat:
            soup = BeautifulSoup(content_pair[0], 'html.parser')

            for elem in soup.find_all('a'):
                # Check if the link is an internal Canvas file
                file_api_endpoint = elem.get('data-api-endpoint')
                if file_api_endpoint:
                    no_check.append({
                        'type': 'internal file',
                        'link_loc': content_pair[1],
                        'media_loc': file_api_endpoint
                    })

                # instructure inline media comment
                inline_media = elem.get('data-media_comment_type')
                if inline_media:
                    no_check.append({
                        'type': '{} media comment'.format(inline_media),
                        'link_loc': content_pair[1],
                        'media_loc': 'N/A'
                    })

                # Check all other specific anchor tags ...

            for elem in soup.find_all('video'):
                no_check.append({
                        'type': 'canvas video comment',
                        'link_loc': content_pair[1],
                        'media_loc': 'N/A'
                    })

            for elem in soup.find_all('audio'):
                no_check.append({
                        'type': 'canvas audio comment',
                        'link_loc': content_pair[1],
                        'media_loc': 'N/A'
                    })

            # Check all iframe elements
            for elem in soup.find_all('iframe'):
                src = elem.get('src')
                if src:
                    check, media_type = classify(src)
                    if check:
                        to_check.append({
                            'type': media_type,
                            'link_loc': content_pair[1],
                            'media_loc': src
                        })
                    else:
                        no_check.append({
                            'type': 'external',
                            'link_loc': content_pair[1],
                            'media_loc': src
                        })
        else:
            # Otherwise not flat and just plain links in content pair to be classified
            check, media_type = classify(content_pair[0])
            if check:
                to_check.append({
                    'type': media_type,
                    'link_loc': content_pair[1],
                    'media_loc': content_pair[0]
                })
            else:
                no_check.append({
                    'type': 'external',
                    'link_loc': content_pair[1],
                    'media_loc': content_pair[0]
                })
                
        
def classify(link):
    """
    Classify the media as youtube or vimeo or other. Returns True if 
    media type allows for further checking of captions.
    """
    if re.search(youtube_playlist_pattern, link):
        return True, 'youtube_playlist'
    elif re.search(youtube_pattern, link):
        return True, 'youtube'
    elif re.search(vimeo_pattern, link):
        return True, 'vimeo'
    else:
        return False, 'external'

RESOURCES = [
    SyllabusService(enabled=True),
    AnnouncementService(enabled=True),
    ModuleService(enabled=True),
    AssignmentService(enabled=True),
    DiscussionService(enabled=True),
    PageService(enabled=True)
]

parser = Parser()

to_check = []
no_check = []

# Get all content_pairs
for resource in RESOURCES:
    retrieved_data = resource.fetch()
    data = retrieved_data['info']
    flat = retrieved_data['is_flat']
    
    for content_pair in data:
        # Each content pair represents a page, or a discussion, etc. (Whole pages) if flat
        # If not flat then each pair is simply a link and a location
        parser.parse_content(content_pair, flat)

import pdb; pdb.set_trace()

# Validate that the media links contain captions

# Generate a report with that data