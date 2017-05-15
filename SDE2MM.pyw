#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# ----- GEBRUIKTE SOFTWARE ---------------------------------------------
#
# python-2.7         http://www.python.org
# cx_Oracle          http://cx-oracle.sourceforge.net/
# psycopg2           http://initd.org/psycopg/docs/install.html
# pymssql            http://pymssql.org/en/latest/
#
#
# ----- GLOBALE VARIABELEN ---------------------------------------------

__doc__      = "Programma om iso xml uit het sde schema te lezen"
__rights__   = 'provincie Noord-Brabant'
__author__   = 'Jan van Sambeek'
__date__     = ['02-2017']
__version__  = '1.0.1'

# ----- IMPORT LIBRARIES -----------------------------------------------

import os, sys, datetime, re, smtplib, logging, gzip, shutil
import cx_Oracle
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import Encoders

# ----- CONFIG CLASS ---------------------------------------------------

class Config:
  """
  Lees config bestand en haal key's op
  Schrijf dictionarie naar config
  """
  def __init__(self, conf_bestand):
    """ ini config object """
    self.conf_bestand = conf_bestand
    self.conf = None

  def get(self, key, default = None):
    """ Lees values uit config bestand """    
    if not self.conf: self.load()
    if self.conf and (key in self.conf): return self.conf[key]
    return default

  def get_dict(self, default = None):
    """ Geef de complete dictionarie """    
    if not self.conf: self.load()
    if self.conf: return self.conf
    return default

  def set(self, key, value):
    """ Voeg keys en values toe aan config """    
    if not self.conf: self.load()
    self.conf[key] = value
    self.save()

  def load(self):
    """
    Laad het config bestand
    Als het niet bestaat maak een lege config
    """    
    try: self.conf = eval(open(self.conf_bestand, 'r').read())
    except: self.conf = {}

  def save(self):
    """ Schijf dictionarie naar config bestand """    
    open(self.conf_bestand, 'w').write(repr(self.conf))

# ----- ZENDMAIL -------------------------------------------------------

def Zendmail(mail_gegevens):
  """
  Functie Zendmail(mail_gegevens)
  
  Is een programma om mail met bijlagen te versturen naar één of meerder ontvangers.
  De mail gegevens bestaan uit, een dictionarie met daarin:
  verzender, wachtwoord, alias, ontvangers, cc, bc,  onderwerp, bericht, de smtp_server en eventueel bijlagen.
  Ontvangers, cc, bc en bijlagen zijn lists, alle overige variabelen zijn strings. 
  verplicht: verzender, ontvangers, onderwerp, bericht, de smtp_server
  optioneel: wachtwoord, alias, cc, bc, bijlagen
  Afhankelijk van de provider kan een SSL beveiliging meegegeven worden 
  door SSL=True of SSL=False mee te geven.
  
  
  voorbeeld:
    
  mail_gegevens = {}
  mail_gegevens['verzender']  = 'verzender@gmail.com'
  mail_gegevens['wachtwoord'] = '********'
  mail_gegevens['alias']      = 'alias verzender'
  mail_gegevens['ontvangers'] = ['ontvanger1@gmail.com', 'ontvanger2@gmail.com']
  mail_gegevens['cc']         = ['cc1@gmail.com, 'cc2@gmail.com']
  mail_gegevens['bc']         = ['bc1@gmail.com, 'bc2@gmail.com']
  mail_gegevens['onderwerp']  = 'onderwerp van de mail'
  mail_gegevens['bericht']    = 'bericht van de mail'
  mail_gegevens['smtp_server']= 'smtp.gmail.com'
  mail_gegevens['bijlagen']   = ['bijlage1.pdf', 'bijlage2.jpg']
  
  Zendmail(mail_gegevens) 
  """
  # stel het bericht samen
  message = MIMEMultipart()
  # kijk of er een alias is anders gebruik de verzender
  if 'alias' in mail_gegevens.keys(): message['From'] = mail_gegevens['alias']
  else: message['From'] = mail_gegevens['verzender']
  # voeg de ontvangers toe aan de message
  message['To'] =  ', '.join(mail_gegevens['ontvangers'])
  # voeg de ontvangers toe aan ontvangers
  ontvangers = mail_gegevens['ontvangers']
  # als er cc's zijn voeg die toe
  if 'cc' in mail_gegevens.keys(): 
    message['CC'] =  ', '.join(mail_gegevens['cc'])
    ontvangers += mail_gegevens['cc']
  # als er bc's zijn voeg die toe
  if 'bc' in mail_gegevens.keys(): 
    message['BC'] =  ', '.join(mail_gegevens['bc'])
    ontvangers += mail_gegevens['bc']
  # voeg het onderwerp toe
  message['Subject'] = mail_gegevens['onderwerp']
  # voeg het bericht toe
  message.attach(MIMEText(mail_gegevens['bericht'], 'plain'))
  # als er bijlagen zijn voeg ze dan toe
  if 'bijlagen' in mail_gegevens.keys():
    # loop door alle bijlagen
    for mail_best in mail_gegevens['bijlagen']:
      bijlage = MIMEBase('application', "octet-stream")
      bijlage.set_payload(open(mail_best,"rb").read())
      Encoders.encode_base64(bijlage)
      bijlage.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(mail_best))
      # voeg de bijlage toe 
      message.attach(bijlage)  
  # maak een beveiligde of onbeveiligde verbinding met de smtp server
  if mail_gegevens['SSL']: 
    smtp = smtplib.SMTP_SSL(mail_gegevens['smtp_server'])
    smtp.login(mail_gegevens['verzender'], mail_gegevens['wachtwoord'])
  else: smtp = smtplib.SMTP(mail_gegevens['smtp_server'])
  # zet het debuglevel op false
  smtp.set_debuglevel(False)
  # verzend de totale mail
  smtp.sendmail(mail_gegevens['verzender'], ontvangers, message.as_string())
  # stop het object
  smtp.quit()
  return	
  
