import unittest
import requests


class TestUserLoginAPI(unittest.TestCase):
    def setUp(self):
        # Initialize the base URL of the API
        self.base_url = "http://127.0.0.1:8000"

        # Sample user credentials
        self.valid_user = {"username": "raj", "password": "Test@123"}
        self.invalid_user = {"username": "rajjj", "password": "NoPassword"}

    def test_valid_login(self):
        # Send a POST request with valid credentials
        response = requests.post(f"{self.base_url}/login", data=self.valid_user)
        # Assert that the response status code is 200
        self.assertEqual(response.status_code, 200)
        # Additional assertions can be added based on the expected response content

    def test_invalid_login(self):
        # Send a POST request with invalid credentials
        response = requests.post(f"{self.base_url}/login", data=self.invalid_user)
        # Assert that the response status code is not 200 (e.g., 401 for unauthorized)
        self.assertNotEqual(response.status_code, 200)
        # Additional assertions can be added based on the expected error response

    def test_empty_credentials(self):
        # Send a POST request with empty username and password fields
        empty_user = {"username": "", "password": ""}
        response = requests.post(f"{self.base_url}/login", data=empty_user)
        # Assert that the response status code is not 200 (e.g., 400 for bad request)
        self.assertNotEqual(response.status_code, 200)
        # Additional assertions can be added based on the expected error response

    # Add more test cases as needed based on your testing scenarios


if __name__ == "__main__":
    unittest.main()