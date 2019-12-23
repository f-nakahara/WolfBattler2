#!/usr/bin/env python
from __future__ import print_function, division

# this is main script
# simple version

from app.LSTM1205.aiwolfpy import contentbuilder as cb
import random
import numpy as np
import keras
import os
import sys
from keras.models import model_from_json
from app.LSTM1205.createDataFunc import saveFunc, setFunc, initFunc, phaseFunc, talk
from keras.backend import tensorflow_backend as backend
import copy
import tensorflow as tf

myname = 'LSTM1205'


class Agent(object):

    def __init__(self, agent_name):
        # myname
        self.graph = tf.get_default_graph()

        self.myname = agent_name
        PATH = os.getcwd()

        """
        # 村人行動決定モデル
        self.vill_action_model = model_from_json(open(
            "%s/model/action/VILL_model.json" % PATH).read())
        self.vill_action_model.load_weights(
            "%s/model/action/VILL_weights.h5" % PATH)
        self.vill_action_model._make_predict_function()

        # 占い師行動決定モデル
        self.seer_action_model = model_from_json(open(
            "%s/model/action/SEER_model.json" % PATH).read())
        self.seer_action_model.load_weights(
            "%s/model/action/SEER_weights.h5" % PATH)
        self.seer_action_model._make_predict_function()
        """
        """
        学習データ作成に関する設定
        """
        self.PLAY_NUM = 5    # プレイヤーの人数 5 or 15
        self.START_TURN = 0  # 何ターン目から取得するか（1日の中で）
        self.END_TURN = 19   # 何ターン目まで取得するか（1日の中で）
        self.DAY_NUM = 2  # 何日目まで取得するか

        """
        予測時に扱うデータ
        """
        self.INFO = {}   # 各プレイヤーの特徴量 {"プレイヤー番号" : [特徴量1, 特徴量2 ...]}
        self.NOT_INFO = {}   # 超過分用  {"プレイヤー番号":[-1,-1,....,-1]}
        self.LSTM_INFO = {}   # 日にちとターンごとにINFOをまとめたもの {"self.DAY":{"ターン" : self.INFO}}
        # self.LABEL_LIST = {"SEER": None, "POSSESSED": None,
        #                    "WEREWOLF": None}   # ラベルデータ用の情報 {"役職" : プレイヤー番号}
        self.LABEL_LIST = {"WOLF": None, "SEER": None, "POSS": None}
        self.TRAIN_LIST = {}  # 訓練データ用の情報 {"ターン":[全プレイヤーの特徴量]}
        self.ACTION_LIST = {"VOTE": 0, "ESTIMATE": 1,
                            "COMINGOUT": 2, "DIVINED": 3, "OTHER": 4}
        self.ACTION_LIST = {"0": "VOTE", "1": "ESTIMATE",
                            "2": "COMINGOUT", "3": "DIVINED", "4": "OTHER"}

        """
        COMINGOUT関連
        OPTION:{"役職":[使用可否,添え字番号]}
        """

        self.COMINGOUT_OPTION = {"VILLAGER": [False, None], "SEER": [True, None],
                                 "POSSESSED": [True, None], "WEREWOLF": [True, None], "BODYGUARD": [False, None], "MEDIUM": [False, None]}
        """
        ESTIMATE関連
        ROLE:{"役職":[使用可否,{OPTION名:添字番号}]}
        OPTION:{"OPTION名":[使用可否,ESTIMATE_ROLE参照]}
        PLAYER:{"プレイヤー番号":{"役職":[推定先プレイヤー番号...]}}
        """
        self.ESTIMATE_ROLE = {"VILLAGER": [True, {}], "SEER": [True, {}],  # {"役職" : [使用可否, 添字番号]}
                              "POSSESSED": [False, {}], "WEREWOLF": [True, {}], "BODYGURD": [False, {}], "MEDIUM": [False, {}]}
        self.ESTIMATE_OPTION = {"ACTIVE": [True, self.ESTIMATE_ROLE],
                                "PASSIVE": [True, self.ESTIMATE_ROLE]}  # ACTIVE:ROLEと推定したプレイヤーの人数 PASSIVE:自分をROLEと推定したプレイヤーの数
        self.ESTIMATE_PLAYER = {}

        """
        DIVINED関連
        ROLE:{"役職":[使用可否,{OPTION名:添字番号}]}
        OPTION:{"OPTION名":[使用可否,DIVINED_ROLE参照]}
        PLAYER:{"プレイヤー番号":{"役職":[占ったプレイヤー番号...]}}
        """
        self.DIVINED_ROLE = {"HUMAN": [True, {}], "WEREWOLF": [True, {}]}
        self.DIVINED_OPTION = {"ACTIVE": [True, self.DIVINED_ROLE],
                               "PASSIVE": [True, self.DIVINED_ROLE]}  # ACTIVE:ROLEと判定したプレイヤーの数 PASSIVE:自分をROLEと判定したプレイヤーの数
        self.DIVINED_PLAYER = {}

        """
        VOTE関連
        OPTION:{"オプション":[使用可否,添字番号]}
        PLAYER:{"プレイヤー番号":{"TARGET":投票予定先のプレイヤー番号, "RUN":投票を実行したか}}
        """
        self.VOTE_OPTION = {"ACTIVE": [True, None], "PASSIVE": [
            True, None], "RESULT": [False, None], "CHANGE": [True, None]}  # ACTIVE:投票予定先のプレイヤー番号 PASSIVE:自分に投票しようと思ってるプレイヤーの数 RESULT:実際に投票したプレイヤー番号 CHANGE:ACTIVEとRESULTが異なった数
        self.VOTE_PLAYER = {}

        """
        AGREE, DISAGREE関連
        OPTION:{"オプション":[使用可否,添字番号]}
        PLAYER:{"プレイヤー番号":[トーク番号...]}
        TALK_HISTROY:{"トーク番号":発言したプレイヤー}
        """
        self.AGREE_OPTION = {"ACTIVE": [True, None], "PASSIVE": [True, None]}
        self.DISAGREE_OPTION = {"ACTIVE": [
            True, None], "PASSIVE": [True, None]}
        self.AGREE_PLAYER = {}
        self.DISAGREE_PLAYER = {}
        self.TALK_HISTORY = {}

        # 使用する特徴リスト
        self.FEATURE_LIST = {"DAY": [True, None], "STATUS": [True, None], "VOTE": [True, self.VOTE_OPTION], "ESTIMATE": [True, self.ESTIMATE_OPTION],    # {"発言" : [使用可否, 添字番号]}
                             "COMINGOUT": [True, self.COMINGOUT_OPTION], "DIVINED": [True, self.DIVINED_OPTION], "AGREE": [False, self.AGREE_OPTION], "DISAGREE": [False, self.DISAGREE_OPTION]}
        self.FEATUER_NUM = 0    # 特徴量の数

        # 人狼推定モデル
        self.wolf_model = model_from_json(open(
            "%s/app/LSTM1205/model/%d/%d/WOLF_model.json" % (PATH, self.START_TURN, self.END_TURN)).read())
        self.wolf_model.load_weights(
            "%s/app/LSTM1205/model/%d/%d/WOLF_weights.h5" % (PATH, self.START_TURN, self.END_TURN))
        self.wolf_model._make_predict_function()

        # 占い師推定モデル
        self.seer_model = model_from_json(open(
            "%s/app/LSTM1205/model/%d/%d/SEER_model.json" % (PATH, self.START_TURN, self.END_TURN)).read())
        self.seer_model.load_weights(
            "%s/app/LSTM1205/model/%d/%d/SEER_weights.h5" % (PATH, self.START_TURN, self.END_TURN))
        self.seer_model._make_predict_function()

        # 狂人推定モデル
        self.poss_model = model_from_json(open(
            "%s/app/LSTM1205/model/%d/%d/POSS_model.json" % (PATH, self.START_TURN, self.END_TURN)).read())
        self.poss_model.load_weights(
            "%s/app/LSTM1205/model/%d/%d/POSS_weights.h5" % (PATH, self.START_TURN, self.END_TURN))
        self.poss_model._make_predict_function()
        """
        変数の基本設定
        """
        self.FEATUER_NUM = setFunc.setFeatureNum(self.FEATURE_LIST)
        setFunc.setSubscript(self.FEATURE_LIST)
        setFunc.setNotInfo(self.PLAY_NUM, self.FEATUER_NUM, self.NOT_INFO)

        """
        各役職ごとの合計推定数
        各役職ごとの推定的中数
        """
        self.totalPredictNum = initFunc.initPredictList(
            self.DAY_NUM, self.START_TURN, self.END_TURN+1)   # {"DAY":{"ターン":{"役職":合計推定数}}}
        self.totalCorrectNum = initFunc.initPredictList(
            self.DAY_NUM, self.START_TURN, self.END_TURN+1)   # {"DAY":{"ターン":{"役職":合計的中数}}}

    def getName(self):
        return self.myname

    def initialize(self, base_info, diff_data, game_setting):
        self.base_info = base_info
        self.game_setting = game_setting
        """
        updateInfo等で使用する変数
        """
        self.DAY = "0"       # 日にち管理用
        self.NOW_TURN = "0"  # ターン管理用

        """
        予測用変数の初期化
        """
        self.INFO = initFunc.initInfo(self.PLAY_NUM, self.FEATUER_NUM)
        self.LSTM_INFO = initFunc.initLstmInfo(self.DAY_NUM, self.START_TURN, self.END_TURN+1,
                                               self.PLAY_NUM, self.FEATUER_NUM)
        self.VOTE_PLAYER = initFunc.initVotePlayer(self.PLAY_NUM)
        self.ESTIMATE_PLAYER = initFunc.initEstimatePlayer(
            self.ESTIMATE_ROLE, self.PLAY_NUM)
        self.DIVINED_PLAYER = initFunc.initDivinedPlayer(
            self.DIVINED_ROLE, self.PLAY_NUM)
        self.TALK_HISTORY = initFunc.initTalkHistroy(self.DAY_NUM)
        self.AGREE_PLAYER = initFunc.initAgreePlayer(self.PLAY_NUM)
        self.DISAGREE_PLAYER = initFunc.initDisagreePlayer(self.PLAY_NUM)
        """
        推定精度計算用
        """
        self.predictList = initFunc.initPredictList(
            self.DAY_NUM, self.START_TURN, self.END_TURN+1)   # {"DAY":{"ターン":{"役職":プレイヤー番号}}}

        """
        基本データ
        """

        self.idx = base_info["agentId"]    # 自分のAgentID
        self.role = base_info["myRole"]  # 自分の役職
        self.target = ""    # 投票先
        self.AliveList = []  # 生きてる人だけのリスト
        self.estimate = False   # 前のターンにestimateしたか
        self.comingout = ""  # カミングアウト
        self.report = False  # 占い結果報告
        self.BlackList = []  # 人狼確定リスト
        self.DivinedList = []  # 占い済みリスト
        self.team = ""  # 仲間のid
        self.turn = -1  # ターン計算用
        self.divined = ""   # 占い結果の内容

    def update(self, base_info, diff_data, request):
        if request == "DAILY_INITIALIZE":
            self.DAY = str(base_info["day"])    # 日にちの更新
            self.NOW_TURN = "0"  # ターンの初期化
            # INFOの日にち部分を更新
            for p in base_info["statusMap"].keys():
                text = ["", "", "", "", p]
                phaseFunc.status(text, self.FEATURE_LIST, self.INFO,
                                 self.LABEL_LIST, self.VOTE_PLAYER, self.DAY)
            # 生きてる人だけAliveListに格納
            for p, state in base_info["statusMap"].items():
                if state == "ALIVE":
                    if int(p) in self.AliveList or int(p) == self.idx:
                        pass
                    else:
                        self.AliveList.append(int(p))
                else:
                    if p in self.AliveList:
                        self.AliveList.remove(int(p))
        # データがある場合、updateInfoの実行
        if len(diff_data) != 0:
            texts = diff_data
            for text in texts:
                text = list(map(str, text))
                print(text)
                # 占い結果の保存
                if text[1] == "divine":
                    self.divined = text[5]
                    # 黒確定の保存
                    if "WEREWOLF" in text[5]:
                        self.BlackList.append(int(text[4]))
                # 役職の保存
                if request == "FINISH":
                    roles = ["WOLF", "SEER", "POSS"]
                    for role in roles:
                        if role in text[5]:
                            self.LABEL_LIST[role] = int(text[4])
                self.updateInfo(text)

    def dayStart(self):
        self.report = False
        return None

    def talk(self):
        if int(self.DAY) >= 1 and int(self.NOW_TURN) <= self.END_TURN and int(self.NOW_TURN) >= self.START_TURN:
            # print(self.INFO)
            # print("トーク{}".format(self.NOW_TURN))
            self.recordPredict("talk")
        self.turn += 1  # ターンを進める
        # 村人
        if self.role == "VILLAGER":
            # 2ターン目以降
            if self.turn >= 2:
                # 前のターンにestimate
                if self.estimate:
                    self.estimate = False
                    return cb.vote(self.target)
                else:
                    targets = self.wolfPredict()
                    for target in targets:
                        # 死んでたら
                        if not target in self.AliveList:
                            pass
                        else:
                            # targetの値と異なる
                            if self.target != target:
                                self.target = target
                                self.estimate = True
                                return cb.estimate(target, "WEREWOLF")
                            else:
                                return cb.skip()
            else:
                return cb.skip()
        # 占い師
        elif self.role == "SEER":
            # カミングアウト済
            if self.comingout != "":
                # 占い結果報告済
                if self.report:
                    # BlackListが空
                    if len(self.BlackList) == 0:
                        # 前のターンにestimate
                        if self.estimate:
                            self.estimate = False
                            return cb.vote(self.target)
                        else:
                            targets = self.wolfPredict()
                            for target in targets:
                                # 死んでいる or DivinedListに含まれている
                                if not target in self.AliveList or target in self.DivinedList:
                                    pass
                                else:
                                    # targetの値と異なる
                                    if target != self.target:
                                        self.target = target
                                        self.estimate = True
                                        return cb.estimate(target, "WEREWOLF")
                                    else:
                                        return cb.skip()
                    else:
                        if self.estimate:
                            self.estimate = False
                            self.target = self.BlackList[-1]
                            return cb.vote(self.BlackList[-1])
                        else:
                            posses = self.possPredict()
                            for poss in posses:
                                if poss in self.BlackList or poss == self.idx:
                                    pass
                                else:
                                    self.estimate = True
                                    return cb.estimate(poss, "POSSESSED")
                else:
                    self.report = True
                    return self.divined
            else:
                self.comingout = "SEER"
                return cb.comingout(self.idx, self.comingout)
        # 狂人
        elif self.role == "POSSESSED":
            # 1日目
            if self.DAY == "1":
                # カミングアウト済
                if self.comingout != "":
                    # 偽占い結果報告済
                    if self.report:
                        # 前のターンにestimate
                        if self.estimate:
                            self.estimate = False
                            return cb.vote(self.target)
                        else:
                            targets = self.seerPredict()
                            for target in targets:
                                # teamと同じ
                                if target == self.team or not target in self.AliveList:
                                    pass
                                else:
                                    # targetと異なる
                                    if self.target != target:
                                        self.target = target
                                        self.estimate = True
                                        return cb.estimate(target, "WEREWOLF")
                                    else:
                                        return cb.skip()
                    else:
                        self.report = True
                        targets = self.wolfPredict()
                        for target in targets:
                            if not target in self.AliveList:
                                pass
                            else:
                                self.team = target
                                return cb.divined(target, "HUMAN")
                else:
                    self.comingout = "SEER"
                    return cb.comingout(self.idx, self.comingout)
            else:
                # 0ターン目
                if self.turn == 0:
                    self.comingout = "POSSESSED"
                    return cb.comingout(self.idx, self.comingout)
                else:
                    targets = self.wolfPredict()
                    for team in targets:
                        # 死んでいる
                        if not team in self.AliveList:
                            pass
                        else:
                            for target in self.AliveList:
                                if team != target:
                                    # 1ターン目 or 結果と違うプレイヤーとtargetが異なる
                                    if self.turn == 1 or target != self.target:
                                        self.target = target
                                        return cb.vote(target)
                                    else:
                                        return cb.skip()
                                else:
                                    pass
        # 人狼
        elif self.role == "WEREWOLF":
            # 1日目
            if self.DAY == "1":
                # 2ターン目以降
                if self.turn >= 2:
                    # 前のターンにestimate
                    if self.estimate:
                        self.estimate = False
                        return cb.vote(self.target)
                    else:
                        targets = self.seerPredict()
                        for target in targets:
                            if not target in self.AliveList:
                                pass
                            else:
                                # targetと異なる
                                if target != self.target:
                                    self.target = target
                                    self.estimate = True
                                    return cb.estimate(target, "WEREWOLF")
                                else:
                                    return cb.skip()
                else:
                    return cb.skip()
            else:
                # 0ターン目
                if self.turn == 0:
                    team = self.possPredict()[0]
                    # 死んでいる
                    if not team in self.AliveList:
                        target = random.choice(self.AliveList)
                        self.target = target
                        self.estimate = True
                        return cb.estimate(target, "WEREWOLF")
                    else:
                        self.team = team
                        for target in self.AliveList:
                            if target != team:
                                self.target = target
                                self.comingout = "WEREWOLF"
                                return cb.comingout(self.idx, self.comingout)
                            else:
                                pass
                else:
                    # 前のターンにestimate
                    if self.estimate:
                        self.estimate = False
                        return cb.vote(self.target)
                    else:
                        self.estimate = True
                        return cb.estimate(self.target, "WEREWOLF")

    def whisper(self):
        return cb.over()

    def vote(self):
        self.recordPredict("vote")
        return self.target

    def attack(self):
        self.recordPredict("attack")
        target = self.seerPredict()[0]
        # 死んでる
        if not target in self.AliveList:
            teams = self.possPredict()
            for team in teams:
                # 死んでる
                if not team in self.AliveList:
                    pass
                else:
                    for target in self.AliveList:
                        if target != team:
                            return target
                        else:
                            pass
        else:
            return target

    def divine(self):
        # 0日目
        if self.DAY == "0":
            target = random.choice(self.AliveList)
            self.DivinedList.append(target)
            return target
        else:
            self.recordPredict("divine")
            targets = self.wolfPredict()
            for target in targets:
                # DivinedListに含まれている or 死んでいる
                if target in self.DivinedList or not target in self.AliveList:
                    pass
                else:
                    self.DivinedList.append(target)
                    return target

    def guard(self):
        return self.base_info['agentIdx']

    def finish(self):
        self.checkPredict()
        self.printValues()
        self.clearBackend()
        return None
    # INFOの更新

    def updateInfo(self, text):
        if text[1] == "talk" and int(self.NOW_TURN) <= self.END_TURN and int(self.DAY) <= self.DAY_NUM:
            if int(self.NOW_TURN) >= self.START_TURN:
                self.updateLstmInfo(text)
                remark = text[5].split()
                remark_type = remark[0]  # 発言の種類
                setFunc.setTalkHistroy(text, self.TALK_HISTORY)
                if remark_type == "AGREE":
                    talk.agree(text, self.FEATURE_LIST, self.INFO,
                               self.TALK_HISTORY, self.AGREE_PLAYER)
                elif remark_type == "DISAGREE":
                    talk.disagree(text, self.FEATURE_LIST, self.INFO,
                                  self.TALK_HISTORY, self.DISAGREE_PLAYER)
                elif "VOTE" in text[5]:
                    talk.vote(text, self.INFO, self.FEATURE_LIST,
                              self.VOTE_OPTION, self.VOTE_PLAYER)
                elif "ESTIMATE" in text[5]:
                    talk.estimate(text, self.INFO, self.FEATURE_LIST,
                                  self.ESTIMATE_OPTION, self.ESTIMATE_PLAYER, self.ESTIMATE_ROLE)
                elif remark_type == "COMINGOUT":
                    talk.comingout(text, self.FEATURE_LIST,
                                   self.INFO, self.COMINGOUT_OPTION)
                elif remark_type == "DIVINED" or (remark_type == "DAY" and "DIVINED" in text[5]):
                    talk.divined(text, self.FEATURE_LIST, self.INFO, self.DIVINED_OPTION,
                                 self.DIVINED_PLAYER, self.DIVINED_ROLE)
                elif "REQUEST" in remark_type:
                    if "VOTE" in remark_type:
                        talk.vote(text, self.INFO, self.FEATURE_LIST,
                                  self.VOTE_OPTION, self.VOTE_PLAYER)
                        # print(self.VOTE_PLAYER)
                        # sys.exit()
            else:
                self.NOW_TURN = text[3]
        elif text[1] == "vote" and int(self.DAY) <= self.DAY_NUM:
            self.updateLstmInfo(text, True)
            phaseFunc.vote(text, self.FEATURE_LIST, self.INFO,
                           self.VOTE_OPTION, self.VOTE_PLAYER)
        elif text[1] == "execute":
            phaseFunc.execute(text, self.FEATURE_LIST, self.INFO)
        elif text[1] == "dead":
            phaseFunc.attack(text, self.FEATURE_LIST, self.INFO)

    # LSTM_INFOの更新
    # vote : 投票フェーズが判定
    def updateLstmInfo(self, text, vote=False):
        if int(self.NOW_TURN) <= self.END_TURN and int(self.NOW_TURN) >= self.START_TURN:
            if vote:
                if - 1 in self.LSTM_INFO[self.DAY][self.NOW_TURN]["1"]:
                    self.LSTM_INFO[self.DAY][self.NOW_TURN] = copy.deepcopy(
                        self.INFO)
                    for turn in range(int(self.NOW_TURN)+1, self.END_TURN+1):
                        self.LSTM_INFO[self.DAY][str(turn)] = copy.deepcopy(
                            self.NOT_INFO)  # 超過した分をNOT_INFOで補う
            elif text[3] != self.NOW_TURN and int(self.DAY) <= self.DAY_NUM:
                self.LSTM_INFO[self.DAY][self.NOW_TURN] = copy.deepcopy(
                    self.INFO)  # 前回のターン情報を書き込む
                self.NOW_TURN = text[3]
        else:
            self.NOW_TURN = text[3]

    # 変数の中身を表示する

    def printValues(self):
        # print("----------LABEL_LIST----------")
        # print(self.LABEL_LIST)
        # print("----------FEATURE_LIST----------")
        # for feature, val in self.FEATURE_LIST.items():
        #     if val[0]:
        #         if type(val[1]) == dict:
        #             for key, val2 in val[1].items():
        #                 if val2[0]:
        #                     if type(val2[1]) == dict:
        #                         for key3, val3 in val2[1].items():
        #                             if val3[0]:
        #                                 print("{}:{}[{}][{}]".format(
        #                                     val3[1][key], feature, key, key3))
        #                     else:
        #                         print("{}:{}[{}]".format(
        #                             val2[1], feature, key))
        #         else:
        #             print("{}:{}".format(val[1], feature))
        # print("----------LSTM_INFO----------")
        # for day, lstm_info in self.LSTM_INFO.items():
            # print("---{}日目---".format(day))
            # for turn, info in lstm_info.items():
            #     print("{}ターン目".format(turn))
            #     for p, feature in info.items():
            #         print("プレイヤー{}：{}".format(p, feature))
        print("----------推定精度----------")
        for day, val1 in self.totalPredictNum.items():
            print("{}日目".format(day))
            for turn, val2 in val1.items():
                print("　{}:".format(turn), end="")
                for role, val3 in val2.items():
                    if val3 != 0:
                        acc = self.totalCorrectNum[day][turn][role]/val3*100
                        print("　　{}:{}({}/{}), ".format(role, round(acc, 1),
                                                        self.totalCorrectNum[day][turn][role], val3), end="")
                    else:
                        print("　　{}:なし, ".format(role), end="")
                print()

    # 推定情報を記録する
    def recordPredict(self, phase):
        if int(self.DAY) <= self.DAY_NUM:
            wolf = self.wolfPredict()[0]
            seer = self.seerPredict()[0]
            poss = self.possPredict()[0]
            if phase == "talk":
                self.predictList[self.DAY][self.NOW_TURN]["WOLF"] = wolf
                self.predictList[self.DAY][self.NOW_TURN]["SEER"] = seer
                self.predictList[self.DAY][self.NOW_TURN]["POSS"] = poss
            elif phase == "vote":
                self.predictList[self.DAY]["vote"]["WOLF"] = wolf
                self.predictList[self.DAY]["vote"]["SEER"] = seer
                self.predictList[self.DAY]["vote"]["POSS"] = poss
            elif phase == "divine":
                self.predictList[self.DAY]["divine"]["WOLF"] = wolf
                self.predictList[self.DAY]["divine"]["SEER"] = seer
                self.predictList[self.DAY]["divine"]["POSS"] = poss
            elif phase == "attack":
                self.predictList[self.DAY]["attack"]["WOLF"] = wolf
                self.predictList[self.DAY]["attack"]["SEER"] = seer
                self.predictList[self.DAY]["attack"]["POSS"] = poss

    # 推定精度計算

    def checkPredict(self):
        for day, val1 in self.predictList.items():
            for turn, val2 in val1.items():
                for role, target in val2.items():
                    if self.predictList[day][turn][role] != 0:
                        self.totalPredictNum[day][turn][role] += 1
                    if target == self.LABEL_LIST[role]:
                        self.totalCorrectNum[day][turn][role] += 1

    # 人狼推定

    def wolfPredict(self):
        with self.graph.as_default():
            self.TRAIN_LIST = initFunc.initTrainList(self.START_TURN,
                                                     (self.END_TURN + 1) * self.DAY_NUM - self.START_TURN)
            setFunc.setTrainList(
                self.LSTM_INFO, self.TRAIN_LIST, self.START_TURN)
            X = [[]]
            for key, val in self.TRAIN_LIST.items():
                X[0].append(val)
            X = np.array(X)
            result = self.wolf_model.predict(X)[0]
            result = (np.argsort(result)[::-1])+1
            # print(result,self.NOW_TURN)
            return result

    # 占い師推定

    def seerPredict(self):
        with self.graph.as_default():
            self.TRAIN_LIST = initFunc.initTrainList(self.START_TURN,
                                                     (self.END_TURN + 1) * self.DAY_NUM - self.START_TURN)
            setFunc.setTrainList(
                self.LSTM_INFO, self.TRAIN_LIST, self.START_TURN)
            X = [[]]
            for key, val in self.TRAIN_LIST.items():
                X[0].append(val)
            X = np.array(X)
            result = self.seer_model.predict(X)[0]
            result = (np.argsort(result)[::-1])+1
            return result

    # 狂人推定

    def possPredict(self):
        with self.graph.as_default():
            self.TRAIN_LIST = initFunc.initTrainList(self.START_TURN,
                                                     (self.END_TURN + 1) * self.DAY_NUM - self.START_TURN)
            setFunc.setTrainList(
                self.LSTM_INFO, self.TRAIN_LIST, self.START_TURN)
            X = [[]]
            for key, val in self.TRAIN_LIST.items():
                X[0].append(val)
            X = np.array(X)
            result = self.poss_model.predict(X)[0]
            result = (np.argsort(result)[::-1])+1
            return result

    def clearBackend(self):
        backend.clear_session()
    """
    # 村人の行動決定

    def villAction(self):
        self.TRAIN_LIST = initFunc.initTrainList(self.START_TURN,
                                                 (self.END_TURN + 1) * self.DAY_NUM - self.START_TURN)
        setFunc.setTrainList(
            self.LSTM_INFO, self.TRAIN_LIST, self.START_TURN)
        X = [[]]
        for key, val in self.TRAIN_LIST.items():
            X[0].append(val)
        X = np.array(X)
        result = self.vill_action_model.predict(X)[0]
        result = np.argsort(result)
        action = []
        for i in result:
            action.append(self.ACTION_LIST[str(i)])
        return action

    def seerAction(self):
        self.TRAIN_LIST = initFunc.initTrainList(self.START_TURN,
                                                 (self.END_TURN + 1) * self.DAY_NUM - self.START_TURN)
        setFunc.setTrainList(
            self.LSTM_INFO, self.TRAIN_LIST, self.START_TURN)
        X = [[]]
        for key, val in self.TRAIN_LIST.items():
            X[0].append(val)
        X = np.array(X)
        result = self.seer_action_model.predict(X)[0]
        result = np.argsort(result)
        action = []
        for i in result:
            action.append(self.ACTION_LIST[str(i)])
        return action
    """


# agent = Agent(myname)


# run
if __name__ == '__main__':
    aiwolfpy.connect_parse(agent)
    pass
