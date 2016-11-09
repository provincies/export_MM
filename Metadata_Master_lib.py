#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# ----- GEBRUIKTE SOFTWARE --------------------------------------------------------------------------------------------------
#
# python-2.7                              http://www.python.org
#
# ----- MET DANK AAN ---------------------------------------------------
#
# http://www.blythe.org/webwork/numbercolor.html
# http://xoomer.virgilio.it/infinity77/wxPython/
# http://www.zetcode.com
#
# ----- GLOBALE VARIABELEN ---------------------------------------------

__doc__      = '''
               Librarie met diverse classes en functies:
               - zoek_tag: Zoek een tag in een xml object en geef de waarde terug van die tag
               - repare_single_tag: Repareer een single tag in een xml object 
               - zoek_tag_waarde: Doorzoek een tag in een xml object en geef een list met waardes terug van die tag
               - repare_multi_tag: Repareer een multi tag in een xml object
               - contact_gegevens: Zoek de contact gegevens
               - remove_xml_data: Verwijder een gedeelte uit een XML tussen begin en een eindstring
               - vervang_creative_commons: Repareer een XML tussen een begin en een eindstring
               - vervang_datestamp: Return xml met een aangepaste dateStamp (vandaag)
               - zoek_tekst_waarde: zoek in de xml naar een waarde na 2 tags
               - vervang_time_period: Vervang de begin en eind tijd in time period als de eind tijd niet correct is in de xml
               - verwijder_time_period: Verwijder de gehele time period uit de xml
               - config: Class om configuratie bestanden uit te lezen/schrijven
               - gzip_log_file: Als een log bestand te groot wordt maak er dan een zip bestand van
               - metadata_validatie: Validatie van de metadata bij Geonovum
               - verwerking_results: Verwerk de resultaten van de validatie
                '''
__rights__   = 'provincie Noord-Brabant'
__author__   = 'Jan van Sambeek'
__date__     = ['03-2016']
__version__  = '1.0'

# ----- IMPORT LIBRARIES -----------------------------------------------

import requests, datetime, time, os, re, sys, multiprocessing, uuid, logging, gzip, shutil
from xml.dom import minidom
from bs4 import BeautifulSoup
 
# ----- ZOEK TAG -------------------------------------------------------

def zoek_tag(xmlObject, tags, std_ns='gmd'):
  """
  Zoek een tag in een xml object en geef
  de waarde terug van die tag
  """
  # splits de tags in stop ze in een list
  tag_list = tags.strip('/').split('/')
  # loop door de verschillende tags
  for tag in tag_list:
    # loop door de child nodes van het object
    for child in xmlObject.childNodes:
      # kijk of de standaard namespace is gebruikt anders voeg die toe
      if len(child.nodeName.split(':')) == 1:
        knoopnaam = std_ns+':'+child.nodeName     
      else: knoopnaam = child.nodeName      
      # als de node naam van het child gelijk is aan de tag
      if knoopnaam == tag:
        # vervang het xml object door de child xml
        xmlObject = child
        # stop de childNodes lus
        break
  # loop door de onderste tag
  for child in xmlObject.childNodes:
    # kijk of de node een tekst node is
    if child.nodeType == child.TEXT_NODE:
      # als de node data bestaat geef deze aan terug
      if child.data: return child.data.strip().encode('utf_8') 
  # als er niets gevonden is geef dan een False terug
  return False

# ----- REPARE SINGLE TAG ----------------------------------------------

def repare_single_tag(xmlObject, repare_data, std_ns='gmd'):
  """
  Repareer een single tag in een xml object 
  """
  # strip en splits de tags in stop ze in een list
  tag_list = repare_data['tags'].strip('/').split('/')
  # loop door de verschillende tags
  for tag in tag_list:
    # loop door de child nodes van het object
    for child in xmlObject.childNodes:
      # kijk of de standaard namespace is gebruikt anders voeg die toe
      if len(child.nodeName.split(':')) == 1:
        knoopnaam = std_ns+':'+child.nodeName     
      else: knoopnaam = child.nodeName      
      # als de node naam van het child gelijk is aan de tag
      if knoopnaam == tag:
        # vervang het xml object door de child xml
        xmlObject = child
        # stop de childNodes lus
        break
  # loop door de onderste tag
  for child in xmlObject.childNodes:
    # kijk of de node een tekst node is
    if child.nodeType == child.TEXT_NODE:
      # als de node data bestaat geef deze aan terug
      if child.data and child.data == repare_data['old_text']: 
        child.data = repare_data['new_text']
  return

