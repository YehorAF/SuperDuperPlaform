from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

class UserCreateForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = ['username','first_name','last_name','password1','password2']
        
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['username'].label = "Email"
        self.fields['password1'].label = "Password"
        self.fields['password2'].label = "Re-enter Password"
        self.fields['first_name'].required = True
        self.fields['first_name'].label = "First Name"
        self.fields['last_name'].label = "Last Name"
        
    def save(self,commit=True):
        user = super(UserCreateForm,self).save(commit=False)
        user.email = user.username
        if commit:
            user.save()
        return user
    