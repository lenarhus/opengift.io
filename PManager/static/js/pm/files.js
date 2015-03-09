/**
 * Created with PyCharm.
 * User: Gvammer
 * Date: 23.11.12
 * Time: 18:55
 * To change this template use File | Settings | File Templates.
 */
// Created by STRd6
    // MIT License
    // jquery.paste_image_reader.js
(function($) {
    var defaults;
    $.event.fix = (function(originalFix) {
        return function(event) {
            event = originalFix.apply(this, arguments);
            if (event.type.indexOf('copy') === 0 || event.type.indexOf('paste') === 0) {
                event.clipboardData = event.originalEvent.clipboardData;
            }
            return event;
        };
    })($.event.fix);
    defaults = {
        callback: $.noop,
        matchType: /image.*/
    };
    return $.fn.pasteImageReader = function(options) {
        if (typeof options === "function") {
            options = {
                callback: options
            };
        }
        options = $.extend({}, defaults, options);
        return this.each(function() {
            var $this, element;
            element = this;
            $this = $(this);
            return $this.bind('paste', function(event) {
                var clipboardData, found;
                found = false;
                clipboardData = event.clipboardData;
                if (!clipboardData) return false;
                return Array.prototype.forEach.call(clipboardData.types, function(type, i) {
                    var file, reader;
                    if (found) {
                        return;
                    }
                    if (type.match(options.matchType) || clipboardData.items[i].type.match(options.matchType)) {
                        file = clipboardData.items[i].getAsFile();
                        reader = new FileReader();
                        reader.onload = function(evt) {
                            return options.callback.call(element, {
                                dataURL: evt.target.result,
                                event: evt,
                                file: file,
                                name: file.name
                            });
                        };
                        reader.readAsDataURL(file);
                        return found = true;
                    }
                });
            });
        });
    };
})(jQuery);
window.pasteObject = false;
$.fn.addFilePaste = function(options){
    function replaceAt(original, range, replacement) {
        return original.substr(0, range.start) + replacement + original.substr(range.end);
    }
    function getInputSelection(el) {
        var start = 0, end = 0, normalizedValue, range,
            textInputRange, len, endRange;

        if (typeof el.selectionStart == "number" && typeof el.selectionEnd == "number") {
            start = el.selectionStart;
            end = el.selectionEnd;
        } else {
            range = document.selection.createRange();

            if (range && range.parentElement() == el) {
                len = el.value.length;
                normalizedValue = el.value.replace(/\r\n/g, "\n");

                // Create a working TextRange that lives only in the input
                textInputRange = el.createTextRange();
                textInputRange.moveToBookmark(range.getBookmark());

                // Check if the start and end of the selection are at the very end
                // of the input, since moveStart/moveEnd doesn't return what we want
                // in those cases
                endRange = el.createTextRange();
                endRange.collapse(false);

                if (textInputRange.compareEndPoints("StartToEnd", endRange) > -1) {
                    start = end = len;
                } else {
                    start = -textInputRange.moveStart("character", -len);
                    start += normalizedValue.slice(0, start).split("\n").length - 1;

                    if (textInputRange.compareEndPoints("EndToEnd", endRange) > -1) {
                        end = len;
                    } else {
                        end = -textInputRange.moveEnd("character", -len);
                        end += normalizedValue.slice(0, end).split("\n").length - 1;
                    }
                }
            }
        }

        return {
            start: start,
            end: end
        };
    }
    if (typeof options === "function") {
        options = {
            callback: options
        };
    }
    var pasteObj = this;
    var pasteFunc = {
        init:function(options){
            if (typeof options === "function") {
                options = {
                    callback: options
                };
            }

            var bIsIe11 = navigator.userAgent.indexOf('Trident') > -1;

            if(navigator.userAgent.toLowerCase().indexOf('chrome') > -1){
                pasteObj.pasteImageReader({'handles': true,'callback':function(data){
                    pasteFunc.showPastedImgForm(data.dataURL);
                }});
            }else if ($.browser.mozilla){
                var $frame = $('iframe#fileinput');
                $frame.each(function(){
                    doc = this.contentDocument || this.contentWindow.document;
                    doc.designMode = "on";
                }).hide();

                pasteObj.keydown(function(e){
                    var frame = $frame.get(0), t=$(this);
                    var key = getKeyPressed(e);

                    if (key == 17 && bIsIe11) {
                        $frame.show().css({
                            'position':'fixed',
                            'top':'50%',
                            'left':'50%',
                            'margin-top':'-50%',
                            'margin-left':'-50%'
                        });
                        $frame.get(0).contentWindow.focus();
                        window.pasteObject = $(this);
                    }
                    if ((e.metaKey || e.ctrlKey) && key==86){  //ctrl + v

                        if (!bIsIe11) {
                            $frame.show().focus().hide();
                            setTimeout(function(){
                                if (frame.contentDocument && frame.contentDocument.images && frame.contentDocument.images.length)
                                    var src = $(frame.contentDocument).find('img').first().attr('src');

                                pasteObj.focus();

                                if (src)
                                    pasteFunc.showPastedImgForm(src);
                                else
                                    var selection = getInputSelection(t.get(0));
                                    var value = replaceAt(t.val(), selection, 
                                        $(frame.contentDocument).find('body').html().replace(/<br>/gi,"\n").replace(/<([^\>]+)>/gi, ''));
                                    t.val(value);

                                setTimeout(function(){
                                    $(frame.contentDocument).find('body').empty();
                                },300);
                            },30);
                        }

                    }
                });
                $($frame.get(0).contentDocument).keyup(function(){

                    if (window.pasteObject){
                        window.pasteObject.focus();
                        var $frame = $('iframe#fileinput').css('position','relative').hide();
                        var frame = $frame.get(0);
                        var pasteObj = window.pasteObject;
                        if (frame.contentDocument && frame.contentDocument.images && frame.contentDocument.images.length)
                                var src = $(frame.contentDocument).find('img').first().attr('src');

                        pasteObj.focus();

                        if (src)
                            pasteFunc.showPastedImgForm(src);
                        else
                            window.pasteObject.val(window.pasteObject.val() + $(frame.contentDocument).find('body').html().replace(/<br>/gi,"\n").replace(/<([^\>]+)>/gi, ''));

                        setTimeout(function(){
                            $(frame.contentDocument).find('body').empty();
                        },300);
                        window.pasteObject = false;
                    }
                });
            }
        },
        removeImgAreaLayers:function(){
            $('.imgareaselect-outer').remove();
            $('.imgareaselect-selection').parent().remove();
        },
        initSelectedCoordinates:function(img,selection){
            $('input[name="posted_image_size_w"]').val($(img).width());
            $('input[name="posted_image_size_h"]').val($(img).height());
            $('input[name="posted_image_x1"]').val(selection.x1);
            $('input[name="posted_image_y1"]').val(selection.y1);
            $('input[name="posted_image_x2"]').val(selection.x2);
            $('input[name="posted_image_y2"]').val(selection.y2);
        },
        showPastedImgForm:function(src){
            //Получить параметры экрана
            var windiwWidth = $(window).width(),
                windowHeight = $(window).height(),
                popupWidth = Math.ceil(windiwWidth/1.5),
                popupMarginLeft = Math.ceil(popupWidth/2);

            showOverlay();
            var $img = $('<img />').attr({'src':src,'id':'newPastedImg','class':'img-responsive'}).appendTo('<div class="picture_container js-pict-container"></div>');
            var $form = $('<form></form>').attr({
                'action':'/sendfile/',
                'method':'POST',
                'enctype':'multipart/form-data',
                'id':'posted_img_form'
            })
                .append('<a href="#" class="edit btn btn-success btn-mini"><i class="fa fa-pencil icon-white"></i></a>')
                .append('<a href="#" class="close btn btn-danger btn-mini"><i class="fa fa-times icon-remove icon-white"></i></a>')
                .append('<h2>Вставка изображения</h2><hr>')
                .append('<p>Выберите участок для вставки</p>')
                .append('<input type="hidden" style="display:none" name="posted_image" value="'+src+'" />')
                .append('<input type="hidden" name="posted_image_x1" />')
                .append('<input type="hidden" name="posted_image_y1" />')
                .append('<input type="hidden" name="posted_image_x2" />')
                .append('<input type="hidden" name="posted_image_y2" />')
                .append('<input type="hidden" name="posted_image_size_w" />')
                .append('<input type="hidden" name="posted_image_size_h" />');

            $form.find('a.close').on("click", function(){
                $(this).closest('.preview_img_form').remove();
				$('.overflow').remove()
                hideOverlay();
                pasteFunc.removeImgAreaLayers();
                return false;
            });

            $form.find('a.edit').on("click", function(){
                var getImg = $form.find("#newPastedImg");
                var setImg = $('<div id="js-setImage" style="display: none;"></div>').append(getImg.clone());
                if($("body").find("#js-setImage").length)
                    $("#js-setImage").remove();
                $("body").append(setImg);

                var InputVal = $form.find("input[name=posted_image]"),
                    getImg_width = setImg.width(),
                    getImg_height = setImg.height(),
                    getImgEdit_width = $form.find("input[name=posted_image_size_w]").val(),
                    getImgEdit_height = $form.find("input[name=posted_image_size_h]").val(),
                    getImgEdit_x1 = $form.find("input[name=posted_image_x1]").val(),
                    getImgEdit_y1 = $form.find("input[name=posted_image_y1]").val(),
                    getImgEdit_x2 = $form.find("input[name=posted_image_x2]").val(),
                    getImgEdit_y2 = $form.find("input[name=posted_image_y2]").val();

                setProportionW = getImg_width/getImgEdit_width;
                setProportionH = getImg_height/getImgEdit_height;
                setImgEditX = Math.ceil(getImgEdit_x1*setProportionW);
                setImgEditY = Math.ceil(getImgEdit_y1*setProportionH);
                setImgEditWidth = Math.ceil((getImgEdit_x2-getImgEdit_x1)*setProportionW);
                setImgEditHeight = Math.ceil((getImgEdit_y2-getImgEdit_y1)*setProportionH);

                // html canvas
                var $canvasEl = '<div id="canvasPaint">'+
                    '<a href="#" class="close btn btn-danger btn-mini"><i class="fa fa-times icon-remove icon-white"></i></a>'+
                    '<div class="canvasTools">'+
                        '<div class="brushColor"></div>'+
                        '<div class="brushDepth"></div>'+
                    '</div><hr>'+
                    '<div class="CanvasContainer"></div>'+
                    '<hr><div class="canvasBottons">'+
                        '<button class="canvasSave btn btn-success">Отправить</button>'+
                        '<button class="canvasClear btn btn-warning">Очистить</button>'+
                    '</div>'+
                    '<div id="savedCopyContainer"></div>'+
                    '</div>';


                $(".preview_img_form.popup").find("form#posted_img_form").hide().end().append($canvasEl);
                $("#canvasPaint").drawCanvas({
                    rezImg: InputVal,
                    width: setImgEditWidth+'px',
                    height: setImgEditHeight+'px',
                    colors: ['rgb(192,15,1)', 'rgb(51,153,51)'],
                    onImages: {
                        img: getImg,
                        x: setImgEditX,
                        y: setImgEditY,
                        w: setImgEditWidth,
                        h: setImgEditHeight
                    }
                });
                $("#canvasPaint").find(".CanvasContainer").css({
                    //'width': (popupWidth-30)+'px',
                    'height': (windowHeight-300)+'px'
                }).end().find(".close")
                    .on("click", function(){
                        $(this).closest("#canvasPaint").remove();
                        $(".preview_img_form.popup").find('a.close').click();
                        $('.overflow').remove();
                        return false;
                    });

                $("#canvasPaint").find(".canvasSave").on("click", function(){
                    $form.find("input[name=posted_image_x1]").remove();
                    $form.find("input[name=posted_image_y1]").remove();
                    $form.find("input[name=posted_image_x2]").remove();
                    $form.find("input[name=posted_image_y2]").remove();
                    $(this).pushTheButton();
                    $form.submit();
                });

                pasteFunc.removeImgAreaLayers();
                return false;
            });

            //$img.appendTo($form);
            $form.append($img.parent()).appendTo('<div class="preview_img_form popup"></div>').parent().appendTo('body');
			$('<div class="overflow"></div>').appendTo('body').show();

            if(popupWidth > 1000){ // Меняем размер окна .preview_img_form
                $(".preview_img_form").css({
                    'width': popupWidth+'px',
                    //'marginLeft': '-'+popupMarginLeft+'px'
                });
            }

            $img.get(0).onload = function(){
                var startedCoords = {
                    'handles':true,
                    'x1': 10,
                    'y1': 10,
                    'x2': $img.width()-10,
                    'y2': $img.height()-10
                }
                $img.imgAreaSelect($.extend({
                    'onSelectEnd': function (img, selection) {
                        pasteFunc.initSelectedCoordinates(img,selection);
                    }},startedCoords));
                pasteFunc.initSelectedCoordinates($img,startedCoords);
            }

            $form.append('<hr><div class="form_submit"><div align="center"><input type="submit" name="posted_image_submit" value="Отправить" class="btn btn-success btn-large" /></div></div>')
                .ajaxForm(function(data) {
                    options.callback.call(pasteObj.get(0),data);
                    $('.preview_img_form').remove();
                    hideOverlay();
                    pasteFunc.removeImgAreaLayers();
                    stopLoaders();
                    $('.overflow').remove();
                }).find('input:submit').click(function(){
                    startLoader('medium',$(this).closest('form'));
                });
        }
    }
    pasteFunc.init(options);
    return this;
}