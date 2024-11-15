from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
import uuid
from datetime import date

reminder_types = [
    "Daily",
    "Every Week",
    "Every Month",
    "Every Year",
    "Once only",
    "Once in every",
]


class ReminderAIO(html.Div):
    class ids:
        @staticmethod
        def reminder_message_input(aio_id):
            return {
                "component": "ReminderAIO",
                "subcomponent": "dbc.Input",
                "aio_id": aio_id,
            }

        @staticmethod
        def reminder_type_dropdown(aio_id):
            return {
                "component": "ReminderAIO",
                "subcomponent": "dcc.Dropdown",
                "aio_id": aio_id,
            }

        @staticmethod
        def reminder_datepicker(aio_id):
            return {
                "component": "ReminderAIO",
                "subcomponent": "datepicker",
                "aio_id": aio_id,
            }

        @staticmethod
        def reminder_time_input(aio_id):
            return {
                "component": "ReminderAIO",
                "subcomponent": "input",
                "aio_id": aio_id,
            }

    ids = ids

    def __init__(
        self,
        aio_id=None,
        reminder_message_input_properties=None,
        reminder_type_dropdown_properties=None,
        reminder_datepicker_properties=None,
        reminder_time_input_properties=None,
    ):
        if aio_id is None:
            aio_id = str(uuid.uuid4())

        # Reminder input properties
        reminder_message_input_properties = (
            reminder_message_input_properties.copy()
            if reminder_message_input_properties
            else {}
        )
        reminder_message_input_properties.setdefault("type", "text")
        reminder_message_input_properties.setdefault("maxlength", 60)

        # Reminder type properties (use dcc.Dropdown here)
        reminder_type_dropdown_properties = (
            reminder_type_dropdown_properties.copy()
            if reminder_type_dropdown_properties
            else {}
        )
        reminder_type_dropdown_properties.setdefault(
            "options", [{"label": item, "value": item}
                        for item in reminder_types]
        )

        # Reminder datepicker properties
        reminder_datepicker_properties = (
            reminder_datepicker_properties.copy()
            if reminder_datepicker_properties
            else {}
        )
        reminder_datepicker_properties.setdefault("min_date_allowed",
                                                  date(1995, 8, 5))

        # Reminder input for time properties
        reminder_time_input_properties = (
            reminder_time_input_properties.copy()
            if reminder_time_input_properties
            else {}
        )
        reminder_time_input_properties.setdefault("type", "time")

        super().__init__(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Input(
                                id=self.ids.reminder_message_input(aio_id),
                                **reminder_message_input_properties
                            ),
                            width=3,
                        ),
                        dbc.Col(
                            dcc.Dropdown(
                                id=self.ids.reminder_type_dropdown(aio_id),
                                **reminder_type_dropdown_properties
                            ),
                            width=3,
                        ),
                        dbc.Col(
                            dcc.DatePickerSingle(
                                id=self.ids.reminder_datepicker(aio_id),
                                **reminder_datepicker_properties
                            ),
                            width=3,
                        ),
                        dbc.Col(
                            dbc.Input(
                                id=self.ids.reminder_time_input(aio_id),
                                **reminder_time_input_properties
                            ),
                            width=3,
                        ),
                    ],
                    justify="start",
                    align="center",
                )
            ]
        )


if __name__ == "__main__":
    app = Dash(__name__, external_stylesheets=[dbc.themes.SIMPLEX])
    reminder = ReminderAIO()
    app.layout = html.Div([reminder])
    app.run(debug=True)
