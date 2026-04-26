def login_admin(client):
    return client.post("/login", data={
        "email": "admin@test.com",
        "password": "admin"
    })


def test_admin_dashboard(client):
    login_admin(client)
    response = client.get("/admin/dashboard")

    assert response.status_code == 200


def test_add_book(client):
    login_admin(client)

    response = client.post("/admin/books/add", data={
        "title": "New Book",
        "author": "Author",
        "isbn": "999",
        "copy_count": 2,
        "available_copies": 2
    }, follow_redirects=True)

    assert b"Successfully added" in response.data