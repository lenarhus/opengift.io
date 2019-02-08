# -*- coding:utf-8 -*-
__author__ = 'Rayleigh'

PIPELINE_ENABLED = False
STATICFILES_STORAGE = 'pipeline.storage.PipelineCachedStorage'
PIPELINE_JS_COMPRESSOR = 'pipeline.compressors.uglifyjs.UglifyJSCompressor'
PIPELINE_JS = {
    'base': {
        'source_filenames': (
            # 'js/libs/jquery.min.js',
            'js/libs/fancybox.js',
            'js/libs/jquery.history.min.js',
            'js/libs/jquery.form.js',
            'js/libs/html5shiv.js',
            'js/libs/howler.min.js',
            'js/libs/sniffer.js',
            'js/libs/string_mod.js',
            'js/libs/timepicker/jquery.datetimepicker.js',
            'js/libs/socket.io.js',
            'js/libs/mask.js',
            'js/libs/backbone.js',
            'js/libs/backbone.iobind.js',
            'js/libs/backbone.iosync.js',
            'js/libs/boostrap.growl.js',
            'js/libs/jquery.createAvatar.js',
            'js/libs/jquery.event.outside.min.js',
            'js/libs/apng-canvas.js',
            'js/libs/jquery.imgareaselect.min.js',
            'js/libs/jquery.cookie.js',
            'js/libs/moment/moment.js',
            'js/libs/moment/moment-timezone-with-data-2012-2022.min.js',
            # 'js/bootstrap/bootstrap.min.js',
            'js/bootstrap/typehead.js',
            'js/bootstrap/bootstrap-combobox.js',
            "js/multiselect/bootstrap-multiselect.js",
            'js/pm/script.js',
            'js/pm/main.js',
            'js/pm/timer.js',
            'js/pm/panel.js',
            'js/pm/tasks.js',
            'js/pm/specialties.js',
            'js/pm/files.js',
            'js/pm/beep.js',
            'js/pm/hint.js',
            'js/pm/user_dynamics.js',
            'js/pm/sock_connector.js',
            'js/pm/user-notice.js',
            'js/pm/current_timer.js',
            'js/pm/drowCanvas.js',
            'js/libs/toastr.js',
            'js/pm/csrf_protector.js',
            'public/js/libs/jquery.waipoints.min.js',
            'js/bootstrap/bootstrap-tooltip.js'
        ),
        'output_filename': 'js_compressed/base.js',
    },
    'fileup': {
        'source_filenames': (
            'js/fileup/header.js',
            'js/fileup/util.js',
            'js/fileup/promise.js',
            'js/fileup/button.js',
            'js/fileup/ajax.requester.js',
            'js/fileup/deletefile.ajax.requester.js',
            'js/fileup/handler.base.js',
            'js/fileup/window.receive.message.js',
            'js/fileup/handler.form.js',
            'js/fileup/handler.xhr.js',
            'js/fileup/paste.js',
            'js/fileup/uploader.basic.js',
            'js/fileup/dnd.js',
            'js/fileup/uploader.js',
            'js/fileup/jquery-plugin.js',
            'js/fileup/task-file-upload.js',
        ),
        'output_filename': 'js_compressed/file_up.js'
    },
    'howitworks': {
        'source_filenames': (
            'public/assets/js/createjs-2015.11.26.min.js',
            'public/assets/js/howitworks.js'
        ),
        'output_filename': 'js_compressed/howitworks.js'
    },
    'chat': {
        'source_filenames': (
            'js/pm/comments.js',
            'widgets/chat/widget.js',

        ),
        'output_filename': 'js_compressed/chat.js'
    },
    'file_list': {
        'source_filenames': (
            'widgets/file_list/widget.js',
        ),
        'output_filename': 'js_compressed/file_list.js'
    },
    'gantt': {
        'source_filenames': (
            'widgets/gantt/dragndrop.js',
            'widgets/gantt/gantt.event.block.js',
            'widgets/gantt/gantt.js',
            'widgets/gantt/gantt.thumbnail.js',
            'widgets/gantt/widget.js',
            'js/libs/fullscreen.js',
        ),
        'output_filename': 'js_compressed/gantt.js'
    },
    'kanban': {
        'source_filenames': (
            'js/libs/jquery-ui.custom.min.js',
            'js/libs/jquery.touchpunch.js',
            'widgets/kanban/widget.js',
        ),
        'output_filename': 'js_compressed/kanban.js'
    },
    'life': {
        'source_filenames': (
            'widgets/life/widget.js',
            'js/libs/charts.js'
        ),
        'output_filename': 'js_compressed/life.js'
    },
    'profile_edit': {
        'source_filenames': (
            'widgets/profile_edit/widget.js',
        ),
        'output_filename': 'js_compressed/profile_edit.js'
    },
    'project_calendar': {
        'source_filenames': (
            'widgets/project_calendar/widget.js',
            'js/jquery.bxslider.min.js',
        ),
        'output_filename': 'js_compressed/project_calendar.js'
    },
    'project_edit': {
        'source_filenames': (
            'js/libs/transliterate.js',
            'widgets/project_edit/widget.js',
        ),
        'output_filename': 'js_compressed/project_edit.js'
    },
    'project_detail': {
        'source_filenames': (
            'js/libs/clipboard/zclib.js',
            'js/pm/ajax_inputs.js',
            'widgets/project_edit/clipboard_init.js',
            'widgets/project_edit/project_edit.js',
            'widgets/project_edit/interfaces_control.js',
            'widgets/project_edit/achievements_control.js',
            'widgets/project_edit/project_avatar.js',
            'widgets/project_edit/payment.js',
            'widgets/project_edit/tabs_navigation.js',
            'widgets/project_edit/docker_check.js',
            'widgets/project_edit/repository_check.js',
        ),
        'output_filename': 'js_compressed/project_detail.js'
    },
    'project_server': {
        'source_filenames': (
            # 'js/libs/clipboard/zclib.js',
            'js/pm/ajax_inputs.js',
            # 'widgets/project_edit/clipboard_init.js',
            # 'widgets/project_edit/project_edit.js',
            # 'widgets/project_edit/interfaces_control.js',
            # 'widgets/project_edit/achievements_control.js',
            # 'widgets/project_edit/project_avatar.js',
            # 'widgets/project_edit/payment.js',
            # 'widgets/project_edit/tabs_navigation.js',
            'widgets/project_edit/docker_check.js',
            # 'widgets/project_edit/repository_check.js',
        ),
        'output_filename': 'js_compressed/project_server.js'
    },

    'project_graph': {
        'source_filenames': (
            'widgets/project_graph/widget.js',
        ),
        'output_filename': 'js_compressed/project_graph.js'
    },
    'project_statistic': {
        'source_filenames': (
            'js/libs/charts.js',
            'widgets/project_statistic/widget.js',
        ),
        'output_filename': 'js_compressed/project_statistic.js'
    },
    'project_summary': {
        'source_filenames': (
            'widgets/project_summary/widget.js',
            'js/libs/charts.js',
        ),
        'output_filename': 'js_compressed/project_summary.js'
    },
    'diagram_editor': {
        'source_filenames': (
            'js/libs/fancybox.js',
            'js/libs/joint.js',
            'widgets/diagram_editor/widget.js',
        ),
        'output_filename': 'js_compressed/diagram_editor.js'
    },
    'task_detail': {
        'source_filenames': (
            'js/pm/comments.js',
            'widgets/task_detail/widget.js',
            'js/bootstrap/bootstrap-tooltip.js',
        ),
        'output_filename': 'js_compressed/task_detail.js'
    },
    'task_edit': {
        'source_filenames': (
            'widgets/task_edit/widget.js',
        ),
        'output_filename': 'js_compressed/qq-upload-button_edit.js'
    },
    'tasklist': {
        'source_filenames': (
            'widgets/tasklist/widget.js',
            'js/pm/show_tutorial.js',
        ),
        'output_filename': 'js_compressed/tasklist.js'
    },
    'user_detail': {
        'source_filenames': (
            'widgets/user_detail/widget.js',
            'widgets/user_detail/key_form.js',
            'js/jquery.bxslider.min.js',
            'js/libs/raphael-min.js',
            'js/libs/charts.js'
        ),
        'output_filename': 'js_compressed/user_detail.js'
    },
    'user_list': {
        'source_filenames': (
            'widgets/user_list/widget.js',
        ),
        'output_filename': 'js_compressed/user_list.js'
    },
    'user_statistic': {
        'source_filenames': (
            'widgets/user_statistic/widget.js',
        ),
        'output_filename': 'js_compressed/user_statistic.js'
    },
    'taskdraft_detail': {
        'source_filenames': (
            'modules/taskdraft/taskdraft_detail.js',
            'modules/taskdraft/taskdraft_task_detail.js',
            'modules/taskdraft/taskdraft_detail_invite_user.js',
        ),
        'output_filename': 'js_compressed/taskdraft_detail.js'
    },
    'markdown': {
        'source_filenames': (
            'js/markdown.js',
            'js/to-markdown.js',
            'js/bootstrap-markdown.js',
            'js/locale/bootstrap-markdown.ru.js',
            'js/markdown-setup.js',
        ),
        'output_filename': 'js_compressed/markdown.js'
    }
}
PIPELINE_DISABLE_WRAPPER = True

