
from bs4 import BeautifulSoup
from pprint import pprint
import re
import requests

from resources import SyllabusService, AnnouncementService, ModuleService, AssignmentService, DiscussionService, PageService

youtube_api_key = ''
youtube_playlist_pattern = r'[?&]list=([^#\&\?\s]+)'  # noqa
youtube_pattern = r'(?:https?:\/\/)?(?:[0-9A-Z-]+\.)?(?:youtube|youtu|youtube-nocookie)\.(?:com|be)\/(?:watch\?v=|watch\?.+&v=|embed\/|v\/|.+\?v=)?([^&=\n%\?]{11})'  # noqa
vimeo_pattern = r'(http|https)?:\/\/(www\.|player\.)?vimeo.com\/(?:channels\/(?:\w+\/)?|video\/(?:\w+\/)?|groups\/([^\/]*)\/videos\/|)(\d+)(?:|\/\?)'  # noqa
vimeo_access_token = ''
lib_media_urls = ['fod.infobase.com', 'search.alexanderstreet.com', 'kanopystreaming-com']

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
                    check, media_type = self.classify(src)
                    if check:
                        to_check.append({
                            'type': media_type,
                            'link_loc': content_pair[1],
                            'media_loc': src,
                            'captions': []
                        })
                    else:
                        no_check.append({
                            'type': 'external',
                            'link_loc': content_pair[1],
                            'media_loc': src
                        })
        else:
            # Otherwise not flat and just plain links in content pair to be classified
            check, media_type = self.classify(content_pair[0])
            if check:
                to_check.append({
                    'type': media_type,
                    'link_loc': content_pair[1],
                    'media_loc': content_pair[0],
                    'captions': []
                })
            else:
                no_check.append({
                    'type': 'external',
                    'link_loc': content_pair[1],
                    'media_loc': content_pair[0]
                })
                
    def classify(self, link):
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

# Validate that the media links contain captions
for link in to_check:
    if link['type'] == 'youtube':
        match = re.search(youtube_pattern, link['media_loc'])
        video_id = match.group(1)
        r = requests.get(
            'https://www.googleapis.com/youtube/v3/captions?part=snippet&videoId={}&key={}'
            .format(video_id, youtube_api_key)
        )

        if r.status_code == 404:
            link['captions'].append('Improper link to video')
            continue

        response = r.json()

        try:
            for item in response['items']:
                if item['snippet']['language'] == 'en':
                    if item['snippet']['trackKind'] == 'ASR':
                        link['captions'].append('automated english')
                    if item['snippet']['trackKind'] == 'standard':
                        link['captions'].append('english')
                elif item['snippet']['language']:
                    link['captions'].append(item['snippet']['language'])
        except:
            print('Passing because of no items in response')
        
    if link['type'] == 'vimeo':
        match = re.search(vimeo_pattern, link['media_loc'])
        video_id = match.group(4)
        r = requests.get(
            'https://api.vimeo.com/videos/{}/texttracks'.format(video_id),
            headers={'Authorization': 'bearer {}'.format(vimeo_access_token)}
        )

        if r.status_code == 404:
            link['captions'].append('Improper link to video')
            continue

        response = r.json()
        
        try:
            for item in response['data']:
                if item['language'] == 'en':
                    link['captions'].append('english')
                elif item['language']:
                    link['captions'].append(item['language'])
        except:
            pass


import pdb; pdb.set_trace()
# Generate a report with that data