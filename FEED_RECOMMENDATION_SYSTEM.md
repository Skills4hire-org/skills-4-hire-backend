# Post Recommendation Feed System - Complete Documentation

## Project Overview

A sophisticated multi-signal post recommendation system for the skills-4-hire platform. The system generates personalized feeds for users by ranking posts based on creator trustworthiness, engagement, relevance, recency, and social vouching.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    FeedListView (Entry Point)                   │
│  GET /api/posts/feed/?category=...&location=...&limit=20        │
└────────────────────────────┬──────────────────────────────────────┘
                             │
                             ▼
                 ┌──────────────────────────┐
                 │ RecommendationService    │
                 │ (Scoring Engine)         │
                 └────┬─────────┬─────────┬──┘
                      │         │         │
        ┌─────────────┴─┐  ┌───┴──┐  ┌──┴───────┐
        │ Layer 1:      │  │Layer2│  │Layer 3:  │
        │ Candidate     │  │Scoring│  │Ranking & │
        │ Generation    │  │       │  │Boosting  │
        └───────────────┘  └───────┘  └──────────┘
                      │
                      ▼
        ┌─────────────────────────────┐
        │ FeedPostSerializer          │
        │ (Response Formatting)       │
        └─────────────────────────────┘
```

## Layer 1: Candidate Generation

Filters posts to identify eligible candidates for recommendation:

**Eligibility Criteria**:
- `is_published = True` - Only published posts
- `is_active = True` - Post is not soft-deleted
- `is_deleted = False` - Not deleted
- Created within last 30 days (configurable)
- **NOT** created by the viewing user
- **NOT** already viewed by the user (unless `exclude_seen=false`)
- Optional category filter

**Query Optimization**:
```python
candidates.select_related('user', 'user__profile')
candidates.prefetch_related('tags', 'likes', 'comments', 'repost_records')
```

## Layer 2: Scoring Algorithm

Multi-signal scoring formula (weights sum to 1.0):

```
Post Score = (trust × 0.35) + (engagement × 0.25) + (relevance × 0.20) +
             (recency × 0.10) + (repost_boost × 0.10)
```

### 2.1 Trust Score (35% weight)

**What**: Creator's normalized reputation score (0.0 - 1.0)

**Why**: Trust is the single most important signal. Users prefer content from creators they know are reliable.

**How computed**:
- Completed jobs: +0.05 each (max 0.50)
- Average rating: Normalized 5-star scale to 0-0.30
- Endorsements: +0.02 each (max 0.20)
- Total capped at 1.0

**Example**:
```json
{
  "completed_jobs": 8,
  "average_rating": 4.5,
  "endorsements": 5,
  "trust_score": 0.75
}
```

### 2.2 Engagement Score (25% weight)

**What**: Normalized count of likes + comments + reposts

**Why**: Community validation. High engagement means others found it valuable.

**How computed**:
```python
engagement = (post.likes_count + post.comments_count + post.reposts_count) / max_engagement
# Normalized to 0.0 - 1.0
```

**Example**: If max engagement is 100 and this post has 50 interactions:
```
engagement_score = 50 / 100 = 0.50
```

### 2.3 Relevance Score (20% weight)

**What**: How well the post matches user's interests and location

**Why**: Users want posts relevant to their needs and capabilities.

**How computed**:
- Location match: +0.5 if post.city == user.location
- Category match: +0.5 if post.tags match user.category_interest
- Past behavior: Boost if user has interacted with this category before

Max score: 1.0

**Example**:
```python
# User in Lagos interested in Plumbing
# Post in Lagos about Plumbing
relevance_score = 0.5 + 0.5 = 1.0

# User in Lagos interested in Plumbing  
# Post in Lagos about Electrical
relevance_score = 0.5 + 0.0 = 0.5

# User in Lagos interested in Plumbing
# Post in Abuja about Plumbing
relevance_score = 0.0 + 0.5 = 0.5
```

### 2.4 Recency Score (10% weight)

**What**: Exponential decay favoring newer posts

**Why**: Newer content is typically more relevant, but we don't over-emphasize age.

**How computed**:
```python
recency_score = 1.0 / (1.0 + days_since_posted)

