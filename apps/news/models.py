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
            errors['redundant'] = 'This username has already been taken! Please choose a different one!'
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
    def delete_story(self, postData, userID): # delete story from user. if no other user has story in reading list, delete story
        errors = {}
        user = User.objects.get(id=userID)
        story = Story.objects.get(id=postData['story_id'])
        user.stories.remove(story)
        return errors

class User(models.Model):
    name = models.CharField(max_length=255)
    username = models.CharField(max_length=255, unique=True)
    password = models.TextField()
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)
    objects = UserManager()
    def __repr__(self):
        return "Username: {}".format(self.username)

class NoteManager(models.Manager):
    def validate_and_create(self, postData, userID):
        errors = {}
        if len(postData['text']) == 0:
            errors['len'] = "You can't post an empty note!"
        if len(postData['title']) > 255:
            errors['titlelen'] = "Titles must be less than 255 characters long!"
        if len(errors) == 0:
            user = User.objects.get(id=userID)
            Note.objects.create(title=postData['title'], text=postData['text'], user=user)
        return errors
    def delete_note(self, postData):
        errors = {}
        note = Note.objects.get(id=postData['note_id'])
        note.delete()
        return errors

class Note(models.Model):
    title = models.CharField(max_length=255, null=True)
    text = models.TextField()
    user = models.ForeignKey(User, related_name="notes")
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)
    objects = NoteManager()

class OutletManager(models.Manager):
    def outlet_validator(self, postData, user_id):
        errors = {}
        user = User.objects.get(id=user_id)
        tempList = []
        for data in postData:
            if len(data) < 2:
                errors['news'] = "Your news outlet is not valid" 
                return errors
        user.outlets.clear()
        for key in postData:
            if postData[key] not in tempList and key != "csrfmiddlewaretoken":
                tempList.append(postData[key])
        for key in tempList:
                dataStr = key
                dataList = dataStr.split(',')
                outlet = NewsOutlet.objects.filter(sourceId=dataList[0]) # the id portion, preceding the comma
                if len(outlet) != 0:
                    outlet[0].users.add(user)
                else:
                    newoutlet = NewsOutlet.objects.create(sourceName=dataList[1], sourceId=dataList[0])
                    newoutlet.users.add(user)
                    newoutlet.save()
        return errors
class NewsOutlet(models.Model):
    sourceName = models.CharField(max_length=255)
    sourceId = models.CharField(max_length=255)
    users = models.ManyToManyField(User, related_name="outlets")
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)
    objects = OutletManager()
    def __repr__(self):
        return "Name: {}".format(self.sourceName)

class LocationManager(models.Manager):
    pass
class Location(models.Model):
    user = models.ManyToManyField(User, related_name="locations")

class StoryManager(models.Manager):
    def story_validator(self, postData, user_id):
        user = User.objects.get(id=user_id)
        errors = {}
        if "http" not in postData['url']:
            errors['url'] = 'not valid url'
            return errors
        story = Story.objects.filter(story_url=postData['url'])
        if len(story) == 0:
            story = Story.objects.create(story_name=postData['title'], story_url=postData['url'])
        else:
            story = story[0]
        if len(errors) == 0:
            this_user = story.users.filter(id=user_id)
            if len(this_user) == 0:
                story.users.add(user)
                story.save()
        return errors

class Story(models.Model):
    story_name = models.CharField(max_length=255)
    story_url = models.CharField(max_length=255)
    users = models.ManyToManyField(User, related_name="stories")
    created_at = models.DateTimeField(auto_now_add=True)
    objects = StoryManager()