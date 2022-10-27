import configparser
import json
import copy

from flask import Flask, request, abort ,jsonify
from linebot import (
    LineBotApi,
    WebhookHandler
)

from linebot.models import *

from linebot.exceptions import (
    InvalidSignatureError
)

import create_richMenu
import call_api

app = Flask(__name__)

# get channel secret , channel access token
config = configparser.ConfigParser()
config.read('config.ini')
channel_secret = config.get('line_bot','channel_secret')
channel_access_token = config.get('line_bot','channel_access_token')

# init
line_bot_api = LineBotApi(channel_access_token)
handler =WebhookHandler(channel_secret)

#range of sensor data 
health_low = 80
temperature_low = 25
temperature_high = 40
humidity_low = 70

#where the user target 
farm_id = 1
block_id = 1
small_block_id = 1


#callback by line platform 
@app.route("/callback", methods=['POST'])
def callback():

    #check if it is send by line platform
    signature = request.headers['X-Line-Signature']
    #content ,type = string 
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        #according to event type ,call different handlers 
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

#get the note and user data ,when get this uri
@app.route("/warning_note",methods=["POST"])
def warning_note():
    
    body = request.get_json()
    push_warning_note_to_user(body)
    
    return 'OK'


@app.errorhandler(Exception)
def error_handle(e):

    return  "Error"



#follow event 
@handler.add(FollowEvent)
def handle_follow(event):

    #api create_rich_menu preprocessing
    before_login_rich_menu = json.load(open('rich_menu/json/before_login_rich_menu.json','r',encoding='utf-8'))
    areas = create_richMenu.get_areas(before_login_rich_menu)
    #create before-login rich menu
    create_before_login_rich_menu = create_richMenu.create_object(before_login_rich_menu,areas)
    #call create rich menu api ,then return rich menu id
    before_login_rich_menu_id = line_bot_api.create_rich_menu(rich_menu=create_before_login_rich_menu)
    #set image 
    with open('rich_menu/before_login.jpg','rb') as f:
        line_bot_api.set_rich_menu_image(before_login_rich_menu_id,'image/jpeg',f)
    
    #set before_login rich menu is default
    line_bot_api.set_default_rich_menu(before_login_rich_menu_id)

#unfollow event
@handler.add(UnfollowEvent)
def handle_unfollow(event):

    lineId=event.source.user_id
    userInfo = call_api.get_userInfo_by_lineId(lineId)
    userId = userInfo["id"]
    accessToken = userInfo["accessToken"]

    #change the lineId to none,represents the user hasn't following the lineBot
    call_api.update_by_lineId(userId ,"none" , accessToken)

#reply result of account link  ,when type is accountLink
@handler.add(AccountLinkEvent)
def handle_accountLink(event):
    link_result = event.link.result
    if link_result == 'ok':


        #api create_rich_menu preprocessing
        after_login_rich_menu = json.load(open('rich_menu/json/after_login_rich_menu.json','r',encoding='utf-8'))
        areas = create_richMenu.get_areas(after_login_rich_menu)
        #create after-login rich menu
        create_after_login_rich_menu = create_richMenu.create_object(after_login_rich_menu,areas)
        #call create rich menu api ,then return rich menu id
        after_login_rich_menu_id = line_bot_api.create_rich_menu(rich_menu=create_after_login_rich_menu)
        #set image 
        with open('rich_menu/after_login.jpg','rb') as f:
            line_bot_api.set_rich_menu_image(after_login_rich_menu_id,'image/jpeg',f)
        #change to after_login.jpg
        line_bot_api.link_rich_menu_to_user(event.source.user_id,after_login_rich_menu_id )
        
        userId = event.link.nonce.split("|")[0]
        accessToken = event.link.nonce.split("|")[1] 
        #update lineId
        call_api.update_by_lineId(userId,event.source.user_id,accessToken)

        line_bot_api.reply_message(event.reply_token,TextSendMessage("綁定成功"))
    else :
        line_bot_api.reply_message(event.reply_token,TextSendMessage("綁定失敗"))


