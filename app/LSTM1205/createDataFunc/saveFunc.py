import sys


# PARAMをファイルに書き込む
def saveParam(SAVE_PATH, PARAM):
    with open("%s/PARAM.txt" % SAVE_PATH, "a") as f1:
        f1.write("{}\n{}\n{}\n".format(
            PARAM["input"], PARAM["output"], PARAM["len_t"]))


# TRAIN_LISTを学習用データとしてファイルに書き込む
def saveTrainList(SAVE_PATH, TRAIN_LIST, END_TURN):
    with open("%s/TRAIN_DATA.txt" % SAVE_PATH, "a") as f1:
        for turn, val in TRAIN_LIST.items():
            f1.write(str(val).replace(" ", "").replace(
                "[", "").replace("]", ""))
            if int(turn) != (END_TURN):
                f1.write("[")
        f1.write("\n")
    # sys.exit()


# ターン情報をファイルに書き込む
def saveTurnInfo(SAVE_PATH, START_TURN, END_TURN):
    with open("{}/PARAM.txt".format(SAVE_PATH), "a") as f1:
        f1.write("{}-{}\n".format(START_TURN, END_TURN))


# LABEL_LISTをファイルに書き込む
def saveLabelList(SAVE_PATH, LABEL_LIST):
    with open("%s/WOLF_LABEL_DATA.txt" % SAVE_PATH, "a") as f1:
        # print("{}".format(LABEL_LIST["WEREWOLF"]))
        f1.write("{}\n".format(LABEL_LIST["WEREWOLF"]))
    with open("%s/SEER_LABEL_DATA.txt" % SAVE_PATH, "a") as f1:
        # print("{}".format(LABEL_LIST["SEER"]))
        f1.write("{}\n".format(LABEL_LIST["SEER"]))
    with open("%s/POSS_LABEL_DATA.txt" % SAVE_PATH, "a") as f1:
        # print("{}".format(LABEL_LIST["POSSESSED"]))
        f1.write("{}\n".format(LABEL_LIST["POSSESSED"]))


# FEATURE_LISTをファイルに書き込む
def saveFeatureList(SAVE_PATH, FEATURE_LIST):
    with open("%s/PARAM.txt" % SAVE_PATH, "a") as f1:
        f1.write("\n")
        for feature, val in FEATURE_LIST.items():
            if val[0]:
                if type(val[1]) == dict:
                    for key, val2 in val[1].items():
                        if val2[0]:
                            if type(val2[1]) == dict:
                                for key3, val3 in val2[1].items():
                                    if val3[0]:
                                        f1.write("{}:{}[{}][{}]\n".format(
                                            val3[1][key], feature, key, key3))
                            else:
                                f1.write("{}:{}[{}]\n".format(
                                    val2[1], feature, key))
                else:
                    f1.write("{}:{}\n".format(val[1], feature))
