from linebot.models import *


def get_action(action):
    if action['type'] == 'uri':
        return URIAction(type=action['type'], uri=action.get('uri'))
    elif action['type'] == 'message':
        return MessageAction(type=action['type'],text=action['text'])

def get_areas(rich_menu_json):
    return [
        RichMenuArea(
            bounds=RichMenuBounds(
                x=info['bounds']['x'],
                y=info['bounds']['y'],
                width=info['bounds']['width'],
                height=info['bounds']['height']
            ),
            action=get_action(info['action'])
        ) for info in rich_menu_json['areas']
    ]


def create_object(rich_menu_json,areas):
    return RichMenu(
        size=RichMenuSize(width=rich_menu_json['size']['width'], height=rich_menu_json['size']['height']),
        selected=rich_menu_json['selected'],
        name=rich_menu_json['name'],
        chat_bar_text=rich_menu_json['name'],
        areas=areas
    )