#reply Message ,when type is message 
@handler.add(MessageEvent,message = TextMessage)
def handle_message(event):
    
    message = event.message.text
    lineId = event.source.user_id
    userInfo = call_api.get_userInfo_by_lineId(lineId)
    if userInfo !="":
        accessToken = userInfo["accessToken"]
        userId = userInfo["id"]
    
    global small_block_id 
    global  block_id
    
    #account linking 
    if "綁定帳號" in message: 

        # if return "" ,represent user hasn't following the lineBot
        if call_api.get_userInfo_by_lineId(lineId) =="":

            try:
                link_token_response = line_bot_api.issue_link_token(lineId)
                linkToken= json.loads(str(link_token_response))['linkToken']
                call_api.push_loginWeb_to_user(lineId,channel_access_token,linkToken)
            except LineBotApiError as e:
                print(e.error.message)
        
        else :

            try:
                line_bot_api.reply_message(event.reply_token,TextSendMessage("已經綁定帳號了"))
            except LineBotApiError as e:
                print(e.error.message)
    
    elif  "解除綁定" in message:

        try:
            line_bot_api.unlink_rich_menu_from_user(event.source.user_id )
        except LineBotApiError as e:
            print(e.error.message)

    elif "介紹產品" in message:

        try:
            line_bot_api.reply_message(event.reply_token,TextSendMessage("此官方帳號的功能為輔助農場用戶查看訊息!"))
        except LineBotApiError as e:
            print(e.error.message)

    elif "聯絡資訊" in message:

        try:
            line_bot_api.reply_message(event.reply_token,TextSendMessage(
            "e-mail : XXXXX@gmail.com\nphone: 09xxxxxxxx"))
        except LineBotApiError as e:
            print(e.error.message)
    
    elif "常見問題" in message:
        
        try:
            line_bot_api.reply_message(event.reply_token,TextSendMessage(
                "切換目標攝影機 -> \n輸入 第x溫室第Y攝影機 \n解除帳號 -> 輸入  解除綁定　\n聯絡資訊 -> 輸入  聯絡資訊 "))
        except LineBotApiError as e:
            print(e.error.message)
    
    elif "農場" in message:
        
        #load flexMessage block.json
        FlexMessage = json.load(open('flexMessage_json/block.json','r',encoding='utf-8'))

        farm_info = call_api.get_farm_by_farmId(farm_id,accessToken)
                
        #don't more than 12 
        block_amount = len(farm_info['blocks'])

        #create more flexMessage
        FlexMessage["contents"] = [ copy.deepcopy(FlexMessage["contents"][0]) for _ in range(block_amount)]
        
        #set detail
        for   block_index ,item in enumerate( FlexMessage["contents"]):
            
            #set name of block
            item["header"]["contents"][0]["text"] = farm_info["blocks"][block_index]["name"]
            item["footer"]["contents"][0]["action"]["text"] = "攝影機區塊_"+str(farm_info["blocks"][block_index]["id"])

            small_blocks_info = farm_info["blocks"][block_index]["smallBlocks"]
            
            for small_block_item in small_blocks_info:
            
                small_blocks_data = call_api.get_sensor_newest_data_by_smallBlockId(small_block_item["id"],accessToken)

                health_data = blockArea_set_sensor_condition(small_blocks_data["healthDatas"])
                humidity_data = blockArea_set_sensor_condition(small_blocks_data["humidityDatas"])
                temperature_data = blockArea_set_sensor_condition(small_blocks_data["temperatureDatas"])

                #set condition
                status =  False
                if health_data !=None :
                    status = status  or (float(health_data) < health_low)
                    
                if humidity_data != None:
                    status = status  or (float(humidity_data) < humidity_low )
            
                if  temperature_data != None :
                    status = status or (float(temperature_data) <  temperature_low  or float(temperature_data) >  temperature_high) 
            
                if status:
                    item["body"]["contents"][0]["contents"][0]["text"] = "異常"
                    item["body"]["contents"][0]["contents"][0]["color"] = "#ff0000"
        
        try:
            line_bot_api.reply_message(event.reply_token,FlexSendMessage("切換溫室",FlexMessage))
        except LineBotApiError as e:
            print(e.error.message)

    elif "攝影機區塊" in message:
        
        #set block id
        if len(message.split("_")) > 1:
            block_id = message.split("_")[1] 
        
        #load flexMessage small_block.json
        FlexMessage = json.load(open('flexMessage_json/small_block.json','r',encoding='utf-8'))
    
        #get all small block information 
        block_info = call_api.get_block_by_blockId(block_id,accessToken)

        #amount of small block 
        small_block_amount = len(block_info["smallBlocks"]) if len(block_info["smallBlocks"]) < 12 else 12
        
        #create flexMessage
        FlexMessage["contents"] = [ copy.deepcopy(FlexMessage["contents"][0]) for _ in range(small_block_amount)]

        #set detail
        for   small_block_index ,item in enumerate( FlexMessage["contents"]):
            
            #set name of greenhouse
            item["header"]["contents"][0]["text"] = block_info["smallBlocks"][small_block_index]["name"]
            item["footer"]["contents"][0]["action"]["text"] = "感測器_"+str(block_info["smallBlocks"][small_block_index]["id"])
            
            #get sensor data 
            small_blocks_data = call_api.get_sensor_newest_data_by_smallBlockId(block_info["smallBlocks"][small_block_index]["id"],accessToken)

            #set value condition 
            health_data = smallBlockArea_set_sensor_condition(small_blocks_data["healthDatas"],FlexMessage , small_block_index  ,0)
            humidity_data = smallBlockArea_set_sensor_condition(small_blocks_data["humidityDatas"],FlexMessage , small_block_index ,1)
            temperature_data = smallBlockArea_set_sensor_condition(small_blocks_data["temperatureDatas"],FlexMessage , small_block_index  ,2)

            if health_data != None :
                if float(health_data) < health_low:
                    item["body"]["contents"][0]["contents"][1]['color'] ="#ff0000"
            if humidity_data != None :
                if float(humidity_data) < humidity_low:
                    item["body"]["contents"][1]["contents"][1]['color'] ="#ff0000"
            if temperature_data != None:
                if float(temperature_data) < temperature_low or float(temperature_data) > temperature_high:
                    item["body"]["contents"][2]["contents"][1]['color'] ="#ff0000"

        try:
            line_bot_api.reply_message(event.reply_token,FlexSendMessage("切換攝影機",FlexMessage))
        except LineBotApiError as e:
            print(e.error.message)

    elif "感測器" in message:

        #set small_block id
        if len(message.split("_")) > 1:
            small_block_id = message.split("_")[1] 
        
        block_id = call_api.get_sensor_newest_data_by_smallBlockId(small_block_id,accessToken)["blockId"]

        #load flexMessage sensor.json
        FlexMessage = json.load(open('flexMessage_json/sensor.json','r',encoding='utf-8'))
        
        #get sensor data 
        small_blocks_data = call_api.get_sensor_newest_data_by_smallBlockId(small_block_id,accessToken)
        
        #set value condition 
        health_data = sensorArea_set_sensor_condition(small_blocks_data["healthDatas"],FlexMessage , 0)
        humidity_data = sensorArea_set_sensor_condition(small_blocks_data["humidityDatas"],FlexMessage , 1)
        temperature_data = sensorArea_set_sensor_condition(small_blocks_data["temperatureDatas"],FlexMessage , 2 )
    
        #check value out of range
        if health_data != None :
            if float(health_data) < health_low:
                sensorArea_value_is_abnormal(FlexMessage,0)
                FlexMessage["contents"][0]["header"]["contents"][2]["contents"][0]["width"]=f"{health_data}%"
        if humidity_data != None :
            if float(humidity_data) < humidity_low:
                sensorArea_value_is_abnormal(FlexMessage,1)
                FlexMessage["contents"][1]["header"]["contents"][2]["contents"][0]["width"]=f"{humidity_data}%"
        if temperature_data != None :
            if float(temperature_data) < temperature_low or float(temperature_data) > temperature_high:
                sensorArea_value_is_abnormal(FlexMessage,2)
                FlexMessage["contents"][2]["header"]["contents"][2]["contents"][0]["width"]=f"{temperature_data}%"
        
        set_progress_bar(FlexMessage, health_data,0)
        set_progress_bar(FlexMessage, humidity_data,1)
        set_progress_bar(FlexMessage, temperature_data,2)

        amount_sensor = 3
        for idx in range (amount_sensor):
            FlexMessage["contents"][idx]["footer"]["contents"][0]["action"]["uri"]=f"http://114.33.145.3/#/sp/{small_block_id}?{farm_id}&{userId}&{accessToken}"

        
        print(FlexMessage["contents"][0]["footer"]["contents"][0]["action"]["uri"])
        #get block name and smallBlock name
        block_name = call_api.get_block_by_blockId(block_id,accessToken)["name"]
        small_block_name = small_blocks_data["name"]
        place =  f"{block_name} {small_block_name} 感測器資料:"

        #reply multiple message
        reply_arr=[TextSendMessage(place),FlexSendMessage('Sensor Data',FlexMessage)]

        try:
            line_bot_api.reply_message(event.reply_token,reply_arr)
        except LineBotApiError as e:
            print(e.error.message)

    elif "訊息欄" in message:

        FlexMessage =json.load(open('flexMessage_json/note.json','r',encoding='utf-8'))
        all_noteInfo = call_api.get_all_noteInfo(accessToken)
        
        for idx in range(len(all_noteInfo)-1,len(all_noteInfo)-3,-1):
        
            FlexMessage["contents"][0]["body"]["contents"][idx]["contents"][0]["text"] = all_noteInfo[idx]["title"]
            
            if all_noteInfo[idx]["icon"] == "1":
                FlexMessage["contents"][0]["body"]["contents"][idx]["contents"][0]["color"]="#ff0000"

            FlexMessage["contents"][0]["body"]["contents"][idx]["contents"][1]["contents"][0]["contents"][0]["text"] = all_noteInfo[idx]["comment"]
            FlexMessage["contents"][0]["body"]["contents"][idx]["contents"][1]["contents"][0]["contents"][1]["text"] = all_noteInfo[idx]["updatedAt"]
        try:
            line_bot_api.reply_message(
                event.reply_token,FlexSendMessage("訊息欄",FlexMessage))
        except LineBotApiError as e:
            print(e.error.message)

    elif "即時影像" in message:
        
        block_name = call_api.get_block_by_blockId(block_id,accessToken)["name"]
        small_block_name = call_api.get_sensor_newest_data_by_smallBlockId(small_block_id,accessToken)["name"]
        
        FlexMessage =json.load(open('flexMessage_json/live_stream.json','r',encoding='utf-8'))
        FlexMessage["body"]["contents"][1]["contents"][0]["contents"][0]["text"]=f"{block_name} {small_block_name}"
        FlexMessage["footer"]["contents"][0]["action"]["uri"] = f"http://114.33.145.3/#/sp/{small_block_id}?{farm_id}&{userId}&{accessToken}"
        print(FlexMessage["footer"]["contents"][0]["action"]["uri"] )
        try:
            line_bot_api.reply_message(
                event.reply_token,FlexSendMessage("即時影像",FlexMessage))
        except LineBotApiError as e:
            print(e.error.message)
    else :
        
        try:
            line_bot_api.reply_message(event.reply_token,TextSendMessage("準備中...")) 
        except LineBotApiError as e:
            print(e.error.message)