# Examples:
# 0 days old: 1.0 / (1.0 + 0) = 1.0
# 1 day old:  1.0 / (1.0 + 1) = 0.5
# 7 days old: 1.0 / (1.0 + 7) = 0.125
```

### 2.5 Repost Boost (10% weight)

**What**: Signal from trusted users endorsing the post

**Why**: When a trusted person shares something with a meaningful comment, it's social proof.

**When Applied**:
1. Post has active reposts, AND
2. Reposter's trust_score > 0.6, AND
3. Repost has non-empty comment (not just sharing), AND
4. Reposter shares location or category interest with viewer

**How computed**:
```python
# Each qualified repost adds +0.2, capped at 0.5 total
repost_boost = min(qualified_repost_count * 0.2, 0.5)
```

**Example**:
```json
{
  "reposts": [
    {
      "reposted_by": "trusted_user_1",
      "trust_score": 0.75,
      "comment": "This is exactly what I need!",
      "location": "Lagos",  // Matches viewer
      "qualifies": true
    },
    {
      "reposted_by": "untrusted_user",
      "trust_score": 0.3,
      "comment": "Check this out",
      "qualifies": false  // Trust too low
    }
  ],
  "repost_boost": 0.2  // 1 qualified repost * 0.2
}
```

## Layer 3: Ranking & Active User Boost

1. Sort all scored posts by final score (descending)
2. Apply 1.1x multiplier to posts from `is_active_user = True` users
3. Return paginated results

**Active User Flag**: Should be set by a scheduled task:
```python
# Update daily - mark users active if they've been active in last 7 days
profile.is_active_user = profile.last_active > (now - timedelta(days=7))
```

## Database Schema

### New Fields on Post

```python
is_published = BooleanField(default=True, db_index=True)
engagement_count = PositiveIntegerField(default=0)
```

### New Fields on BaseProfile (User)

```python
trust_score = FloatField(default=0.0, db_index=True)
location = CharField(max_length=200, blank=True, null=True)
category_interest = JSONField(default=list, blank=True)
is_active_user = BooleanField(default=True, db_index=True)
last_active = DateTimeField(blank=True, null=True)
```

### New Tables

**Repost**
```python
repost_id = UUIDField (PK)
original_post = FK(Post)
reposted_by = FK(User)
comment = TextField (optional, non-empty = endorsement)
created_at = DateTimeField
is_active = BooleanField

# Unique constraint: one repost per user per post
```

**UserPostInteraction**
```python
interaction_id = UUIDField (PK)
user = FK(User)
post = FK(Post)
interaction_type = CharField ['view', 'like', 'comment', 'repost']
created_at = DateTimeField

# Unique constraint: one interaction type per user per post
```

## API Endpoints

### 1. Get Personalized Feed

**Endpoint**: `GET /api/posts/feed/`

**Authentication**: Required (IsAuthenticated)

**Query Parameters**:
```
category    (optional) - Filter by category slug, e.g., "plumbing"
location    (optional) - Override user's location for relevance, e.g., "Lagos"
exclude_seen (optional) - Exclude already-viewed posts. Default: true
limit       (optional) - Results per page. Default: 20, Max: 50
page        (optional) - Page number. Default: 1
```

**Example Requests**:
```bash
# Basic - get 20 recommended posts
GET /api/posts/feed/

# Filtered - plumbing in Lagos
GET /api/posts/feed/?category=plumbing&location=Lagos&limit=20

# Including already-seen posts, page 2
GET /api/posts/feed/?exclude_seen=false&page=2
```

**Response** (200 OK):
```json
{
  "count": 20,
  "next": null,
  "previous": null,
  "results": [
    {
      "post_id": "550e8400-e29b-41d4-a716-446655440000",
      "post_title": "Need experienced plumber",
      "post_content": "Looking for someone to fix pipes in my apartment...",
      "post_type": "SERVICE",
      "creator_profile": {
        "username": "john_doe",
        "full_name": "John Doe",
        "trust_score": 0.85,
        "location": "Lagos",
        "display_name": "John"
      },
      "tags": [
        {"id": 1, "name": "Plumbing"},
        {"id": 2, "name": "Maintenance"}
      ],
      "attachments": [],
      "comments_count": 3,
      "likes_count": 5,
      "reposts_count": 1,
      "engagement_count": 9,
      "is_reposted": false,
      "repost_comment": null,
      "amount": null,
      "start_date": null,
      "end_date": null,
      "is_remote": false,
      "country": "Nigeria",
      "city": "Lagos",
      "state": null,
      "created_at": "2024-05-10T14:30:00Z",
      "updated_at": "2024-05-11T09:15:00Z",
      "recommendation_score": 0.82
    },
    // ... more posts
  ]
}
```

**Error Responses**:
```json
// 401 Unauthorized
{"detail": "Authentication credentials were not provided."}