# ----- GZIP_LOG_FILE --------------------------------------------------

def gzip_log_file(log_file, max_bytes = 100000):
  """
  Als een log bestand te groot wordt maak er dan een zip bestand van
  input: log file, maximum bytes
  output: gezipt log bestand en een leeg log bestand
  """
  # kijk of het bestand groter is als het maximum aantal bytes
  if os.path.getsize(log_file) > max_bytes:
    # maak een list met 0
    nummers = [0]
    # loop door de directorie van de log file
    for mail_best in os.listdir(os.path.dirname(log_file)):
      # lees alle bestanden die beginnen met de naam van de log file een eindigen op .gz
      if mail_best.startswith(os.path.basename(log_file)) and mail_best.endswith('.gz'): 
        # voeg de volg nummer toe aan de nummers list
        nummers.append(int(mail_best[len(os.path.basename(log_file))+1:-len('.gz')]))
    # bepaal de naam van de zip file (log_file. + nummer + .gz
    gz_file = '%s.%s.gz' %(log_file, max(nummers)+1)
    # open de log file en de zip file
    with open(log_file, 'rb') as log_in, gzip.open(gz_file, 'wb') as log_out_file:
      # vul de zip file met de data uit de log file
      shutil.copyfileobj(log_in, log_out_file)
    # maak een lege log file
    open(log_file, 'w').close() 
  return

# ----- GEONOVUM XML ---------------------------------------------------

def xml_substring(xml, string):
  """
  functie om een gedeelte (bijv. Geonovum) uit een xml te selecteren
  """
  # als de zoeks string bestaat
  if xml.find(string) != -1:
    # return de substring
    return xml[xml[:xml.find(string)].rfind('<'): xml.rfind(string)+xml[xml.rfind(string):].find('>')+1]
  return ''

# ----- VERWIJDER TAG --------------------------------------------------

def verwijder_tag(xml, string):
  """
  functie om een tag te verwijderen, waarin string voorkomt:
  <????string????>
  """
  # als de zoeks string bestaat
  if xml.find(string) != -1:
    # zoek de tags rondom de string
    lpoint = xml[:xml.find(string)].rfind('<')
    rpoint = lpoint + xml[lpoint:].find('>')+1
    # return de substring
    return xml[lpoint: rpoint]
  return xml
  
# ----- ZOEK TEKST ---------------------------------------
 
def zoek_tekst(xml, strings):
  """
  Return tekst uit een xml binnen 2 strings
  bijv: file_id = zoek_tekst(xml, ['fileIdentifier', 'CharacterString'])
  """
  # bepaal de linker en rechter pointer
  lpoint = xml.find(strings[0])
  lpoint += xml[xml.find(strings[0]):].find(strings[1])
  lpoint += xml[xml.find(strings[0])+xml[xml.find(strings[0]):].find(strings[1]):].find('>')+1
  rpoint = lpoint + xml[lpoint:].find('<')
  # return de tekst binnen de tags
  return xml[lpoint: rpoint]
  
