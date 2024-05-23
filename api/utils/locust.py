from locust import HttpUser, task, between

class MyUser(HttpUser):
    wait_time = between(1, 5)

    @task
    def insert_data(self):
        self.client.post("/insert_data", json={"category": "test_category"})