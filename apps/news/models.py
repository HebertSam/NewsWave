from __future__ import unicode_literals
from django.db import models
import re
import bcrypt
import datetime

class UserManager(models.Manager):
    def register(self, postData):
        errors = {}
        alphaRegex = re.compile(r'^[a-zA-Z]+[ ]*[a-zA-Z]*$')
        if (len(postData['name']) < 3) or (len(postData['name']) > 255):
            errors['name'] = "Names must be between 3 and 255 characters in length!"
        if (len(postData['username']) < 3) or (len(postData['username']) > 255):
            errors['alias'] = "A username must be between 3 and 255 characters in length!"
        if not alphaRegex.match(postData['name']) or not alphaRegex.match(postData['username']):
            errors['name'] = "Your name and alias can only contain alphabetical characters and spaces!"
        if postData['password'] != postData['confirm_password']:
            errors['password_match'] = "Your passwords do not match!"
        if len(postData['password']) < 8:
            errors['password'] = "Your password must be at least 8 characters in length!"
        user = User.objects.filter(username=postData['username'])
        if len(user) > 0:
            errors['redundant'] = 'This username has already been taken! Please chosse a different one!'
        user = None
        if len(errors) == 0:
            hash1 = bcrypt.hashpw(postData['password'].encode(), bcrypt.gensalt())
            user = User.objects.create(name=postData['name'], username=postData['username'], password=hash1)
        return {'errors': errors, 'user': user}
    def login(self, postData):
        errors = {}
        user = User.objects.filter(username=postData['username'])
        if len(user) == 0:
            errors['missing'] = 'This username does not exist in the system! Maybe you need to sign up.'  
        else:
            if not bcrypt.checkpw(postData['password'].encode(), user[0].password.encode()): 
                errors['password'] = 'Your password is incorrect!'
        user = None
        if len(errors) == 0:
            user = User.objects.get(username=postData['username'])
        return {'errors': errors, 'user': user}
class User(models.Model):
    name = models.CharField(max_length=255)
    username = models.CharField(max_length=255, unique=True)
    password = models.TextField()
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)
    objects = UserManager()

class NoteManager(models.Manager):
    def validate_and_create(self, postData):
        errors = {}
        if len(postData['note']) == 0:
            errors['len'] = "You can't post an empty note!"
        if len(errors) == 0:
            Note.objects.create(text=postData['note'])
        return errors
class Note(models.Model):
    text = models.TextField()
    user = models.ForeignKey(User, related_name="notes")
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)
    objects = NoteManager()

class OutletManager(models.Manager):
    pass
class Outlet(models.Model):
    user = models.ManyToManyField(User, related_name="outlets")

class LocationManager(models.Manager):
    pass
class Location(models.Model):
    user = models.ManyToManyField(User, related_name="locations")

class StoryManager(models.Manager):
    pass
class Story(models.Model):
    user = models.ManyToManyField(User, related_name="stories")