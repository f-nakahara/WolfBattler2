var room_name
var player_name
var room_id
var player_list = []
var chatSocket
var request
var message
var send_contents = { "request": null, "player_name": null, "message": null }
var dead = false

// ページ移動時
$(window).on("beforeunload", function (e) {
    // 退出メッセージの送信
    send_contents["request"] = "disconnect"
    send_contents["player_name"] = player_name
    chatSocket.send(JSON.stringify(send_contents))
    $.ajax({
        url: "/ajax",
        type: "post",
        async: false,
        data: {
            "func": "exit_room"
        }
    })
});

// ウェブソケットの立ち上げ
function create_web_socket() {
    var protocol = '';
    if (window.location.protocol === 'https:') {
        protocol = 'wss:';
    } else {
        protocol = 'ws:';
    }
    chatSocket = new WebSocket(
        protocol + '//' + window.location.host + '/room/' + room_id + '/');

    // ウェブソケット接続時
    chatSocket.onopen = function () {
        console.log("接続されました。")
        send_contents["request"] = "connect"
        send_contents["player_name"] = player_name
        chatSocket.send(JSON.stringify(send_contents));
    }

    // ウェブソケット切断時
    chatSocket.onclose = function (e) {
        console.error('切断されました。')
        $.ajax({
            url: "/ajax",
            type: "post",
            async: false,
            data: {
                "func": "exit_room"
            }
        })
        window.location.href = "/"
    }

    // メッセージ受信時
    chatSocket.onmessage = function (e) {
        var receiveData = JSON.parse(e.data)["message"]
        request = receiveData["request"]
        message = receiveData["message"]

        if (receiveData["player_list"])
            player_list = JSON.parse(receiveData["player_list"])
        if (receiveData["dead"]) {
            if (player_name == receiveData["dead"])
                dead = true
        }
        changeInput()

        // お知らせ系はセンター寄せで表示する
        if (receiveData["type"] == "notice") {
            console.log(request)
            $(".card-body").append("<div class='card-text text-center'>" + message + "</div>")
        }
        // 自分の発言は右寄せ、それ以外は左寄せで表示する
        else if (receiveData["player_name"] == player_name)
            $(".card-body").append("<div class='card-text text-right'>" + message + "</div>")
        else
            $(".card-body").append("<div class='card-text text-left'>" + receiveData["player_name"] + ":" + message + "</div>")

        // ゲーム開始
        if (request == "start")
            $("#start").hide()
        // 役職など与えられたとき
        else if (request == "initialize") {
            initialize()
        }
        // 
        else if (request == "daily_initialize") {
            daily_initialize()
        }
        else if (request == "talk") {
        }
        else if (request == "vote") {
            vote()
        }
        else if (request == "execute") {
            execute()
        }
        else if (request == "divine") {
            console.log(player_list)
            divine()
        }
        else if (request == "attack") {
            attack()
        }
        else if (request == "finish") {
            finish()
        }

        $('.card-body').animate({ scrollTop: $('.card-body')[0].scrollHeight }, 'fast');
    }
}
function finish() {
    dead = false
    $("#start").show()
}

function execute() {
}

function vote() {
    $(".player_list").show()
    setPlayerList()
}

function talk() {
    allClassRemove()
    $(".role_list").addClass("w-50")
    $(".player_list").hide()
    $(".role_list").show()
    $(".result_list").hide()
    $(".other_list").hide()
    $(".remark_type").val("カミングアウト")
}

function daily_initialize() {
    request = "talk"
    $(".player_list").hide()
    $(".role_list").show()
    $(".result_list").hide()
    $(".other_list").hide()
}

function attack() {
    $(".player_list").show()
    setPlayerList()
}

function divine() {
    $(".player_list").show()
    setPlayerList()
}

function initialize() {
    setPlayerList()
}

function start() {
    dead = false
    $("#start").hide()
}

// ゲーム開始ボタンを押したとき
function pusuGameStart() {
    $("#start").on("click", function () {
        send_contents["request"] = "start"
        chatSocket.send(JSON.stringify(send_contents))
    })
}

// inputの切り換え
function changeInput() {
    if (request == "normal" || request == "connect" || request == "finish") {
        $(".talk").hide()
        $(".action").hide()
        $(".normal").show()
    }
    else if (request == "start") {
        $(".talk").hide()
        $(".action").hide()
        $(".normal").hide()
    }
    else if (!dead) {
        if (request == "talk" || request == "daily_initialize") {
            $(".normal").hide()
            $(".action").hide()
            $(".talk").show()
        }
        else if (request == "divine" || request == "vote" || request == "attack") {
            $(".normal").hide()
            $(".talk").hide()
            $(".action").show()
        }
    }
}

