from dash import Dash, html, dcc, callback, Input, Output, State, ALL, MATCH
from dash.exceptions import PreventUpdate
from dash import callback_context as ctx
import dash_bootstrap_components as dbc
import uuid
from threading import Thread
import webview
from components.reminderAIO import ReminderAIO
from components.app_header import render_appheader
from components import ids
import time
from datetime import datetime, timedelta
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
import os

log_dir = r"Log"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
log_handler = logging.FileHandler(
    filename=os.path.join(log_dir, "Neuron.log"), encoding="utf-8"
)
log_format = "%(asctime)s: %(levelname)s: %(message)s"
logging.basicConfig(handlers=[log_handler], level=logging.DEBUG, format=log_format)
scheduler = BackgroundScheduler()

app = Dash(__name__, external_stylesheets=[dbc.themes.SIMPLEX])
server = app.server


def schedule_reminder(
    reminder_message, reminder_id, reminder_time, reminder_type, n_days=None
):
    """Schedule a reminder based on the reminder type."""
    trigger = None

    if reminder_type == "Once only":
        trigger = DateTrigger(run_date=reminder_time)
    elif reminder_type == "Daily":
        trigger = IntervalTrigger(days=1, start_date=reminder_time)
    elif reminder_type == "Every Week":
        trigger = CronTrigger(
            day_of_week="sun", hour=reminder_time.hour, minute=reminder_time.minute
        )
    elif reminder_type == "Every Month":
        trigger = CronTrigger(
            day=reminder_time.day, hour=reminder_time.hour, minute=reminder_time.minute
        )
    elif reminder_type == "Every Year":
        trigger = CronTrigger(
            month=reminder_time.month,
            day=reminder_time.day,
            hour=reminder_time.hour,
            minute=reminder_time.minute,
        )
    elif reminder_type == "Once in every" and n_days:
        trigger = IntervalTrigger(days=n_days, start_date=reminder_time)

    if trigger is not None:
        scheduler.add_job(
            func=trigger_reminder,
            trigger=trigger,
            args=[reminder_message, reminder_id, reminder_time, reminder_type],
            id=reminder_id,
        )

        print(scheduler.get_jobs())
        logging.info(
            f"Scheduled reminder {reminder_id} at {reminder_time} with type {reminder_type}"
        )
        return reminder_id


reminder_status = None


def trigger_reminder(reminder_message, reminder_id, reminder_time, reminder_type):
    """Function to trigger a reminder (e.g., show modal)."""
    msg = f"""Reminder {reminder_id} with message {reminder_message} and
            type {reminder_type} triggered at {datetime.now()}"""
    logging.info(msg)
    global reminder_status
    reminder_status = (reminder_id, f"{reminder_message} scheduled at {reminder_time} is triggered")
    return reminder_message, reminder_type, reminder_time


def create_reminder(reminder_id):
    new_reminder = ReminderAIO(aio_id=reminder_id)
    return html.Div(
        [
            html.Div(new_reminder, id=reminder_id),
            html.Button("🗑️", id={"type": "delete-button", "index": reminder_id}),
        ]
    )


def start_scheduler():
    """Start the APScheduler in the background."""
    scheduler.start()


reminder_tabs = html.Div(
    [
        dcc.Tabs(
            id=ids.UPCOMING_MISSED_REMINDERS_TABS,
            value="upcoming-reminders",
            children=[
                dcc.Tab(label="Upcoming Reminders", value="upcoming-reminders"),
                dcc.Tab(label="Missed Reminders", value="missed-reminders"),
            ],
        ),
        html.Div(
            id=ids.TAB_CONTENT_CONTAINER,
            style={"pointer-events": "none", "cursor": "not-allowed"},
        ),
    ]
)


def get_upcoming_reminders(current_reminders):
    div_elements = []

    for reminder in current_reminders:
        reminder_message, reminder_type, reminder_datetime, n_days_value = get_reminderinfo(reminder)

        if reminder_datetime > datetime.now():
            if n_days_value:
                msg = f"Reminder {reminder_message} of type: {reminder_type} scheduled for {reminder_datetime} repeating every {n_days_value}"
            else:
                msg = f"Reminder {reminder_message} of type: {reminder_type} scheduled for {reminder_datetime}"
            div_elements.append(msg)

    return div_elements