def set_progress_bar(FlexMessage ,data,idx):

    if data == None :
        FlexMessage["contents"][idx]["header"]["contents"][2]["contents"][0]["width"]="0%"
    else :
        FlexMessage["contents"][idx]["header"]["contents"][2]["contents"][0]["width"]=f"{data}%"




def blockArea_set_sensor_condition(data_list):

    if len(data_list) == 0:
        sensor_value = None
    else :
        value  = data_list[0]["value"]

        if float(value) != -1.0 :
            sensor_value = value
        else :
            sensor_value = None
    return  sensor_value

def smallBlockArea_set_sensor_condition(data_list , FlexMessage ,idx_1,idx_2 ):
    
    if len(data_list) == 0 :        
        sensor_value= None
    else :
        value  = data_list[0]["value"]

        if float(value) != -1.0 :
            sensor_value = value
            FlexMessage['contents'][idx_1]['body']['contents'][idx_2]['contents'][1]['text'] =str(sensor_value)+ ("%" if idx_2 != 2 else "°C")
            return  sensor_value
        else :
            sensor_value = None

    smallBlockArea_value_is_none(FlexMessage,idx_1,idx_2)
    
    return  sensor_value


def smallBlockArea_value_is_none(FlexMessage,idx_1,idx_2):

    FlexMessage['contents'][idx_1]['body']['contents'][idx_2]["contents"][1]['text'] =str(None)
    FlexMessage['contents'][idx_1]['body']['contents'][idx_2]["contents"][1]['color'] ="#8C8C8C"


