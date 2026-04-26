def test_register(client):
    response = client.post("/register", data={
        "name": "New User",
        "email": "new@test.com",
        "password": "1234",
        "confirm_password": "1234"
    }, follow_redirects=True)

    assert b"Registration successful" in response.data


def test_login(client):
    response = client.post("/login", data={
        "email": "user@test.com",
        "password": "1234"
    }, follow_redirects=True)

    assert response.status_code == 200