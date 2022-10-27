import json
import requests

def get_farm_by_farmId(id,accessToken):
    url = f"http://114.33.145.3/api/farms/{id}"
    headers={"Content-Type": "application/json","Authorization":f"Bearer {accessToken}"}
    data = requests.get(url=url,headers=headers)
    farm_all_data = json.loads(data.text)
    return farm_all_data

def get_block_by_blockId(id,accessToken):
    
    url = f"http://114.33.145.3/api/blocks/{id}"
    headers={"Content-Type": "application/json","Authorization":f"Bearer {accessToken}"}
    data = requests.get(url=url,headers=headers)
    small_block_all_data = json.loads(data.text)

    return small_block_all_data

def get_sensor_newest_data_by_smallBlockId(id,accessToken):
    
    url = f"http://114.33.145.3/api/smallBlocks/new/{id}"
    headers={"Content-Type": "application/json","Authorization":f"Bearer {accessToken}"}
    data = requests.get(url=url,headers=headers)
    sensor_newest_data = json.loads(data.text)

    return sensor_newest_data


def get_note_by_noteId(id,accessToken):
    
    url = f"http://114.33.145.3/api/notes/{id}"
    headers={"Content-Type": "application/json","Authorization":f"Bearer {accessToken}"}
    data = requests.get(url=url,headers=headers)
    note_info = json.loads(data.text)

    return note_info


def get_all_noteInfo(accessToken):
    url ="http://114.33.145.3/api/notes/allNotes"
    headers={"Content-Type": "application/json","Authorization":f"Bearer {accessToken}"}
    data = requests.get(url=url,headers=headers)
    all_noteInfo = json.loads(data.text)

    return all_noteInfo

def update_lineId_by_userId(userId,lineId,accessToken):
    
    url = f"http://114.33.145.3/api/users/{userId}"
    headers={"Content-Type": "application/json","Authorization":f"Bearer {accessToken}"}
    body={"LINE_ID":lineId}
    
    requests.put(url=url,headers=headers,data=json.dumps(body))
    

def update_lineSmallBlock_by_userId(userId,lineSmallBlock,accessToken):
    url = f"http://114.33.145.3/api/users/{userId}"
    headers={"Content-Type": "application/json","Authorization":f"Bearer {accessToken}"}
    body={"lineSmallBlockId":lineSmallBlock}
    
    requests.put(url=url,headers=headers,data=json.dumps(body))


def get_userInfo_by_lineId(lineId):
    
    url = f"http://114.33.145.3/api/users/line/{lineId}"
    headers={"Content-Type": "application/json"}
    data = requests.get(url=url,headers=headers)
    
    if(data.status_code != 200):
        return ""
    userInfo = json.loads(data.text)
    
    return userInfo


def get_user_choose_area_by_smallBlockId(userId,accessToken):
    
    url =f"http://114.33.145.3/api/smallBlocks/line/{userId}"
    headers={"Content-Type": "application/json","Authorization":f"Bearer {accessToken}"}
    data = requests.get(url=url,headers=headers)
    all_noteInfo = json.loads(data.text)

    return all_noteInfo
def push_loginWeb_to_user(user_id,access_token ,linkToken):
    url = "https://api.line.me/v2/bot/message/push"
    headers={"Content-Type": "application/json","Authorization":f"Bearer {access_token}"}
    data = {"to": f"{user_id}",
    "messages": [{
        "type": "template",
        "altText": "帳號連結",
        "template": {
            "type": "buttons",
            "text": "透過連結登入帳號，進行綁定",
            "actions": [{
                "type": "uri",
                "label": "點擊此處",
                "uri": f"http://114.33.145.3/#/login?linkToken={linkToken}"
            }]
        }
    }]}
    requests.post(url=url , json=data ,headers=headers)