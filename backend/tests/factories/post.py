import factory
import faker

from apps.posts.models import Post, Likes, Comment
from .users import  CustomUserFactory

faker_instance = faker.Faker()

class PostFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Post
    post_content = faker_instance.text(max_nb_chars=100)
    user = factory.SubFactory(CustomUserFactory)

class LikesFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Likes
    post = factory.SubFactory(PostFactory)
    user = factory.SubFactory(CustomUserFactory)


class CommentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Comment

    post = factory.SubFactory(PostFactory)
    user = factory.SubFactory(CustomUserFactory)
    message = faker_instance.text(max_nb_chars=10)




