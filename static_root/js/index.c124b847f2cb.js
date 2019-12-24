
// ルーム作成
function createRoom() {
    $("input[name='create_room']").on("click", function (e) {
        // $("input[name='create_room']").click()
        e.preventDefault()
        room_name = $("input[name='room_name']").val()
        $.ajax({
            url: "/ajax",
            type: "POST",
            data: {
                "func": "create_room",
                "room_name": room_name
            }
        })
            .done(function (data) {
                if (data == "false") {
                    $(".error").text("既に使用されています！")
                }
                else {
                    window.location.href = "room"
                }
            })
    })
}

// ルーム参加
function enterRoom() {
    $(".enter_room").on("click", function (e) {
        e.preventDefault()
        room_name = $(this).parent().parent().children().find("h5").text()
        console.log(room_name)
        $.ajax({
            url: "/ajax",
            type: "POST",
            data: {
                "func": "enter_room",
                "room_name": room_name
            }
        })
            .done(function (data) {
                if (data == "true") {
                    window.location.href = "room"
                }
                else {
                    window.location.href = "/"
                }
            })
    })
}

// サイドバーの高さを画面の高さに合わせる
$(window).on("load resize", function () {
    var wH = $(window).height();
    var wW = $(window).width();
    $(".player_list").css({
        "height": wH / 2 + "px"
    });
});

$(function () {
    createRoom()
    enterRoom()
})