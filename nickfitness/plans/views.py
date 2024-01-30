from django.shortcuts import render, get_object_or_404, redirect
from .forms import CustomSignupForm
from django.urls import reverse_lazy
from django.views import generic
from .models import FitnessPlan, Customer
from django.contrib.auth import authenticate, login, logout 
from django.contrib.auth.decorators import login_required, user_passes_test
import stripe
from django.http import HttpResponse

# Set your Stripe API key
stripe.api_key = "sk_test_51OeEy4SAKYz2Bq3AfJTiF3IT3iRd0CdsizdhKQZUjLDmmbkwUb7ttPtxojlDWdG5cecrBFlxTyAI1WzsyE1AWZ8s00IlCvz1F7"

# Define a view for the home page
def home(request):
    # Retrieve all fitness plans from the database
    plans = FitnessPlan.objects
    # Render the home page with the retrieved fitness plans
    return render(request, 'plans/home.html', {'plans':plans})

# Define a view for a specific fitness plan
def plan(request, pk):
    # Retrieve the fitness plan with the given primary key from the database
    plan = get_object_or_404(FitnessPlan, pk=pk)
    # Check if the plan is premium and if the user is authenticated
    if plan.premium:
        if request.user.is_authenticated:
            try:
                # Check if the user has an active membership
                if request.user.customer.membership:
                    return render(request, 'plans/plan.html', {'plan':plan})
            except Customer.DoesNotExist:
                # Redirect to the 'join' page if the user does not have a customer record
                return redirect('join')
        # Redirect to the 'join' page if the plan is premium and the user is not authenticated
        return redirect('join')
    else:
        # Render the plan page for non-premium plans
        return render(request, 'plans/plan.html', {'plan':plan})

# Define a view for the 'join' page
def join(request):
    return render(request, 'plans/join.html')

# Define a view for the checkout process
@login_required
def checkout(request):
    # Check if the user already has an active membership
    try:
        if request.user.customer.membership:
            return redirect('settings')
    except Customer.DoesNotExist:
        pass

    # Define available coupons
    coupons = {'halloween':31, 'welcome':10}

    # Handle the form submission for the checkout process
    if request.method == 'POST':
        # Create a Stripe customer with the provided email and payment source
        stripe_customer = stripe.Customer.create(email=request.user.email, source=request.POST['stripeToken'])
        # Set the default plan ID to monthly
        plan = 'price_1OeF4ySAKYz2Bq3AaDCA2BAQ'
        # Change the plan ID to yearly if the user selected the yearly plan
        if request.POST['plan'] == 'yearly':
            plan = 'price_1OeF23SAKYz2Bq3A7MDBNlO3'
        # Check if the user applied a coupon and create a subscription accordingly
        if request.POST['coupon'] in coupons:
            percentage = coupons[request.POST['coupon'].lower()]
            try:
                coupon = stripe.Coupon.create(duration='once', id=request.POST['coupon'].lower(), percent_off=percentage)
            except:
                pass
            subscription = stripe.Subscription.create(customer=stripe_customer.id, items=[{'plan':plan}], coupon=request.POST['coupon'].lower())
        else:
            subscription = stripe.Subscription.create(customer=stripe_customer.id, items=[{'plan':plan}])

        # Create a Customer record in the database for the user
        customer = Customer()
        customer.user = request.user
        customer.stripeid = stripe_customer.id
        customer.membership = True
        customer.cancel_at_period_end = False
        customer.stripe_subscription_id = subscription.id
        customer.save()

        # Redirect to the home page after successful checkout
        return redirect('home')
    else:
        # Initialize variables for pricing details
        coupon = 'none'
        plan = 'monthly'
        price = 1000
        og_dollar = 10
        coupon_dollar = 0
        final_dollar = 10

        # Update variables based on selected plan and applied coupon (if any)
        if request.method == 'GET' and 'plan' in request.GET:
            if request.GET['plan'] == 'yearly':
                plan = 'yearly'
                price = 10000
                og_dollar = 100
                final_dollar = 100
        if request.method == 'GET' and 'coupon' in request.GET:
            if request.GET['coupon'].lower() in coupons:
                coupon = request.GET['coupon'].lower()
                percentage = coupons[request.GET['coupon'].lower()]
                coupon_price = int((percentage / 100) * price)
                price = price - coupon_price
                coupon_dollar = str(coupon_price)[:-2] + '.' + str(coupon_price)[-2:]
                final_dollar = str(price)[:-2] + '.' + str(price)[-2:]

        # Render the checkout page with pricing details
        return render(request, 'plans/checkout.html',
        {'plan':plan,'coupon':coupon,'price':price,'og_dollar':og_dollar,
        'coupon_dollar':coupon_dollar,'final_dollar':final_dollar})

# Define a view for user settings
def settings(request):
    # Initialize membership and cancel_at_period_end variables
    membership = False
    cancel_at_period_end = False

    # Handle form submission to cancel the subscription
    if request.method == 'POST':
        subscription = stripe.Subscription.retrieve(request.user.customer.stripe_subscription_id)
        subscription.cancel_at_period_end = True
        request.user.customer.cancel_at_period_end = True
        cancel_at_period_end = True
        subscription.save()
        request.user.customer.save()
    else:
        try:
            # Check if the user has an active membership and if subscription cancellation is pending
            if request.user.customer.membership:
                membership = True
            if request.user.customer.cancel_at_period_end:
                cancel_at_period_end = True
        except Customer.DoesNotExist:
            membership = False

    # Render the settings page with membership and cancellation information
    return render(request, 'registration/settings.html', {'membership':membership,
    'cancel_at_period_end':cancel_at_period_end})

# Define a view accessible only to superusers to update customer accounts based on Stripe subscription status
@user_passes_test(lambda u: u.is_superuser)
def updateaccounts(request):
    # Retrieve all Customer objects from the database
    customers = Customer.objects.all()
    # Loop through each customer and update their membership status based on the corresponding Stripe subscription status
    for customer in customers:
        subscription = stripe.Subscription.retrieve(customer.stripe_subscription_id)
        if subscription.status != 'active':
            customer.membership = False
        else:
            customer.membership = True
        customer.cancel_at_period_end = subscription.cancel_at_period_end
        customer.save()
    # Return a response indicating completion
    return HttpResponse('completed')

# Define a view for user registration (sign up)
class SignUp(generic.CreateView):
    form_class = CustomSignupForm
    success_url = reverse_lazy('home')
    template_name = 'registration/signup.html'

    # Override the form_valid method to authenticate the user after successful registration
    def form_valid(self, form):
        valid = super(SignUp, self).form_valid(form)
        username, password = form.cleaned_data.get('username'), form.cleaned_data.get('password1')
        new_user = authenticate(username=username, password=password)
        login(self.request, new_user)
        return valid

# Define a view for user logout
def user_logout(request):
    # Use the built-in Django logout function
    logout(request)
    # Redirect to the home page after logout
    return redirect('home')
