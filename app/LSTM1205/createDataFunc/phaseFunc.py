# 処刑フェーズ時
def execute(text, FEATURE_LIST, INFO):
    # 処刑されたプレイヤーのINFOを更新する
    # 処刑:1
    if FEATURE_LIST["STATUS"][0]:
        idx = text[4]
        sub_num = FEATURE_LIST["STATUS"][1]
        INFO[idx][sub_num] = 1  # 1は処刑（2は襲撃->attack(text)）


# 襲撃フェーズ時
def attack(text, FEATURE_LIST, INFO):
    # 襲撃されたプレイヤーのINFOを更新する
    # 襲撃:2
    if FEATURE_LIST["STATUS"][0]:
        idx = text[4]
        sub_num = FEATURE_LIST["STATUS"][1]
        INFO[idx][sub_num] = 2


# 投票フェーズのときの処理
def vote(text, FEATURE_LIST, INFO, VOTE_OPTION, VOTE_PLAYER):
    idx = text[2]   # 投票主
    target = int(text[3])  # 投票先
    # 各プレイヤーの投票先をINFOに書き込む
    if FEATURE_LIST["VOTE"][0]:
        if VOTE_OPTION["RESULT"][0]:
            sub_num = VOTE_OPTION["RESULT"][1]
            INFO[idx][sub_num] = target

        # 投票先を変更した場合
        if VOTE_OPTION["CHANGE"][0]:
            # 投票予定と異なり、1度も投票をしてなく、投票予定発言をしていたら
            if VOTE_PLAYER[idx]["TARGET"] != target and not VOTE_PLAYER[idx]["RUN"] and VOTE_PLAYER[idx]["TARGET"] != None:
                sub_num = VOTE_OPTION["CHANGE"][1]
                INFO[idx][sub_num] += 1
        VOTE_PLAYER[idx]["RUN"] = True


# ステータスフェーズ時
def status(text, FEATURE_LIST, INFO, LABEL_LIST, VOTE_PLAYER, DAY):
    idx = text[4]  # プレイヤー番号
    # 日にちをINFOに書き込む
    if FEATURE_LIST["DAY"][0]:
        sub_num = FEATURE_LIST["DAY"][1]
        INFO[idx][sub_num] = int(DAY)

    # 投票を未実行設定する
    VOTE_PLAYER[idx]["RUN"] = False
