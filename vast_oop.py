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
        return (syllabus.syllabus_body, url)


class AnnouncementService(ResourceProvider):
    def get_resources(self):
        announcements = course.get_discussion_topics(only_announcements=True)
        content = []
        for announcement in announcements:
            content.append((announcement.message, announcement.html_url))
        return content
        

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
            content.append((course.get_page(page.url), page.html_url))
        return content


RESOURCES = [
    SyllabusService(enabled = True),
    AnnouncementService(enabled = False),
    ModuleService(enabled = False),
    AssignmentService(enabled = False),
    DiscussionService(enabled = False),
    PageService(enabled = False)
]

for resource in RESOURCES:
    content = resource.fetch()
    # media, success = resource.parse()
    import pdb; pdb.set_trace()