def get_reminderinfo(reminder):
    aio_component = reminder["props"]["children"][0]
    subcomponents = aio_component["props"]["children"]["props"]["children"][0]["props"][
        "children"
    ]
    message_component = subcomponents[0]
    reminder_type_component = subcomponents[1]
    date_component = subcomponents[2]
    time_component = subcomponents[3]
    every_n_days_component = subcomponents[4]

    message = message_component["props"]["children"]["props"]["value"]
    reminder_type = reminder_type_component["props"]["children"]["props"]["value"]
    date_value = date_component["props"]["children"]["props"]["date"]
    time_value = time_component["props"]["children"]["props"]["value"]

    if not (every_n_days_component["props"]["children"]["props"]["disabled"]):
        n_days_value = every_n_days_component["props"]["children"]["props"]["value"]
    else:
        n_days_value = None
    reminder_datetime_str = f"{date_value} {time_value}"
    reminder_datetime = datetime.strptime(reminder_datetime_str, "%Y-%m-%d %H:%M")

    return message, reminder_type, reminder_datetime, n_days_value


app.layout = html.Div(
    [
        render_appheader(),
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Reminder Status"), close_button=False),
                dbc.ModalBody(id=ids.REMINDER_STATUS_MODAL_BODY),
                dbc.ModalFooter([dbc.Button("Snooze", id=ids.SNOOZE_BUTTON, n_clicks=0,color="dark"),
                                 dbc.Button("OK", id=ids.OK_BUTTON, n_clicks=0, color="info")]),
            ],
            id=ids.REMINDER_STATUS_MODAL,
            is_open=False,
            centered=True,
            keyboard=False
        ),
        html.Button("Add Reminder", id=ids.ADD_REMINDER_BUTTON),
        html.Div(id=ids.REMINDER_CONTAINER),
        dcc.Interval(id=ids.UPDATE_TIME_IN_INTERVALS, interval=1000, n_intervals=0),
        dcc.Store(id=ids.REMINDER_STATUS_MESSAGE_STORE),
        dcc.Interval(
            id=ids.REMINDER_POLL_UPDATE_IN_INTERVALS, interval=50, n_intervals=0
        ),
        reminder_tabs,
    ]
)


def run_app():
    app.run_server(debug=False)


@callback(
    output=Output(ids.REMINDER_CONTAINER, "children", allow_duplicate=True),
    inputs=Input("add-reminder-button", "n_clicks"),
    state=State(ids.REMINDER_CONTAINER, "children"),
    prevent_initial_call=True,
)
def add_reminder(add_reminder_button_click, current_reminders):
    try:
        if current_reminders is None:
            current_reminders = []

        if add_reminder_button_click is None or add_reminder_button_click == 0:
            return current_reminders
        reminder_id = str(uuid.uuid4())
        new_reminder = create_reminder(reminder_id)
        return current_reminders + [new_reminder]
    except Exception as ex:
        logging.error("Exception occurred when adding reminder %ex", ex)


@callback(
    output=Output(ids.REMINDER_CONTAINER, "children"),
    inputs=Input({"type": "delete-button", "index": ALL}, "n_clicks"),
    state=State(ids.REMINDER_CONTAINER, "children"),
    prevent_initial_call=True,
)
def delete_reminder(delete_button_click, current_reminders):
    try:
        if not delete_button_click or not any(delete_button_click):
            return current_reminders

        reminder_id = ctx.triggered_id["index"]
        updated_reminders = []

        job = scheduler.get_job(str(reminder_id))

        if job:
            scheduler.remove_job(str(reminder_id))
            logging.info(f"Removed reminder {reminder_id} from scheduler")
        else:
            logging.info(f"No job found for reminder {reminder_id}, skipping removal.")

        for reminder in current_reminders:
            if reminder["props"]["children"][0]["props"]["id"] != reminder_id:
                updated_reminders.append(reminder)
        print(f'Jobs during scheduling {scheduler.get_jobs()}')
        return updated_reminders

    except Exception as ex:
        logging.error(f"Exception occurred when deleting reminder: {ex}")
        raise PreventUpdate()


@callback(
    Output("current-time", "children"),
    Input(ids.UPDATE_TIME_IN_INTERVALS, "n_intervals"),
)
def update_time(n_intervals):
    return time.strftime("%d/%m/%Y - %H:%M:%S")


