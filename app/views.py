from django.shortcuts import render, HttpResponse, HttpResponseRedirect, redirect
from . import modelControler as mc
import json

# Create your views here.


# トップページ
def index(request):
    login = False
    player_name = "　"
    error = False
    room_list = {}
    try:
        if "player_name" in request.session:
            player_name = mc.getPlayer(request.session["player_name"])["name"]
            login = True
            room_list = mc.getAllRoom()
        if "player_name" in request.POST:
            try:
                mc.createPlayer(request.POST["player_name"])
                login = True
                request.session["player_name"] = request.POST["player_name"]
                player_name = request.POST["player_name"]
                room_list = mc.getAllRoom()
            except:
                error = True
        if "logout" in request.POST:
            login = False
            mc.destroyPlayer(request.session["player_name"])
            player_name = "　"
            del request.session["player_name"]
    except:
        if "player_name" in request.session:
            del request.session["player_name"]
        login = False
        player_name = "　"
        error = False

    return render(request, "app/index.html", {"login": login, "player_name": player_name, "error": error, "room_list": room_list})


# ルーム画面
def room(request):
    try:
        player_name = mc.getPlayer(request.session["player_name"])["name"]
        room_name = mc.getRoom(request.session["room_name"])["name"]
        room_num = mc.getRoom(room_name)["num"]
        room_state = mc.getRoom(room_name)["game"]
        if room_num < 5 and not room_state:
            mc.setRoomNum(room_name)
            return render(request, "app/room.html", {"player_name": player_name, "room_name": room_name})
        else:
            return HttpResponseRedirect("/")
    except:
        return HttpResponseRedirect("/")


# ajax用
def ajax(request):
    func = request.POST["func"]
    if func == "create_room":
        try:
            mc.createRoom(request.POST["room_name"])
            request.session["room_name"] = request.POST["room_name"]
            room_id = mc.getRoom(request.POST["room_name"])["id"]
            mc.setRoomId(request.session["player_name"], room_id)
            return HttpResponse("true")
        except:
            return HttpResponse("false")
    elif func == "enter_room":
        try:
            room_num = mc.getRoom(request.POST["room_name"])["num"]
            if room_num >= 5:
                return HttpResponse("false")
            else:
                request.session["room_name"] = request.POST["room_name"]
                room_id = mc.getRoom(request.POST["room_name"])["id"]
                mc.setRoomId(request.session["player_name"], room_id)
                return HttpResponse("true")
        except:
            return HttpResponseRedirect("/")
    elif func == "get_room_id":
        room_id = mc.getRoom(request.session["room_name"])["id"]
        return HttpResponse(room_id)
    elif func == "get_player_list":
        room_id = request.POST["room_id"]
        players = list(mc.getAllPlayer().filter(room_id=room_id))
        return HttpResponse(json.dumps(players, ensure_ascii=False))
    elif func == "exit_room":
        mc.setRoomId(request.session["player_name"], None)
        if "room_name" in request.session:
            mc.setRoomNum(request.session["room_name"])
            del request.session["room_name"]
        return HttpResponseRedirect("/")