def sensorArea_set_sensor_condition(data_list , FlexMessage ,idx ):
    
    if len(data_list) == 0 :        
        sensor_value= None
    else :
        value  = data_list[0]["value"]

        if float(value) != -1.0 :
            sensor_value = value
            FlexMessage['contents'][idx]['header']['contents'][1]['text'] =str(sensor_value)+ ("%" if idx != 2 else "°C")
            return  sensor_value
        else :
            sensor_value = None

    sensorArea_value_is_none(FlexMessage,idx)
    
    return  sensor_value


def sensorArea_value_is_abnormal(FlexMessage,idx):
    
    FlexMessage['contents'][idx]['body']['contents'][0]["contents"][0]['text'] ="狀況異常"
    FlexMessage['contents'][idx]['body']['contents'][0]["contents"][0]['color'] ="#ff0000"

def sensorArea_value_is_none(FlexMessage,idx):

    FlexMessage['contents'][idx]['header']['contents'][1]['text'] =str(None)
    FlexMessage['contents'][idx]['body']['contents'][0]["contents"][0]['text'] ="無資料"
    FlexMessage['contents'][idx]['body']['contents'][0]["contents"][0]['color'] ="#8C8C8C"


def push_warning_note_to_user(body):
    
    all_user_lineId_and_userId = body["farm"]["users"]
    noteInfo = body["note"]
    
    note_content = noteInfo["comment"].split("，")
    
    FlexMessage = json.load(open('flexMessage_json/warning_note.json','r',encoding='utf-8'))
    block_place =noteInfo["smallBlock"]["block"]["name"]
    small_block_place = noteInfo["smallBlock"]["name"]
    place = f"位於{block_place} {small_block_place}"
    FlexMessage["body"]["contents"][1]["contents"][0]["contents"][0]["text"] = note_content[0]
    FlexMessage["body"]["contents"][1]["contents"][0]["contents"][1]["text"] = place
    FlexMessage["body"]["contents"][1]["contents"][0]["contents"][2]["text"] = note_content[1][3:]
    FlexMessage["body"]["contents"][1]["contents"][0]["contents"][3]["text"] = note_content[2]
    FlexMessage["body"]["contents"][1]["contents"][0]["contents"][4]["text"] = note_content[3]
    FlexMessage["body"]["contents"][1]["contents"][0]["contents"][5]["text"] = noteInfo["updatedAt"]
    
    for item in all_user_lineId_and_userId :
        
        item["LINE_ID"] ="Ub1afb95bbb313d55b5f02749d68a86d6"

        if item["LINE_ID"]!= "null":
            
            lineId = item["LINE_ID"]
            userId = item["id"]
            accessToken = call_api.get_userInfo_by_lineId(lineId)
            FlexMessage["footer"]["contents"][0]["uri"] = f"http://114.33.145.3/#/sp/{small_block_id}?{farm_id}&{userId}&{accessToken}"
            
            try:
                #line_bot_api.push_message(lineId, FlexSendMessage("緊急通知",FlexMessage))
                line_bot_api.push_message("Ub1afb95bbb313d55b5f02749d68a86d6", FlexSendMessage("緊急通知",FlexMessage))
                break
            except LineBotApiError as e:
                print(e.error.message)



if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)