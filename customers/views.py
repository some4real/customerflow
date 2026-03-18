from django.urls import reverse
from django.views.generic import ListView, CreateView
from .models import Customer

class CustomerListView(ListView):

    model = Customer
    template_name = "customers/list.html"
    context_object_name = "customers"

    def get_queryset(self):

        return Customer.objects.filter(
            organization=self.request.user.organization
        )
    
class CustomerCreateView(CreateView):

    model = Customer
    template_name = "customers/create.html"
    fields = ["name", "email", "phone", "address"]

    def form_valid(self, form):

        form.instance.organization = self.request.user.organization
        return super().form_valid(form)
    
    def get_success_url(self):

        return reverse("customers:list")