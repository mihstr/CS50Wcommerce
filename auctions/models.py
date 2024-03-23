from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass

class Category(models.Model):
    name = models.CharField(max_length=50, blank=False, null=False)
    description = models.CharField(max_length=120, blank=True, null=True)

    def __str__(self):
        return f"{self.pk} - {self.name} ({self.description})"
    
    class Meta:
        verbose_name_plural = "Categories"

class Status(models.Model):
    name = models.CharField(max_length=20, blank=False, null=False)
    description = models.CharField(max_length=120, blank=True, null=True)
    
    def __str__(self):
        return f"{self.pk} - {self.name} ({self.description})"
    
    class Meta:
        verbose_name_plural = "Statuses"

class Listing(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="user", blank=False, null=False)
    title = models.CharField(max_length=50, blank=False, null=False)
    description = models.TextField(blank=False, null=False)
    image = models.URLField(blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="categories", blank=True, null=True)
    status = models.ForeignKey(Status, on_delete=models.PROTECT, related_name="statuses", blank=False, null=False)

    def __str__(self):
        if self.category is not None:
            return f"ID:{self.pk} - {self.status.name} | {self.title} | {self.category.name}"
        else:
            return f"{self.status.name} | {self.title} | Uncategorised"
    
class Bid(models.Model):
    bid_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="bidder", blank=False, null=False)
    listing = models.ForeignKey(Listing, on_delete=models.PROTECT, related_name="bids", blank=False, null=False)
    bid = models.PositiveIntegerField(blank=False, null=False)
    date = models.DateTimeField(auto_now_add=True, blank=False, null=False)
    won = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"Listing {self.listing.pk}: {self.bid} EUR at {self.date}"


class Comment(models.Model):
    comment_by = models.ForeignKey(User, on_delete=models.PROTECT)
    listing = models.ForeignKey(Listing, on_delete=models.PROTECT, related_name="comments", blank=False, null=False)
    comment = models.CharField(max_length=120, blank=False, null=False)
    date = models.DateTimeField(auto_now_add=True, blank=False, null=False)
    
    def __str__(self) -> str:
        return f"Listing {self.listing.pk}: {self.comment} | {self.date}"
    
class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_watchlist", blank=False, null=False)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="watchlist_items", blank=False, null=False)

    def __str__(self) -> str:
        return f"{self.user.username} - {self.listing.title}"