# ----- ZOEK TAG WAARDE ------------------------------------------------

def zoek_tag_waarde(xmlObject, tags, std_ns='gmd'):
  """
  Doorzoek een tag in een xml object en geef een list
  met waardes terug van die tag
  """
  # haal de / aan de voorkant en achterkant weg
  tags = tags.strip('/')
  # splits de tags in stop ze in een list
  tag_list = tags.split('/')
  # draai de list om
  tag_list.reverse()
  # maak een lege list voor de waardes de terug gegeven worden
  waarde_list = []
  # maak een get_tag met de zoekwaarde
  get_tag = tag_list[0]
  # als de tag niet met gmd: begint pas dan de get_tag aan met alleen het laatste stuk 
  if xmlObject.getElementsByTagName(get_tag) == []: get_tag = get_tag.split(':')[1]
  # loop door de elementen met onderste tag      
  for xml_element in xmlObject.getElementsByTagName(get_tag):
    # maak een tweede tag list om te kijken of die klopt met de eerste
    tag2_list = []
    # maak een copy van het element
    tag_obj = xml_element
    # loop door het aantal tags
    for num in range(len(tag_list)):
      # kijk of de standaard namespace is gebruikt anders voeg die toe
      if len(tag_obj.tagName.split(':')) == 1:
        tagnaam = std_ns+':'+tag_obj.tagName     
      else: tagnaam = tag_obj.tagName      
      # als parent tag en tag uit de list niet gelijk zijn stop de lus
      if str(tag_list[num]) != str(tagnaam): break
      # vul de list met tag naam
      tag2_list.append(str(tagnaam))
      # ga een element hoger (parent)
      tag_obj = tag_obj.parentNode
    # als tag list en tag2 list gelijk zijn  
    if tag_list == tag2_list:
      # loop door de onderste tag
      for child in xml_element.childNodes:
        # kijk of de node een tekst node is
        if child.nodeType == child.TEXT_NODE:
          # als de node data bestaat geef deze aan terug
          if child.data: elem_waarde = child.data
      # kijk of element waarde gevuld is
      if 'elem_waarde' in locals():    
        # voeg de element waarde toe aan de list met waardes    
        waarde_list.append(elem_waarde.strip().encode('utf_8'))
  # geef de list met waardes terug
  return waarde_list
  
# ----- REPARE MULTI TAG -----------------------------------------------

def repare_multi_tag(xmlObject, repare_data, std_ns='gmd'):
  """
  Repareer een multi tag in een xml object
  """
  # splits de tags in stop ze in een list
  tag_list = repare_data['tags'].strip('/').split('/')
  # draai de list om
  tag_list.reverse()
  # maak een lege list voor de waardes de terug gegeven worden
  waarde_list = []
  # maak een get_tag met de zoekwaarde
  get_tag = tag_list[0]
  # als de tag niet met gmd: begint pas dan de get_tag aan met alleen het laatste stuk 
  if xmlObject.getElementsByTagName(get_tag) == []: get_tag = get_tag.split(':')[1]
  # loop door de elementen met onderste tag      
  for xml_element in xmlObject.getElementsByTagName(get_tag):
    # maak een tweede tag list om te kijken of die klopt met de eerste
    tag2_list = []
    # maak een copy van het element
    tag_obj = xml_element
    # loop door het aantal tags
    for num in range(len(tag_list)):
      # kijk of de standaard namespace is gebruikt anders voeg die toe
      if len(tag_obj.tagName.split(':')) == 1: tagnaam = std_ns+':'+tag_obj.tagName     
      else: tagnaam = tag_obj.tagName      
      # als parent tag en tag uit de list niet gelijk zijn stop de lus
      if str(tag_list[num]) != str(tagnaam): break
      # vul de list met tag naam
      tag2_list.append(str(tagnaam))
      # ga een element hoger (parent)
      tag_obj = tag_obj.parentNode
    # als tag list en tag2 list gelijk zijn  
    if tag_list == tag2_list:
      # loop door de onderste tag
      for child in xml_element.childNodes:
        # kijk of de node een tekst node is
        if child.nodeType == child.TEXT_NODE:
          # als de node data bestaat geef deze aan terug
          if child.data == repare_data['old_text']:
            child.data = repare_data['new_text']
  return 

