#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# ----- GEBRUIKTE SOFTWARE ---------------------------------------------
#
# python-2.7         http://www.python.org
#
# ----- GLOBALE VARIABELEN ---------------------------------------------

__doc__      = "Programma om iso xmls klaar te zetten voor een export directorie"
__rights__   = 'provincie Noord-Brabant'
__author__   = 'Jan van Sambeek'
__date__     = ['03-2017']
__version__  = '1.1'

# ----- IMPORT LIBRARIES -----------------------------------------------

import os, sys, datetime, re, smtplib, ssl, socket, logging, gzip, shutil
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

# ----- GZIP_LOG_FILE --------------------------------------------------

def gzip_log_file(log_file, max_bytes = 10000):
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
    for log_best in os.listdir(os.path.dirname(log_file)):
      # lees alle bestanden die beginnen met de naam van de log file een eindigen op .gz
      if log_best.startswith(os.path.basename(log_file)) and log_best.endswith('.gz'): 
        # voeg de volg nummer toe aan de nummers list
        nummers.append(int(log_best[len(os.path.basename(log_file))+1:-len('.gz')]))
    # bepaal de naam van de zip file (log_file. + nummer + .gz
    gz_file = '%s.%s.gz' %(log_file, max(nummers)+1)
    # open de log file en de zip file
    with open(log_file, 'rb') as log_in, gzip.open(gz_file, 'wb') as log_out_file:
      # vul de zip file met de data uit de log file
      shutil.copyfileobj(log_in, log_out_file)
    # maak een lege log file
    open(log_file, 'w').close() 
  return

# ----- ZENDMAIL -------------------------------------------------------

