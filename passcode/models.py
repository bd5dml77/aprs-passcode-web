from django.db import models
from django.core.validators import EMPTY_VALUES, RegexValidator
from django.core.mail import EmailMessage, send_mail
from django.conf import settings
import re

import callpass

LOCATOR_REGEX = r'^[a-z]{2}[0-9]{2}([a-z]{2})?$'

class UpperCaseCharField(models.CharField):
    def to_python(self, value):
        return models.CharField.to_python(self, value.upper().strip())

class PasscodeRequest(models.Model):
    full_name = models.CharField(max_length=100)
    callsign = UpperCaseCharField(max_length=10, unique=True)
    loc_validator = RegexValidator(re.compile(LOCATOR_REGEX, re.I), "You need to supply a valid QTH locator!")
    locator = models.CharField("Maidenhead locator", max_length=8, validators=[loc_validator])
    email = models.EmailField()
    comment = models.TextField(blank=True)
    submitted = models.DateTimeField(auto_now_add=True)
    last_action = models.DateTimeField(auto_now=True)
    action_by = models.ForeignKey('auth.User', related_name='requests_modified', null=True, blank=True)
    status = models.CharField(max_length=20,choices=(
        ('pending', 'pending'),
        ('approved', 'approved'),
        ('denied', 'denied'),
    ), blank=True)
    passcode = models.CharField(max_length=5, blank=True, null=True)
    
    def save(self):
        if self.status in EMPTY_VALUES:
            self.status = 'pending'
    	    new_req = True
    	else:
    	    new_req = False

        super(PasscodeRequest, self).save()

    	if new_req:
            from textwrap import dedent
            EmailMessage(
                'APRS-IS Passcode Request: %s' % self.callsign,
                dedent('''\
                %s (%s, %s) requested a passcode for %s:
                %s
                ''' % (
                    self.full_name,
                    self.email,
                    self.locator,
                    self.callsign,
                    self.comment,
                )),
                settings.EMAIL_FROM,
                settings.EMAIL_NOTIFY,
                [], # BCC
                headers={'Reply-To': self.email}
            ).send(fail_silently=True)
    
    def generate_passcode(self):
        self.passcode = callpass.do_hash(self.callsign)
        return self.passcode
    
    def approve(self):
        self.generate_passcode()
        self.status = 'approved'
        self.save()
        send_mail(
            'APRS-IS Passcode Approved!',
            '''
%s,

Your APRS-IS passcode for %s is %s.
''' % (self.full_name, self.callsign, self.passcode),
            settings.EMAIL_FROM,
            [self.email],
            fail_silently=False
        )
    
    def deny(self):
        self.status = 'denied'
        self.save()
        send_mail(
            'APRS-IS Passcode Denied!',
            '''
%s,

Your APRS-IS passcode request for %s was denied.
''' % (self.full_name, self.callsign),
            settings.EMAIL_FROM,
            [self.email],
            fail_silently=False
        )
    
    def resend_mail(self):
        if self.status == 'approved':
            self.approve()
        elif self.status == 'denied':
            self.deny()
    
    def qrz(self):
        return u'<a href="http://www.qrz.com/db/%s" target="_blank">%s</a>' % (self.callsign, self.callsign)
    qrz.allow_tags = True
    
    def qth(self):
        return u'<a href="http://f6fvy.free.fr/qthLocator/fullScreen.php?locator=%s" target="_blank">%s</a>' % (self.locator, self.locator)
    qth.allow_tags = True
    
    def decision(self):
        return u'<a href="%s/approve">Approve</a>&nbsp;/&nbsp;<a href="%s/deny">Deny</a>' % (self.id, self.id)
    decision.allow_tags = True

    class Meta:
        ordering = ['-submitted']
    
    def __unicode__(self):
        return u'%s (%s)' % (self.full_name, self.callsign)