# ----- CONTACT GEGEVENS -----------------------------------------------

def contact_gegevens(xmlObject, contact_tags, std_ns='gmd'):
  """
  Zoek de contact gegevens
  """
  contact_dict = {}
  for contact_tag in contact_tags.keys():
    # maak een lege dict value
    contact_dict[contact_tag] = u''
    contactObject = xmlObject
    contact_list = contact_tags[contact_tag].strip('/').split('/')
    # loop door de verschillende tags
    for tag in contact_list:
      # loop door de child nodes van het object
      for child in contactObject.childNodes:
        # kijk of de standaard namespace is gebruikt anders voeg die toe
        if len(child.nodeName.split(':')) == 1:
          knoopnaam = std_ns+':'+child.nodeName     
        else: knoopnaam = child.nodeName      
        # als de node naam van het child gelijk is aan de tag
        if knoopnaam == tag:
          # vervang het xml object door de child xml
          contactObject = child
          # stop de childNodes lus
          break
    # loop door de onderste tag
    for child in contactObject.childNodes:
      # kijk of de node een tekst node is
      if child.nodeType == child.TEXT_NODE:
        # als de node data bestaat geef deze aan terug
        if child.data: contact_dict[contact_tag] = child.data.strip().encode('utf_8')
  return contact_dict

# ----- REMOVE XML DATA ------------------------------------------------

def remove_xml_data(metadata_xml, strings):
  """
  Verwijder een gedeelte uit een XML tussen begin en een eindstring
  """
  # de eerste string is de begin eind string
  begin_eind_string = strings[0]
  # de laatste string is de hoofd zoekstring
  zoekstring = strings[-1]
  # lees het meta bestand uit 
  with open(metadata_xml, 'r') as bestand: xml = bestand.read()
  # als de zoeks tring bestaat
  if xml.find(zoekstring) != -1:
    string_oke = True
    # zoek de begin en eind pointer in de xml
    begin_pointer = xml[:xml[:xml.find(zoekstring)].rfind(begin_eind_string)].rfind('<')
    eind_pointer = xml.find(zoekstring)+xml[xml.find(zoekstring):].find(begin_eind_string)+len(begin_eind_string)
    # als alle strings in de sub tekst voorkomen
    for string in strings:
      if string not in xml[begin_pointer:eind_pointer]: 
        string_oke = False
        break
    # als alles goed is
    if string_oke:
      xml = xml[:begin_pointer] + xml[eind_pointer:]
      # pas de datestamp aan
      xml = vervang_datestamp(xml)
      # schrijf alles naar het bestand
      with open(metadata_xml, 'w') as bestand: bestand.write(xml)
  return
    
# ----- VERVANG CREATIVE COMMONS ---------------------------------------
 
