# -*- coding: utf-8 -*-

"""
gmncurses.ui.widgets.milestones
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

import urwid

from gmncurses import data

from . import generic, mixins, utils


class MilestoneInfo(urwid.WidgetWrap):
    def __init__(self, project):
        self.project = project
        self.widget = urwid.Columns([])
        super().__init__(self.widget)

    def populate(self, milestone):
        self._w = urwid.Columns([
            ("weight", 1, generic.ListText(data.milestone_name(milestone))),
        ])


class MilestoneStats(urwid.WidgetWrap):
    def __init__(self, project):
        self.project = project
        self.widget = urwid.Columns([])
        super().__init__(self.widget)

    def populate(self, milestone_stats):
        self._w = urwid.Columns([
            ("weight", 0.2, urwid.LineBox(MilestoneStatsStatus(milestone_stats), "Status")),
            ("weight", 0.3, urwid.LineBox(MilestoneStatsPoints(milestone_stats), "Points")),
            ("weight", 0.3, urwid.LineBox(MilestoneStatsTasks(milestone_stats), "Tasks")),
            ("weight", 0.3, urwid.LineBox(MilestoneStatsDates(milestone_stats), "Dates")),
         ])


class MilestoneStatsStatus(urwid.Pile):
    def __init__(self, milestone_stats):
        items = [generic.box_solid_fill(" ", 1)]
        items.append(urwid.ProgressBar("progressbar-normal",
                                       "progressbar-complete",
                                       data.milestone_completed_points(milestone_stats),
                                       data.milestone_total_points(milestone_stats),
                                       "progressbar-smooth"))
        super().__init__(items)


class MilestoneStatsPoints(urwid.Pile):
    def __init__(self, milestone_stats):
        total = data.milestone_total_points(milestone_stats)
        completed = data.milestone_completed_points(milestone_stats)
        remaining = total - completed

        items = [
            urwid.Pile([generic.ListText("Total"), generic.SemaphorePercentText(total, max_value=total)]),
            urwid.Pile([generic.ListText("Completed"), generic.SemaphorePercentText(completed, max_value=total)]),
            urwid.Pile([generic.ListText("Remaining"), generic.SemaphorePercentText(remaining, max_value=total,
                                                                                    invert=True)])
        ]
        super().__init__([urwid.Columns(items)])


class MilestoneStatsTasks(urwid.Pile):
    def __init__(self, milestone_stats):
        total = data.milestone_total_tasks(milestone_stats)
        completed = data.milestone_completed_tasks(milestone_stats)
        remaining = total - completed

        items = [
            urwid.Pile([generic.ListText("Total"), generic.SemaphorePercentText(total, max_value=total)]),
            urwid.Pile([generic.ListText("Completed"), generic.SemaphorePercentText(completed, max_value=total)]),
            urwid.Pile([generic.ListText("Remaining"), generic.SemaphorePercentText(remaining, max_value=total,
                                                                                    invert=True)])
        ]
        super().__init__([urwid.Columns(items)])


class MilestoneStatsDates(urwid.Pile):
    def __init__(self, milestone_stats):
        items = [
            urwid.Pile([generic.ListText("Start"), generic.ListText(("cyan", data.milestone_estimated_start(
                                                                                             milestone_stats)))]),
            urwid.Pile([generic.ListText("Finish"), generic.ListText(("cyan", data.milestone_estimated_finish(
                                                                                               milestone_stats)))])
        ]
        remaining_days = data.milestone_remaining_days(milestone_stats)
        if remaining_days > 1 :
            items.append(urwid.Pile([generic.ListText("Remaining"), generic.ListText(
                                          ("green", "{} days".format(remaining_days)))]))
        elif remaining_days == 1:
            items.append(urwid.Pile([generic.ListText("Remaining"), generic.ListText(
                                           ("green", "{} day".format(remaining_days)))]))
        else:
            items.append(urwid.Pile([generic.ListText("Remaining"), generic.ListText(
                                                                    ("red", "0 days"))]))

        super().__init__([urwid.Columns(items)])


class MilestoneTaskboard(urwid.WidgetWrap):
    def __init__(self, project):
        self.project = project
        self.roles = data.computable_roles(project)
        self.widget = urwid.Pile([generic.ListText("Fetching data")])
        super().__init__(self.widget)

    def populate(self, user_stories, milestone_tasks):
        if user_stories:
            self.reset()

        # Task with user stories
        for us in user_stories:
            self.widget.contents.append((UserStoryEntry(us, self.project, self.roles),
                                         ("weight", 0.1)))
            for task in data.tasks_per_user_story(milestone_tasks, us):
                self.widget.contents.append((TaskEntry(task, self.project), ("weight", 0.1)))

        # Unasigned task
        self.widget.contents.append((UnasignedTasksHeaderEntry(), ("weight", 0.1)))
        for task in data.unassigned_tasks(milestone_tasks):
            self.widget.contents.append((TaskEntry(task, self.project), ("weight", 0.1)))

        if len(self.widget.contents):
            self.widget.contents.focus = 0

    def reset(self):
        self.widget.contents = []


class UserStoryEntry(urwid.WidgetWrap):
    def __init__(self, us, project, roles):
        if us.get("is_closed", False):
            is_closed = urwid.AttrMap(generic.ListText("☑"), "green", "focus-header")
        else:
            is_closed = urwid.AttrMap(generic.ListText("☒"), "red", "focus-header")
        colum_items = [("weight", 0.05, is_closed)]

        us_ref_and_name = "US #{0: <4} {1}".format(str(data.us_ref(us)), data.us_subject(us))
        colum_items.append(("weight", 0.6, generic.ListText(us_ref_and_name, align="left")))

        hex_color, status = data.us_status_with_color(us, project)
        color = utils.color_to_hex(hex_color)
        attr = urwid.AttrSpec("h{0}".format(color), "default")
        colum_items.append(("weight", 0.15, generic.ListText( (attr, status) )))

        points_by_role = data.us_points_by_role_whith_names(us, project, roles.values())
        for role, point in points_by_role:
            colum_items.append(("weight", 0.1, generic.ListText("{}: {}".format(role, str(point)))))
        colum_items.append(("weight", 0.1, generic.ListText(("green", "TOTAL: {0:.1f}".format(
                                                                      data.us_total_points(us))))))

        self.widget = urwid.Columns(colum_items)
        super().__init__(urwid.AttrMap(urwid.LineBox(urwid.AttrMap(self.widget, "cyan", "focus-header")),
                                       "green"))

    def selectable(self):
        return True


class UnasignedTasksHeaderEntry(urwid.WidgetWrap):
    def __init__(self):
        self.widget = urwid.Columns([generic.ListText("Unassigned tasks")])
        super().__init__(urwid.AttrMap(urwid.LineBox(urwid.AttrMap(self.widget, "cyan", "focus-header")),
                                       "green"))

    def selectable(self):
        return True


class TaskEntry(urwid.WidgetWrap):
    def __init__(self, task, project):
        if data.task_finished_date(task):
            is_closed = urwid.AttrMap(generic.ListText("☑"), "green", "focus")
        else:
            is_closed = urwid.AttrMap(generic.ListText("☒"), "red", "focus")
        colum_items = [("weight", 0.05, is_closed)]

        task_ref_and_subject = "Task #{0: <4} {1}".format(data.task_ref(task), data.task_subject(task))
        colum_items.append(("weight", 1, generic.ListText(task_ref_and_subject, align="left")))

        hex_color, assigned_to = data.task_assigned_to_with_color(task, project)
        color = utils.color_to_hex(hex_color)
        attr = urwid.AttrSpec("h{0}".format(color), "default")
        colum_items.append(("weight", 0.2, generic.ListText((attr, assigned_to))))

        hex_color, status = data.task_status_with_color(task, project)
        color = utils.color_to_hex(hex_color)
        attr = urwid.AttrSpec("h{0}".format(color), "default")
        colum_items.append(("weight", 0.2, generic.ListText((attr, status))))

        self.widget = urwid.Columns(colum_items)
        super().__init__(urwid.AttrMap(self.widget, "default", "focus"))

    def selectable(self):
        return True

class MIlestoneSelectorPopup(mixins.FormMixin, urwid.WidgetWrap):
    def __init__(self, project, current_milestone={}):
        self.project = project
        self.current_milestone = current_milestone
        self.options = []

        contents = [
            generic.box_solid_fill(" ", 2),
            urwid.Padding(self._milestone_selector(), right=2, left=2),
            generic.box_solid_fill(" ", 2),
            self._buttons(),
            generic.box_solid_fill(" ", 1),
        ]
        self.widget = urwid.Pile(contents)

        title = "Change to another Milestone"
        super().__init__(urwid.AttrMap(urwid.LineBox(urwid.Padding(self.widget, right=2, left=2),
                                                     title), "popup"))

    def _milestone_selector(self):
        content = []
        for milestone in data.list_of_milestones(self.project):
            option = MilestoneOptionEntry(milestone, not data.milestones_are_equals(self.current_milestone,
                                                                               milestone))
            if option.selectable():
                self.options.append(option)

            content.append(option)
            content.append(generic.box_solid_fill(" ", 1))

        list_walker = urwid.SimpleFocusListWalker(content)
        if len(content) > 0:
            list_walker.set_focus(0)
        return urwid.BoxAdapter(urwid.ListBox(list_walker), 20)

    def _buttons(self):
        self.cancel_button = generic.PlainButton("Cancel")

        colum_items = [("weight", 1, urwid.Text(""))]
        colum_items.append((15, urwid.AttrMap(urwid.Padding(self.cancel_button, right=1, left=2),
                                              "popup-cancel-button")))
        return urwid.Columns(colum_items)


class MilestoneOptionEntry(mixins.KeyPressMixin, urwid.WidgetWrap):
    is_selectable = True

    def __init__(self, milestone, is_selectable=True):
        self.milestone = milestone
        self.is_selectable = is_selectable

        content = [
            urwid.Columns([
                (3, self._is_closed_widget()),
                ("weight", 0.8, self._name_widget()),
                ("weight", 0.2, self._progress_status_widget()),
            ]),
            urwid.Columns([
                (3, urwid.Text("")),
                ("weight", 0.4, self._finish_date_widget()),
                ("weight", 0.4, self._total_points_widget()),
                ("weight", 0.4, self._closed_points_widget()),
            ])
        ]

        self.widget = urwid.Pile(content)
        super().__init__(urwid.AttrMap(urwid.LineBox(urwid.AttrMap(self.widget, "default")),
                                       "default" if self.is_selectable else "popup-selected", "focus"))

    def selectable(self):
        return self.is_selectable

    def _is_closed_widget(self):
        if self.milestone.get("closed", False):
            return urwid.AttrMap(generic.ListText("☑"), "green")
        else:
            return urwid.AttrMap(generic.ListText("☒"), "red")

    def _name_widget(self):
        return urwid.Text(data.milestone_name(self.milestone))

    def _progress_status_widget(self):
        return urwid.ProgressBar("progressbar-normal",
                                 "progressbar-complete",
                                 data.milestone_closed_points(self.milestone),
                                 data.milestone_total_points(self.milestone),
                                 "progressbar-smooth")

    def _finish_date_widget(self):
        return urwid.Columns([
           urwid.Text("Finish date"),
           urwid.Text(("cyan", data.milestone_finish_date(self.milestone))),
        ])

    def _total_points_widget(self):
        return urwid.Columns([
           urwid.Text("Total points"),
           generic.SemaphorePercentText(data.milestone_total_points(self.milestone),
                                        data.milestone_total_points(self.milestone))
        ])

    def _closed_points_widget(self):
         return urwid.Columns([
           urwid.Text("Closed points"),
           generic.SemaphorePercentText(data.milestone_closed_points(self.milestone),
                                        data.milestone_total_points(self.milestone))
        ])
