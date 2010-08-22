from django.contrib import admin
from aprspasscode.passcode.models import *

class PasscodeRequestAdmin(admin.ModelAdmin):
    readonly_fields = (
        'comment',
        'submitted',
        'status',
        'passcode',
        'last_action',
        'action_by',
    )
    list_display  = (
        'full_name',
        'qrz',
        'email',
        'submitted',
        'approve_link',
        'deny_link',
        'status',
        'passcode',
        'last_action',
        'action_by',
    )
    list_filter = ('status',)
    search_fields = ['full_name', 'callsign', 'email',]
    
    def save_model(self, request, obj, form, change):
        obj.action_by = request.user
        obj.save()

admin.site.register(PasscodeRequest, PasscodeRequestAdmin)