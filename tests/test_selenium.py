
from selenium import webdriver
from selenium.webdriver.common.by import By


def test_ntiro_home_page():
    driver = webdriver.Edge()

    try:
        driver.get("http://127.0.0.1:8000/")

        page_text = driver.find_element(
            By.TAG_NAME, "body"
        ).text

        assert (
            "NTIRO" in page_text
            or "threat" in page_text.lower()
        )

        print("Home page test passed")

    finally:
        driver.quit()


def test_ntiro_api_documentation():
    driver = webdriver.Edge()

    try:
        driver.get("http://127.0.0.1:8000/docs")

        assert "NTIRO API" in driver.title

        print("API documentation test passed")

    finally:
        driver.quit()
