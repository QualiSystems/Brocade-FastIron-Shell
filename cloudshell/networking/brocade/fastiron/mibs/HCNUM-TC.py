#
# PySNMP MIB module HCNUM-TC (http://pysnmp.sf.net)
# ASN.1 source file://F:\foundry\HCNUM-TC
# Produced by pysmi-0.0.6 at Tue Sep 20 14:02:02 2016
# On host ? platform ? version ? by user ?
# Using Python version 2.7.10 (default, May 23 2015, 09:40:32) [MSC v.1500 32 bit (Intel)]
#
( Integer, ObjectIdentifier, OctetString, ) = mibBuilder.importSymbols("ASN1", "Integer", "ObjectIdentifier", "OctetString")
( NamedValues, ) = mibBuilder.importSymbols("ASN1-ENUMERATION", "NamedValues")
( ConstraintsUnion, SingleValueConstraint, ConstraintsIntersection, ValueSizeConstraint, ValueRangeConstraint, ) = mibBuilder.importSymbols("ASN1-REFINEMENT", "ConstraintsUnion", "SingleValueConstraint", "ConstraintsIntersection", "ValueSizeConstraint", "ValueRangeConstraint")
( NotificationGroup, ModuleCompliance, ) = mibBuilder.importSymbols("SNMPv2-CONF", "NotificationGroup", "ModuleCompliance")
( Integer32, MibScalar, MibTable, MibTableRow, MibTableColumn, NotificationType, MibIdentifier, mib_2, IpAddress, TimeTicks, Counter64, Unsigned32, iso, Gauge32, ModuleIdentity, ObjectIdentity, Bits, Counter32, ) = mibBuilder.importSymbols("SNMPv2-SMI", "Integer32", "MibScalar", "MibTable", "MibTableRow", "MibTableColumn", "NotificationType", "MibIdentifier", "mib-2", "IpAddress", "TimeTicks", "Counter64", "Unsigned32", "iso", "Gauge32", "ModuleIdentity", "ObjectIdentity", "Bits", "Counter32")
( DisplayString, TextualConvention, ) = mibBuilder.importSymbols("SNMPv2-TC", "DisplayString", "TextualConvention")
hcnumTC = ModuleIdentity((1, 3, 6, 1, 2, 1, 78)).setRevisions(("2000-06-08 00:00",))
class CounterBasedGauge64(Counter64, TextualConvention):
    pass

class ZeroBasedCounter64(Counter64, TextualConvention):
    pass

mibBuilder.exportSymbols("HCNUM-TC", hcnumTC=hcnumTC, PYSNMP_MODULE_ID=hcnumTC, ZeroBasedCounter64=ZeroBasedCounter64, CounterBasedGauge64=CounterBasedGauge64)
