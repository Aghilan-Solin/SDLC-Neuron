from dash import Dash, html, dcc, callback, Input, Output, State, ALL, MATCH
from dash.exceptions import PreventUpdate
from dash import callback_context as ctx
import dash_bootstrap_components as dbc
import uuid
from threading import Thread
import webview
from components.reminderAIO import ReminderAIO
from components.app_header import render_appheader
import time
from datetime import datetime
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
import os


log_dir = r"Log"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
log_handler = logging.FileHandler(filename=os.path.join(log_dir, "Neuron.log"), encoding="utf-8")
log_format = "%(asctime)s: %(levelname)s: %(message)s"
logging.basicConfig(handlers=[log_handler], level=logging.DEBUG, format=log_format)
scheduler = BackgroundScheduler()


def schedule_reminder(reminder_id, reminder_time, reminder_type):
    """Schedule a reminder based on the reminder type."""

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
    elif reminder_type == "Once in every N days":
        n_days = int(input("Enter number of days: "))
        trigger = IntervalTrigger(days=n_days, start_date=reminder_time)

    if trigger is not None:
        scheduler.add_job(
            trigger_reminder,
            trigger,
            args=[reminder_id],
            id=str(reminder_id),  # Use the reminder's ID as job ID to track it
        )
        logging.info(
            f"Scheduled reminder {reminder_id} at {reminder_time} with type {reminder_type}"
        )


def trigger_reminder(reminder_id):
    """Function to trigger a reminder (e.g., show modal)."""
    logging.info(f"Reminder {reminder_id} triggered at {datetime.now()}")
    # Trigger the modal window when the reminder is hit
    # Use Dash callbacks to show the modal with two buttons: 'OK' and 'Snooze'
    return reminder_id  # This can trigger the modal to be shown


def create_reminder(reminder_id):
    new_reminder = ReminderAIO()
    return html.Div(
        [
            html.Div(new_reminder, id=reminder_id),
            html.Button("🗑️", id={"type": "delete-button", "index": reminder_id}),
        ]
    )


def start_scheduler():
    """Start the APScheduler in the background."""
    scheduler.start()


app = Dash(__name__, external_stylesheets=[dbc.themes.SIMPLEX])

app.layout = html.Div(
    [
        render_appheader(),  # Header component that will display current time
        html.Button("Add Reminder", id="add-reminder-button"),
        html.Div(id="reminder-container"),
        dcc.Interval(
            id="interval-update",
            interval=1000,
            n_intervals=0,
        ),
        dbc.Modal(
            [
                dbc.ModalHeader("Reminder Triggered"),
                dbc.ModalBody("Reminder details will be shown here."),
                dbc.ModalFooter(
                    dbc.Button("OK", id="close-modal", className="ml-auto")
                ),
            ],
            id="reminder-modal",
            is_open=False,
        ),
    ]
)

server = app.server


def run_app():
    app.run_server(debug=True)


@callback(
    output=Output("reminder-container", "children", allow_duplicate=True),
    inputs=Input("add-reminder-button", "n_clicks"),
    state=State("reminder-container", "children"),
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
    output=Output("reminder-container", "children"),
    inputs=Input({"type": "delete-button", "index": ALL}, "n_clicks"),
    state=State("reminder-container", "children"),
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

        return updated_reminders

    except Exception as ex:
        logging.error(f"Exception occurred when deleting reminder: {ex}")
        raise PreventUpdate()


def get_current_time():
    return time.strftime("%d/%m/%Y - %H:%M:%S")


@callback(Output("current-time", "children"), Input("interval-update", "n_intervals"))
def update_time(n_intervals):
    return get_current_time()


@callback(
    Output(
        {"component": "ReminderAIO", "subcomponent": "input", "aio_id": MATCH}, "value"
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
    prevent_initial_call=True,
)
def schedule_new_reminder(reminder_date, reminder_time, reminder_type):
    """Callback to schedule the reminder."""
    try:
        if not reminder_date or not reminder_time or not reminder_type:
            return None

        triggered_id = ctx.triggered_id
        reminder_id = triggered_id["aio_id"]

        if reminder_date and reminder_time:
            print(f"Reminder ID {reminder_id}")
            print(f"Reminder Date {reminder_date}")
            print(f"Reminder Time {reminder_time}")
            print(f"Reminder Type {reminder_type}")

        reminder_datetime = datetime.combine(
            datetime.strptime(reminder_date, "%Y-%m-%d"),
            datetime.strptime(reminder_time, "%H:%M").time(),
        )
        print(f"Reminder datetime {reminder_datetime}")
        schedule_reminder(reminder_id, reminder_datetime, reminder_type)

        logging.info(
            f"Reminder {reminder_id} scheduled for {reminder_datetime} of type {reminder_type}"
        )

        raise PreventUpdate()

    except Exception as e:
        logging.error(f"Error while scheduling reminder: {e}")
        raise PreventUpdate()

@callback(
    output=Output('reminder-modal', 'is_open'),
    inputs=Input()
)
if __name__ == "__main__":

    t_scheduler = Thread(target=start_scheduler)
    t_scheduler.daemon = True
    t_scheduler.start()

    # run_app()
    t_app = Thread(target=run_app)
    t_app.daemon = True
    t_app.start()
    webview.create_window("Neuron", server)
    webview.start(debug=False)
