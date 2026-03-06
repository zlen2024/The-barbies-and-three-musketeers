from forecasting import schedule_forecasting
def on_starting(server):
    from app import app
    schedule_forecasting(app)
