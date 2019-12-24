from channels.generic.websocket import WebsocketConsumer
import json
from asgiref.sync import async_to_sync
import random
from threading import Thread
import time
import copy
import numpy as np
from collections import Counter
import sys
from app.LSTM1205 import LSTM1205 as CPU
import threading
import copy
from . import modelControler as mc
from app.models import Player, Room


class GameInfo():
    def __init__(self, channel_list):
        self.player_info = {}
        self.role_list = ["村人", "村人", "占い師", "狂人", "人狼"]
        self.base_info = {"myRole": None, "statusMap": {}, "day": "0", "num": 5}
        self.player_list = {}
        self.vote_list = []
        self.turn = 0
        self.vote = 0
        self.talk_id = 0
        self.dead_player = None
        self.diff_data = []
        self.cpu_list = {}
        for player_name, channel_name in channel_list.items():
            self.player_info[player_name] = {"myRole": None, "agentId": None, "status": "ALIVE", "talk": None, "vote": None, "skip": 0, "over": False,
                                             "channel": channel_name, "action": False}
        cpu_num = self.base_info["num"] - len(self.player_info)
        for i in range(1, cpu_num+1):
            cpu_name = "cpu_{}".format(i)
            k = i
            while cpu_name in self.player_info.keys():
                k += 1
                cpu_name = "cpu_{}".format(k)
            self.player_info[cpu_name] = {"myRole": None, "agentId": None, "status": "ALIVE", "talk": None, "vote": None, "skip": 0, "over": False,
                                          "channel": None, "action": False}
            self.cpu_list[cpu_name] = None


class Translator():
    role = {"村人": "VILLAGER", "占い師": "SEER", "狂人": "POSSESSED", "人狼": "WEREWOLF", "人間": "HUMAN",
            "VILLAGER": "村人", "SEER": "占い師", "POSSESSED": "狂人", "WEREWOLF": "人狼", "HUMAN": "人間"}

    def playerToCpu(self, game, text, request):
        if request == "execute":
            dead_player = game.dead_player
            agentId = game.player_info[dead_player]["agentId"]
            day = game.base_info["day"]
            typex = "execute"
            diff_data = "{} {} 0 0 {} 'Over'".format(day, typex, agentId).split()
            return diff_data
        elif request == "attack":
            dead_player = game.dead_player
            targetId = game.player_info[dead_player]["agentId"]
            day = game.base_info["day"]
            typex = "dead"
            diff_data = "{} {} 0 0 {} 'Over'".format(
                day, typex, targetId).split()
            return diff_data
        elif request == "talk":
            remark_type = text["remark_type"]
            agentId = game.player_info[text["player_name"]]["agentId"]
            talk_trans = None
            if remark_type == "カミングアウト":
                role = text["role"]
                talk_trans = "COMINGOUT Agent[{:02}] {}".format(
                    agentId, self.role[role])
            elif remark_type == "推定発言":
                target = game.player_info[text["target"]]["agentId"]
                role = text["role"]
                talk_trans = "ESTIMATE Agent[{:02}] {}".format(
                    target, self.role[role])
            elif remark_type == "投票発言":
                target = game.player_info[text["target"]]["agentId"]
                talk_trans = "VOTE Agent[{:02}]".format(target)
            elif remark_type == "占い発言":
                target = game.player_info[text["target"]]["agentId"]
                result = text["result"]
                talk_trans = "DIVINED Agent[{:02}] {}".format(
                    target, self.role[result])
            elif remark_type == "様子を見る":
                talk_trans = "Skip"
            elif remark_type == "会話を終了する":
                talk_trans = "Over"

            return talk_trans

    def cpuToPlayer(self,game,text,request):
        if request == "divine":
            targetId = text[0]
            target = text[1]
            result = "人狼" if game.player_info[target]["myRole"] == "人狼" else "人間"
            divined = "DIVINED Agent[{:02}] {}".format(
                targetId, self.role[result])
            return divined
        elif request == "talk":
            remark_type = text[0]
            player_name = text[-1]
            talk_trans = None  # text
            if remark_type != "Skip":
                game.player_info[player_name]["skip"] = 0
            if game.player_info[player_name]["over"]:
                # Over
                talk_trans = "これ以上話すことはありません。"
            elif remark_type == "COMINGOUT":
                # 私は〇です。
                role = text[2]
                talk_trans = "私は{}です。".format(self.role[role])
            elif remark_type == "ESTIMATE":
                # 〇は〇だと思います。
                targetId = int(text[1].split("[")[1].split("]")[0])
                for name, player in game.player_info.items():
                    if player["agentId"] == targetId:
                        target = name
                        role = text[2]
                        talk_trans = "{}は{}だと思います。".format(
                            target, self.role[role])
                        break
            elif remark_type == "VOTE":
                # 私は〇に投票します。
                targetId = int(text[1].split("[")[1].split("]")[0])
                for name, player in game.player_info.items():
                    if player["agentId"] == targetId:
                        target = name
                        talk_trans = "私は{}に投票します。".format(
                            target)
                        break
            elif remark_type == "DIVINED":
                # 〇を占った結果、〇でした。
                targetId = int(text[1].split("[")[1].split("]")[0])
                for name, player in game.player_info.items():
                    if player["agentId"] == targetId:
                        target = name
                        result = text[2]
                        talk_trans = "{}を占った結果、{}でした。".format(
                            target, self.role[result])
                        break
            elif remark_type == "Skip":
                # 様子を見ます。
                talk_trans = "様子を見ます。"
                game.player_info[player_name]["skip"] += 1
                if game.player_info[player_name]["skip"] >= 3:
                    game.player_info[player_name]["over"] = True
                    talk_trans = "これ以上話すことはありません。"
            elif remark_type == "Over":
                # これ以上話すことはありません。
                talk_trans = "これ以上話すことはありません。"
                game.player_info[player_name]["over"] = True
            return talk_trans


