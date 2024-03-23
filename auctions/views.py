from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse

from .models import User, Category, Listing, Status, Bid, Watchlist, Comment

from django.template.defaulttags import register

from datetime import datetime

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

def listing(request, listing_id):
    try:
        listing = Listing.objects.get(pk=listing_id)
    except Listing.DoesNotExist:
        raise Http404("Flight not found.")
    
    user = request.user
    listing_bids = Bid.objects.filter(listing=listing).order_by('-date')
    is_starting = False if len(listing_bids) > 1 else True
    starting_bid = listing_bids.last()
    latest_bid = listing_bids.first()
    comments = Comment.objects.filter(listing=listing_id).order_by("-date").all()

    if user.is_authenticated:
        watchlisted = True if len(Watchlist.objects.filter(user=user, listing=listing_id)) == 1 else False
    else:
        watchlisted = None

    return render(request, "auctions/listing.html", {
        "listing": listing,
        "is_starting": is_starting,
        "latest_bid": latest_bid,
        "starting_bid": starting_bid,
        "watchlisted": watchlisted,
        "comments": comments,
    })

def post_comment(request, listing_id):
    if request.method == "POST":
        try:
            listing = Listing.objects.get(pk=listing_id)
        except Listing.DoesNotExist:
            messages.error(request, "Something went wrong. Try again.")
            return redirect("auctions:listing", listing_id=listing_id)
        comment = request.POST["post_comment"]
        user = request.user
        if comment and user:
            new_comment = Comment(
                comment_by = user,
                listing = listing,
                comment = comment,
            )
            new_comment.save()
            messages.success(request, "Your comment was posted!")
            return redirect("auctions:listing", listing_id=listing_id)
        else:
            messages.error(request, "Your comment was not posted!. Try again.")
            return redirect("auctions:listing", listing_id=listing_id)
    else:
        return HttpResponseRedirect(reverse("auctions:listing", args=[listing_id]))

def watchlist(request):
    if request.user.is_authenticated:
        user = User.objects.get(pk=request.user.id)
        watchlist_listings = Watchlist.objects.filter(user=user).all()
        if watchlist_listings:
            listings = [listing.listing for listing in watchlist_listings]
        latest_bids = {}
        for listing in listings:
            latest_bid = Bid.objects.filter(listing=listing).order_by('-date').first()
        if latest_bid:
            latest_bids[listing.pk] = latest_bid.bid
        else:
            latest_bids[listing.pk] = None
        if watchlist_listings:
            return render(request, "auctions/watchlist.html", {
                # "watchlist_listings": watchlist_listings,
                "listings": listings,
                "latest_bids": latest_bids,
            })
        else:
            messages.warning(request, "Your watchlist is empty.")
            return render(request, "auctions/watchlist.html")
    else:
        return HttpResponseRedirect(reverse("auctions:index"))


def add_to_watchlist(request, listing_id):
    user = User.objects.get(pk=request.user.id)
    listing = Listing.objects.get(pk=listing_id)
    add_watchlist_item = Watchlist.objects.filter(user=user, listing=listing).first()
    if user and listing:
        if not add_watchlist_item:
            new_watchlist_item = Watchlist(
                user=user,
                listing=listing
            )
            new_watchlist_item.save()
    return redirect("auctions:listing", listing_id=listing_id)

def remove_from_watchlist(request, listing_id):
    user = User.objects.get(pk=request.user.id)
    listing = Listing.objects.get(pk=listing_id)
    if user and listing:
        remove_watchlist_item = Watchlist.objects.filter(user=user, listing=listing).first()
        if remove_watchlist_item:
            # Delete the watchlist item if it exists
            remove_watchlist_item.delete()
    return HttpResponseRedirect(reverse("auctions:listing", args=[listing_id]))

def create_bid(request, listing_id):
    if request.method == "POST":
        try:
            submited_bid = int(request.POST["create_bid"])
        except ValueError:
            messages.error(request, "Invalid bid amount. Your bid should be positive round number.")
            return redirect("auctions:listing", listing_id=listing_id)
        bid_by = request.user
        current_bids = Bid.objects.filter(listing=listing_id).order_by('-date').all()
        listing = Listing.objects.get(pk=listing_id)
        bids_number = len(current_bids)
        if bids_number == 1:
            if submited_bid >= current_bids[0].bid:
                create_bid = Bid(
                    bid_by=bid_by,
                    listing=listing,
                    bid=submited_bid,
                )
                create_bid.save()
                print(f"bid {submited_bid} created")
                return HttpResponseRedirect(reverse("auctions:listing", args=[listing_id]))
            else:
                messages.error(request, "Invalid bid amount. Bid should be equal or greater than the starting bid.")
                return redirect("auctions:listing", listing_id=listing_id)
        elif bids_number > 1:
            if submited_bid > current_bids[0].bid:
                create_bid = Bid(
                    bid_by=bid_by,
                    listing=listing,
                    bid=submited_bid,
                )
                create_bid.save()
                print(f"bid {submited_bid} created")
                return HttpResponseRedirect(reverse("auctions:listing", args=[listing_id]))
            else:
                messages.error(request, "Invalid bid amount. Bid should be greater than the last placed bid.")
                return redirect("auctions:listing", listing_id=listing_id)
        else:
            messages.error(request, "Bid cannot be placed.")
            return redirect("auctions:listing", listing_id=listing_id)
    else:
        return HttpResponseRedirect(reverse("auctions:listing", args=[listing_id]))
    
