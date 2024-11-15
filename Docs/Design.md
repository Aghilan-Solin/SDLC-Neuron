# Design Document

**Core of the Neuron app**

- UI
- Callbacks
- Logging
- Utils


## UI
Main UI components are categorized into
  - App header
  - Reminder (All in One Component)
  - Pages/Tabs for Upcoming and Missed Reminders

## Callbacks
Callbacks are the event handlers for the app
- Reminder AIO component will have its own callbacks defined in itself
- Each component will its callback is associated

## Logging
- Logging is done using *logging* library in python
- Errors and exceptions will be logged for callbacks and controller.
- Debug messages for each logging will be handled wherever necessary

## Utils
- Utility functions needed for conversions, data handling etc.,



## Architecture Diagram
![Architecture Diagram](..\assets\images\Neuron-Architecture.png)
