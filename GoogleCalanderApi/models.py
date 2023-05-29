from django.db import models

class Event(models.Model):
    title = models.CharField(max_length=100)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    # Add any other fields you want to store for an event

    def __str__(self):
        return self.title