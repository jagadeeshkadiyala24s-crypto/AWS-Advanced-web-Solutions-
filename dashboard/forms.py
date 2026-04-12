from django import forms
from .models import FrameComment


class FrameCommentForm(forms.ModelForm):
    class Meta:
        model = FrameComment
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Add your note for this time point...'})
        }
