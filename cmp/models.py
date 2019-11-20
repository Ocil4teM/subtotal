from django.db import models

#Para los signals
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum

from bases.models import ClaseModelo
from inv.models import Producto
# Create your models here.
class Proveedor (ClaseModelo):
    descripcion=models.CharField(max_length=100, unique=True)
    direccion=models.CharField(max_length=250, null=True, blank= True)
    contacto=models.CharField(max_length=100)
    telefono=models.CharField(max_length=10, null=True, blank=True)
    email=models.CharField(max_length=250, null=True, blank=True)

    def __str__(self):
        return '{}'.format(self.descripcion)

    def save(self):
        self.descripcion=self.descripcion.upper()
        super(Proveedor, self).save()

    class Meta:
        verbose_name_plural= "Proveedores"



class ComprasEnc(ClaseModelo):
    fecha_compra=models.DateField(null=True, blank=True)
    observacion=models.TextField(null=True, blank=True)
    no_factura=models.CharField(max_length=100)
    fecha_factura=models.DateField()
    sub_total=models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    descuento=models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    total=models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    proveedor=models.ForeignKey(Proveedor, on_delete=models.CASCADE)

    def __str__(self):
        return '{}'.format(self.observacion)

    def save (self):
        self.observacion = self.observacion.upper()
        self.total =self.sub_total - self.descuento
        super(ComprasEnc, self).save()

    class Meta:
        verbose_name_plural="Encabezado Compras"
        verbose_name="Encabezado Compra"


class Comprasdet(ClaseModelo):
    compra=models.ForeignKey(ComprasEnc, on_delete=models.CASCADE)
    producto=models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad=models.BigIntegerField(default=0)
    precio_prv=models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    sub_total=models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    descuento=models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    total=models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    costo=models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    def __str__(self):
        return '{}'.format(self.producto)

    def save (self):
        self.sub_total = float(float(int(self.cantidad)) * float(self.precio_prv))
        self.total=self.sub_total - float(self.descuento)
        super(Comprasdet, self).save()

    class Meta:
        verbose_name_plural="Detalles Compras"
        verbose_name="Detalle Compra"


@receiver(post_delete, sender=Comprasdet)
def detalle_compra_borrar(sender,instance, **kwargs):
    id_producto = instance.producto.id
    id_compra = instance.compra.id

    enc = ComprasEnc.objects.filter(pk=id_compra).first()
    if enc:
        sub_total = Comprasdet.objects.filter(compra=id_compra).aggregate(Sum('sub_total'))
        descuento = Comprasdet.objects.filter(compra=id_compra).aggregate(Sum('descuento'))
        enc.sub_total=sub_total['sub_total__sum']
        enc.descuento=descuento['descuento__sum']
        enc.save()
    
    prod=Producto.objects.filter(pk=id_producto).first()
    if prod:
        cantidad = int(prod.existencia) - int(instance.cantidad)
        prod.existencia = cantidad
        prod.save()


@receiver(post_save, sender=Comprasdet)
def detalle_compra_guardar(sender,instance,**kwargs):
    id_producto = instance.producto.id
    fecha_compra=instance.compra.fecha_compra

    prod=Producto.objects.filter(pk=id_producto).first()
    if prod:
        cantidad = int(prod.existencia) + int(instance.cantidad)
        prod.existencia = cantidad
        prod.ultima_compra=fecha_compra
        prod.save()