from django.shortcuts import render, redirect, get_object_or_404
from django.db import IntegrityError 
from django.contrib import auth 
from django.contrib.auth.models import User
from .models import User
from .models import Listing
from django.contrib import messages
from decimal import *
from django.utils import timezone
from .forms import *
from .models import Bid
from .models import Comment
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta
from crystal.transactions import remaining_time
from django.contrib import messages
import datetime
from datetime import datetime
from django.utils.dateformat import DateFormat
import time
from django.core.paginator import Paginator


def main(request):
    return render(request, "main.html")

def signup(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        
        if password != confirmation:
            return render(request, "signup.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            auth.login(request, user)
        except IntegrityError:
            return render(request, "signup.html", {
                "message": "Username already taken."
            })
        
        return redirect('main')
    return render(request, "signup.html")

def login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST["password"]
        user = auth.authenticate(request, username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect('main')
        else:
            return render(request, 'login.html', {'error':'username or password is incorrect'})
    else:
        return render(request, 'login.html')

def logout(request):
    auth.logout(request)
    return redirect('main')

def mypage(request):
    return render(request, "mypage.html")

def mygallery(request):
    today = datetime.today().strftime("%Y%m%d")
    today = int(today)
    my_upload_arts= Listing.objects.all().filter(user=request.user)
    my_bid_arts_list = []
    my_bid_arts = Bid.objects.all().filter(user=request.user)
    for bid_art in my_bid_arts:
        deadline = bid_art.listing.time_ending
        deadline = deadline.strftime("%Y%m%d")
        deadline = int(deadline)
        if today >= deadline:
            my_bid_arts_list.append(bid_art)

    return render(request, "mygallery.html", {'my_upload_arts':my_upload_arts, "my_bid_arts_list": my_bid_arts_list})

def auctionArts(request):
    all_listing = Listing.objects.all()
    all_bids = Bid.objects.all()        
    highest_bid_art = Bid.objects.all().order_by('-highest_bid')[:3]

    
    today = datetime.today().strftime("%Y%m%d")
    today = int(today)
    
    listings=[]
    underway_bids=[]
    finished_bids=[]

    for bid in all_bids:
        deadline = bid.listing.time_ending
        deadline = deadline.strftime("%Y%m%d")
        deadline = int(deadline)
        if today < deadline:
            underway_bids.append(bid)
        else:
            finished_bids.append(bid)

    listings = list(underway_bids)
    #???????????????????????????&?????? ?????? ?????? ????????? ?????? ????????? ????????? Bid ??????????????? ??????
    #?????? ?????? ?????? ????????? -listings ??? ?????? ???????????? ?????? Bid ??????????????? ??????
    if request.method == "POST":
        view_type = request.POST['bid']
        
        if str(view_type) == "finished_bids":
            listings = list(finished_bids)
        else:
            listings = list(underway_bids)
        
        #if view_type == "underway_bids":  
    return render(request, "auctionArts.html", {'listings' : listings, 'top1': highest_bid_art[0], 'top2': highest_bid_art[1], 'top3': highest_bid_art[2]})

def auction(request, listings_id):
    listings = get_object_or_404(Listing, pk=listings_id)
    bid = Bid.objects.get(listing=listings)
    comments = Comment.objects.filter(listing=listings)
    deadline = listings.time_ending
    today = datetime.today().strftime("%Y%m%d")
    today = int(today)
    deadline = deadline.strftime("%Y%m%d")
    deadline = int(deadline)
    timegap = today - deadline
            
    if timegap > 0 :
        return render(request, "auction.html", {'listings':listings, 'bid':bid, 'comments':comments, "timegap" : timegap})
    
    return render(request, 'auction.html', {'listings':listings, 'bid':bid, 'comments':comments, "timegap" : timegap})

def about(request):
    return render(request, "about.html")
     
def bid(request):
    if request.method == "POST":
        # ?????? ??????
        listing_id = request.POST["listing_id"]
        listing = get_object_or_404(Listing, pk=listing_id)
        deadline = listing.time_ending
        today = datetime.today().strftime("%Y%m%d")
        today = int(today)
        deadline = deadline.strftime("%Y%m%d")
        deadline = int(deadline)
        timegap = today - deadline
        #??? ?????????
        new_bid = request.POST["new_highest_bid"]
        bid_id = request.POST["bid_id"]
        old_bid = get_object_or_404(Bid, pk=bid_id)

        if today-deadline > 0 :
            return redirect("auction", listing_id)
        
        if request.user.coin >= int(new_bid)  and old_bid.highest_bid < int(new_bid) :
            
            # 1) ?????? ????????? ????????? coin ??????
                # ?????? ???????????? ????????? ????????? ?????? : # ?????? ???????????? ?????? ?????? ?????? Bid????????? user = ????????? ????????????
            if old_bid.user != old_bid.listing.user:

                old_bid.user.coin = old_bid.user.coin + old_bid.highest_bid
                old_bid.user.save()

            # 2) ????????? ????????? ????????? coin ?????? & Bid ??????
            request.user.coin = request.user.coin - int(new_bid) 
            request.user.save()
            old_bid.user = request.user
            old_bid.highest_bid = new_bid
            old_bid.added = timezone.now()
            old_bid.save()

    return redirect("auction", listing_id)

IMAGE_FILE_TYPES = ['png', 'jpg', 'jpeg']

def create_profile(request):
    form = Profile_Form()
    if request.method == 'POST':
        form = Profile_Form(request.POST, request.FILES)
        if form.is_valid():
            user_pr = form.save(commit=False)
            user_pr.display_picture = request.FILES['display_picture']
            user_pr.user = request.user

            file_type = user_pr.display_picture.url.split('.')[-1]
            file_type = file_type.lower()
            if file_type not in IMAGE_FILE_TYPES:
                return render(request, 'error.html')
            user_pr.save()
            new_Bid = Bid()
            new_Bid.user = request.user
            
            request.user.coin = request.user.coin + 5000000
            request.user.save()

            new_Bid.listing = user_pr
            new_Bid.highest_bid = request.POST['initial']
            new_Bid.added = timezone.now()
            new_Bid.save()
            return render(request, 'details.html', {'user_pr': user_pr})
    context = {"form": form,}
    return render(request, 'create.html', context)

@login_required
def comment(request):
    if request.method == "POST":
        content = request.POST["content"]
        item_id = request.POST["list_id"]
        item = Listing.objects.get(pk=item_id)
        newComment = Comment(user=request.user, comment=content, listing=item)
        newComment.save()
        return redirect("auction", item_id)
    return redirect("main")

def edit(request, listings_id):
    myart = Listing.objects.get(id=listings_id)
    # ?????? ??????????????? ???????????? ????????? ????????? ???
    if request.method == "POST":
        form = Edit_Form(request.POST, request.FILES)
        if form.is_valid():
            print(form.cleaned_data)
            # {'name': '????????? ??????', 'image': <InMemoryUploadedFile: Birman_43.jpg 	(image/jpeg)>, 'gender': 'female', 'body': '????????? ??????'}
            myart.name = form.cleaned_data['name']
            myart.explain = form.cleaned_data['explain']
            myart.save()
            return redirect('/auction/'+str(myart.pk))
        
    # ??????????????? ???????????? ?????? ???????????? ?????? ???????????? ???
    else:
        form = Edit_Form()
        return render(request, 'edit.html',{'form':form})