class GameMaster(WebsocketConsumer):
    sendContents = {"request": None, "type": None,
                    "player_name": None, "message": None}
    player_name = None
    game_info = {}  # {"グループ名":クラス}
    channel_list = {}   # "グループ名":{"プレイヤー名":チャンネル名}
    translator = Translator()
    cpu = CPU.Agent("cpu")

    # 接続時

    def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = "room_{}".format(self.room_id)

        # グループに追加
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()

    # 切断時
    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    # ウェブソケットからメッセージを受信時
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        request = text_data_json["request"]
        player_name = text_data_json["player_name"]
        print(text_data_json)
        # 入室、退出したとき
        if request == "connect":
            if self.room_group_name in self.channel_list.keys():
                self.channel_list[self.room_group_name][player_name] = self.channel_name
            else:
                self.channel_list[self.room_group_name] = {}
                self.channel_list[self.room_group_name][player_name] = self.channel_name
            self.player_name = player_name
            message = "{}が入室しました。".format(player_name)
            self.sendContents = {"request": request, "type": "notice",
                                 "player_name": player_name, "message": message}
            self.sendToGroup()
        elif request == "disconnect":
            message = "{}が退室しました。".format(player_name)
            self.sendContents = {"request": request, "type": "notice",
                                 "player_name": player_name, "message": message}
            self.sendToGroup()
            # del self.channel_list[self.room_group_name][player_name]
            if player_name in self.game_info[self.room_group_name].player_info:
                self.game_info[self.room_group_name].player_info[player_name]["status"] = "DEAD"
            print(self.game_info[self.room_group_name].player_info)

        # 普通のチャットモードのとき
        elif request == "normal":
            message = text_data_json["message"]
            self.sendContents = {"request": request, "type": "chat",
                                 "player_name": player_name, "message": message}
            self.sendToGroup()

        # ゲーム開始ボタンを押されたとき
        elif request == "start":
            print("チャンネルリスト\n{}".format(self.channel_list))
            self.game_info[self.room_group_name] = GameInfo(self.channel_list[self.room_group_name])
            print("ゲームリスト\n{}".format(self.game_info))
            threads = threading.Thread(target=self.main, args=[
                                       self.game_info[self.room_group_name], True])
            threads.start()

        # 役職を渡した後、占いフェーズに突入
        elif request == "initialize":
            self.initialize(self.game_info[self.room_group_name], player_name)

        # 占い先の取得
        elif request == "divine":
            target = text_data_json["target"]
            self.divine(
                self.game_info[self.room_group_name], player_name, target)
        elif request == "talk":
            self.talk(
                self.game_info[self.room_group_name], player_name, text_data_json)
        elif request == "vote":
            target = text_data_json["target"]
            self.vote(
                self.game_info[self.room_group_name], player_name, target)
        elif request == "attack":
            target = text_data_json["target"]
            self.attack(
                self.game_info[self.room_group_name], player_name, target)

    """
    メッセージ送信用メソッド
    """

    # 個人に送信
    def sendToSingle(self, channel_name):
        self.sendContents["target"] = None
        async_to_sync(self.channel_layer.send)(
            channel_name,
            {
                "type": "chat.message",
                "message": self.sendContents,
                "channel_name": channel_name
            }
        )

    # グループに送信
    def sendToGroup(self):
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'chat_message',
                "message": self.sendContents
            }
        )

    # jsに送信
    def chat_message(self, event):
        print(event)
        message = event["message"]
        self.send(text_data=json.dumps({
            "message": message
        }))

    # リクエスト送信
    def sendRequest(self, game, request):
        self.sendContents["type"] = "notice"
        self.sendContents["request"] = request
        if request == "start":
            self.startGame()
            self.sendContents["message"] = "【ゲームを開始します。】"
            self.sendToGroup()
        elif request == "divine":
            self.sendContents["message"] = "占うプレイヤーを選択してください。<br>（占い師以外は人狼だと思うプレイヤーを選択してください。）"
            player_list = []
            for player_name in game.player_info.keys():
                player_list.append(player_name)
            self.sendContents["player_list"] = json.dumps(
                player_list, ensure_ascii=False)
            self.sendToGroup()
        elif game.base_info["day"] != "0":
            if request == "daily_initialize":
                self.sendContents["message"] = "{}日目の朝が来ました。".format(
                    game.base_info["day"])
                self.sendToGroup()
                print("死亡プレイヤー：{}".format(game.dead_player))
                if game.dead_player != None:
                    self.sendContents["dead"] = game.dead_player
                    self.sendContents["message"] = "昨晩の犠牲者は{}です。".format(game.dead_player)
                else:
                    self.sendContents["message"] = "昨晩の犠牲者はいませんでした。"
                self.sendToGroup()
            elif request == "talk_start":
                self.sendContents["request"] = "talk"
                self.sendContents["message"] = "会話を開始してください。"
                self.sendToGroup()
            elif request == "talk_end":
                self.sendContents["type"] = "chat"
                self.sendContents["request"] = "talk"
                for name, player in game.player_info.items():
                    # 生存者の発言を1つずつ、全員に送信する
                    if player["status"] == "ALIVE":
                        self.sendContents["player_name"] = name
                        self.sendContents["message"] = player["talk"]
                        self.sendToGroup()
            elif request == "vote_start":
                self.sendContents["request"] = "vote"
                self.sendContents["message"] = "処刑したいプレイヤーを選択してください。"
                player_list = game.vote_list
                self.sendContents["player_list"] = json.dumps(player_list, ensure_ascii=False)
                self.sendToGroup()
            elif request == "vote_end":
                self.sendContents["request"] = "vote"
                for name, player in game.player_info.items():
                    # 生存者の発言を1つずつ、全員に送信する
                    if player["status"] == "ALIVE" or name == game.dead_player:
                        self.sendContents["player_name"] = name
                        self.sendContents["message"] = "{}が{}に投票".format(name,player["vote"])
                        self.sendToGroup()
            elif request == "execute":
                self.sendContents["dead"] = game.dead_player
                self.sendContents["message"] = "{}が処刑されました。".format(game.dead_player)
                self.sendToGroup()
            elif request == "attack":
                self.sendContents["message"] = "襲撃するプレイヤーを選択してください。<br>（人狼以外は処刑したいプレイヤーを選択してください。）"
                self.sendToGroup()
        

    def main(self, game, first=False):
        print("ゲーム開始")
        print(game.player_info)
        try:
            if first:
                self.sendRequest(game, "start")
                self.divideRole(game)
                self.initialize(game)
                self.syncWaiting(game)
            self.dayStart(game, first)
            self.sendRequest(game, "daily_initialize")
            self.dailyInitialize(game)
            self.syncWaiting(game)
            self.sendRequest(game, "talk_start")
            while game.turn <= 4 and game.base_info["day"] != "0":
                self.talk(game)
                self.syncWaiting(game)
                self.update(game, "TALK")
                self.sendRequest(game, "talk_end")
                game.turn += 1
            while game.dead_player == None and game.base_info["day"] != "0":
                self.sendRequest(game, "vote_start")
                self.vote(game)
                self.syncWaiting(game)
                self.checkDeadPlayer(game)
                self.sendRequest(game, "vote_end")
            self.update(game,"VOTE")
            self.sendRequest(game,"execute")
            self.execute(game)
            self.syncWaiting(game)
            
            if self.judgeResult(game) == None:
                self.update(game, "DAILY_INITIALIZE")
                self.sendRequest(game, "divine")
                self.divine(game)
                self.syncWaiting(game)
                self.sendRequest(game, "attack")
                self.attack(game)
                self.syncWaiting(game)
                if self.judgeResult(game) == None:
                    self.update(game,"DAILY_INITIALIZE")
                    self.main(game)
                else:
                    self.finish(game, self.judgeResult(game))
            else:
                self.finish(game, self.judgeResult(game))
        except:
            print("エラー発生！")
            game = None
            self.endGame()
            self.sendContents["type"] = "notice"
            self.sendContents["message"] = "エラーが発生しました。"
            self.sendContents["request"] = "finish"
            self.sendToGroup()
            return

    # 役職の振り分け

    def divideRole(self, game):
        random.shuffle(game.role_list)
        player_name = list(game.player_info.keys())
        for key in range(game.base_info["num"]):
            game.player_info[player_name[key]
                             ]["myRole"] = game.role_list[key]
            game.player_info[player_name[key]]["agentId"] = key+1

    # 同期待ち
    def syncWaiting(self, game):
        while not self.checkAction(game):
            time.sleep(1)
            player_list = []
            for player_name, player in game.player_info.items():
                if player["channel"] != None:
                    player_list.append(player_name)
            flag = False
            for player in player_list:
                if not player in self.channel_list[self.room_group_name].keys():
                    pass
                else:
                    flag = True
            if flag:
                print("ループ中・・・")
            else:
                game = None
                # self.resetCpu(game)
                return
        print("ループ脱出！！")
        self.initCheckAction(game)

    # 初期化
    def initialize(self, game):
        # cpu用
        def isCpu(game):
            self.cpu.clearBackend()
            for cpu_name in game.cpu_list.keys():
                # CPU.Agent()
                game.cpu_list[cpu_name] = CPU.Agent(cpu_name)
                game.base_info["myRole"] = self.translator.role[game.player_info[cpu_name]["myRole"]]
                game.base_info["agentId"] = game.player_info[cpu_name]["agentId"]
                game.cpu_list[cpu_name].initialize(
                    game.base_info, game.diff_data, None)
                game.player_info[cpu_name]["action"] = True
        threads = threading.Thread(target=isCpu, args=[game])
        threads.start()

        # 人用
        for name, player in game.player_info.items():
            game.player_list[str(player["agentId"])] = name
            if player["channel"] != None:
                self.sendContents["request"] = "initialize"
                self.sendContents["message"] = "あなたの役職は{}です。".format(
                    game.player_info[name]["myRole"])
                self.sendToSingle(player["channel"])
                game.player_info[name]["action"] = True

    # 1日スタート
    def dayStart(self, game, first):
        if first:
            pass
        else:
            game.base_info["day"] = str(int(game.base_info["day"]) + 1)

    """
    プレイヤー、CPUのターン、スキップ数など初期化
    """

    def dailyInitialize(self, game):
        def isCpu(game):
            for cpu_name, cpu in game.cpu_list.items():
                cpu.update(game.base_info, game.diff_data, "DAILY_INITIALIZE")
                game.player_info[cpu_name]["action"] = True
        game.vote_list = []
        for player_name,player in game.player_info.items():
            if player["channel"] != None:
                player["action"] = True
            player["skip"] = 0
            player["over"] = False
            player["vote"] = None
            game.final_voting = False
            game.base_info["statusMap"][str(player["agentId"])] = player["status"]
            if player["status"] == "ALIVE":
                game.vote_list.append(player_name)
        game.dead_player = None
        game.turn = 0
        threads = threading.Thread(target=isCpu, args=[game])
        threads.start()

    """
    プレイヤー、CPUのトーク制御
    """

    def talk(self, game, player_name=None, text=None):
        def isCpu(game):
            game.diff_data = []
            for cpu_name, cpu in game.cpu_list.items():
                if game.player_info[cpu_name]["status"] == "ALIVE":
                    texts = cpu.talk()
                    text = texts.split()
                    text.append(cpu_name)
                    talk_trans = self.translator.cpuToPlayer(game, text, "talk")
                    diff_data = []  # day type talk_id turn agentId text
                    day = game.base_info["day"]
                    typex = "talk"
                    turn = game.turn
                    talk_id = game.talk_id
                    agentId = game.player_info[cpu_name]["agentId"]

                    diff_data = "{} {} {} {} {}".format(
                        day, typex, talk_id, turn, agentId).split()
                    diff_data.append(texts)
                    game.diff_data.append(diff_data)
                    game.player_info[cpu_name]["talk"] = talk_trans
                    game.player_info[cpu_name]["action"] = True
        if game.base_info["day"] != "0":
            if player_name == None:
                self.sendContents["type"] = "notice"
                self.sendContents["request"] = "talk"
                self.sendContents["message"] = "【{}ターン目】".format(game.turn)
                self.sendToGroup()
                threads = threading.Thread(target=isCpu, args=[game])
                threads.start()
            else:
                if game.player_info[player_name]["status"] == "ALIVE":
                    remark_type = text["remark_type"]
                    talk_trans = None
                    if remark_type != "様子を見る":
                        game.player_info[player_name]["skip"] = 0
                    if game.player_info[player_name]["over"]:
                        # Over
                        game.player_info[player_name]["talk"] = "これ以上話すことはありません。"
                        text["remark_type"] = "会話を終了する"
                    else:
                        if remark_type == "カミングアウト":
                            # COMINGOUT agent[idx] role
                            role = text["role"]
                            game.player_info[player_name]["talk"] = "私は{}です。".format(
                                role)
                        elif remark_type == "推定発言":
                            # ESTIMATE agent[idx] role
                            target = text["target"]
                            role = text["role"]
                            game.player_info[player_name]["talk"] = "{}は{}だと思います。".format(
                                target, role)
                        elif remark_type == "投票発言":
                            # VOTE agent[idx]
                            target = text["target"]
                            game.player_info[player_name]["talk"] = "私は{}に投票します。".format(
                                target)
                        elif remark_type == "占い発言":
                            # DIVINED agent[idx] result
                            target = text["target"]
                            result = text["result"]
                            game.player_info[player_name]["talk"] = "{}を占った結果、{}でした。".format(
                                target, result)
                        elif remark_type == "様子を見る":
                            # Skip
                            game.player_info[player_name]["talk"] = "様子を見ます。"
                            game.player_info[player_name]["skip"] += 1
                            if game.player_info[player_name]["skip"] >= 3:
                                game.player_info[player_name]["talk"] = "これ以上話すことはありません。"
                                game.player_info[player_name]["over"] = True
                                text["remark_type"] = "会話を終了する"
                        elif remark_type == "会話を終了する":
                            # Over
                            game.player_info[player_name]["talk"] = "これ以上話すことはありません。"
                            game.player_info[player_name]["over"] = True

                    diff_data = []  # day type talk_id turn agentId text
                    day = game.base_info["day"]
                    typex = "talk"
                    turn = game.turn
                    talk_id = game.talk_id
                    agentId = game.player_info[player_name]["agentId"]
                    talk_trans = self.translator.playerToCpu(game,text, "talk")
                    diff_data = "{} {} {} {} {}".format(
                        day, typex, talk_id, turn, agentId).split()
                    diff_data.append(talk_trans)
                    game.diff_data.append(diff_data)
                    game.player_info[player_name]["action"] = True
        else:
            for player in game.player_info.values():
                player["action"] = True

    """
    プレイヤー、CPUの投票制御
    """

    def vote(self, game,player_name=None,target=None):
        def isCpu(game):
            for cpu_name, cpu in game.cpu_list.items():
                if game.player_info[cpu_name]["status"] == "ALIVE":
                    agentId = game.player_info[cpu_name]["agentId"]
                    targetId = cpu.vote()
                    target = game.player_list[str(targetId)]
                    game.player_info[cpu_name]["vote"] = target
                    game.player_info[cpu_name]["action"] = True
        if game.base_info["day"] != "0":
            if player_name == None:
                threads = threading.Thread(target=isCpu, args=[game])
                threads.start()
            else:
                game.player_info[player_name]["vote"] = target
                agentId = game.player_info[player_name]["agentId"]
                target = game.player_info[target]["agentId"]
                day = game.base_info["day"]
                typex = "vote"
                vote_trans = "{} {} {} {}".format(
                    day, typex, agentId, target).split()
                game.diff_data.append(vote_trans)
                game.player_info[player_name]["action"] = True
        else:
            for player in game.player_info.values():
                player["action"] = True
    
    
    def checkDeadPlayer(self,game):
        if game.base_info["day"] != "0":
            vote_list = []
            for player in game.player_info.values():
                if player["status"] == "ALIVE":
                    target = player["vote"]
                    if game.player_info[target]["status"] == "ALIVE":
                        if target in game.vote_list:
                            vote_list.append(target)
                        else:
                            target = random.choice(game.vote_list)
                            vote_list.append(target)
                            player["vote"] = target
                    else:
                        target = random.choice(game.vote_list)
                        vote_list.append(target)
                        player["vote"] = target
            
            c = Counter(vote_list)
            vote_count = 0
            dead_list = []
            game.vote_list = []
            for i in c.most_common():
                if i[1] >= vote_count:
                    vote_count = i[1]
                    game.vote_list.append(i[0])
                    dead_list.append(i[0])
            print(game.vote_list)
            if len(dead_list) == 1:
                game.dead_player = dead_list[0]
                game.player_info[dead_list[0]]["status"] = "DEAD"
                targetId = game.player_info[dead_list[0]]["agentId"]
                game.base_info["statusMap"][str(targetId)] = "DEAD"
            elif game.final_voting:
                game.dead_player = random.choice(vote_list)
                game.player_info[dead_list[0]]["status"] = "DEAD"
                targetId = game.player_info[dead_list[0]]["agentId"]
                game.base_info["statusMap"][str(targetId)] = "DEAD"
            else:
                game.final_voting = True

    """
    プレイヤー、CPUに処刑情報を送信
    """

    def execute(self, game):
        def isCpu(game):
            text = []
            game.diff_data = []
            diff_data = self.translator.playerToCpu(game, text, "execute")
            game.diff_data.append(diff_data)
            for cpu_name, cpu in game.cpu_list.items():
                game.player_info[cpu_name]["action"] = True
        if game.base_info["day"] != "0":
            threads = threading.Thread(target=isCpu, args=[game])
            threads.start()
            for player in game.player_info.values():
                if player["channel"] != None:
                    player["action"] = True
        else:
            for player in game.player_info.values():
                player["action"] = True

    def divine(self, game, player_name=None, target=None):
        def isCpu(game):
            for cpu_name, cpu in game.cpu_list.items():
                if game.player_info[cpu_name]["status"] == "ALIVE" and game.player_info[cpu_name]["myRole"] == "占い師":
                    text = []
                    agentId = str(game.player_info[cpu_name]["agentId"])
                    day = game.base_info["day"]
                    typex = "divine"
                    targetId = cpu.divine()
                    target = game.player_list[str(targetId)]
                    text.append(targetId)
                    text.append(target)
                    divined_trans = self.translator.cpuToPlayer(game,text,"divine")
                    diff_data = "{} {} {} {} {}".format(
                        day, typex, agentId, agentId, targetId).split()
                    diff_data.append(divined_trans)
                    game.diff_data.append(diff_data)
                    self.update(game,"DIVINE")
                game.player_info[cpu_name]["action"] = True
        if player_name == None:
            threads = threading.Thread(target=isCpu, args=[game])
            threads.start()
        else:
            if game.player_info[player_name]["myRole"] == "占い師":
                if game.player_info[player_name]["status"] == "ALIVE":
                    self.sendContents["type"] = "notice"
                    self.sendContents["request"] = "divine_result"
                    if game.player_info[target]["status"] == "ALIVE":
                        role = game.player_info[target]["myRole"]
                        result = "人狼" if role == "人狼" else "人間"
                        self.sendContents["message"] = "{}は{}でした。".format(
                            target, result)
                        self.sendToSingle(game.player_info[player_name]["channel"])
                    else:
                        self.sendContents["message"] = "{}は既に死亡しているため、占うことができませんでした。".format(
                            target)
                        self.sendToSingle(game.player_info[player_name]["channel"])
            game.player_info[player_name]["action"] = True

    def attack(self, game, player_name=None, target=None):
        def isCpu(game):
            game.diff_data = []
            for cpu_name, cpu in game.cpu_list.items():
                if game.player_info[cpu_name]["myRole"] == "人狼":
                    targetId = cpu.attack()
                    target = game.player_list[str(targetId)]
                    print("襲撃先：{}".format(target))
                    if game.player_info[target]["status"] == "ALIVE":
                        game.dead_player = target
                        game.player_info[target]["status"] = "DEAD"
                        game.base_info["statusMap"][str(targetId)] = "DEAD"
                        text = []
                        diff_data = self.translator.playerToCpu(game,text,"attack")
                        game.diff_data.append(diff_data)
                    else:
                        game.dead_player = None
                game.player_info[cpu_name]["action"] = True
        if game.base_info["day"] != "0":
            if player_name == None:
                threads = threading.Thread(target=isCpu, args=[game])
                threads.start()
            else:
                if game.player_info[player_name]["status"] == "ALIVE":
                    if game.player_info[player_name]["myRole"] == "人狼":
                        if game.player_info[target]["status"] == "ALIVE":
                            game.dead_player = target
                            game.player_info[target]["status"] == "DEAD"
                            targetId = game.player_info[target]["agentId"]
                            game.base_info["statusMap"][str(targetId)] = "DEAD"
                            text = []
                            diff_data = self.translator.playerToCpu(game,text,"attack")
                            game.diff_data.append(diff_data)
                        else:
                            game.dead_player = None
                    game.player_info[player_name]["action"] = True
        else:
            for player in game.player_info.values():
                player["action"] = True

    def finish(self, game, winner):
        self.endGame()
        self.sendContents["type"] = "notice"
        self.sendContents["request"] = "finish"
        self.sendContents["message"] = "{}の勝利！！".format(winner)
        self.sendToGroup()
        for cpu in game.cpu_list.values():
            cpu.clearBackend()

    def judgeResult(self, game):
        alive_role = []
        for player_name, player in game.player_info.items():
            if player["status"] == "ALIVE":
                alive_role.append(player["myRole"])
        winner = None
        if not "人狼" in alive_role:
            winner = "村陣営"
        elif len(alive_role) <= 2:
            winner = "狼陣営"

        return winner

    def update(self, game, request):
        for cpu_name, cpu in game.cpu_list.items():
            cpu.update(game.base_info, game.diff_data, request)
        game.diff_data = []

    

    # 全員が行動したか確認

    def checkAction(self, game):
        check = True
        for player in game.player_info.values():
            if not player["action"] and player["status"] == "ALIVE":
                check = False
                break
        return check

    def initCheckAction(self, game):
        for player in game.player_info.values():
            player["action"] = False
    
    # CPUのモデルリセット
    def resetCpu(self,game):
        for cpu in game.cpu_list.values():
            cpu.clearBackend()
            
    def startGame(self):
        room_name = Room.objects.filter(id=self.room_id).values()[0]["name"]
        mc.setRoomGame(room_name,True)
    
    def endGame(self):
        room_name = Room.objects.filter(id=self.room_id).values()[0]["name"]
        mc.setRoomGame(room_name, False)
