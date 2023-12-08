from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.contrib.auth.views import LoginView, LogoutView
from . import forms

class SignUp(CreateView):
    form_class = forms.UserCreateForm
    success_url = reverse_lazy('accounts:login')
    template_name = 'registration/signup2.html'
    
    def get_context_data(self,*args,**kwargs):
        context =  super().get_context_data(*args,**kwargs)
        context['form'].fields['username'].help_text = None
        context['form'].fields['password1'].help_text = None
        context['form'].fields['password2'].help_text = None

        context['form'].fields['username'].label = 'Пошта'
        context['form'].fields['first_name'].label = 'Ім\'я'
        context['form'].fields['last_name'].label = 'Прізвище'
        context['form'].fields['password1'].label = 'Пароль'
        context['form'].fields['password2'].label = 'Введіть пароль ще раз'

        return context
    
class Login(LoginView):
    template_name = 'registration/login2.html'
    
    def get_context_data(self,*args,**kwargs):
        context =  super().get_context_data(*args,**kwargs)
        context['form'].fields['username'].label = 'Пошта'
        context['form'].fields['password'].label = 'Пароль'
        return context

    
