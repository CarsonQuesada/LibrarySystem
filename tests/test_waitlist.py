def login(client, email, password):
    return client.post("/login", data={"email": email, "password": password})


def test_join_waitlist(client):
    login(client, "user@test.com", "1234")
    client.get("/borrow/1")  # take copy

    # create second user
    client.get("/logout")
    client.post("/register", data={
        "name": "User2",
        "email": "user2@test.com",
        "password": "1234",
        "confirm_password": "1234"
    })

    response = client.post("/waitlist/1/join", follow_redirects=True)
    assert b"added to the waitlist" in response.data


def test_multiple_waitlist(client):
    login(client, "user@test.com", "1234")
    client.get("/borrow/1")

    # user2
    client.get("/logout")
    client.post("/register", data={
        "name": "User2",
        "email": "user2@test.com",
        "password": "1234",
        "confirm_password": "1234"
    })
    client.post("/waitlist/1/join")

    # user3
    client.get("/logout")
    client.post("/register", data={
        "name": "User3",
        "email": "user3@test.com",
        "password": "1234",
        "confirm_password": "1234"
    })
    response = client.post("/waitlist/1/join", follow_redirects=True)

    assert b"added to the waitlist" in response.data