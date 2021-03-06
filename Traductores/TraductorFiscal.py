# -*- coding: utf-8 -*-
from Traductores.TraductorInterface import TraductorInterface
import math


class TraductorFiscal(TraductorInterface):
    def dailyClose(self, type):
        "Comando X o Z"
        # cancelar y volver a un estado conocido
        self.comando.cancelAnyDocument()

        ret = self.comando.dailyClose(type)
        return ret

    def getStatus(self, *args):
        "getStatus"
        ret = self.comando.getStatus(list(args))
        return ret

    def setHeader(self, *args):
        "SetHeader"
        ret = self.comando.setHeader(list(args))
        return ret

    def setTrailer(self, *args):
        "SetTrailer"
        ret = self.comando.setTrailer(list(args))
        return ret

    def openDrawer(self, *args):
        "Abrir caja registradora"
        return self.comando.openDrawer()

    def getLastNumber(self, tipo_cbte):
        "Devuelve el último número de comprobante"

        letra_cbte = tipo_cbte[-1] if len(tipo_cbte) > 1 else None
        return self.comando.getLastNumber(letra_cbte)

    def cancelDocument(self, *args):
        "Cancelar comprobante en curso"
        return self.comando.cancelDocument()

    def printTicket(self, encabezado=None, items=[], pagos=[], percepciones=[], addAdditional=None, setHeader=None, setTrailer=None):
      try:
          if setHeader:
              self.setHeader(*setHeader)

              if setTrailer:
                self.setTrailer(*setTrailer)

              if encabezado:
                self._abrirComprobante(**encabezado)
              else:
                self._abrirComprobante()

              for item in items:
                self._imprimirItem(**item)

              if pagos:
                for pago in pagos:
                    self._imprimirPago(**pago)

          if percepciones:
              for percepcion in percepciones:
                self._imprimirPercepcion(**percepcion)

              if pagos:
                for pago in pagos:
                    self._imprimirPago(**pago)

              if addAdditional:
                  self.comando.addAdditional(**addAdditional)

          rta = self._cerrarComprobante()
          return rta
      except Exception, e:
        self.cancelDocument()
        raise

    def _abrirComprobante(self,
                          tipo_cbte="T",  # tique
                          tipo_responsable="CONSUMIDOR_FINAL",
                          tipo_doc="SIN_CALIFICADOR",
                          nro_doc=" ",  # sin especificar
                          nombre_cliente=" ",
                          domicilio_cliente=" ",
                          referencia=None,  # comprobante original (ND/NC)
                          **kwargs
                          ):
        "Creo un objeto factura (internamente) e imprime el encabezado"
        # crear la estructura interna
        self.factura = {"encabezado": dict(tipo_cbte=tipo_cbte,
                                           tipo_responsable=tipo_responsable,
                                           tipo_doc=tipo_doc, nro_doc=nro_doc,
                                           nombre_cliente=nombre_cliente,
                                           domicilio_cliente=domicilio_cliente,
                                           referencia=referencia)}
        printer = self.comando

        letra_cbte = tipo_cbte[-1] if len(tipo_cbte) > 1 else None

        # mapear el tipo de cliente (posicion/categoria)
        pos_fiscal = printer.ivaTypes.get(tipo_responsable)

        # mapear el numero de documento según RG1361
        doc_fiscal = printer.docTypes.get(tipo_doc)

        ret = False
        # enviar los comandos de apertura de comprobante fiscal:
        if tipo_cbte.startswith('T'):
            if letra_cbte:
                ret = printer.openTicket(letra_cbte)
            else:
                ret = printer.openTicket()
        elif tipo_cbte.startswith("F"):
            ret = printer.openBillTicket(letra_cbte, nombre_cliente, domicilio_cliente,
                                         nro_doc, doc_fiscal, pos_fiscal)
        elif tipo_cbte.startswith("ND"):
            ret = printer.openDebitNoteTicket(letra_cbte, nombre_cliente,
                                              domicilio_cliente, nro_doc, doc_fiscal,
                                              pos_fiscal)
        elif tipo_cbte.startswith("NC"):
            ret = printer.openBillCreditTicket(letra_cbte, nombre_cliente,
                                               domicilio_cliente, nro_doc, doc_fiscal,
                                               pos_fiscal, referencia)

        return ret

    def _imprimirItem(self, ds, qty, importe, alic_iva=21., itemNegative=False, discount=0, discountDescription='',
                      discountNegative=True):
        "Envia un item (descripcion, cantidad, etc.) a una factura"

        if importe < 0:
            importe = math.fabs(importe)
            itemNegative = True

        self.factura["items"].append(dict(ds=ds, qty=qty,
                                          importe=importe, alic_iva=alic_iva, itemNegative=itemNegative,
                                          discount=discount, discountDescription=discountDescription,
                                          discountNegative=discountNegative))

        # Nota: no se calcula neto, iva, etc (deben venir calculados!)
        if discountDescription == '':
            discountDescription = ds

        return self.comando.addItem(ds, float(qty), float(importe), float(alic_iva),
                                    itemNegative, float(discount), discountDescription, discountNegative)

    def _imprimirPago(self, ds, importe):
        "Imprime una linea con la forma de pago y monto"
        self.factura["pagos"].append(dict(ds=ds, importe=importe))
        return self.comando.addPayment(ds, float(importe))

    def _imprimirPercepcion(self, ds, importe):
        "Imprime una linea con nombre de percepcion y monto"
        self.factura["percepciones"].append(dict(ds=ds, importe=importe))
        return self.comando.addPerception(ds, float(importe))

    def _cerrarComprobante(self, *args):
        "Envia el comando para cerrar un comprobante Fiscal"
        return self.comando.closeDocument()
