$(function () {
    var COOKIES_NAME = 'today_tasks',
        PROJECT_DATA_NAME = 'project',
        PROJECT_MILESTONE_ID = 'milestone',
        TODAY_COLUMN_CODE = 'today',
        READY_COLUMN_CODE = 'ready',
        REVISION_COLUMN_CODE = 'revision',
        PREVINDEX_NAME = 'data-previndex',
        TASK_COLUMN_SELECTOR = '.js-tasks-column',
        REL_ATTRIBUTE = 'rel',
        PARENT_BLOCK_MODEL_KEY = 'parentBlock',
        TASK_SELECTOR = '.task',
        EMPTY_TASK_CLASS = 'kanban-empty-task',
        UI_SORTABLE_HELPER_CLASS = 'ui-sortable-helper',
        EASING_EFFECT_WHITESPACE = 'easeOutCubic',
        EASING_EFFECT = 'easeOutCubic',
        PROJECT_ROW_SELECTOR = '.js-project-row',
        PLACEHOLDER_CLASS = 'task-kanban-dummy',
        insertTask = function insertTask(index, column, what) {
            if (index === -1) {
                return what.appendTo(column);
            }
            if (index >= 1) {
                return what.insertAfter(column.find(TASK_SELECTOR + ':eq(' + (index - 1) + ')'));
            } else {
                return what.prependTo(column);
            }
        },
        animateAppendTo = function animateAppendTo(item, sel, speed, fn) {
            item = $(item);

            var frame = {top: 0, left: 0},
                origin = item.offset(),
                whiteSpace = $('<div>').addClass(EMPTY_TASK_CLASS),
                whiteSpaceOrigin = whiteSpace.clone(),
                currentIndex = item.index(),
                column = item.parent(),
                destination, adjustDuration, previndex;
            previndex = parseInt(item.attr(PREVINDEX_NAME));
            if (isNaN(previndex)) {
                previndex = -1;
            }
            item.removeAttr(PREVINDEX_NAME);
            insertTask(previndex, sel, whiteSpace);
            destination = whiteSpace.offset();
            item.css({
                position: 'absolute',
                width: item.width(),
                height: item.height(),
                left: origin.left - frame.left,
                top: origin.top - frame.top,
                margin: 0,
                'z-index': 99999
            }).addClass(UI_SORTABLE_HELPER_CLASS);
            insertTask(currentIndex, column, whiteSpaceOrigin);
            whiteSpaceOrigin.hide({
                duration: speed,
                complete: function () {
                    whiteSpaceOrigin.remove();
                },
                easing: EASING_EFFECT_WHITESPACE
            });
            adjustDuration = Math.sqrt(
                    Math.pow(destination.top - origin.top, 2) +
                    Math.pow(destination.left - origin.left, 2)
                ) * speed / 400;
            item.animate({
                top: destination.top - frame.top,
                left: destination.left - frame.left
            }, adjustDuration, EASING_EFFECT, function () {
                insertTask(previndex, sel, item);
                whiteSpace.remove();
                item.attr('style', '').removeClass(UI_SORTABLE_HELPER_CLASS);
                if (typeof(fn) === 'function') {
                    fn.call(item);
                }
            });

            return false;
        };

    window.taskViewKanbanClass = window.taskViewClass.extend({
        'showResponsibleArrow': function (userList) {
            var TASK_EXECUTOR_SELECTOR = '.js-task-executor',
                ARROW_DISTANCE_TO_CENTER = 8,
                ARROW_SELECTOR = '.add-user-popup-top-arrow',
                taskExecutor = this.$(TASK_EXECUTOR_SELECTOR),
                linkLeftOffset = taskExecutor.offset(),
                linkWidth = taskExecutor.innerWidth(),
                ulOffset = userList.offset(),
                arrowPos;
            arrowPos = linkWidth / 2 - ARROW_DISTANCE_TO_CENTER;
            if (ulOffset.left < linkLeftOffset.left) {
                arrowPos += linkLeftOffset.left - ulOffset.left + ARROW_DISTANCE_TO_CENTER;
            }
            userList.find(ARROW_SELECTOR).css('left', arrowPos);
        },
        'responsibleMenuPosition': function (userList) {
            var TASK_EXECUTOR_SELECTOR = '.js-task-executor',
                taskExecutor = this.$(TASK_EXECUTOR_SELECTOR),
                offset = this.$el.offset(),
                height = taskExecutor.height() + taskExecutor.position().top,
                width = this.$el.width(),
                ulistW = userList.width(),
                totalW = $(window).width(),
                left;
            left = offset.left + 20;
            if (left + ulistW >= totalW - 4) {
                left = totalW - ulistW - 5;
            }
            userList.css({
                'position': 'absolute',
                'top': offset.top + height,
                'left': left,
                'right': 'auto',
                'z-index': 999999
            });
        },
    });
    $.widget("custom.kanban", {
        requestUrl: '/task_handler',
        options: {
            value: 0,
            project: 0,
            useColors: false,
            revertDuration: 50,
            animateDuration: 300,
            appendItemsTo: 'body',
            taskidKey: 'taskid'
        },
        _create: function () {
            this.ajax = {};
            this._columns = {};
            this.taskViews = {};
            this.columnProperty = 'status';
            this.initOptions();
            this.initColumns();
            this.initRequest();
            this.getTasksFromServer();
            this.initListeners();
        },
        initColumns: function initColumns() {
            var column;
            this.$columns = this.element.find(TASK_COLUMN_SELECTOR);
            for (var i = this.$columns.length - 1; i >= 0; i--) {
                column = this.$columns[i];
                this._columns[$(column).attr(REL_ATTRIBUTE)] = $(column);
            }
        },
        initOptions: function initOptions() {
            this.options.project = this.element.data(PROJECT_DATA_NAME);
            this.options.milestone_id = this.element.data(PROJECT_MILESTONE_ID);
            this.options.useColors = this.element.data('use_colors');
            if (this.options.useColors) {
                this.columnProperty = 'color';
            }
        },
        initRequest: function initRequest() {
            var t = this,
                propName = this.options.useColors == false ? 'status__code' : this.columnProperty,
                props = [propName],
                propVals = {};
            for (var i = this._columns.length - 1; i >= 0; i--) {
                propVals['gantt_prop_' + propName] = [i];
            }
            this.ajax.props = props;
            this.ajax.propVals = propVals;
        },
        initListeners: function () {
            baseConnector.addListener('fs.comment.add', function (message) {
                if (message.project.id != window.currentProject) return;
                var mesType, code = (message.code + '').toLowerCase();
                if (code == 'warning') {
                    mesType = "warning"
                }
                else {
                    mesType = "info"
                }
                toastr[mesType]((message.task ? '<a href="' + message.task.url + '">Новое сообщение</a><br />' : '') + message.text + '</a>');
            });
        },
        getTasksFromServer: function getTasksFromServer() {
            var t = this;

            var extFilter = {};
            if (!this.options.milestone_id) {
                extFilter['closed[]'] = 'N';
            }

            PM_AjaxPost(
                t.requestUrl,
                $.extend({
                    'action': 'all',
                    'milestone_id': this.options.milestone_id,
                    'startPage': 3,
                    'project': this.options.project,
                    'withoutParent': 'Y',
                    'gantt_props': this.ajax.props
                }, this.ajax.propVals, extFilter),
                function (data) {
                    var i, taskData;
                    for (i in data.tasks) {
                        taskData = data.tasks[i];
                        t.addTaskRow(taskData);
                    }
                    //t.filterTodayTasks();
                    t.onModelChange();
                    t.makeItSortable();
                },
                'json'
            )
        },
        getXls: function () {
            var t = this;

            PM_AjaxPost(
                t.requestUrl,
                $.extend({
                    'action': 'all',
                    'milestone_id': this.options.milestone_id,
                    'startPage': 3,
                    'withoutParent': 'Y',
                    'project': this.options.project,
                    'gantt_props': this.ajax.props,
                    'xls': 1
                }, this.ajax.propVals),
                function (data) {
                    if (data.file)
                        document.location.href = data.file;
                },
                'json'
            )
        },
        addTaskToColumn: function addTaskToColumn(taskid, column, oldColumn) {
            //var todayTasks = getTodayTasks(this.options.project);
            //if (column == TODAY_COLUMN_CODE) {
            //    if ($.inArray(taskid, todayTasks) == -1) {
            //        todayTasks.push(taskid);
            //    }
            //    setTodayTasks(this.options.project, todayTasks);
            //} else if (oldColumn == TODAY_COLUMN_CODE) {
            //    for (var i = todayTasks.length; --i >= 0;) {
            //        if (todayTasks[i] === taskid) todayTasks.splice(i, 1);
            //    }
            //    setTodayTasks(this.options.project, todayTasks)
            //}
        },
        onModelChange: function onModelChange() {
            var t = this;
            baseConnector.addListener('fs.task.update', function (data) {
                if (!data || !data.id || !t.taskViews[data.id]) {
                    return;
                }
                var view = t.taskViews[data.id],
                    oldColumn = view.$el.parent().attr(REL_ATTRIBUTE),
                    returnToFix = function () {
                        return (data['status'] == REVISION_COLUMN_CODE &&
                            ($.inArray(view.model.get('status'), [READY_COLUMN_CODE, TODAY_COLUMN_CODE]) > -1) &&
                            view.model.get('resp') && view.model.get('resp')[0] &&
                            document.mainController.userId == view.model.get('resp')[0]['id']
                        );
                    };

                if (data['closed']) {
                    data['status'] = 'closed';
                }
                for (var i in data) {
                    if (i == 'viewedOnly') {
                        if (data[i] != document.mainController.userId) {
                            view.model.set('viewed', false);
                        }
                    }
                    if (i == 'resp' && data[i][0] && data[i][0].hasOwnProperty('avatar')) {
                        view.model.set('avatar', data[i][0].avatar);
                    }
                    if (i != 'id') {
                        view.model.set(i, data[i]);
                    }
                }

                view.render();
                var col = view.model.get(t.columnProperty);
                if (col && oldColumn != col) {
                    animateAppendTo(view.$el, t._columns[col], t.options.animateDuration, function () {
                        t.addTaskToColumn(view.model.id, col, oldColumn);
                    });
                }

                t._columns[col].sortable("refresh");
            });

            baseConnector.addListener('fs.task.add', function (data) {
                if (!data || !data.id) {
                    return;
                }

                if (data.project.id != t.options.project) return;

                if (t.options.milestone_id) {
                    if (data.milestoneId != t.options.milestone_id) return;
                }

                t.addTaskRow(data);
            });
        },
        makeItSortable: function makeItSortable() {
            var t = this;
            this.$columns.sortable({
                connectWith: PROJECT_ROW_SELECTOR + '#project_' + t.options.project + ' ' + TASK_COLUMN_SELECTOR,
                items: "> " + TASK_SELECTOR + ":not(.closed)",
                placeholder: PLACEHOLDER_CLASS,
                dropOnEmpty: true,
                revert: t.options.revertDuration,
                appendTo: $(t.options.appendItemsTo),
                start: function (event, ui) {
                    var taskid = ui.item.data('taskid'),
                        view = t.taskViews[taskid];
                    ui.item.attr(PREVINDEX_NAME, ui.item.index());
                    view.model.set(PARENT_BLOCK_MODEL_KEY, view.$el.parent());
                    view.model.set('oldStatusName', t.columnProperty);
                    view.model.set('oldStatus', view.model.get(t.columnProperty));
                },
                receive: function (event, ui) {
                    var toColumn = $(event.target).attr(REL_ATTRIBUTE);
                    var fromColumn = ui.sender.attr(REL_ATTRIBUTE);
                    var taskid = ui.item.data(t.options.taskidKey);
                    t.addTaskToColumn(taskid, toColumn, fromColumn);
                    if (toColumn == TODAY_COLUMN_CODE) {
                        t.taskViews[taskid].model.set(t.columnProperty, toColumn);
                        t.taskViews[taskid].render();
                        return;
                    }
                    var cb = function (data) {
                        try {
                            data = $.parseJSON(data);
                        } catch (e) {
                            console.log(e);
                            return;
                        }
                        if (data.error) {
                            alert(data.error);
                            animateAppendTo(t.taskViews[taskid].$el, t._columns[fromColumn], t.options.animateDuration, function () {
                                t.$columns.sortable('refreshPositions');
                            });
                        } else {
                            t.taskViews[taskid].model.set(t.columnProperty, toColumn);
                            t.taskViews[taskid].render();
                        }
                    };

                    if (toColumn == 'closed') {
                        taskManager.TaskClose(taskid, cb);
                    } else {
                        taskManager.SetTaskProperty(
                            taskid,
                            t.columnProperty,
                            toColumn,
                            cb
                        );
                    }
                }
            });
        },
        addTaskRow: function addTaskRow(taskData) {
            var t = this;
            var key = taskData[t.columnProperty];
            if (taskData['closed']) {
                key = 'closed'
            }
            var task = new window.taskClass(taskData);
            var taskView = new window.taskViewKanbanClass({'model': task});
            if (t._columns[key]) {
                task.set(t.columnProperty, key);
                taskView.createEl().render();
                t._columns[key].append(taskView.$el);
                t.taskViews[task.id] = taskView;
            } else {
                console.log('error encountered, task could not resolve column');
                return false;
            }
        }
    });

    $('.js-project-row').each(function () {
        var t = this;
        $(this).kanban();

        $(this).find('.js-get-xls-milestone').click(function () {
            $(t).kanban('getXls');
            return false;
        });
    });

    $('.js-select-milestone').change(function () {
        document.location.href = '?milestone=' + $(this).val();
    });
});