// 500 Internal Server Error
{"error": "Failed to generate feed"}
```

### 2. Record User Interaction

**Endpoint**: `POST /api/posts/{post_id}/interact/`

**Authentication**: Required (IsAuthenticated)

**Request Body**:
```json
{
  "interaction_type": "view|like|comment|repost",
  "comment": "optional text for reposts"
}
```

**Example Requests**:

```bash
# Record a view (usually automatic from feed)
POST /api/posts/550e8400-e29b-41d4-a716-446655440000/interact/
{
  "interaction_type": "view"
}

# Record a like
POST /api/posts/550e8400-e29b-41d4-a716-446655440000/interact/
{
  "interaction_type": "like"
}

# Record a repost with endorsement comment
POST /api/posts/550e8400-e29b-41d4-a716-446655440000/interact/
{
  "interaction_type": "repost",
  "comment": "This plumber is exactly what I needed!"
}
```

**Response** (201 Created / 200 OK):
```json
{
  "status": "success",
  "interaction_id": "660e9411-f30c-52e5-b827-557766551111",
  "interaction_type": "like",
  "message": "Interaction recorded: like",
  "created": true
}
```

**Error Responses**:
```json
// 400 Bad Request
{"error": "Invalid interaction_type: invalid_type"}

// 404 Not Found
{"detail": "Not found."}

// 500 Internal Server Error
{"error": "Failed to record interaction"}
```

## Signal Handlers (Real-time Updates)

The system uses Django signals to keep data synchronized in real-time:

### Engagement Count Updates

Triggered by:
- Creating a UserPostInteraction (view, like, comment, repost)
- Creating/updating a Like
- Creating a Comment
- Creating a Repost

Automatically updates `post.engagement_count` to reflect current state.

### Trust Score Computation

Triggered by:
- Booking completion (status = "COMPLETED")
- Can also be called by Celery task for batch updates

Recomputes user's trust_score and updates `user.profile.trust_score`.

### Last Active Tracking

Can be added for:
- Post creation
- Comment creation
- Any UserPostInteraction

Updates `user.profile.last_active = timezone.now()`.

## Code Examples

### Using the Recommendation Service Directly

```python
from apps.posts.services import RecommendationService

# Get service instance
service = RecommendationService(user=request.user)

# Get ranked feed
feed_posts = service.get_feed(
    category='plumbing',
    location='Lagos',
    exclude_seen=True,
    limit=20,
    offset=0
)

# Each item is a dict: {'post': Post, 'score': float}
for item in feed_posts:
    post = item['post']
    score = item['score']
    print(f"{post.post_title}: {score:.3f}")
```

### Computing Trust Score

```python
from apps.posts.services import compute_trust_score

# Compute for a specific user
score = compute_trust_score(user)
print(f"Trust score: {score:.3f}")

# Update profile
user.profile.trust_score = score
user.profile.save()
```

### Checking Interactions

```python
from apps.posts.models import UserPostInteraction

# Check if user has seen a post
has_viewed = UserPostInteraction.objects.filter(
    user=user,
    post=post,
    interaction_type=UserPostInteraction.InteractionType.VIEW
).exists()

# Get all likes by a user
user_likes = UserPostInteraction.objects.filter(
    user=user,
    interaction_type=UserPostInteraction.InteractionType.LIKE
)
```

## Performance Characteristics

### Query Optimization

- **select_related()** for ForeignKey relationships
- **prefetch_related()** for reverse FK and M2M
- **Indexes** on frequently queried fields

Example optimized query:
```python
candidates = Post.objects.filter(
    is_published=True, is_active=True, is_deleted=False
).select_related(
    'user', 'user__profile'
).prefetch_related(
    'tags', 'likes', 'comments', 'repost_records'
).distinct()
```

### Complexity Analysis

- **Candidate Generation**: O(n) where n = posts in time window
- **Scoring**: O(n * m) where m = average interactions per post
- **Sorting**: O(n log n)
- **Pagination**: O(k) where k = limit

For typical usage (1000 posts, 20 results), processing time < 500ms.

### Database Load

- Minimal write overhead (signals are fast)
- Read-heavy: candidates query + engagement counts + related data
- Engagement count updates done atomically to prevent race conditions

## Migration Steps

### 1. Create and Review Migrations

```bash
cd backend
python manage.py makemigrations posts users
```

Review the generated migration files in:
- `apps/posts/migrations/`
- `apps/users/migrations/`

### 2. Apply Migrations

```bash
python manage.py migrate
```

### 3. Initialize Trust Scores (Optional)

```bash
python manage.py shell