# ----- VERVANG CREATIVE COMMONS ---------------------------------------
 
def vervang_creative_commons(xml):
  """
  Repareer een XML tussen een begin en een eindstring
  """
  # zoek stings
  zoekstring = 'MD_LegalConstraints'
  ccstring = 'http://creativecommons.org/publicdomain/mark/1.0/deed.nl'
  # vervang string
  vervangstring = '<MD_LegalConstraints>\n'
  vervangstring += '<accessConstraints>\n'
  vervangstring += '<MD_RestrictionCode codeList="./resources/codeList.xml#MD_RestrictionCode" codeListValue="otherRestrictions" />\n'
  vervangstring += '</accessConstraints>\n'
  vervangstring += '<useConstraints>\n'
  vervangstring += '<MD_RestrictionCode codeList="./resources/codeList.xml#MD_RestrictionCode" codeListValue="otherRestrictions" />\n'
  vervangstring += '</useConstraints>\n'
  vervangstring += '<otherConstraints>\n'
  vervangstring += '<gco:CharacterString>geen beperkingen</gco:CharacterString>\n'
  vervangstring += '</otherConstraints>\n'
  vervangstring += '<otherConstraints>\n'
  vervangstring += '<gco:CharacterString>http://creativecommons.org/publicdomain/mark/1.0/deed.nl</gco:CharacterString>\n'
  vervangstring += '</otherConstraints>\n'
  vervangstring += '</MD_LegalConstraints>'
  # als de zoek string aanwezig is
  if xml.find(zoekstring) >= 0 and ccstring in xml:
    # bepaal de nieuwe xml inhoud
    xml = '%s%s%s' %(xml[:xml[:xml.find(zoekstring)].rfind('<')], vervangstring, xml[xml.rfind(zoekstring)+xml[xml.rfind(zoekstring):].find('>')+1:])
  return xml
  
# ----- HOOFD PROGRAMMA ------------------------------------------------

