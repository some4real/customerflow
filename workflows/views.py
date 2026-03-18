from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from workflows.models import WorkflowStage
from django import forms

# Form for creating/editing a stage
class WorkflowStageForm(forms.ModelForm):
    class Meta:
        model = WorkflowStage
        fields = ['name', 'position', 'is_final', 'color', 'customer_message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'border rounded px-3 py-2 w-full'}),
            'position': forms.NumberInput(attrs={'class': 'border rounded px-3 py-2 w-full'}),
            'is_final': forms.CheckboxInput(attrs={'class': 'mr-2'}),
            'color': forms.Select(attrs={'class': 'border rounded px-3 py-2 w-full'}),
            'customer_message': forms.Textarea(attrs={
                "class": "border rounded px-3 py-2 w-full",
                "rows": 4,
                "placeholder": "Hello {customer_name}, your order #{order_number} has reached this stage."
            })
        }


@login_required
def workflow_list(request):
    org = request.user.organization
    stages = WorkflowStage.objects.filter(organization=org).order_by('position')

    COLOR_TAILWIND_MAP = {
        "blue": "bg-blue-500 text-white",
        "light-blue": "bg-sky-400 text-white",
        "sky": "bg-sky-500 text-white",
        "indigo": "bg-indigo-500 text-white",
        "emerald": "bg-emerald-500 text-white",
        "lime": "bg-lime-500 text-white",
        "yellow": "bg-yellow-500 text-black",
        "amber": "bg-amber-500 text-black",
        "orange": "bg-orange-500 text-white",
        "red": "bg-red-500 text-white",
        "rose": "bg-rose-500 text-white",
        "pink": "bg-pink-500 text-white",
        "fuchsia": "bg-fuchsia-500 text-white",
        "purple": "bg-purple-500 text-white",
        "violet": "bg-violet-500 text-white",
        "slate": "bg-slate-500 text-white",
        "zinc": "bg-zinc-500 text-white",
        "stone": 	"bg-stone-500 text-white"
    }

    for stage in stages:
        stage.color_class = COLOR_TAILWIND_MAP.get(stage.color, 'bg-gray-500 text-white')

    return render(request, 'workflows/list.html', {'stages': stages})

@login_required
def workflow_create(request):
    org = request.user.organization
    if request.method == 'POST':
        form = WorkflowStageForm(request.POST)
        if form.is_valid():
            stage = form.save(commit=False)
            stage.organization = org
            stage.save()
            return redirect('workflows:list')
    else:
        form = WorkflowStageForm()
    return render(request, 'workflows/form.html', {'form': form, 'title': 'Add Stage'})

@login_required
def workflow_edit(request, pk):
    org = request.user.organization
    stage = get_object_or_404(WorkflowStage, pk=pk, organization=org)
    if request.method == 'POST':
        form = WorkflowStageForm(request.POST, instance=stage)
        if form.is_valid():
            form.save()
            return redirect('workflows:list')
    else:
        form = WorkflowStageForm(instance=stage)
    return render(request, 'workflows/form.html', {'form': form, 'title': 'Edit Stage'})

@login_required
def workflow_delete(request, pk):
    org = request.user.organization
    stage = get_object_or_404(WorkflowStage, pk=pk, organization=org)
    if request.method == 'POST':
        stage.delete()
        return redirect('workflows:list')
    return render(request, 'workflows/delete_confirmation.html', {'stage': stage})