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
    def __init__(self, get_function, enabled = True):
        self.get_function = get_function
        self.enabled = enabled

    def fetch(self):
        if not self.enabled:
            return
        
        resources = self.get_resources()
        return resources

    def get_resources(self):
        raise NotImplementedError


class SyllabusService(ResourceProvider):
    def get_resources(self):
        syllabus = self.get_function(course_id, include='syllabus_body')
        url = '{}/courses/{}/assignments/syllabus'.format(api_url, course_id)
        return (syllabus.syllabus_body, url)


class AnnouncementService(ResourceProvider):
    def get_resources(self):
        announcements = self.get_function(only_announcements=True)
        content = []
        for announcement in announcements:
            content.append((announcement.message, announcement.html_url))
        return content
        

class ModuleService(ResourceProvider):
    def get_resources(self):
        modules = self.get_function()
        content = []
        for module in modules:
            for item in module.get_module_items(include='content_details'):
                if item.type == 'ExternalUrl':
                    content.append((item.external_url, item.html_url))
        return content


class AssignmentService(ResourceProvider):
    def get_resources(self):
        assignments = self.get_function()
        content = []
        for assignment in assignments:
            content.append((assignment.description, assignment.html_url))
        return content


class DiscussionService(ResourceProvider):
    def get_resources(self):
        discussions = self.get_function()
        content = []
        for discussion in discussions:
            content.append((discussion.message, discussion.html_url))
        return content


class PageService(ResourceProvider):
    def get_resources(self):
        pages = self.get_function()
        content = []
        for page in pages:
            content.append((course.get_page(page.url), page.html_url))
        return content


RESOURCES = [
    SyllabusService(get_function = canvas.get_course, enabled = True),
    AnnouncementService(get_function = course.get_discussion_topics, enabled = True),
    ModuleService(get_function = course.get_modules, enabled = True),
    AssignmentService(get_function = course.get_assignments, enabled = True),
    DiscussionService(get_function = course.get_discussion_topics, enabled = True),
    PageService(get_function = course.get_pages, enabled = True)
]

for resource in RESOURCES:
    content = resource.fetch()
    media, success = resource.parse()
    import pdb; pdb.set_trace()