@callback(
    Output(
        {"component": "ReminderAIO", "subcomponent": "input", "aio_id": MATCH}, "value"
    ),
    Input(
        {"component": "ReminderAIO", "subcomponent": "dbc.Input", "aio_id": MATCH},
        "value",
    ),
    Input(
        {"component": "ReminderAIO", "subcomponent": "datepicker", "aio_id": MATCH},
        "date",
    ),
    Input(
        {"component": "ReminderAIO", "subcomponent": "input", "aio_id": MATCH}, "value"
    ),
    Input(
        {"component": "ReminderAIO", "subcomponent": "dcc.Dropdown", "aio_id": MATCH},
        "value",
    ),
    Input(
        {"component": "ReminderAIO", "subcomponent": "n-days-input", "aio_id": MATCH},
        "value",
    ),
    prevent_initial_call=True,
)
def schedule_new_reminder(
    reminder_message, reminder_date, reminder_time, reminder_type, n_days
):
    """Callback to schedule the reminder."""
    try:
        if not reminder_date or not reminder_time or not reminder_type:
            return None

        triggered_id = ctx.triggered_id
        reminder_id = triggered_id["aio_id"]

        if (
            reminder_message
            and reminder_date
            and reminder_time
            and reminder_type
            and reminder_id
        ):
            reminder_datetime = datetime.combine(
                datetime.strptime(reminder_date, "%Y-%m-%d"),
                datetime.strptime(reminder_time, "%H:%M").time(),
            )

            if reminder_type == "Once in every" and n_days:
                schedule_reminder(
                    reminder_message,
                    reminder_id,
                    reminder_datetime,
                    reminder_type,
                    n_days,
                )
            else:
                schedule_reminder(
                    reminder_message, reminder_id, reminder_datetime, reminder_type
                )
        raise PreventUpdate()
    except Exception as e:
        logging.error(f"Error while scheduling reminder: {e}")
        raise PreventUpdate()


@callback(
    Output(ids.REMINDER_STATUS_MESSAGE_STORE, "data"),
    Input(ids.REMINDER_POLL_UPDATE_IN_INTERVALS, "n_intervals"),
)
def poll_data(n_intervals):
    global reminder_status
    if reminder_status:
        return reminder_status
    raise PreventUpdate()


@callback(
    [
        Output(ids.REMINDER_STATUS_MODAL, "is_open"),
        Output(ids.REMINDER_STATUS_MODAL_BODY, "children"),
        Output(ids.OK_BUTTON, 'n_clicks'),
        Output(ids.SNOOZE_BUTTON, 'n_clicks'),
    ],
    [
        Input(ids.REMINDER_STATUS_MESSAGE_STORE, "data"),
        Input(ids.OK_BUTTON, "n_clicks"),
        Input(ids.SNOOZE_BUTTON, "n_clicks"),
    ],
    [State(ids.REMINDER_STATUS_MODAL, "is_open"), State(ids.REMINDER_CONTAINER, 'children')],
    prevent_initial_call=True,
)
def show_modal(store_object_data, ok_click , snooze_click, is_open, current_reminders):
    """Callback to show/hide the modal and update its content."""
    global reminder_status
    reminder_id = store_object_data[0]
    message = store_object_data[1]
    print(f'reminder status {reminder_status}')
    if ok_click:
        reminder_status = None
        return False, None, None, None
    if snooze_click:
        snooze_reminder(reminder_id, current_reminders)
        reminder_status = None
        return False, None, None, None
    if message:
        reminder_status = None
        return True, message, None, None
    return is_open, None, None, None



@callback(
    output=Output(ids.TAB_CONTENT_CONTAINER, "children"),
    inputs=Input(ids.UPCOMING_MISSED_REMINDERS_TABS, "value"),
    state=State(ids.REMINDER_CONTAINER, "children"),
    prevent_initial_call=True,
)
def render_tab_content(tab, current_reminders):
    if tab == "upcoming-reminders":
        upcoming_reminders = get_upcoming_reminders(current_reminders)
        return html.Ul([html.Li(x) for x in upcoming_reminders])
    elif tab == "missed-reminders":
        return html.Div("Missed reminders yet to be implemented")


def snooze_reminder(reminder_id, current_reminders):
    reminder = search_reminder_with_reminder_id(reminder_id, current_reminders)
    reminder_message, reminder_type, reminder_datetime, n_days_value = get_reminderinfo(reminder)
    print(reminder_datetime)
    reminder_datetime = reminder_datetime + timedelta(seconds=10)
    print(reminder_datetime)
    if n_days_value:
        schedule_reminder(reminder_message, reminder_id, reminder_datetime, reminder_type, n_days_value)
    schedule_reminder(reminder_message, reminder_id, reminder_datetime, reminder_type)
    print("Snoozed Reminder successfully")

def search_reminder_with_reminder_id(reminder_id, current_reminders):
    for reminder in current_reminders:
        if reminder["props"]["children"][0]["props"]["id"] == reminder_id:
            return reminder



if __name__ == "__main__":
    # t_scheduler = Thread(target=start_scheduler)
    # t_scheduler.daemon = True
    # t_scheduler.start()
    start_scheduler()

    run_app()
    # t_app = Thread(target=run_app)
    # t_app.daemon = True
    # t_app.start()
    # webview.create_window("Neuron", server)
    # webview.start(debug=True)