def vervang_creative_commons(metadata_xml):
  """
  Repareer een XML tussen een begin en een eindstring
  """
  # zoek stings
  zoekstring = 'gmd:MD_LegalConstraints>'
  ccstring = 'http://creativecommons.org/publicdomain/mark/1.0/deed.nl'
  # lees het meta bestand uit 
  with open(metadata_xml, 'r') as bestand: xml = bestand.read()
  if xml.find(zoekstring) >= 0: 
    ns_gmd = 'gmd:'
    ns_gco = ' xmlns:gco="http://www.isotc211.org/2005/gco"'
  elif xml.find(zoekstring.split(':')[-1]) >= 0: 
    ns_gmd = ''
    ns_gco = ''
    zoekstring = zoekstring.split(':')[-1]
  # vervang string
  vervangstring = '%sMD_LegalConstraints>\n' %(ns_gmd)
  vervangstring += '<%saccessConstraints>\n' %(ns_gmd)
  vervangstring += '<%sMD_RestrictionCode codeList="./resources/codeList.xml#MD_RestrictionCode" codeListValue="otherRestrictions" />\n' %(ns_gmd)
  vervangstring += '</%saccessConstraints>\n' %(ns_gmd)
  vervangstring += '<%suseConstraints>\n' %(ns_gmd)
  vervangstring += '<%sMD_RestrictionCode codeList="./resources/codeList.xml#MD_RestrictionCode" codeListValue="otherRestrictions" />\n' %(ns_gmd)
  vervangstring += '</%suseConstraints>\n' %(ns_gmd)
  vervangstring += '<%sotherConstraints>\n' %(ns_gmd)
  vervangstring += '<gco:CharacterString%s>geen beperkingen</gco:CharacterString>\n' %(ns_gco)
  vervangstring += '</%sotherConstraints>\n' %(ns_gmd)
  vervangstring += '<%sotherConstraints>\n' %(ns_gmd)
  vervangstring += '<gco:CharacterString%s>http://creativecommons.org/publicdomain/mark/1.0/deed.nl</gco:CharacterString>\n' %(ns_gco)
  vervangstring += '</%sotherConstraints>\n' %(ns_gmd)
  vervangstring += '</%sMD_LegalConstraints>\n' %(ns_gmd)
  # als de zoek string aanwezig is
  if xml.find(zoekstring) >= 0 and ccstring in xml:
    # bepaal de nieuwe xml inhoud
    xml = '%s%s%s' %(xml[:xml.find(zoekstring)], vervangstring, xml[xml.rfind(zoekstring)+len(zoekstring):])
    # pas de datestamp aan
    xml = vervang_datestamp(xml)
    # schrijf alles weg
    with open(metadata_xml, 'w') as bestand: bestand.write(xml)
  return

# ----- ZOEK TEKST WAARDE ------------------------------------------

def zoek_tekst_waarde(xml, tags):
  """
  zoek in de xml naar een waarde na 2 tags
  """
  # bepaal de linker en rechter pointer
  if xml.find(tags[0]) > 0: 
    lpoint = xml.find(tags[0])
    if xml[xml.find(tags[0]):].find(tags[1]) > 0:
      lpoint += xml[xml.find(tags[0]):].find(tags[1])
      lpoint += xml[xml.find(tags[0])+xml[xml.find(tags[0]):].find(tags[1]):].find('>')+1
      rpoint = lpoint + xml[lpoint:].find('<')
      # return xml 
      return xml[lpoint:rpoint]
    else: return False
  else: return False

# ----- VERVANG TIME PERIOD --------------------------------------------

def vervang_time_period(xml, begin_eind_tijd):
  """
  Vervang de begin en eind tijd in time period als de eind tijd niet correct is in de xml
  """ 
  # zoek stings
  zoekstring = 'gmd:temporalElement>'
  if xml.find(zoekstring) >= 0: 
    ns_gmd = 'gmd:'
    ns_gml = ' xmlns:gml="http://www.opengis.net/gml"'
  elif xml.find(zoekstring.split(':')[-1]) >= 0: 
    ns_gmd = ''
    ns_gml = ''
    zoekstring = zoekstring.split(':')[-1]  
  # vervang string
  vervangstring = '%stemporalElement>\n' %(ns_gmd)
  vervangstring += '<%sEX_TemporalExtent>\n' %(ns_gmd)
  vervangstring += '<%sextent>\n' %(ns_gmd)
  vervangstring += '<gml:TimePeriod%s gml:id="tp1">\n' %(ns_gml)
  vervangstring += '<gml:begin>\n'
  vervangstring += '<gml:TimeInstant gml:id="ti1">\n'
  vervangstring += '<gml:timePosition>%s</gml:timePosition>\n' %(begin_eind_tijd[0])
  vervangstring += '</gml:TimeInstant>\n'
  vervangstring += '</gml:begin>\n'
  vervangstring += '<gml:end>\n'
  vervangstring += '<gml:TimeInstant gml:id="ti2">\n'
  vervangstring += '<gml:timePosition>%s</gml:timePosition>\n' %(begin_eind_tijd[1])
  vervangstring += '</gml:TimeInstant>\n'
  vervangstring += '</gml:end>\n'
  vervangstring += '</gml:TimePeriod>\n'
  vervangstring += '</%sextent>\n' %(ns_gmd)
  vervangstring += '</%sEX_TemporalExtent>\n' %(ns_gmd)
  vervangstring += '</%stemporalElement>' %(ns_gmd)
  # als de zoek string aanwezig is
  if xml.find(zoekstring) >= 0:
    # bepaal de nieuwe xml inhoud
    xml = '%s%s%s' %(xml[:xml.find(zoekstring)], vervangstring, xml[xml.rfind(zoekstring)+len(zoekstring):])
    # pas de datestamp aan
    xml = vervang_datestamp(xml)
  return xml

