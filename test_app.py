from app import app
with app.test_client() as client:
    resp = client.get('/robots933456.txt')
    print(resp.status_code)
    print(resp.data)