from django.contrib.auth import get_user_model
from apps.posts.services import compute_trust_score

User = get_user_model()

for user in User.objects.filter(is_provider=True):
    score = compute_trust_score(user)
    user.profile.trust_score = score
    user.profile.save()
    print(f"Updated {user.username}: {score:.3f}")
```

### 4. Set is_published Flag

```bash
python manage.py shell

from apps.posts.models import Post

# Mark all active posts as published
Post.objects.filter(is_active=True, is_deleted=False).update(is_published=True)
```

## Configuration & Tuning

### In RecommendationService

```python
class RecommendationService:
    # How many days back to look for posts (default: 30)
    DEFAULT_DAYS_LOOKBACK = 30
    
    # Minimum trust score for repost to provide boost (default: 0.6)
    REPOST_TRUST_THRESHOLD = 0.6
    
    # Score multiplier for posts from active users (default: 1.1)
    ACTIVE_USER_BOOST = 1.1
    
    # Scoring weights (must sum to 1.0)
    WEIGHT_TRUST = 0.35
    WEIGHT_ENGAGEMENT = 0.25
    WEIGHT_RELEVANCE = 0.20
    WEIGHT_RECENCY = 0.10
    WEIGHT_REPOST = 0.10
```

To adjust weights (e.g., emphasize trust more):
```python
WEIGHT_TRUST = 0.45       # Increased
WEIGHT_ENGAGEMENT = 0.20  # Decreased
WEIGHT_RELEVANCE = 0.15   # Decreased
WEIGHT_RECENCY = 0.10
WEIGHT_REPOST = 0.10
# Total: 1.0 ✓
```

## Testing

### Unit Tests for Scorers

```python
from django.test import TestCase
from apps.posts.services import RecommendationService
from apps.posts.models import Post

class RecommendationServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test')
        self.service = RecommendationService(user=self.user)
    
    def test_trust_score_normalization(self):
        post = Post.objects.create(user=self.create_user(trust_score=0.75))
        score = self.service._trust_score(post)
        self.assertEqual(score, 0.75)
        self.assertLessEqual(score, 1.0)
        self.assertGreaterEqual(score, 0.0)
    
    def test_recency_score(self):
        post = Post.objects.create(user=self.user)
        score = self.service._recency_score(post)
        self.assertEqual(score, 1.0)  # Just created
```

### Integration Tests

```python
def test_feed_endpoint():
    user = User.objects.create_user(username='test')
    # Create sample posts with varied properties
    # Make API call
    # Verify ranking order
    # Check pagination
```

## Future Improvements

1. **Caching**: Add Redis caching for frequently accessed feeds
2. **ML Integration**: Replace hand-crafted scoring with ML model
3. **A/B Testing**: Framework for testing different weights
4. **Metrics**: Collect CTR, dwell time, conversion data
5. **Endorsements**: Implement proper endorsement model
6. **Collaborative Filtering**: Add similarity-based recommendations
7. **Serendipity**: Add randomization to prevent echo chambers

## Troubleshooting

### Feed Returns Empty

Check:
1. Are there published posts in the last 30 days?
2. Are those posts from different users (not the requester)?
3. Check `exclude_seen=false` to include already-viewed posts

```bash
python manage.py shell

from apps.posts.models import Post
from django.utils import timezone
from datetime import timedelta

cutoff = timezone.now() - timedelta(days=30)
posts = Post.objects.filter(
    is_published=True,
    is_active=True,
    is_deleted=False,
    created_at__gte=cutoff
)
print(f"Available posts: {posts.count()}")
```

### Trust Scores Not Updating

Check:
1. Is signal connected? Look for errors in logs
2. Has booking status actually changed to "COMPLETED"?
3. Try manual update:

```python
from apps.posts.services import compute_trust_score
score = compute_trust_score(user)
user.profile.trust_score = score
user.profile.save()
```

### Performance Issues

1. Check database indexes are created: `SHOW INDEXES FROM posts_post`
2. Monitor slow queries in logs
3. Profile with `django-debug-toolbar`
4. Consider adding query result caching

## Support & Maintenance

For questions or issues:
1. Check the model docstrings
2. Review signal handlers in signals.py
3. Add logging to identify bottlenecks
4. Run tests: `python manage.py test apps.posts`

---

**Last Updated**: May 2024  
**System Version**: 1.0
