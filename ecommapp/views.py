from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Product,Cart,Order
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
import random
import razorpay
from django.core.mail import send_mail

# Create your views here.
def home(request):
    products = Product.objects.all() #fetch all data from database 
    context = {}
    context['products']= products
    print(context['products'])
    # context['name'] = "oreo"
    return render(request,"index.html",context)


def productdetail(request,pid):
    product = Product.objects.get(id=pid)
    context = {}
    context['product']=product
    return render(request,'product_detail.html',context)

def catfilter(request,cid):
    context={}
    q1 = Q(is_active=True)
    q2 = Q(category=cid)
    products = Product.objects.filter(q1&q2)
    context['products']=products
    return render(request,'index.html',context)

def sortbyprice(request,s):
    context={}
    if s=='0':
        products = Product.objects.all().order_by('-price')
    elif s=='1':
        products = Product.objects.all().order_by('price')
    context['products']=products
    return render(request,'index.html',context)

def register(request):
    context={}
    if(request.method=="GET"):
        return render(request,'registration.html')
    else:
        uname = request.POST['uname']
        upass = request.POST['upass']
        ucpass = request.POST['ucpass']
        if uname=="" or upass=="" or ucpass=="":
            context["error"]="please fill all the fileds"
        elif upass!=ucpass:
            context["error"]="password & confirm password must be same"
        else:
            user_object =User.objects.create(password=upass, username=uname, email=uname)
            user_object.set_password(upass)
            user_object.save()
            context["success"]="User registration succesfully"
        return render(request,'registration.html',context)
        
def user_login(request):
    context ={}
    if(request.method=='GET'):
        return render(request,'login.html')
    else:
        uname = request.POST['uname']
        upass = request.POST['upass']
        if uname=="" or upass=="":
            context['error']="please fill all the fields"
        else:
            u = authenticate(username=uname,password=upass)
            if u is not None:
                login(request,u)
                return redirect('/')
            else:
                context['error']='Invalid Credentials'
        return render(request,'login.html',context)

def user_logout(request):
    logout(request)
    return redirect('/')

def pricerange(request):
    context={}
    if request.method=="GET":
        return render(request,'index.html')
    else:
        min = request.POST['min']
        max = request.POST['max']
        products = Product.objects.filter(price__gte=min, price__lte=max)
        context['products']=products
        return render(request,'index.html',context)
    
def addtocart(request,pid):
    if request.user.is_authenticated:
        uid = request.user.id
        u = User.objects.get(id=uid)
        p = Product.objects.get(id=pid)
        c = Cart.objects.create(uid=u,pid=p)
        c.save()
        return redirect('/')
    else:
        return redirect('/login')
    
def cart(request):
    context={}
    user_id = request.user.id
    c = Cart.objects.filter(uid = user_id)
    context['products']=c
    np = len(c)
    context['np'] = np
    sum=0
    for i in c:
        sum =sum + i.pid.price*i.quantity
    context['sum']= sum
    return render(request,'card.html',context)

def removefromcart(request, cid):
    c = Cart.objects.get(id = cid)
    c.delete()
    return redirect('/viewcart')

def updateqty(request,cid,qv):
    c = Cart.objects.filter(id=cid) 
    if qv == "1":
        t = c[0].quantity+1
        c.update(quantity=t)
    elif qv == "0":
        if c[0].quantity>1:
            t = c[0].quantity-1
            c.update(quantity=t)
        elif c[0].quantity==1:
            c.delete()
    
    return redirect("/viewcart")

def placeorder(request):
    if request.user.is_authenticated:
        context={}
        user = request.user
        context['email']=user.email
        c = Cart.objects.filter(uid = user)
        context['c']=c
        order_id = random.randrange(1000,9999)
        for i in c:
            o = Order.objects.create(order_id=order_id,uid=user,pid=i.pid,quantity=i.quantity)
            o.save()
            i.delete()
        o = Order.objects.filter(uid = user)
        np = len(o)
        
        context['products']=o
        context['np']=np
        sum=0
        for i in o:
            sum = sum+i.pid.price*i.quantity
        context['sum']=sum
    return render(request,"order.html",context)

def makepayment(request):
    context={}
    o = Order.objects.filter(uid=request.user.id)
    sum=0
    for i in o:
        sum = sum+i.pid.price*i.quantity
        oid = i.order_id
    context['sum']=sum*100
    client = razorpay.Client(auth=("rzp_test_xxxxxxxxxxxxx", "XXXXXXxxxxxxxxxX"))
    data = { "amount": sum, "currency": "INR", "receipt": oid }
    payment = client.order.create(data=data)
    print(payment) 
    context['payment']=payment
    return render(request,'pay.html',context)

def senduseremail(request):
    context={}
    user = request.user
    mail=user.email #user email
    send_mail(
    "Ekart Order",
    "Order placed successfully",
    "---@gmail.com",
    ["---@gmail.com"], # mail to send loged in user email
    fail_silently=False,
    )
    return redirect('/')