def Zendmail(mail_gegevens, SSL=True):
  """
  Functie Zendmail(mail_gegevens, SSL=False)
  
  Is een programma om mail met bijlagen te versturen naar één of meerder ontvangers.
  De mail gegevens bestaan uit, een dictionarie met daarin:
  verzender, wachtwoord, alias, ontvangers, cc, bc,  onderwerp, bericht, de smtp_server en eventueel bijlagen.
  Ontvangers, cc, bc en bijlagen zijn lists, alle overige variabelen zijn strings. 
  verplicht: verzender, ontvangers, onderwerp, bericht, de smtp_server
  optioneel: wachtwoord, alias, cc, bc, bijlagen
  Afhankelijk van de provider kan een SSL beveiliging meegegeven worden 
  door SSL=True of SSL=False bij het oproepen van de functie mee te geven.
  
  
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
  
  Zendmail(mail_gegevens, SSL=True) 
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
  if SSL: smtp = smtplib.SMTP_SSL(mail_gegevens['smtp_server'])
  else: smtp = smtplib.SMTP(mail_gegevens['smtp_server'])
  # zet het debuglevel op false
  smtp.set_debuglevel(False)
  # login bij de smtp server
  if 'wachtwoord' in mail_gegevens.keys():
    smtp.login(mail_gegevens['verzender'], mail_gegevens['wachtwoord'].decode('base64','strict'))
  # verzend de totale mail
  smtp.sendmail(mail_gegevens['verzender'], ontvangers, message.as_string())
  # stop het object
  smtp.quit()
  return	
  
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

# ----- VOEG IN STYLE SHEET --------------------------------------------

def voeg_in_style_sheet(xml, string, style_sheet):
  """
  functie om een style sheet toe te voegen
  """
  # return de aangepaste xml
  pointer = xml[:xml.find(string)].rfind('<')
  return xml[:pointer]+style_sheet+xml[pointer:]

# ----- VERVANG CONTACT ------------------------------------------------
 
def vervang_contact(xml, cont_gegevens):
  """
  Vervang de contact gegevens door algemene contact gegevens
  """
  # zoek op MD_DataIdentification
  zoekstring = 'MD_DataIdentification'
  # maak een list van de MD_DataIdentification pointers
  id_pointers = sorted([pointer.start() for pointer in re.finditer(zoekstring, xml)])
  # zoek MD_Distributor
  zoekstring = 'MD_Distributor'
  # maak een list van de MD_Distributor pointers
  dist_pointers = sorted([pointer.start() for pointer in re.finditer(zoekstring, xml)])
  # verwijder de quality contact gegevens
  # bepaal de zoekstring voor de quality contact gegevens met > ivm CI_RoleCode lijst
  zoekstring = 'processor>'
  # maak een list van de begin pointers en sorteer reverse om vanaf achter de contact gegevens te verwijderen
  pointers = sorted([pointer.start() for pointer in re.finditer(zoekstring, xml)], reverse = True)
  # als ze gevuld zijn
  if pointers:
    # loop in stappen van 2 door de pointers
    for num in range(len(pointers))[::2]:
      # bepaal de left pointer
      lpoint = xml[: pointers[num+1]].rfind('<') 
      # bepaal de right pointer
      rpoint = pointers[num] + len(zoekstring)
      # verwijder de quality contact gegevens uit de xml
      xml = xml[: lpoint] + xml[rpoint: ]
  # wijzig de overige contact gegevens
  # zoek stings
  zoekstring = 'gmd:CI_ResponsibleParty'
  # als de zoek string bestaat bepaal dan de namespaces
  if xml.find(zoekstring) >= 0: 
    ns_gmd = 'gmd:'
    ns_gco = ' xmlns:gco="http://www.isotc211.org/2005/gco"'
  # kijk of de zoekstring zonder namespace bestaat en bepaal de namespaces
  elif xml.find(zoekstring.split(':')[-1]) >= 0: 
    ns_gmd = ''
    ns_gco = ''
    zoekstring = zoekstring.split(':')[-1]
  # de zoekstring komt niet voor, verlaat de functie
  else: return xml
  # maak een list van de begin pointers en sorteer reverse om vanaf achter de contact gegevens te vervangen
  pointers = sorted([pointer.start() for pointer in re.finditer(zoekstring, xml)], reverse = True)    
  # bepaal de vervang gegevens
  vervangstring = '<%sCI_ResponsibleParty>\n' %(ns_gmd)
  if 'organisatie' in cont_gegevens.keys():
    vervangstring += '<%sorganisationName>\n' %(ns_gmd)
    vervangstring += '<gco:CharacterString%s>%s</gco:CharacterString>\n' %(ns_gco, cont_gegevens['organisatie'])
    vervangstring += '</%sorganisationName>\n' %(ns_gmd)
  vervangstring += '<%scontactInfo>\n' %(ns_gmd)
  vervangstring += '<%sCI_Contact>\n' %(ns_gmd)
  if 'tel' in cont_gegevens.keys():
    vervangstring += '<%sphone>\n' %(ns_gmd)
    vervangstring += '<%sCI_Telephone>\n' %(ns_gmd)
    vervangstring += '<%svoice>\n' %(ns_gmd)
    vervangstring += '<gco:CharacterString%s>%s</gco:CharacterString>\n' %(ns_gco, cont_gegevens['tel'])
    vervangstring += '</%svoice>\n' %(ns_gmd)
    vervangstring += '</%sCI_Telephone>\n' %(ns_gmd)
    vervangstring += '</%sphone>\n' %(ns_gmd)
  vervangstring += '<%saddress>\n' %(ns_gmd)
  vervangstring += '<%sCI_Address>\n' %(ns_gmd)
  if 'adres' in cont_gegevens.keys():
    vervangstring += '<%sdeliveryPoint>\n' %(ns_gmd)
    vervangstring += '<gco:CharacterString>%s</gco:CharacterString>\n' %(ns_gco, cont_gegevens['adres'])
    vervangstring += '</%sdeliveryPoint>\n' %(ns_gmd)
  if 'plaats' in cont_gegevens.keys():
    vervangstring += '<%scity>\n' %(ns_gmd)
    vervangstring += '<gco:CharacterString>%s</gco:CharacterString>\n' %(ns_gco, cont_gegevens['plaats'])
    vervangstring += '</%scity>\n' %(ns_gmd)
  if 'provincie' in cont_gegevens.keys():  
    vervangstring += '<%sadministrativeArea>\n' %(ns_gmd)
    vervangstring += '<gco:CharacterString>%s</gco:CharacterString>\n' %(ns_gco, cont_gegevens['provincie'])
    vervangstring += '</%sadministrativeArea>\n' %(ns_gmd)
  if 'postcode' in cont_gegevens.keys():
    vervangstring += '<%spostalCode>\n' %(ns_gmd)
    vervangstring += '<gco:CharacterString>%s</gco:CharacterString>\n' %(ns_gco, cont_gegevens['postcode'])
    vervangstring += '</%spostalCode>\n' %(ns_gmd)
  if 'land' in cont_gegevens.keys():
    vervangstring += '<%scountry>\n' %(ns_gmd)
    vervangstring += '<gco:CharacterString>Nederland</gco:CharacterString>\n' %(ns_gco, cont_gegevens['land'])
    vervangstring += '</%scountry>\n' %(ns_gmd)
  if 'email' in cont_gegevens.keys(): 
    vervangstring += '<%selectronicMailAddress>\n' %(ns_gmd)
    vervangstring += '<gco:CharacterString%s>%s</gco:CharacterString>\n' %(ns_gco, cont_gegevens['email'])
    vervangstring += '</%selectronicMailAddress>\n' %(ns_gmd)
  vervangstring += '</%sCI_Address>\n' %(ns_gmd)
  vervangstring += '</%saddress>\n' %(ns_gmd)
  if 'url' in cont_gegevens.keys():
    vervangstring += '<%sonlineResource>\n' %(ns_gmd)
    vervangstring += '<%sCI_OnlineResource>\n' %(ns_gmd)
    vervangstring += '<%slinkage>\n' %(ns_gmd)
    vervangstring += '<URL%s>%s</URL>\n' %(ns_gco, cont_gegevens['url'])
    vervangstring += '</%slinkage>\n' %(ns_gmd)
    vervangstring += '</%sCI_OnlineResource>\n' %(ns_gmd)
    vervangstring += '</%sonlineResource>\n' %(ns_gmd)
  vervangstring += '</%sCI_Contact>\n' %(ns_gmd)
  vervangstring += '</%scontactInfo>\n' %(ns_gmd)
  # loop in stappen van 2 door de pointers
  for num in range(len(pointers))[::2]:
    # bepaal de left pointer
    lpoint = xml[: pointers[num+1]].rfind('<')
    # bepaal de right pointer
    rpoint = pointers[num] + xml[pointers[num]: ].find('>') + 1    
    # bepaal afhankelijk van de plaats in de xml de CI RoleCode
    RoleCodeString = vervangstring 
    RoleCodeString += '<%srole>\n' %(ns_gmd)
    # voor de contacten binne de MD_DataIdentification tags is de CI RoleCode owner 
    if lpoint > id_pointers[0] and lpoint < id_pointers[1]:
      RoleCodeString += '<%sCI_RoleCode codeList="./resources/codeList.xml#CI_RoleCode" codeListValue="owner" />\n' %(ns_gmd)
    # voor de contacten binne de MD_DataIdentification tags is de CI RoleCode distibutor
    elif lpoint > dist_pointers[0] and lpoint < dist_pointers[1]:
      RoleCodeString += '<%sCI_RoleCode codeList="./resources/codeList.xml#CI_RoleCode" codeListValue="distributor" />\n' %(ns_gmd)
    # voor de overige contacten is de CI RoleCode pointOfContact
    else:
      RoleCodeString += '<%sCI_RoleCode codeList="./resources/codeList.xml#CI_RoleCode" codeListValue="pointOfContact" />\n' %(ns_gmd)
    RoleCodeString += '</%srole>\n' %(ns_gmd)    
    RoleCodeString += '</%sCI_ResponsibleParty>' %(ns_gmd)
    # vervang dmv de RoleCodeString
    xml = xml[: lpoint] + RoleCodeString + xml[rpoint: ]
  # verwijder overbodige contacten
  # verwijder overbodige pointOfContacts
  zoekstring = 'pointOfContact'
  if xml.count(zoekstring) > 2:
    # maak een list van de begin pointers en sorteer reverse om overbodige contact gegevens te verwijderen
    pointers = sorted([pointer.start() for pointer in re.finditer(zoekstring, xml)], reverse = True)
    # verwijder de codelistvalues "pointOfContact"
    for pointer in re.finditer('"'+zoekstring+'"', xml): 
      if pointer.start()+1 in pointers: pointers.remove(pointer.start()+1)
    # verwijder de laatste 2 pointers (die moeten blijven)
    pointers = pointers[:-2]
    # als pointers niet leeg is verwijder dan de overige pointOfContacts
    if pointers:
      # loop in stappen van 2 door de pointers
      for num in range(len(pointers))[::2]:
        # bepaal de left pointer
        lpoint = xml[: pointers[num+1]].rfind('<') 
        # bepaal de right pointer
        rpoint = pointers[num] + xml[pointers[num]: ].find('>') + 1
        # verwijder de overbodige contact gegevens
        xml = xml[: lpoint] + xml[rpoint: ]      
  return xml
  
# ----- HOOFD PROGRAMMA ------------------------------------------------

if __name__ == '__main__':
  """
  Programma om iso xmls klaar te zetten voor een export directorie
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
  # lees de xml directories uit
  MM_xml_dir = cfg.get('dirs')['MM_xml_dir']
  export_xml_dir = cfg.get('dirs')['export_xml_dir']
  log_dir = cfg.get('dirs')['log_dir']
  # maak een log bestand
  log_file = log_dir+os.sep+os.path.splitext(os.path.split(__file__)[-1])[0]+'.log'
  # maak een basis configuratie voor het loggen
  logging.basicConfig(filemode='a', format='%(asctime)s - %(levelname)-8s "%(message)s"', datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO, filename=log_file)
  # het programma is gestart
  logging.info('-'*50)
  logging.info('%s is opgestart' %(__file__))
  logging.info('-'*50)
  # maak een lege list
  export_namen = []
  # maak een leeg mail bericht
  mail_bericht = ''
  # bepaal alle bestanden die doorlopen worden
  if cfg.get('xml_namen'): metadata_xmls = cfg.get('xml_namen')
  else: metadata_xmls = [os.path.splitext(xml)[0] for xml in os.listdir(MM_xml_dir)]
  # loop door alle metadata xmls
  for metadata_xml in metadata_xmls:
    # als lees xml op niet exporteren bestaat
    if cfg.get('xml_niet_exporteren'):
      # kijk of de xml hierin voorkomt 
      if metadata_xml in cfg.get('xml_niet_exporteren'):         
        # vul de logging
        logging.info('Bestand: %s.xml wordt niet geëxporteerd' %(metadata_xml))
        # ga naar de volgende xml
        continue
    # als het bestand bestaat in de MM xml dir
    if os.path.isfile(('%s%s%s.xml' %(MM_xml_dir, os.sep, metadata_xml))):
      # open dan de xml_new
      with open('%s%s%s.xml' %(MM_xml_dir, os.sep, metadata_xml)) as xml_best: xml_new = xml_best.read().decode('utf-8')
      # als style-sheet is ingevuld vul die dan toe aan de xml
      if cfg.get('style-sheet'): xml_new = voeg_in_style_sheet(xml_new, 'MD_Metadata', cfg.get('style-sheet'))
      # als de file_id True is maak dan de file_id als bestandsnaam anders de metadata xml
      if cfg.get('file_id'): export_naam = zoek_tekst(xml_new, ['fileIdentifier', 'CharacterString'])
      else: export_naam = metadata_xml
      # voeg de export_naam toe aan export_namen
      export_namen.append(export_naam)
      # lees de wijzingings datum van de metadata uit
      metadata_datum = zoek_tekst(xml_new, ['dateStamp', 'Date'])      
      # als het bestand bestaat in de export xml dir
      if os.path.isfile(('%s%s%s.xml' %(export_xml_dir, os.sep, export_naam))):
        # open dan export xml
        with open('%s%s%s.xml' %(export_xml_dir, os.sep, export_naam)) as xml_best: export_xml = xml_best.read()
        # lees de wijzingings datum van de metadata uit
        metadata_datum_export = zoek_tekst(export_xml, ['dateStamp', 'Date'])
        # als er een nieuwere datum is vervang de xml
        if metadata_datum > metadata_datum_export:
          # vervang de contact gegevens als de contact gegevens ingevuld zijn
          if cfg.get('cont_gegevens'): xml_new = vervang_contact(xml_new, cfg.get('cont_gegevens'))
          # vervang het bestand
          with open('%s%s%s.xml' %(export_xml_dir, os.sep, export_naam), 'w') as xml_best: xml_best.write(xml_new.encode('utf-8'))
          logging.info('Bestand: %s%s%s.xml (%s) is vervangen' %(export_xml_dir, os.sep, export_naam, metadata_xml))
          mail_bericht += 'Bestand: %s%s%s.xml (%s) is vervangen\n' %(export_xml_dir, os.sep, export_naam, metadata_xml)
      # als het bestand niet bestaat voeg het dan toe
      else:
        # vervang de contact gegevens als de contact gegevens ingevuld zijn
        if cfg.get('cont_gegevens'): xml_new = vervang_contact(xml_new, cfg.get('cont_gegevens'))
        # voeg het bestand toe
        with open('%s%s%s.xml' %(export_xml_dir, os.sep, export_naam), 'w') as xml_best: xml_best.write(xml_new.encode('utf-8'))
        logging.info('Bestand: %s%s%s.xml (%s) is toegevoegd' %(export_xml_dir, os.sep, export_naam, metadata_xml))
        mail_bericht += 'Bestand: %s%s%s.xml (%s) is toegevoegd\n' %(export_xml_dir, os.sep, export_naam, metadata_xml)
    # anders
    else:
      # zet in de log dat de xml niet bestaat in de MM_xml_dir
      logging.info('Bestand: %s%s%s.xml bestaat niet' %(MM_xml_dir, os.sep, metadata_xml))
      mail_bericht += 'Bestand: %s%s%s.xml bestaat niet\n' %(MM_xml_dir, os.sep, metadata_xml)
  # loop door alle bestanden (zonder .xml) in de export_xml_dir
  for xml_export in [os.path.splitext(xml_export)[0] for xml_export in os.listdir(export_xml_dir)]: 
    # als het bestand niet voorkomt in export_namen verwijder het dan
    if xml_export not in export_namen: 
      os.remove('%s%s%s.xml' %(export_xml_dir, os.sep, xml_export))
      logging.info('Bestand: %s%s%s.xml is verwijderd' %(export_xml_dir, os.sep, xml_export))
      mail_bericht += 'Bestand: %s%s%s.xml is verwijderd\n' %(export_xml_dir, os.sep, xml_export)
  # als er iets veranderd is stuur dan een mail naar de beheerders
  if mail_bericht:
    # lees de gegevens uit
    mail_gegevens = cfg.get('mail_gegevens')
    # vul de gegevens aan
    mail_gegevens['onderwerp'] = 'Bestand: %s is uitgevoerd' %(os.path.splitext(bestand)[0]) 
    bericht = 'Beste beheerder, \n\n\n' 
    bericht += 'Bij de verwerking van %s zijn de volgende wijzigingen aangebracht:\n\n' %(os.path.splitext(bestand)[0])
    bericht += '%s\n\n\n' %(mail_bericht)
    bericht += '%s\n' %(mail_gegevens['bericht_naam'])
    bericht += '%s\n' %(mail_gegevens['bericht_org'])
    bericht += '%s\n' %(mail_gegevens['bericht_email'])
    bericht += '%s\n' %(mail_gegevens['bericht_post'])
    bericht += '%s  %s\n\n' %(mail_gegevens['bericht_postcode'], mail_gegevens['bericht_plaats'])
    bericht += '%s' %(mail_gegevens['bericht_www'])
    mail_gegevens['bericht'] = bericht
    # verstuur de gegevens
    Zendmail(mail_gegevens, SSL=False)
  # beperk de omvang van de log file
  gzip_log_file(log_file) 
      
# ----- EINDE PROGRAMMA ------------------------------------------------
