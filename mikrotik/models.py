from django.db import models


# Create your models here.
class profile(models.Model):
    name = models.CharField(max_length=200)
    ipadd = models.CharField(max_length=200)
    username = models.CharField(max_length=200)
    password = models.CharField(max_length=200)
    portapi = models.IntegerField(default=0)
    portssh = models.IntegerField(default=0)

    class Meta:
        managed = True
        db_table = 'mikrotik_profile'
    
    def __str__(self):
        return self.name

class influx(models.Model):
    host = models.CharField(max_length=200)
    ports = models.IntegerField(default=0)
    database = models.CharField(max_length=200)

    def __str__(self):
        return self.host

class parent(models.Model):
    router = models.ForeignKey(profile, on_delete=models.CASCADE)
    pname = models.CharField(max_length=200)
    pminlimitup = models.CharField(max_length=200)
    pminlimitdown = models.CharField(max_length=200)
    pmaxlimitup = models.CharField(max_length=200)
    pmaxlimitdown = models.CharField(max_length=200)

    def __str__(self):
        return self.pname

class toogle(models.Model):
    is_working = models.BooleanField(default=False)

    def __str__(self):
        return self.is_working        

class configuration(models.Model):
    orouter = models.ForeignKey(profile,  on_delete=models.CASCADE, default=None)
    odedicated = models.ForeignKey(parent, on_delete=models.CASCADE, default=None)
    oshared = models.ForeignKey(parent, related_name='odedicated', on_delete=models.CASCADE, default=None)
    #ostatus = models.ForeignKey(toogle, on_delete=models.CASCADE, default=False)
    oinflux = models.ForeignKey(influx, on_delete=models.CASCADE, default=None)