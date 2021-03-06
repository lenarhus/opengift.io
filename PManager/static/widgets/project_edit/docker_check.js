;$(function(){
    var JS_WORKING = '.js-working',
        JS_SERVER_STATUS = '.js-server-status',
        JS_SERVER_CREATE = '.js-server-create',
        JS_SERVER_ACTIVE_BTN = '.js-server-active',
        MSG_SERVER_NOT_UP_YET = 'Сервер запустится в течении 10 минут',
        MSG_SERVER_FAILED = 'Произошла ошибка, пожалуйста свяжитесь с администратором.',
        MSG_SERVER_WORKING = 'Сервер работает',
        MSG_SERVER_NOT_WORKING = 'Сервер не работает',
        AJAX_SETUP_URL = "/project/" + heliardData.project + "/server-setup",
        AJAX_STATUS_URL = "/project/" + heliardData.project + "/server-status",
        RESPONSE_OK = 'OK',
        requestForServer = function(is_new, callback) {
            is_new = is_new || false;
            var servUp = $.ajax({
                type: "GET",
                url: AJAX_SETUP_URL,
                data: { "new" : is_new }
            });
            servUp.done(function(msg){

            });
            servUp.fail(function(jqXHR, textStatus){
                alert(MSG_SERVER_FAILED);
            });
            servUp.always(callback);
        },
        requestForStatus = function(callback){
            var servStatus = $.ajax({
                type: "GET",
                url: AJAX_STATUS_URL
            });
            servStatus.done(function(msg){
                if (msg === RESPONSE_OK) {
                    $(JS_SERVER_ACTIVE_BTN).addClass('active');
                }
                else {
                    alert(MSG_SERVER_NOT_WORKING);
                    $(JS_SERVER_ACTIVE_BTN).removeClass('active');
                }
            });
            servStatus.fail(function(jqXHR, textStatus){
                alert(MSG_SERVER_FAILED);
            });
            servStatus.always(callback);
        },
        $work_progress = $(JS_WORKING);     

    $(JS_SERVER_STATUS).click(function(){
        $work_progress.show();
        requestForStatus(function(){
            $work_progress.hide();
        });
    });

    $(JS_SERVER_CREATE).click(function(){
        $work_progress.show();
        requestForServer(true, function(){
            $work_progress.hide();
        });
    });

    window.requestForStatus = requestForStatus;
});