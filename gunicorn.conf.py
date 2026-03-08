import multiprocessing

# Network binding
bind = "0.0.0.0:8000"

# Worker processes configuration
workers = 1
worker_class = "geventwebsocket.gunicorn.workers.GeventWebSocketWorker"

# Timeout settings (for AI generation)
timeout = 120

# Logging configuration
accesslog = "-"
errorlog = "-"