# ----- VERWIJDER TIME PERIOD ------------------------------------------

def verwijder_time_period(xml):
  """
  Verwijder de gehele time period uit de xml
  """ 
  zoekstring = 'temporalElement'
  # zoek de begin en eind pointer in de xml
  begin_pointer = xml[:xml.find(zoekstring)].rfind('<')
  eind_pointer = xml.rfind(zoekstring)+xml[xml.rfind(zoekstring):].find('>')+1 
  # geef de xml terug zonder de tags binnen de zoekstring
  return xml[:begin_pointer]+xml[eind_pointer:]
  
# ----- VERVANG DATESTAMP ----------------------------------------------
 
def vervang_datestamp(xml):
  """
  Return xml met een aangepaste dateStamp (vandaag)
  """
  strings = ['dateStamp', 'Date']
  # bepaal de linker en rechter pointer
  lpoint = xml.find(strings[0])
  lpoint += xml[xml.find(strings[0]):].find(strings[1])
  lpoint += xml[xml.find(strings[0])+xml[xml.find(strings[0]):].find(strings[1]):].find('>')+1
  rpoint = lpoint + xml[lpoint:].find('<')
  # return xml met aangepaste datestamp
  return xml[:lpoint] + datetime.date.today().isoformat() + xml[rpoint:]

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
    for bestand in os.listdir(os.path.dirname(log_file)):
      # lees alle bestanden die beginnen met de naam van de log file een eindigen op .gz
      if bestand.startswith(os.path.basename(log_file)) and bestand.endswith('.gz'): 
        # voeg de volg nummer toe aan de nummers list
        nummers.append(int(bestand[len(os.path.basename(log_file))+1:-len('.gz')]))
    # bepaal de naam van de zip file (log_file. + nummer + .gz
    gz_file = '%s.%s.gz' %(log_file, max(nummers)+1)
    # open de log file en de zip file
    with open(log_file, 'rb') as log_in, gzip.open(gz_file, 'wb') as log_out_file:
      # vul de zip file met de data uit de log file
      shutil.copyfileobj(log_in, log_out_file)
    # maak een lege log file
    open(log_file, 'w').close() 
  return

# ----- METADATA_VALIDATIE ---------------------------------------------

