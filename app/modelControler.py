from app.models import Player, Room


# プレイヤー作成
def createPlayer(name):
    player = Player(name=name)
    player.save()


# プレイヤー削除
def destroyPlayer(name):
    Player.objects.filter(name=name).delete()


# プレイヤー情報の取得
def getPlayer(name):
    return Player.objects.filter(name=name).values()[0]


# プレイヤー全体の取得
def getAllPlayer():
    return Player.objects.all().values()


# room_idをセットする
def setRoomId(player_name, room_id):
    player = Player.objects.get(name=player_name)
    player.room_id = room_id
    player.save()


# ルーム作成
def createRoom(name):
    room = Room(name=name)
    room.save()


# 人数をセットする
def setRoomNum(room_name):
    room_id = Room.objects.filter(name=room_name).values()[0]["id"]
    players = Player.objects.filter(room_id=room_id).values()
    room_num = len(players)
    room = Room.objects.get(name=room_name)
    room.num = room_num
    room.save()
    if room.num <= 0:
        destroyRoom(room_name)


def setRoomGame(room_name, state):
    room = Room.objects.get(name=room_name)
    room.game = state
    room.save()


# ルーム削除
def destroyRoom(name):
    Room.objects.filter(name=name).delete()


# ルーム情報の取得
def getRoom(name):
    return Room.objects.filter(name=name).values()[0]


# ルーム全体の取得
def getAllRoom():
    return Room.objects.all().values()
