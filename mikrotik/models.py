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

class parent(models.Model):
    router = models.ForeignKey(profile, on_delete=models.CASCADE)
    pname = models.CharField(max_length=200)
    pminlimitup = models.CharField(max_length=200)
    pminlimitdown = models.CharField(max_length=200)
    pmaxlimitup = models.CharField(max_length=200)
    pmaxlimitdown = models.CharField(max_length=200)

    def __str__(self):
        return self.pname

class child(models.Model):
    dedicated = models.ForeignKey(parent, on_delete=models.CASCADE, default=None)
    routers = models.ForeignKey(profile,  on_delete=models.CASCADE, default=None)
    cname = models.CharField(max_length=200)
    cminlimitup = models.CharField(max_length=200)
    cminlimitdown = models.CharField(max_length=200)
    cmaxlimitup = models.CharField(max_length=200)
    cmaxlimitdown = models.CharField(max_length=200)
    
    class Meta:
        managed = True
        db_table = 'mikrotik_child'
    
    def __str__(self):
        return self.cname


