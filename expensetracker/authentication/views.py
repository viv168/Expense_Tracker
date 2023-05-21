from django.shortcuts import render, redirect
from django.views import View
import json
from django.http import JsonResponse
from django.contrib.auth.models import User
from validate_email import validate_email
from django.contrib import messages
from django.core.mail import EmailMessage
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.sites.shortcuts import get_current_site
from .utils import token_generator
from django.contrib import auth
from django.contrib.auth.tokens import PasswordResetTokenGenerator
import threading
from django.db.models.signals import post_save
from django.dispatch import receiver
from userpreferences.models import UserPreference


# Create your views here.

@receiver(post_save, sender=User)
def create_default_preference(sender, instance, created, **kwargs):
    if created:
        UserPreference.objects.create(user=instance, currency ='INR')

class EmailThread(threading.Thread):
    
    def __init__(self, email) -> None:
        self.email = email
        threading.Thread.__init__(self)


    def run(self) -> None:
        self.email.send(fail_silently=False)
        




class EmailValidationView(View):
    def post(self, request):
        data = json.loads(request.body)
        email = data['email']
        
        if not validate_email(email):
            return JsonResponse({'email_error': 'Email is invalid'}, status= 400)

        if User.objects.filter(email=email).exists():
            return JsonResponse({'email_error': 'Email already registered.'}, status= 409)
        
        return JsonResponse({'email_valid': True})
class UsernameValidationView(View):
    def post(self, request):
        data = json.loads(request.body)
        username = data['username']
        
        if not str(username).isalnum():
            return JsonResponse({'username_error': 'username should only contain alphanumeric characters'}, status= 400)

        if User.objects.filter(username=username).exists():
            return JsonResponse({'username_error': 'Sorry this username is already taken, please choose another.'}, status= 409)
        
        return JsonResponse({'username_valid': True})


class RegistrationView(View):
    def get(self, request):
        return render(request, 'authentication/register.html')

    def post(self, request):

        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        context = {
            'fieldValues' : request.POST
        }
        if not User.objects.filter(username=username):
            if not User.objects.filter(email=email):
                if len(password) < 6:
                    messages.error(request, 'Password too short')
                    return render(request, 'authentication/register.html',context)
                user = User.objects.create_user(username=username,email=email)
                user.set_password(password)
                user.is_active = False
                user.save()

                uid = urlsafe_base64_encode(force_bytes(user.pk))

                domain = get_current_site(request).domain
                email_contents = {
                    'user': user,
                    'domain': domain,
                    'uid': uid,
                    'token': token_generator.make_token(user),
                }
                link = reverse('activate', kwargs={'uid': email_contents['uid'], 'token': email_contents['token']})
                activate_url = f'http://{domain}{link}'

                email_subject = 'Activate your account.'
                email_body = f'Hi {user.username}, Please use this link to verify your account.\n{activate_url}'
                email = EmailMessage(
                    email_subject,
                    email_body,
                    'noreply@semicolon.com',
                    [email],
                )
                EmailThread(email).start()
                messages.success(request, 'Account created successfully')
                return render(request, 'authentication/register.html')

        return render(request, 'authentication/register.html')

class VerifivationView(View):
    def get(self, request, uid, token):
        try:
            id= force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk = id)

            if not token_generator.check_token(user, token):
                return redirect('login'+'?message='+'User already activated.')

            if user.is_active:
                return redirect('login')
            user.is_active = True
            user.save()
            messages.success(request,'Account activated successfully')
            return redirect('login')

        except Exception as ex:
            pass

        

class LoginView(View):
    def get(self, request):
        return render(request, 'authentication/login.html')

    def post(self, request):

        username = request.POST['username']
        password = request.POST['password']

        if username and password:
            user = auth.authenticate(username=username, password=password)

            if user:
                if user.is_active:
                    auth.login(request, user)
                    messages.success(request, f'Welcome {user.username}, You are now logged in.')
                    return redirect('expenses')

                messages.error(request, 'Account is not active, please check your email.')
                return render(request, 'authentication/login.html')
            
            messages.error(request, 'Invalid Credentials, try again.')
            return render(request, 'authentication/login.html')

        messages.error(request, 'Please fill all fields.')
        return render(request, 'authentication/login.html')


class LogoutView(View):

    def post(self, request):
        auth.logout(request)
        messages.success(request, 'You have been logged out.')
        return redirect('login')


class RequestPasswordResetEmail(View):

    def get(self, request):
        return render(request, 'authentication/reset_password.html')

    def post(self, request):
        email = request.POST['email']
        context = {
            'values': request.POST
        }
        if not validate_email(email):
            messages.error(request, 'Please enter a valid Email.')
            return render(request, 'authentication/reset_password.html',context)

        user = User.objects.filter(email = email)
        if user.exists():
            uid = urlsafe_base64_encode(force_bytes(user[0].pk))
            domain = get_current_site(request).domain
            email_contents = {
                    'user': user[0],
                    'domain': domain,
                    'uid': uid,
                    'token': PasswordResetTokenGenerator().make_token(user[0]),
                } 
            link = reverse('reset-user-password', kwargs={'uid': email_contents['uid'], 'token': email_contents['token']})

            reset_url = f'http://{domain}{link}'

            email_subject = 'Reset Password'
            email_body = f'Hi there, Please use this link to reset your password.\n{reset_url}'
            email = EmailMessage(
                email_subject,
                email_body,
                'noreply@semicolon.com',
                [email],
                )
            EmailThread(email).start()
            messages.success(request, 'We have sent you an email to reset your password.')
            return render(request, 'authentication/reset_password.html')
        else:
            messages.info(request, 'Email provided is not registered in our database.')
            return render(request, 'authentication/reset_password.html')
            

        
        
class CompletePasswordReset(View):
    def get(self, request, uid, token):
        context = {
            'uid': uid,
            'token': token,
        }
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk = user_id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                messages.info(request, 'Reset link has expired, please request another link.')
                return render(request, 'authentication/reset_password.html', context)
        except Exception as identifier:
            pass
        return render(request, 'authentication/set_new_password.html', context)

    def post(self, request, uid, token):
        context = {
            'uid': uid,
            'token': token,
        }

        password = request.POST['password1']
        confirm_password = request.POST['password2']

        if password != confirm_password:
            messages.error(request, 'Password does not match.')
            return render(request, 'authentication/set_new_password.html', context)

        if len(password) < 6:
            messages.error(request, 'Password is too short.')
            return render(request, 'authentication/set_new_password.html', context)
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk = user_id)
            user.set_password(password)
            user.save()
            messages.success(request, 'Password changed succesfully, you can login with your new password now.')
            return redirect('login')
        except Exception as identifier:
            messages.info(request, 'Something went wrong')
            return render(request, 'authentication/set_new_password.html', context)
