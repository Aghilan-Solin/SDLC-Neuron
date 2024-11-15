from dash import Dash, html, dcc, callback, Input, Output, State, ALL
from dash import callback_context as ctx
import dash_bootstrap_components as dbc
import uuid
from threading import Thread
import webview
from components.reminderAIO import ReminderAIO
from components.app_header import render_appheader
import time
import logging

log_handler = logging.FileHandler(filename=r"Log\Neuron.log", encoding="utf-8")
logging.basicConfig(handlers=[log_handler], level=logging.DEBUG)


def create_reminder():
    new_reminder = ReminderAIO()
    reminder_id = str(uuid.uuid4())
    return html.Div(
        [
            html.Div(new_reminder, id=reminder_id),
            html.Button("🗑️", id={"type": "delete-button",
                                   "index": reminder_id}),
        ]
    )


app = Dash(__name__, external_stylesheets=[dbc.themes.SIMPLEX])

# Create layout for the app
app.layout = html.Div(
    [
        render_appheader(),  # Header component that will display current time
        html.Button("Add Reminder", id="add-reminder-button"),
        html.Div(id="reminder-container"),
        dcc.Interval(  # Interval to trigger time updates
            id="interval-update",
            interval=1000,  # Update every 1000 milliseconds (1 second)
            n_intervals=0,
        ),
    ]
)

server = app.server
reminders = []


def run_app():
    app.run_server(debug=True)


@callback(
    output=Output("reminder-container", "children", allow_duplicate=True),
    inputs=Input("add-reminder-button", "n_clicks"),
    prevent_initial_call=True,
)
def add_reminder(add_reminder_button_click):
    try:
        if add_reminder_button_click is None or add_reminder_button_click == 0:
            return []

        reminder = create_reminder()
        reminders.append(reminder)
        return reminders
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

        for reminder in current_reminders:
            if reminder["props"]["children"][0]["props"]["id"] != reminder_id:
                updated_reminders.append(reminder)
        return updated_reminders
    except Exception as ex:
        logging.error("Exception occurred when deleting reminder %ex", ex)


def get_current_time():
    return time.strftime("%d/%m/%Y - %H:%M:%S")


@callback(Output("current-time", "children"), 
          Input("interval-update", "n_intervals"))
def update_time(n_intervals):
    return get_current_time()


if __name__ == "__main__":
    # run_app()
    t = Thread(target=run_app)
    t.daemon = True
    t.start()
    webview.create_window("Neuron", server)
    webview.start(debug=False)
