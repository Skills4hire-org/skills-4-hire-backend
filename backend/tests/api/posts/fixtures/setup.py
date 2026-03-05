import pytest
from faker import  Faker

from apps.posts.models import Post

faker_instance = Faker()


@pytest.fixture
def setup_post_create():
    post_create_data = {
        "post_content": faker_instance.text(max_nb_chars=5),
        "post_type": "job",
        "amount": 3000,
        "duration": 5,
        "attachment": [
            {
                "attachment_type": "VIDEO",
                "attachmentURL": "https://www.google.com/"
            },
            {
                "attachment_type": "FILE",
                "attachmentURL": "https://www.google.com/"
            }
        ],
        "post_tag": [
            {
                "service": "Backend Engineering"
            },
            {
                "service": "Devops"
            }
        ]
    }
    return post_create_data

@pytest.fixture
def general_post():
    return "general_post"

@pytest.fixture
def job_post():
    return "job_post"

@pytest.fixture
def service_post():
    return "service_post"


def valid_post_content(request_data: dict, post_type: str):
    if post_type == "general_post":
        request_data["amount"] = None
        request_data["post_type"] = Post.PostType.GENERAL.value
    elif post_type == "job_post":
        request_data["post_type"] = Post.PostType.JOB.value
    else:
        request_data["amount"] = None
        request_data["post_type"] = Post.PostType.SERVICE.value

    return  request_data