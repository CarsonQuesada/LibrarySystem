def test_view_books(client):
    client.post("/login", data={
        "email": "user@test.com",
        "password": "1234"
    })

    response = client.get("/")
    assert b"Test Book" in response.data