from canvasapi import Canvas

# Canvas API Key
api_key = ''
# Canvas URL e.g. https://example.instructure.com
api_url = 'https://webcourses2c.test.instructure.com'

course_id = 1346257
canvas = Canvas(api_url, api_key)
course = canvas.get_course(course_id)


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