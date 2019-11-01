from canvasapi import Canvas
from pprint import pprint


# Canvas API Key
api_key = ''
# Canvas URL e.g. https://example.instructure.com
api_url = 'https://webcourses2c.test.instructure.com'

course_id = 1334463
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

class PageService(ResourceProvider):
    def get_resources(self):
        pages = course.get_pages()
        return pages

RESOURCES = [
    PageService(get_function = course.get_pages(), enabled = False)
]
"""
Resources in Canvas:
- Pages
- Assignments
- Announcements
- Discussions
- Syllabus
- Modules
"""
class Resource:
    def __init__(self, id, full_url, content=None):
        self.id = id
        self.full_url = full_url
        self.content = content

class Page(Resource):
    def __init__(self, id, full_url, content=None, url=None):
        self.url = url
        Resource.__init__(self, id, full_url, content=None)

    def get_content(self):
        self.content = course.get_page(self.url)

class Assignment(Resource):
    def get_content(self):
        pass

class Announcement(Resource):
    def get_content(self):
        pass

class Discussion(Resource):
    def get_content(self):
        pass

class Module_Item(Resource):
    def get_content(self):
        pass

class Syllabus(Resource):
    def get_content(self):
        pass

"""
Parser must be able to detect:
- 
"""
class Parser():
    

resources = []

def fetch_content():
    syllabus = canvas.get_course(course_id, include='syllabus_body')
    full_url = '{}/courses/{}/assignments/syllabus'.format(api_url, course_id)
    s = Syllabus(syllabus.id, full_url, syllabus.syllabus_body)
    resources.append(s)

    modules = course.get_modules()
    for module in modules:
        for item in module.get_module_items(include='content_details'):
            if item.type == 'ExternalUrl':
                i = Module_Item(item.id, item.html_url, item.external_url)
                resources.append(i)

    for page in course.get_pages():
        p = Page(page.page_id, page.html_url, None, page.url)
        resources.append(p)

    for assignment in course.get_assignments():
        a = Assignment(assignment.id, assignment.html_url, assignment.description)
        resources.append(a)

    for announcement in course.get_discussion_topics(only_announcements=True):
        a = Announcement(announcement.id, announcement.html_url, announcement.message)
        resources.append(a)

    for discussion in course.get_discussion_topics():
        d = Discussion(discussion.id, discussion.html_url, discussion.message)
        resources.append(d)

fetch_content()

for resource in resources:
    resource.get_content()
    media, success = parser.parse_content(resource.content)

    if success:
        print(resource.full_url)

import pdb; pdb.set_trace()
