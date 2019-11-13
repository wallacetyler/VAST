from pprint import pprint
import re
import requests

from resources import SyllabusService, AnnouncementService, ModuleService, AssignmentService, DiscussionService, PageService
from parser import Parser, youtube_pattern, youtube_playlist_pattern, vimeo_pattern

youtube_api_key = 'AIzaSyBVYm2Uph__TQHFzKwDjAVpYzuzWHwUBu0'
vimeo_access_token = 'daf302128e2f3819c027da680dcc982c'

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
        to_check, no_check = parser.parse_content(content_pair, flat)

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