PIPELINE_CSS = {
    'base': {
        'source_filenames': (
            'css/reset.css',
            'css/external/imgareaselect-animated.css',
            'css/external/fancybox.css',
            'css/external/carousel.css',
            'css/external/bootstrap-responsive.css',
            'css/external/bootstrap3.min.css',
            'css/external/font-awesome.css',
            'css/external/font-awesome-animation.css',
            'css/external/linecons/linecons.css',
            'css/styles.css',
            'css/project.edit.css',
            'css/add.css',
            'css/panel.css',
            'css/drowCanvas.css',
            'js/libs/timepicker/jquery.datetimepicker.css',
            'css/toastr.css',
            "js/multiselect/bootstrap-multiselect.css",
        ),
        'output_filename': 'css_compressed/base.css',
    },
    'project_detail': {
        'source_filenames': (
            'css/project.edit.css',
            'css/project.edit.achievements.css',
        ),
        'output_filename': 'css_compressed/project_detail.css'
    },
    'kanban': {
        'source_filenames': (
            'widgets/kanban/task.css',
        ),
        'output_filename': 'css_compressed/kanban.css'
    },
    'taskdraft_detail': {
        'source_filenames': (
            'modules/taskdraft/taskdraft_detail.css',
        ),
        'output_filename': 'css_compressed/taskdraft_detail.css'
    },

    'markdown': {
        'source_filenames': (
            'css/bootstrap-markdown.css',
        ),
        'output_filename': 'css_compressed/markdown.css'
    },
    'user_detail': {
        'source_filenames': (
            'widgets/user_detail/style.css',
        ),
        'output_filename': 'css_compressed/user_detail.css'
    },
    'task_detail': {
        'source_filenames': (
            'widgets/task_detail/style.css',
        ),
        'output_filename': 'css_compressed/task_detail.css'
    },
    'jira_projects': {
        'source_filenames': (
            'css/project.list.css',
        ),
        'output_filename': 'css_compressed/jira.projects.css'
    },
}
