;$(function(){
    var JS_PROJECT_SUBMIT = '.js-project-submit',
        JS_ADD_INTERFACE = '.js-add-interface',
        JS_INTERFACE_CONTAINER = '.js-interface-container',
        JS_COPY_PASSWORD = '.js-copy-password',
        JS_ADD_INTERFACE_WRAPPER = '.js-add-interface-wrapper',
        JS_ADD_INTERFACE_INPUT = '.js-add-interface-input',
        JS_INTERFACE_REMOVE = '.js-interface-remove',
        JS_INTERFACE_BLOCK = '.js-interface-block',
        JS_ADD_INTERFACE_BUTTON = '.js-add-interface-button';

    $(JS_PROJECT_SUBMIT).click(function(){
        $(JS_ADD_INTERFACE).ajaxSubmit(function(data){
            var $ic = $(JS_INTERFACE_CONTAINER); 
            $ic.append(data);
            clipboardAppend($ic.find(JS_COPY_PASSWORD).last());
            $(JS_ADD_INTERFACE_WRAPPER)
                .toggle()
                .find(JS_ADD_INTERFACE_INPUT)
                .val('');
        });
        return false;
    });

    $(JS_INTERFACE_CONTAINER).on('click', JS_INTERFACE_REMOVE, function () {
        var $interface = $(this).closest(JS_INTERFACE_BLOCK),
            id = $interface.data('id');
        $interface.remove();
        PM_AjaxPost(
                '/remove_interface/',
                {
                    'id': id
                }
        );
    });

    $(JS_ADD_INTERFACE_BUTTON).click(function() {
        $(JS_ADD_INTERFACE_WRAPPER).toggle();
    });
});