def close_auction(request, listing_id):
    won_bid = Bid.objects.filter(listing=listing_id).order_by("-date").first()
    won_bid.won = True
    listing = Listing.objects.get(pk=listing_id)
    listing.status = Status.objects.get(pk=3)
    listing.save()
    won_bid.save()
    messages.success(request, f"Your auction has ended. Bid placed by {won_bid.bid_by} on {won_bid.date.day}-{won_bid.date.month}-{won_bid.date.year} at {won_bid.date.hour}:{won_bid.date.minute} with {won_bid.bid} EUR has won.")
    return redirect("auctions:index")

def index(request):
    listings = Listing.objects.all()
    latest_bids = {}
    for listing in listings:
        latest_bid = Bid.objects.filter(listing=listing).order_by('-date').first()
        if latest_bid:
            latest_bids[listing.pk] = latest_bid.bid
        else:
            latest_bids[listing.pk] = None


    return render(request, "auctions/index.html", {
        "listings": listings,
        "latest_bids": latest_bids,
    })

def category(request):
    categories = Category.objects.all()
    return render(request, "auctions/categories.html", {
        "categories": categories,
    })

def category_item(request, category_id):
    try:
        category = Category.objects.get(pk=category_id)
    except (ValueError, Category.DoesNotExist):
        messages.error(request, "Invalid category.")
        return redirect("auctions:index")
    listings = Listing.objects.filter(category=category)
    latest_bids = {}
    for listing in listings:
        latest_bid = Bid.objects.filter(listing=listing).order_by('-date').first()
        if latest_bid:
            latest_bids[listing.pk] = latest_bid.bid
        else:
            latest_bids[listing.pk] = None
    return render(request, "auctions/category.html", {
        "listings": listings,
        "latest_bids": latest_bids,
    })


@login_required
def create(request):
    categories = Category.objects.all()
    if request.method == "POST":
        form_data= request.POST
        try:
            title = str(request.POST["title"])
        except ValueError:
            return render(request, "auctions/create.html", {
                "message": "Invalid title. Try again.",
                "form_data": form_data,
                "categories": categories,
            })
        
        try:
            description = str(request.POST["description"])
        except ValueError:
            return render(request, "auctions/create.html", {
                "message": "Invalid description. Try again.",
                "form_data": form_data,
                "categories": categories,
            })
        
        try:
            starting_bid = int(request.POST["starting_bid"])
        except ValueError:
            return render(request, "auctions/create.html", {
                "message": "Invalid starting bid. Try again.",
                "form_data": form_data,
                "categories": categories,
            })
        
        try:
            image = str(request.POST["image"])
        except ValueError:
            return render(request, "auctions/create.html", {
                "message": "Invalid image URL. Try again.",
                "form_data": form_data,
                "categories": categories,
            })
        created_by = request.user
        status = Status.objects.get(name="Active")
        
        try:
            category = Category.objects.get(pk=request.POST["category"])
        except ValueError:
            category = None

        if not (title and description and starting_bid):

            return render(request, "auctions/create.html", {
                "message": "Your form had missing data. Please try again.",
                "form_data": form_data,
                "categories": categories,
            })

        new_listing = Listing(
            created_by=created_by,
            title=title,
            description=description,
            image=image,
            category=category,
            status = status
        )
        new_bid = Bid(
            bid_by=created_by,
            listing = new_listing,
            bid = starting_bid,
        )
        new_listing.save()
        new_bid.save()


        return HttpResponseRedirect(reverse("auctions:index"), {
            "message": "Listing created successfully!"
        })
    else:
        return render(request, "auctions/create.html", {
            "categories": categories,
        })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("auctions:index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        if request.user.is_authenticated:
            return HttpResponseRedirect(reverse("auctions:index"))
        else:
            return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("auctions:index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("auctions:index"))
    else:
        if request.user.is_authenticated:
            return HttpResponseRedirect(reverse("auctions:index"))
        else:
            return render(request, "auctions/register.html")