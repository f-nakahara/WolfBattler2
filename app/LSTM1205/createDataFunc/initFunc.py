import sys


# 保存先ファイルの中身を初期化する
def initFile(SAVE_PATH):
    print("保存場所：" + SAVE_PATH)
    with open("%s/TRAIN_DATA.txt" % SAVE_PATH, "w") as f1:
        f1.write("")
    with open("%s/WOLF_LABEL_DATA.txt" % SAVE_PATH, "w") as f2:
        f2.write("")
    with open("%s/SEER_LABEL_DATA.txt" % SAVE_PATH, "w") as f2:
        f2.write("")
    with open("%s/POSS_LABEL_DATA.txt" % SAVE_PATH, "w") as f2:
        f2.write("")
    with open("%s/PARAM.txt" % SAVE_PATH, "w") as f2:
        f2.write("")


# INFO内の情報をプレイヤーの数や特徴量の数に合わせて初期化する
def initInfo(PLAY_NUM, FEATUER_NUM):
    INFO = {}
    for p in range(1, PLAY_NUM+1):
        INFO[str(p)] = []
        for j in range(FEATUER_NUM):
            INFO[str(p)].append(0)
    return INFO


# 使用するターン数に合わせてLSTM_INFOを初期化する
def initLstmInfo(DAY_NUM, START_TURN, END_TURN, PLAY_NUM, FEATUER_NUM):
    LSTM_INFO = {}
    for day in range(1, DAY_NUM+1):
        LSTM_INFO[str(day)] = {}
        for turn in range(START_TURN, END_TURN):
            LSTM_INFO[str(day)][str(turn)] = {}
            for p in range(1, PLAY_NUM+1):
                LSTM_INFO[str(day)][str(turn)][str(p)] = []
                for j in range(FEATUER_NUM):
                    LSTM_INFO[str(day)][str(turn)][str(
                        p)].append(-1)  # 超過部分用といて-1で初期化する
    # print(LSTM_INFO["1"].keys())
    # print(LSTM_INFO["2"].keys())
    # sys.exit()
    return LSTM_INFO


# TALK_HISTORYの初期化
def initTalkHistroy(DAY_NUM):
    TALK_HISTORY = {}
    for day in range(1, DAY_NUM + 1):
        TALK_HISTORY[str(day)] = {}
    # print(TALK_HISTORY)
    # sys.exit()
    return TALK_HISTORY


# AGREE_PLAYERの初期化
def initAgreePlayer(PLAY_NUM):
    AGREE_PLAYER = {}
    for p in range(1, PLAY_NUM + 1):
        AGREE_PLAYER[str(p)] = []
    # print(AGREE_PLAYER)
    # sys.exit()
    return AGREE_PLAYER


# DISAGREE_PLATERの初期化
def initDisagreePlayer(PLAY_NUM):
    DISAGREE_PLAYER = {}
    for p in range(1, PLAY_NUM + 1):
        DISAGREE_PLAYER[str(p)] = []
    # print(DISAGREE_PLAYER)
    # sys.exit()
    return DISAGREE_PLAYER


# VOTE_PLAYERの初期化
def initVotePlayer(PLAY_NUM):
    VOTE_PLAYER = {}
    for p in range(1, PLAY_NUM + 1):
        VOTE_PLAYER[str(p)] = {"TARGET": None, "RUN": False}
    # print(VOTE_PLAYER)
    # sys.exit()
    return VOTE_PLAYER


# ESTIMATE_PLAYERの初期化
def initEstimatePlayer(ESTIMATE_ROLE, PLAY_NUM):
    ESTIMATE_PLAYER = {}
    for p in range(1, PLAY_NUM + 1):
        ESTIMATE_PLAYER[str(p)] = {}
        for role, val in ESTIMATE_ROLE.items():
            if val[0]:
                ESTIMATE_PLAYER[str(p)][role] = []
    # print(ESTIMATE_PLAYER)
    # sys.exit()
    return ESTIMATE_PLAYER


# DIVINED_PLAYERの初期化
def initDivinedPlayer(DIVINED_ROLE, PLAY_NUM):
    DIVINED_PLAYER = {}
    for p in range(1, PLAY_NUM + 1):
        DIVINED_PLAYER[str(p)] = {}
        for role, val in DIVINED_ROLE.items():
            if val[0]:
                DIVINED_PLAYER[str(p)][role] = []
    # print(DIVINED_PLAYER)
    # sys.exit()
    return DIVINED_PLAYER


# TRAIN_LISTを初期化する
def initTrainList(START_TURN, END_TURN):
    """
    [[0ターン目],
     [1ターン目],
     [0ターン目(2日目)] 
     [1ターン目(2日目)]]
    """
    TRAIN_LIST = {}
    for turn in range(START_TURN, END_TURN):
        TRAIN_LIST[str(turn)] = []
    # print(TRAIN_LIST)
    # sys.exit()
    return TRAIN_LIST

# predictListの初期化


def initPredictList(DAY_NUM, START_TURN, END_TURN):
    roles = ["WOLF", "SEER", "POSS"]
    predictList = {}
    for day in range(1, DAY_NUM+1):
        predictList[str(day)] = {}
        for turn in range(START_TURN, END_TURN):
            predictList[str(day)][str(turn)] = {}
            for role in roles:
                predictList[str(day)][str(turn)][role] = 0
        # print(predictList)
        # sys.exit()
        predictList[str(day)]["vote"] = {}
        predictList[str(day)]["divine"] = {}
        predictList[str(day)]["attack"] = {}
        for role in roles:
            predictList[str(day)]["vote"][role] = 0
            predictList[str(day)]["divine"][role] = 0
            predictList[str(day)]["attack"][role] = 0
    return predictList
