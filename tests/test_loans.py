def test_borrow_book(client):
    client.post("/login", data={
        "email": "user@test.com",
        "password": "1234"
    })

    response = client.get("/borrow/1", follow_redirects=True)
    assert b"Borrowed" in response.data


def test_cannot_borrow_twice(client):
    client.post("/login", data={
        "email": "user@test.com",
        "password": "1234"
    })

    client.get("/borrow/1")
    response = client.get("/borrow/1", follow_redirects=True)

    assert b"already have this book" in response.data