if __name__ == '__main__':
  """
  """
  # bepaal de start directorie 
  start_dir, bestand  = os.path.split(os.path.abspath(__file__))
  # maak een object van de configuratie data
  if os.path.isfile(start_dir+os.sep+os.path.splitext(bestand)[0]+'.cfg'): 
    cfg = Config(start_dir+os.sep+os.path.splitext(bestand)[0]+'.cfg')
  # verlaat anders het programma
  else: sys.exit('het configuratie bestand is niet gevonden')
  # als het configuratie bestand niet goed is verlaat het programma
  if cfg.get_dict() == None: sys.exit('er is iets niet goed met het configuratie bestand')  
  # lees de xml directorie uit
  MM_xml_dir = cfg.get('dirs')['MM_xml_dir']
  # lees de overige directorie uit
  attr_dir = cfg.get('dirs')['attr_dir']
  tools_dir = cfg.get('dirs')['tools_dir']
  image_dir =  cfg.get('dirs')['image_dir']
  # lees de log dir uit
  log_dir = cfg.get('dirs')['log_dir']
  # maak een log bestand
  log_file = log_dir+os.sep+os.path.splitext(os.path.split(__file__)[-1])[0]+'.log'
  # maak een basis configuratie voor het loggen
  logging.basicConfig(filemode='a', format='%(asctime)s - %(levelname)-8s "%(message)s"', 
                        datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO, filename=log_file)
  # het programma is gestart
  logging.info('-'*50)
  logging.info('%s is opgestart' %(__file__))
  logging.info('-'*50)  
  # lees de inlog gegevens uit
  inlog_geg = cfg.get('inlog_geg')
  # lees de ISO profielen 
  ISO_profielen = cfg.get('ISO_profielen')
  # bepaal de xml versie
  xml_versie = '<?xml version="1.0" encoding="UTF-8"?>'
  # maak een leeg mail bericht
  mail_bericht = ''  
  # maak een lege list voor alle SDE metadata
  alle_SDE_Metadata = []
  # loop door de verschillende dbases
  for dbase in inlog_geg.keys():
    # lees de inlog voor gegevens voor de betreffende dbase
    if 'user' in inlog_geg[dbase]: user = inlog_geg[dbase]['user']
    if 'password' in inlog_geg[dbase]: password = inlog_geg[dbase]['password']
    if 'server' in inlog_geg[dbase]: server = inlog_geg[dbase]['server']
    if 'poort' in inlog_geg[dbase]: poort = inlog_geg[dbase]['poort']
    # maak connectie met de database
    try:
      db = cx_Oracle.connect(u'%s' %(user), u'%s' %(password), cx_Oracle.makedsn('%s' %(server), poort, '%s' %(dbase)))
    # verlaat het programma als het niet lukt
    except cx_Oracle.DatabaseError, foutje:
      # werk de logging bij
      logging.info('database %s geeft een foutmelding: %s' %(dbase, foutje))
      sys.exit('database %s geeft een foutmelding: %s' %(dbase, foutje))
    # werk de logging bij
    else: 
      logging.info('database %s is aangekoppeld' %(dbase))
      logging.info('database characterset: %s' %(db.encoding))
    # open een cursor
    cursor = db.cursor() 
    # select alle namen uit SDE.GDB_ITEMS
    cursor.execute(u'SELECT NAME, DOCUMENTATION FROM SDE.GDB_ITEMS')
    # loop door de resultaten
    for row in cursor.fetchall(): 
      # als er een uniek nummer is 
      if row[1]:
        # selecteer de bijbehorende xml
        cursor.execute(u'SELECT sde.sdexmltotext(XML_DOC) FROM SDE.SDE_XML_DOC2 WHERE SDE_XML_ID=%d' %(row[1]))
        # lees de resultaten uit de xml
        SDE_xml = cursor.fetchone()[0].read().decode(db.encoding, 'replace')
        # als de xml niet leeg is
        if not SDE_xml:
          logging.info('Metadata tabel: %s is niet aanwezig' %(row[0]))
        else:
          # zet iso_xml op false
          iso_xml = False
          # loop door de ISO profielen
          for iso_profiel in ISO_profielen:
            # als in de xml een iso profiel aanwezig is voer de rest van het programma uit
            if iso_profiel in SDE_xml:
              alle_SDE_Metadata.append(row[0])
              #~ with open('%s%s%s.xml' %(overig_dir, os.sep, row[0]), 'w') as xml_best: xml_best.write(SDE_xml.encode('utf-8'))
              # zet iso_xml op true
              iso_xml = True
              # lees de attribute gegevens
              ATTR_xml = unicode(xml_substring(SDE_xml, 'FC_FeatureCatalogue'))
              ATTR_xml += unicode(xml_substring(SDE_xml, 'eainfo'))
              # als het bestand nog niet bestaat
              if not os.path.isfile('%s%s%s_ATTR.xml' %(attr_dir, os.sep, row[0])):
                # als ATTR_xml niet leeg is
                if ATTR_xml:
                  # schrijf de attribuut gegevens weg
                  with open('%s%s%s_ATTR.xml' %(attr_dir, os.sep, row[0]), 'w') as xml_best: xml_best.write(ATTR_xml.encode('utf-8'))
              # lees de tool gegevens
              tool_xml = unicode(xml_substring(SDE_xml, 'ToolSource'))
              # als het bestand nog niet bestaat
              if not os.path.isfile('%s%s%s_tool.xml' %(tools_dir, os.sep, row[0])):
                # als tool_xml niet leeg is
                if tool_xml:
                  # schrijf de tool gegevens weg
                  with open('%s%s%s_tool.xml' %(tools_dir, os.sep, row[0]), 'w') as xml_best: xml_best.write(tool_xml.encode('utf-8'))
              # lees de thumbnail uit en sla die op
              jpeg = zoek_tekst(SDE_xml, ['Thumbnail', 'Data'])
              # als de jpeg niet leeg is
              if len(jpeg) > 0:
                # als het bestand nog niet bestaat
                if not os.path.isfile('%s%s%s.jpg' %(image_dir, os.sep, row[0])):
                  with open('%s%s%s.jpg' %(image_dir, os.sep, row[0]), 'w') as xml_best: xml_best.write(jpeg.decode('base64','strict'))
              # selecteer alleen de metadata tussen de tags MD_Metadata
              SDE_xml = xml_substring(SDE_xml, 'MD_Metadata')
              # kijk of de metadata al in de MM aanwezig is
              if os.path.isfile(('%s%s%s.xml' %(MM_xml_dir, os.sep, row[0]))):
                # open dan de MM_xml
                with open('%s%s%s.xml' %(MM_xml_dir, os.sep, row[0])) as xml_best: MM_xml = xml_best.read()
                # lees de wijzingings datum van de metadata uit
                MM_metadata_datum = zoek_tekst(MM_xml, ['dateStamp', 'Date'])   
                #lees de wijzingings datum van de metadata uit
                SDE_metadata_datum = zoek_tekst(SDE_xml, ['dateStamp', 'Date'])       
                # als er een nieuwere datum is vervang de xml
                if SDE_metadata_datum > MM_metadata_datum:
                  # vervang de creative commons (bug Esri)
                  SDE_xml = vervang_creative_commons(SDE_xml)
                  # verwijder de tag waarin withheld voorkomt
                  if 'withheld' in SDE_xml: verwijder_tag(SDE_xml, 'withheld')
                  # kijk if de xml begint met de xml versie, anders voeg die toe
                  if xml_versie not in SDE_xml: SDE_xml = '%s\n%s' %(xml_versie, SDE_xml)
                  # sla de gegevens op
                  with open('%s%s%s.xml' %(MM_xml_dir, os.sep, row[0]), 'w') as xml_best: xml_best.write(SDE_xml.encode('utf-8'))
                  logging.info('Bestand (%s): %s%s%s.xml is vervangen' %(dbase, MM_xml_dir, os.sep, row[0]))
                  mail_bericht += 'Bestand (%s): %s%s%s.xml is vervangen\n' %(dbase, MM_xml_dir, os.sep, row[0])
              # als de metadata nog niet bestaat schrijf die dan weg
              else:
                # vervang de creative commons (bug Esri)
                SDE_xml = vervang_creative_commons(SDE_xml)
                # verwijder de tag waarin withheld voorkomt
                if 'withheld' in SDE_xml: verwijder_tag(SDE_xml, 'withheld')
                # kijk if de xml begint met de xml versie, anders voeg die toe
                if xml_versie not in SDE_xml: SDE_xml = '%s\n%s' %(xml_versie, SDE_xml)
                # sla de gegevens op
                with open('%s%s%s.xml' %(MM_xml_dir, os.sep, row[0]), 'w') as xml_best: xml_best.write(SDE_xml.encode('utf-8'))
                logging.info('Bestand (%s): %s%s%s.xml is toegevoegd' %(dbase, MM_xml_dir, os.sep, row[0]))
                mail_bericht += 'Bestand (%s): %s%s%s.xml is toegevoegd\n' %(dbase, MM_xml_dir, os.sep, row[0])
          # geef aan dat de xml geen iso profiel heeft      
          if not iso_xml: logging.info('XML: %s voldoet niet aan het ISO_profiel' %(row[0]))  
  # loop door alle bestanden (zonder .xml) in de MM_xml_dir
  for xml_bestand in [os.path.splitext(xml_bestand)[0] for xml_bestand in os.listdir(MM_xml_dir)]:
    # als het bestand niet voorkomt in alle SDE Metadata, verwijder het dan
    if xml_bestand not in alle_SDE_Metadata and not os.path.isdir(MM_xml_dir+os.sep+xml_bestand): 
      os.remove('%s%s%s.xml' %(MM_xml_dir, os.sep, xml_bestand))
      logging.info('Bestand: %s%s%s.xml is verwijderd' %(MM_xml_dir, os.sep, xml_bestand))
      mail_bericht += 'Bestand: %s%s%s.xml is verwijderd\n' %(MM_xml_dir, os.sep, xml_bestand)
  # als er iets veranderd is stuur dan een mail naar de beheerders
  if mail_bericht:
    # lees de gegevens uit
    mail_gegevens = cfg.get('mail_gegevens')
    # vul de gegevens aan
    mail_gegevens['onderwerp'] = 'Bestand: %s is uitgevoerd' %(os.path.splitext(bestand)[0]) 
    bericht = 'Beste beheerder, \n\n\n' 
    bericht += 'Bij de verwerking van: %s zijn de volgende wijzigingen aangebracht:\n\n' %(os.path.splitext(bestand)[0])
    bericht += '%s\n\n\n' %(mail_bericht)
    bericht += '%s\n' %(mail_gegevens['bericht_naam'])
    bericht += '%s\n' %(mail_gegevens['bericht_org'])
    bericht += '%s\n' %(mail_gegevens['bericht_email'])
    bericht += '%s\n' %(mail_gegevens['bericht_post'])
    bericht += '%s  %s\n\n' %(mail_gegevens['bericht_postcode'], mail_gegevens['bericht_plaats'])
    bericht += '%s' %(mail_gegevens['bericht_www'])
    mail_gegevens['bericht'] = bericht
    # verstuur de gegevens
    Zendmail(mail_gegevens)
  # beperk de omvang van de log file
  gzip_log_file(log_file)        

# ----- EINDE PROGRAMMA ------------------------------------------------
