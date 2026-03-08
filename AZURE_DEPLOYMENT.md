# Azure App Service Deployment

When deploying the application to Azure App Service (Linux container), ensure the startup command is explicitly configured so Gunicorn uses the correct configuration file. If this isn't set, Azure will auto-detect the Flask app and launch it with a default `sync` worker, which will cause timeout errors and websocket failures for this application.

## Startup Configuration

To configure Azure App Service to use the correct `geventwebsocket` worker and settings defined in `gunicorn.conf.py`:

1. Go to the Azure Portal.
2. Navigate to your App Service instance.
3. In the left menu, select **Settings > Configuration**.
4. Go to the **General settings** tab.
5. In the **Startup Command** field, enter:
   ```
   startup.sh
   ```
   (Alternatively, you can directly enter `gunicorn --config gunicorn.conf.py app:app` if you don't wish to use the script).
6. Save your changes. The App Service will automatically restart with the new configuration.

By explicitly running `startup.sh`, Gunicorn is instructed to load its settings from `gunicorn.conf.py`, ensuring it runs `geventwebsocket.gunicorn.workers.GeventWebSocketWorker` rather than the default `sync` worker.