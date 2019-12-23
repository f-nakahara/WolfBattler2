import sys


# VOTE発言
def vote(text, INFO, FEATURE_LIST, VOTE_OPTION, VOTE_PLAYER):
    remark = text[5].split()  # 分割された発言内容
    target = int(text[5].split("VOTE Agent[")[1].split("]")[0])  # 発言対象のプレイヤー番号
    idx = text[4]  # 発言したプレイヤー番号
    if FEATURE_LIST["VOTE"][0]:
        if VOTE_OPTION["ACTIVE"][0]:
            sub_num = VOTE_OPTION["ACTIVE"][1]
            INFO[idx][sub_num] = target
        if VOTE_OPTION["PASSIVE"][0]:
            sub_num = VOTE_OPTION["PASSIVE"][1]
            if VOTE_PLAYER[idx]["TARGET"] != target:
                if VOTE_PLAYER[idx]["TARGET"] != None:
                    old_target = VOTE_PLAYER[idx]["TARGET"]
                    # 前の投票先のプレイヤーのVOTEDを1減らす
                    INFO[str(old_target)][sub_num] -= 1
                INFO[str(target)][sub_num] += 1  # 投票先のプレイヤーのVOTEDを1増やす
                VOTE_PLAYER[idx]["TARGET"] = target
            # print(VOTE_PLAYER)


# ESTIMATE発言
def estimate(text, INFO, FEATURE_LIST, ESTIMATE_OPTION, ESTIMATE_PLAYER, ESTIMATE_ROLE):
    remark = text[5].split("ESTIMATE Agent[")   # 分割された発言内容
    roles = []  # 役職
    target = int(remark[1].split("]")[0])  # 発言対象のプレイヤー番号
    for i in remark[1:]:
        for r, val in ESTIMATE_ROLE.items():
            if val[0]:
                if r in i:
                    roles.append(r)
    idx = text[4]  # 発言したプレイヤー番号
    if FEATURE_LIST["ESTIMATE"][0]:
        for role in roles:
            if ESTIMATE_ROLE[role][0]:
                if not target in ESTIMATE_PLAYER[idx][role]:
                    ESTIMATE_PLAYER[idx][role].append(target)
                    if ESTIMATE_OPTION["ACTIVE"][0]:
                        sub_num = ESTIMATE_ROLE[role][1]["ACTIVE"]
                        INFO[idx][sub_num] = len(
                            ESTIMATE_PLAYER[idx][role])    # roleだと思っているプレイヤーの数
                    if ESTIMATE_OPTION["PASSIVE"][0]:
                        sub_num = ESTIMATE_ROLE[role][1]["PASSIVE"]
                        # 自分のことをroleだと思っているプレイヤー数
                        INFO[str(target)][sub_num] += 1


# COMINGOUT発言
def comingout(text, FEATURE_LIST, INFO, COMINGOUT_OPTION):
    remark = text[5].split()   # 分割された発言内容
    role = remark[2]
    idx = text[4]  # 発言したプレイヤー番号
    if FEATURE_LIST["COMINGOUT"][0]:
        if COMINGOUT_OPTION[role][0]:
            sub_num = COMINGOUT_OPTION[role][1]
            INFO[idx][sub_num] = 1


# DIVINED発言
def divined(text, FEATURE_LIST, INFO, DIVINED_OPTION, DIVINED_PLAYER, DIVINED_ROLE):
    remark = text[5].split()   # 分割された発言内容
    role = "HUMAN" if "HUMAN" in text[5] else "WEREWOLF"
    target = int(text[5].split("DIVINED Agent[")[1].split("]")[0])
    idx = text[4]  # 発言したプレイヤー番号
    if FEATURE_LIST["DIVINED"][0]:
        if DIVINED_ROLE[role][0]:
            if not target in DIVINED_PLAYER[idx][role]:
                DIVINED_PLAYER[idx][role].append(target)
                if DIVINED_OPTION["ACTIVE"][0]:
                    sub_num = DIVINED_ROLE[role][1]["ACTIVE"]
                    INFO[idx][sub_num] = len(DIVINED_PLAYER[idx][role])
                if DIVINED_OPTION["PASSIVE"][0]:
                    sub_num = DIVINED_ROLE[role][1]["PASSIVE"]
                    INFO[str(target)][sub_num] += 1


# AGREE発言
def agree(text, FEATURE_LIST, INFO, TALK_HISTROY, AGREE_PLAYER):
    remark = text[5].split()   # 分割された発言内容
    idx = text[4]  # 発言したプレイヤー番号
    day = remark[2].replace("day", "")
    idt = remark[3].replace("ID:", "")
    if idt in TALK_HISTROY[day].keys():
        target = TALK_HISTROY[day][idt]
        if FEATURE_LIST["AGREE"][0]:
            if not day+idt in AGREE_PLAYER[idx]:
                AGREE_PLAYER[idx].append(day+idt)
                if FEATURE_LIST["AGREE"][1]["ACTIVE"][0]:
                    sub_num = FEATURE_LIST["AGREE"][1]["ACTIVE"][1]
                    INFO[idx][sub_num] += 1
                if FEATURE_LIST["AGREE"][1]["PASSIVE"][0]:
                    sub_num = FEATURE_LIST["AGREE"][1]["PASSIVE"][1]
                    INFO[str(target)][sub_num] += 1


# DISAGREE発言
# AGREE発言
def disagree(text, FEATURE_LIST, INFO, TALK_HISTROY, DISAGREE_PLAYER):
    remark = text[5].split()   # 分割された発言内容
    idx = text[4]  # 発言したプレイヤー番号
    day = remark[2].replace("day", "")
    idt = remark[3].replace("ID:", "")
    if idt in TALK_HISTROY[day].keys():
        target = TALK_HISTROY[day][idt]
        if FEATURE_LIST["DISAGREE"][0]:
            if not day+idt in DISAGREE_PLAYER[idx]:
                DISAGREE_PLAYER[idx].append(day+idt)
                if FEATURE_LIST["DISAGREE"][1]["ACTIVE"][0]:
                    sub_num = FEATURE_LIST["DISAGREE"][1]["ACTIVE"][1]
                    INFO[idx][sub_num] += 1
                if FEATURE_LIST["DISAGREE"][1]["PASSIVE"][0]:
                    sub_num = FEATURE_LIST["DISAGREE"][1]["PASSIVE"][1]
                    INFO[str(target)][sub_num] += 1
