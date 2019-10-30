from canvasapi import Canvas
from pprint import pprint


# Canvas API Key
api_key = ''
# Canvas URL e.g. https://example.instructure.com
api_url = 'https://webcourses2c.test.instructure.com'

course_id = 1334463
canvas = Canvas(api_url, api_key)
course = canvas.get_course(course_id)

"""
Resources:
- Pages
- Assignments
- Announcements
- Discussions
- Syllabus
- Modules
"""
resources = []

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


syllabus = canvas.get_course(course_id, include='syllabus_body')

def fetch_syllabus_content():
    syllabus = canvas.get_course(course_id, include='syllabus_body')
    full_url = '{}/courses/{}/assignments/syllabus'.format(api_url, course_id)
    s = Syllabus(syllabus.id, full_url, syllabus.syllabus_body)
    resources.append(s)

def fetch_modules_content():
    modules = course.get_modules()
    for module in modules:
        for item in module.get_module_items(include='content_details'):
            if item.type == 'ExternalUrl':
                i = Module_Item(item.id, item.html_url, item.external_url)
                resources.append(i)

def fetch_page_content():
    for page in course.get_pages():
        p = Page(page.page_id, page.html_url, None, page.url)
        resources.append(p)

def fetch_assignment_content():
    for assignment in course.get_assignments():
        a = Assignment(assignment.id, assignment.html_url, assignment.description)
        resources.append(a)

def fetch_announcement_content():
    for announcement in course.get_discussion_topics(only_announcements=True):
        a = Announcement(announcement.id, announcement.html_url, announcement.message)
        resources.append(a)

def fetch_discussion_content():
    for discussion in course.get_discussion_topics():
        d = Discussion(discussion.id, discussion.html_url, discussion.message)
        resources.append(d)

fetch_syllabus_content()
fetch_modules_content()
fetch_page_content()
fetch_assignment_content()
fetch_announcement_content()
fetch_discussion_content()

for resource in resources:
    resource.get_content()

import pdb; pdb.set_trace()
