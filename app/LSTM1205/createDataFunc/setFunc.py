import sys
import glob
import os
import shutil


# ログフォルダ内の全ファイル名をFILE_LISTに格納
def setLogPath(PLAY_NUM, YEAR):
    LOG_PATH = glob.glob(
        sys.path[0] + "/../data/log/{}/{}/*".format(PLAY_NUM, YEAR))
    return LOG_PATH


# 「START_TURN-END_TURN」フォルダを作成する
# SAVE_PATHをセットする
def setSavePath(PLAY_NUM, YEAR, TYPE, FOLDER_NAME, START_TURN, END_TURN):
    SAVE_PATH = sys.path[0] + "/../data/train/{}/{}/{}/{}/{}/{}".format(
        PLAY_NUM, YEAR, TYPE, FOLDER_NAME, START_TURN, END_TURN)
    if not os.path.exists(SAVE_PATH):
        os.makedirs(SAVE_PATH)
    else:
        shutil.rmtree(SAVE_PATH)

    return SAVE_PATH


# 学習データ用にLSTM_INFO内の値をTRAIN_LISTに格納する
def setTrainList(LSTM_INFO, TRAIN_LIST, START_TURN):
    turn = START_TURN  # ターン用
    for lstm_info in LSTM_INFO.values():  # {"ターン":{}}
        for info in lstm_info.values():     # {"プレイヤー":[]}
            for val in info.values():
                for i in val:
                    TRAIN_LIST[str(turn)].append(i)
            turn += 1


# 各特徴量を入れる配列の添字を振り分ける
def setSubscript(FEATURE_LIST):
    ref_num = 0
    for feature, val in FEATURE_LIST.items():
        if val[0]:
            if type(val[1]) == dict:
                for feature2, val2 in val[1].items():
                    if val2[0]:
                        if type(val2[1]) == dict:
                            for role, j in val2[1].items():
                                if j[0]:
                                    j[1][feature2] = ref_num
                                    ref_num += 1
                        else:
                            val2[1] = ref_num
                            ref_num += 1
            else:
                val[1] = ref_num
                ref_num += 1


# ROLE辞書に特徴名を追加
def setRoleFeature(feature, role):
    for val in role.values():
        if val[0]:
            val[1][feature] = None
    # print(DIVINED_ROLE)


# トーク履歴を追加する
def setTalkHistroy(text, TALK_HISTROY):
    remark = text[5].split()
    idx = text[4]  # 発言したプレイヤー番号
    idt = text[2]  # トークのID
    day = text[0]  # 日にち
    TALK_HISTROY[day][idt] = int(idx)


# 使用する特徴量の数を計算
def setFeatureNum(FEATURE_LIST):
    count = 0
    for val in FEATURE_LIST.values():
        if val[0]:
            if type(val[1]) == dict:
                for feature, i in val[1].items():
                    if i[0]:
                        if type(i[1]) == dict:
                            setRoleFeature(feature, i[1])
                            for j in i[1].values():
                                if j[0]:
                                    count += 1
                        else:
                            count += 1
            else:
                count += 1
    # print(FEATUER_NUM)
    return count


# PARAMに値を格納
def setParam(PARAM, FEATUER_NUM, PLAY_NUM, START_TURN, END_TURN, DAY_NUM):
    PARAM["input"] = FEATUER_NUM * PLAY_NUM
    PARAM["output"] = PLAY_NUM
    PARAM["len_t"] = (END_TURN - START_TURN + 1) * DAY_NUM
    # print(PARAM)
    # sys.exit()


# NOT_INFOにプレイヤー番号と-1を書き込む
def setNotInfo(PLAY_NUM, FEATUER_NUM, NOT_INFO):
    for p in range(1, PLAY_NUM+1):
        NOT_INFO[str(p)] = []
        for j in range(FEATUER_NUM):
            NOT_INFO[str(p)].append(-1)
