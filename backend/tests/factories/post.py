import factory
import faker

from apps.posts.models import Post, PostLike, Comment
from .users import  CustomUserFactory

faker_instance = faker.Faker()

class PostFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Post
    post_content = faker_instance.text(max_nb_chars=100)
    user = factory.SubFactory(CustomUserFactory)

class PostLikeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PostLike
    post = factory.SubFactory(PostFactory)
    user = factory.SubFactory(CustomUserFactory)


class CommentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Comment

    post = factory.SubFactory(PostFactory)
    user = factory.SubFactory(CustomUserFactory)
    message = faker_instance.text(max_nb_chars=10)