// ホームに戻る
function pushHomeBack() {
    $("#back").on("click", function () {
        window.location.href = "/"
    })
}

// プレイヤーをセットする
function setPlayerList() {
    $(".player_list").html("")
    player_list.forEach(function (player) {
        $(".player_list").append("<option>" + player + "</option>")
    })
}


// 基本情報の取得
function getBaseInfo() {
    room_name = $("#room_name").text()
    player_name = $("#player_name").text()
    send_contents["player_name"] = player_name
    $.ajax({
        url: "/ajax",
        type: "POST",
        async: false,
        data: {
            "func": "get_room_id",
        }
    })
        .done(function (data) {
            room_id = data
        })
}

// メッセージの送信
function sendMessage() {
    $(".send").on("click", function (e) {
        e.preventDefault()
        if (request == "connect" || request == "normal") {
            send_contents["request"] = "normal"
            send_contents["message"] = $("input[name=input_word]").val()
            chatSocket.send(JSON.stringify(send_contents))
            $("input[name=input_word]").val("")
        }
        else if (request == "divine" || request == "vote" || request == "attack") {
            send_contents["request"] = request
            send_contents["target"] = $(this).prev(".player_list").val()
            console.log(send_contents)
            chatSocket.send(JSON.stringify(send_contents))
            $(".action").hide()
        }
        else if (request == "talk") {
            send_contents["request"] = "talk"
            var remark_type = $(".remark_type").val()
            send_contents["remark_type"] = remark_type
            if (remark_type == "カミングアウト") {
                send_contents["role"] = $(".role_list").val()
                chatSocket.send(JSON.stringify(send_contents))
            }
            else if (remark_type == "推定発言") {
                send_contents["target"] = $(".player_list").val()
                send_contents["role"] = $(".role_list").val()
                chatSocket.send(JSON.stringify(send_contents))
            }
            else if (remark_type == "投票発言") {
                send_contents["target"] = $(".player_list").val()
                chatSocket.send(JSON.stringify(send_contents))
            }
            else if (remark_type == "占い発言") {
                send_contents["target"] = $(".player_list").val()
                send_contents["result"] = $(".result_list").val()
                chatSocket.send(JSON.stringify(send_contents))
            }
            else if (remark_type == "その他") {
                send_contents["remark_type"] = $(".other_list").val()
                chatSocket.send(JSON.stringify(send_contents))
            }
            talk()
            $(".talk").hide()
        }
    })
}

function allClassRemove() {
    $(".player_list").removeClass("w-25 w-50")
    $(".role_list").removeClass("w-25 w-50")
}

function changeRemarkType() {
    $(".remark_type").bind("change", function () {
        allClassRemove()
        var remark_type = $(".remark_type").val()
        if (remark_type == "カミングアウト") {
            $(".player_list").hide()
            $(".role_list").addClass("w-50")
            $(".role_list").show()
            $(".result_list").hide()
            $(".other_list").hide()
        }
        else if (remark_type == "推定発言") {
            $(".player_list").addClass("w-25")
            $(".player_list").show()
            $(".role_list").addClass("w-25")
            $(".role_list").show()
            $(".result_list").hide()
            $(".other_list").hide()
        }
        else if (remark_type == "投票発言") {
            $(".player_list").addClass("w-50")
            $(".player_list").show()
            $(".role_list").hide()
            $(".result_list").hide()
            $(".other_list").hide()
        }
        else if (remark_type == "占い発言") {
            $(".role_list").hide()
            $(".player_list").addClass("w-25")
            $(".player_list").show()
            $(".result_list").show()
            $(".other_list").hide()
        }
        else if (remark_type == "その他") {
            $(".other_list").show()
            $(".player_list").hide()
            $(".role_list").hide()
            $(".result_list").hide()
        }
    })
}


// サイドバーの高さを画面の高さに合わせる
$(window).on("load resize", function () {
    var wH = $(window).height();
    var wW = $(window).width();
    $(".card-body").css({
        "height": wH / 2 + "px"
    });
});


$(function () {
    getBaseInfo()
    create_web_socket()
    sendMessage()
    pushHomeBack()
    pusuGameStart()
    changeRemarkType()
})