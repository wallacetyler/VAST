
from bs4 import BeautifulSoup
from canvasapi import Canvas
from collections import namedtuple
from pprint import pprint

# Canvas API Key
api_key = ''
# Canvas URL e.g. https://example.instructure.com
api_url = 'https://webcourses2c.test.instructure.com'

course_id = 1346257
canvas = Canvas(api_url, api_key)
course = canvas.get_course(course_id)


class ResourceProvider:
    def __init__(self, enabled = True):
        self.enabled = enabled
        
    def fetch(self):
        if not self.enabled:
            return
        
        resources = self.get_resources()
        return resources

    def get_resources(self):
        if not self.function:
            raise Exception('Service has no function.')

        if hasattr(self, 'kwargs'):
            items = self.function(**self.kwargs)
        else:
            items = self.function()

        content = []
        for item in items:
            content.append((
                getattr(item, self.field),
                item.html_url
            ))

        return content


class SyllabusService(ResourceProvider):
    def get_resources(self):
        syllabus = canvas.get_course(course_id, include='syllabus_body')
        url = '{}/courses/{}/assignments/syllabus'.format(api_url, course_id)
        return [(syllabus.syllabus_body, url)]


class AnnouncementService(ResourceProvider):
    function = course.get_discussion_topics
    field = "message"
    kwargs = {'only_announcements': 'True'}


class ModuleService(ResourceProvider):
    def get_resources(self):
        modules = course.get_modules()
        content = []
        for module in modules:
            for item in module.get_module_items(include='content_details'):
                if item.type == 'ExternalUrl':
                    content.append((item.external_url, item.html_url))
        return content


class AssignmentService(ResourceProvider):
    function = course.get_assignments
    field = "description"


class DiscussionService(ResourceProvider):
    function = course.get_discussion_topics
    field = "message"
    

class PageService(ResourceProvider):
    def get_resources(self):
        pages = course.get_pages()
        content = []
        for page in pages:
            p = course.get_page(page.url)
            content.append((p.body, page.html_url))
        return content

class Parser:
    def csv_writer(self, *args):
        pprint(args)
        print('------------------------------------------')
        # write to csv

    def parse_content(self, tuple):
        soup = BeautifulSoup(tuple[0], 'html.parser')
        # Collect all hrefs from any anchor tag
        for link in soup.find_all('a'):
            # Check if the link is an internal Canvas file
            if link.has_attr('data-api-endpoint'):
                file_id = link.get('data-api-endpoint')
                file = course.get_file(file_id.split('/')[-1])
                self.csv_writer(
                    'Course file: {}'.format(file.display_name),
                    'No captioning data found',
                    '',
                    '{}'.format(tuple[1])
                )

    def media_check(self, link):
        pass
        

        #   - Check for linked media files (data-api-endpoint)
        #   - Check for youtube link
        #   - Check for vimeo link
        #   - Check for any library links
        #   - Check for iframe media
        #   - Check for embedded video
        #   - Check for embedded audio

RESOURCES = [
    SyllabusService(enabled = False),
    AnnouncementService(enabled = False),
    ModuleService(enabled = False),
    AssignmentService(enabled = False),
    DiscussionService(enabled = False),
    PageService(enabled = True)
]

parser = Parser()

for resource in RESOURCES:
    content = resource.fetch()

    if content is not None:
        for tuple in content:
            parser.parse_content(tuple)

    # media, success = resource.parse(
