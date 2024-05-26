from locust import HttpUser, task, between

class MyUser(HttpUser):
    wait_time = between(1, 5)

    @task
    def insert_data(self):
        self.client.get("/get_category")

# lodust -f path/of/locust --host=http://localhost:8000/api/v1 (root endpoint)