def metadata_validatie(metadata_xml):
  """
  Validatie van de metadata bij Geonovum
  """
  # als de metadata file niet bestaat geef dan een foutmelding
  if not os.path.isfile(metadata_xml[0]):
    logging.info('Metadata bestand: %s bestaat niet' %(os.path.basename(metadata_xml[0])))
    return
  # lees de metadata xml uit
  with open(metadata_xml[0], 'r') as bestand: xml = bestand.read().strip()
  # loop door de versie nummers in omgekeerde volgorde
  for item in sorted(metadata_xml[1].keys(), reverse=True): 
    # als beide voorwaarden uit de validaties codes voorkomen in de xml wordt versie het item en verlaat de lus
    if metadata_xml[1][item][0] in xml and metadata_xml[1][item][1] in xml:
      versie = item
      break
  # als versie niet voorkomt in de locale variabelen heeft de xml geen actueel ISO profiel
  if 'versie' not in locals():
    logging.info('Metadata bestand: %s heeft geen actueel ISO profiel' %(os.path.basename(metadata_xml[0])))
    return
  # random variabele
  rand_var = uuid.uuid4()
  # dictionarie voor de headers
  headers = {'Host': 'validatie-dataspecificaties.geostandaarden.nl',
             'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:44.0) Gecko/20100101 Firefox/44.0',
             'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
             'Accept-Language': 'en-US,en;q=0.5',
             'Accept-Encoding': 'gzip, deflate',
             'Referer': 'http://validatie-dataspecificaties.geostandaarden.nl/genericvalidator/content/standard/%s' %(versie),
             'Connection': 'keep-alive',
             'Content-Type': 'multipart/form-data; boundary=%s' %(rand_var)}
  # stel de data samen
  data = str('--%s\r\nContent-Disposition: form-data; name="standardId"\r\n\r\n%s\r\n') %(rand_var, versie)
  data += str('--%s\r\nContent-Disposition: form-data; name="file"; filename="%s"\r\n') %(rand_var, metadata_xml[0])
  data += str('Content-Type: text/xml\r\n\r\n') 
  data += xml
  data += str('\r\n--%s--\r\n') %(rand_var)
  # geef de validatie URL
  URL = 'http://validatie-dataspecificaties.geostandaarden.nl/genericvalidator/content/validateFile'
  try:
    # post request
    response = requests.post(URL, headers=headers, data=data)
  # als de request niet goed wordt afgehandeld geef dan een foutmelding
  except Exception, foutmelding:
    logging.info('Metadata bestand: %s geeft een %s foutmelding' %(os.path.basename(metadata_xml[0]), foutmelding))
    return
  else:
    # kijk of de status code oké is
    if response.status_code == requests.codes.ok: 
      # maak een paar lege dictionaries/lists
      samenvatting = {} 
      details = []
      # maak een beautifulsoup object
      soup = BeautifulSoup(response.content, 'html.parser')
      # lees de verschillende tabellen uit
      tables = soup.find_all('table')
      # lees uit de tweede tabel de regels
      rows = tables[1].find_all('tr')
      # loop door alle regels
      for row in rows:
        # lees alle th en td cellen uit
        cols = row.find_all(['th', 'td'])
        # verwijder overbodige info
        cols = [col.text.strip() for col in cols]
        # voeg de kolommen toe aan de samenvatting
        samenvatting[cols[0]] = cols[1:] 
      # lees uit de derde tabel de regels
      rows = tables[2].find_all('tr')
      # loop door alle regels
      for row in rows:
        temp_list = []
        # lees alle th en td cellen uit
        cols = row.find_all(['th', 'td'])
        # verwijder overbodige info
        cols = [col.text.strip() for col in cols]
        # loop door de kolommen en voeg ze toe aan de temp_list
        for col in cols: temp_list.append(col)
        # voeg de temp_list toe aan de details list
        details.append(temp_list)      
      return (samenvatting, details)
    # als de status code niet oké is geef dan de html foutmelding
    else: 
      logging.info('Metadata bestand: %s geeft HTML foutmelding "%s"' %(os.path.basename(metadata_xml[0]), response.status_code))
      return           

# ----- VERWERKING_RESULTS ---------------------------------------------

def verwerking_results(results):
  """
  Verwerk de resultaten van de validatie
  """
  # maal lege list/dictionarie
  xml_oke = []
  xml_error = {}
  # verwerk de resultaten
  for result in results:
    # kijk of result een tuple is
    if type(result) is tuple: 
      # maak een tijdelijke list
      temp_error = []
      # als eerste result, totaal bevat en daarvan de eerste van de lijst succesvol afgeeft
      # voeg dan de bestandsnaam toe aan xml oké 
      if result[0]['Totaal'][0] == 'Succesvol': xml_oke.append(result[0]['Bestand'][0])
      # anders loop door de tweede result en kijk of er fouten in zitten
      else:
        for item in [items for items in result[1] if len(items) > 1 and items[1] == 'Fout']:
          # voeg de foutmelding toe aan de tijdelijke list
          temp_error.append(item[2])
        # voeg de verzamelde list toe aan de xml error dictionarie
        xml_error[result[0]['Bestand'][0]] = temp_error
  # geef xml_oke list en xml_error dictionarie terug
  return xml_oke, xml_error
  
# ----- EINDE PROGRAMMA ------------------------------------------------
