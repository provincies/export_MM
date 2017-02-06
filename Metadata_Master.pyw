#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# ----- GEBRUIKTE SOFTWARE ---------------------------------------------
#
# python-2.7         http://www.python.org
# wxPython           http://www.wxpython.org/
#
# ----- MET DANK AAN ---------------------------------------------------
#
# http://xoomer.virgilio.it/infinity77/wxPython/APIMain.html
# http://www.zetcode.com
# http://svn.wxwidgets.org/viewvc/wx/wxPython/trunk/demo/Grid_MegaExample.py?view=markup
# http://www.blog.pythonlibrary.org/2010/07/10/the-dialogs-of-wxpython-part-2-of-2/
#
# ----- DICTIONARIE, LIST ----------------------------------------------
#
# self.XML_bestanden = [[bestandsnaam zonder pad en extensie, metadata titel],
#                       [bestandsnaam zonder pad en extensie, metadata titel]]
#
# self.XML_data = {bestandsnaam zonder pad en extensie : {single of multi tag : [list met uitgelezen tag data], 
#                                                         single of multi tag : [list met uitgelezen tag data]},
#                  bestandsnaam zonder pad en extensie : {single of multi tag : [list met uitgelezen tag data],
#                                                         single of multi tag : [list met uitgelezen tag data], 
#                                                         single of multi tag : [list met uitgelezen tag data]}}
# 
# ----- GLOBALE VARIABELEN ---------------------------------------------

__doc__      = "Programma om iso xml's te beheren"
__rights__   = 'provincie Noord-Brabant'
__author__   = 'Jan van Sambeek'
__date__     = ['03-2016', '01-2017']
__version__  = '1.0.3'

# ----- IMPORT LIBRARIES -----------------------------------------------

import wx, wx.grid, sys, os, datetime, time, re, logging, multiprocessing, codecs, psutil, getpass
from Metadata_Master_lib import *
from xml.dom import minidom

# ----- FILTER DIALOG --------------------------------------------------

class FilterDialog(wx.Dialog):
  """
  Hierin wordt het menu filter gemaakt.
  """
  def __init__(self, parent, id, title, titel, resume):
    wx.Dialog.__init__(self, parent, id, title, size=(270, 220))
    # bij microsoft gebruik een andere onder afstand voor de buttons
    if sys.platform == 'win32': button_dist = 60
    else: button_dist = 50
    # plaats tekst in het dialoog venster
    wx.StaticText(self, -1, 'filter voor de Titel: ', pos=(15, 20))
    # maak een tekst control venster    
    self.titel = wx.TextCtrl(self, 113, pos=(10,40), size=(245, -1), value=titel)
    # plaats tekst in het dialoog venster
    wx.StaticText(self, -1, 'of ', pos=(15, 70))
    # plaats tekst in het dialoog venster
    wx.StaticText(self, -1, 'filter voor de Samenvatting: ', pos=(15, 100))
    # lees de window grote uit
    scherm_breedte, scherm_hoogte = self.GetSize()
    # maak een tekst control venster    
    self.resume = wx.TextCtrl(self, 113, pos=(10,120), size=(245, -1))
    # zet 2 buttons met de focus op oke
    self.btn_cc = wx.Button(self, 120, 'Cancel', pos=(25, scherm_hoogte-button_dist))
    self.btn_ok = wx.Button(self, 121, 'Ok', pos=(160, scherm_hoogte-button_dist))
    self.btn_ok.SetFocus()
    self.btn_ok.SetDefault()
    # laat het venster zien    
    self.Center()
    self.Show(True)
    # vang de events af
    wx.EVT_BUTTON(self, 120, self.OnCancel)
    wx.EVT_BUTTON(self, 121, self.OnOK)

# -----

  def OnCancel(self, event):
    """   """
    self.titel = ''
    self.resume = ''
    self.Close()
    return

# -----
        
  def OnOK(self, event):
    """   """
    self.titel = unicode(self.titel.GetValue())
    self.resume = unicode(self.resume.GetValue())
    self.Close()
    return 

# ----- REPARE DIALOG --------------------------------------------------

class RepareDialog(wx.Dialog):
  """
  Hierin wordt de repareer dialoog gemaakt.
  """
  def __init__(self, parent, id, title, text_old):
    # bij microsoft gebruik een andere onder afstand voor de buttons
    if sys.platform == 'win32': button_dist = 60
    else: button_dist = 50
    # lees de schermresolutie uit
    max_breedte, max_hoogte = wx.GetDisplaySize()
    # bereken de breedte voor het dialoog scherm
    dialog_breedte = len(text_old[1])*10
    # als het dialoog scherm te groot of te klein wordt pas het dan aan
    if dialog_breedte >= 0.75*max_breedte: dialog_breedte = 0.75*max_breedte
    if dialog_breedte <= 270: dialog_breedte = 270
    # geef de init voor de parent
    wx.Dialog.__init__(self, parent, id, title, size=(dialog_breedte, 220))
    # lees de window grote uit
    scherm_breedte, scherm_hoogte = self.GetSize()    
    # plaats tekst in het dialoog venster
    wx.StaticText(self, -1, 'Bestaande gegevens (%d maal):' %(text_old[0]), pos=(15, 20))
    wx.StaticText(self, -1, '%s' %(text_old[1]), pos=(15, 40))
    # plaats tekst in het dialoog venster
    wx.StaticText(self, -1, 'wijzigen in:', pos=(15, 70))
    # plaats tekst in het dialoog venster
    wx.StaticText(self, -1, 'Nieuwe gegevens: ', pos=(15, 100))
    # maak een tekst control venster    
    self.text_new = wx.TextCtrl(self, 113, pos=(10,120), size=(dialog_breedte-30, -1))
    # zet 2 buttons met de focus op oke
    self.btn_cc = wx.Button(self, 120, 'Cancel', pos=(25, scherm_hoogte-button_dist))
    self.btn_ok = wx.Button(self, 121, 'Ok', pos=(dialog_breedte-121, scherm_hoogte-button_dist))
    self.btn_ok.SetFocus()
    self.btn_ok.SetDefault()
    # laat het venster zien    
    self.Center()
    self.Show(True)
    # vang de events af
    wx.EVT_BUTTON(self, 120, self.OnCancel)
    wx.EVT_BUTTON(self, 121, self.OnOK)

# -----

  def OnCancel(self, event):
    """   """
    self.text_new = False
    self.Close()
    return

# -----
        
  def OnOK(self, event):
    """   """
    self.text_new = unicode(self.text_new.GetValue())   
    self.Close()
    return 
    
# ----- ListCtrlDialog ------------------------------------------------

class ListCtrlDialog(wx.Dialog):
  """
  Dialoog box voor het maken van een filter
  """
  def __init__(self, parent, id, title, header, lijst):
    wx.Dialog.__init__(self, parent, id, title)
    # bij microsoft gebruik een andere onder afstand voor de buttons
    if sys.platform == 'win32': button_dist = 60
    else: button_dist = 50    
    # zet de response voorlopig op False
    self.response = False
    # zet de sorteer richting op False
    self.sorteer_richting = True
    # maak selfs
    self.header = header
    self.lijst = lijst
    # bepaal de breedte van de randen
    rand = 30
    # begin breedte van het window
    breedte = 2*rand
    # bepaal de kolom breedtes
    for num in range(len(self.header)): breedte += self.header[num][1]+2
    # zet de hoogte
    hoogte = 400
    # zet de grote van het scherm
    self.SetSize((breedte, hoogte))
    # maak een list control
    self.listctrl = wx.ListCtrl(self, -1, pos=(rand, rand), style=wx.LC_REPORT|wx.BORDER_SUNKEN|wx.LC_SINGLE_SEL, size=(breedte-2*rand, hoogte-100))
    # zet de kolom headers
    for col_num in range(len(self.header)): self.listctrl.InsertColumn(col_num, self.header[col_num][0], width=self.header[col_num][1])                         
    # vul de data
    self.vul_data()
    # zet 2 buttons met de focus op oke
    self.btn_cc = wx.Button(self, 123, 'Cancel', pos = (rand+15, hoogte-button_dist))
    self.btn_ok = wx.Button(self, 124, 'Ok', pos = (breedte-rand-100, hoogte-button_dist))
    self.btn_ok.SetFocus()
    self.btn_ok.SetDefault()
    # laat het venster zien    
    self.Center()
    self.Show(True)
    # vang de events af
    # double click
    self.listctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnOK)
    # left click op label
    self.listctrl.Bind(wx.EVT_LIST_COL_CLICK, self.onLabelClick)
    # click op de buttons
    wx.EVT_BUTTON(self, 123, self.OnCancel)
    wx.EVT_BUTTON(self, 124, self.OnOK)

# -----

  def onLabelClick(self, event):
    """ sorteer de data op aangeklikte kolom """
    # sorteer de lijst op de geselecteerde kolom
    self.lijst = sorted(self.lijst, key=lambda item: item[event.GetColumn()], reverse = self.sorteer_richting)
    # verander de sorteer richting
    if self.sorteer_richting == True : self.sorteer_richting = False
    else: self.sorteer_richting = True
    # vul de gesorteerde data
    self.vul_data()
    return

# -----

  def OnCancel(self, event):
    """ Druk cancel event  """
    # geef een False terug
    self.response = False
    self.Close()
    return

# -----
        
  def OnOK(self, event):
    """ Druk oke event  """
    # als er niet geselecteerd is
    if self.listctrl.GetFirstSelected() == -1: self.response = False
    # geef anders het item terug
    else: self.response = self.lijst[self.listctrl.GetFirstSelected()]
    self.Close()
    return

# -----

  def vul_data(self):
    """ Vul de self.lijst met data  """
    # verwijder de huidige items
    self.listctrl.DeleteAllItems()
    # plaats de data in de control list
    for row_num in range(len(self.lijst)): 
      # bepaal een index voor de insert string
      index = self.listctrl.InsertStringItem(sys.maxint, str(self.lijst[row_num][0]))
      # als de laatste kolom begint met #, zet de achtergrond kleur met de laatste kolom
      if self.lijst[row_num][-1].startswith('#'): self.listctrl.SetItemBackgroundColour(row_num, self.lijst[row_num][-1])
      # zet anders de kleuren om en om
      elif (row_num % 2) == 0: self.listctrl.SetItemBackgroundColour(row_num, '#F1DBDB')
      else: self.listctrl.SetItemBackgroundColour(row_num, '#F8ECEC')
      # vul de kolommen met de gegevens uit de lijst
      for col_num in range(len(self.header)): self.listctrl.SetStringItem(index, col_num, unicode(self.lijst[row_num][col_num]))   
    # refresh de window
    self.Refresh()
        
# ----- MAINWINDOW FRAME -----------------------------------------------

class MainWindow(wx.Frame):
  """
  """
  def __init__(self, parent, id):
    """
    """    
    wx.Frame.__init__(self, parent, id)
    # bepaal de begin tijd
    start_tijd = time.time()
    # bepaal de pid naam
    if sys.platform == 'linux2': pid_name = 'python'
    elif sys.platform == 'win32': pid_name = 'Metadata_Master.exe'
    # loop door alle proces ids
    for pid_dict in [pid.as_dict(attrs=['name', 'username']) for pid in psutil.process_iter()]:
      # kijk of python al geopend is door een andere gebruiker
      if pid_dict['name'] == pid_name and str(pid_dict['username']).split('\\')[-1] != getpass.getuser():
        # als er een username is
        if pid_dict['username']:
          # open een message dialog
          MsgBox = wx.MessageDialog(None, 'Metadata Master is al in gebruik door: %s' %(str(pid_dict['username']).split('\\')[-1]), 'METADATA MASTER', wx.OK|wx.ICON_INFORMATION)
        else:
          # open een message dialog
          MsgBox = wx.MessageDialog(None, 'Metadata Master is al in gebruik', 'METADATA MASTER', wx.OK|wx.ICON_INFORMATION)
        # als in de message dialog op ok wordt gedrukt, stop dan het programma
        if MsgBox.ShowModal() == wx.ID_OK: sys.exit('Metadata Master is al in gebruik')
    # bepaal de start directorie 
    self.start_dir, self.bestand  = os.path.split(os.path.abspath(__file__))
    # maak een object van de configuratie data
    if os.path.isfile(self.start_dir+os.sep+os.path.splitext(self.bestand)[0]+'.cfg'): 
      self.cfg = Config(self.start_dir+os.sep+os.path.splitext(self.bestand)[0]+'.cfg')
    # verlaat anders het programma
    else: sys.exit('het configuratie bestand is niet gevonden')
    # als het configuratie bestand niet goed is verlaat het programma
    if self.cfg.get_dict() == None: sys.exit('er is iets niet goed met het configuratie bestand')
    # lees verschillende directories uit
    self.log_dir = self.cfg.get('dirs')['log_dir']
    self.csv_dir = self.cfg.get('dirs')['csv_dir']
    # maak een log bestand
    self.log_file = self.log_dir+os.sep+os.path.splitext(os.path.split(__file__)[-1])[0]+'.log'
    # maak een basis configuratie voor het loggen
    logging.basicConfig(filemode='a', format='%(asctime)s - %(levelname)-8s "%(message)s"', 
                        datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO, filename=self.log_file)
    # het programma is gestart
    logging.info('-'*50)
    logging.info('%s is opgestart' %(__file__)) 
    # bepaal de standaard xml directorie 
    self.XML_dir = self.cfg.get('dirs')['xml_dir']
    # lees de ISO profielen 
    self.ISO_profielen = self.cfg.get('ISO_profielen')
    # bepaal of oplopend of aflopend gesorteerd moet worden
    self.sorteer_richting = True
    # scheidingsteken
    self.sep = ';'    
    # zet de gebruikte fonts
    self.font = wx.Font(8, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
    # zet de window styles
    self.SetWindowStyle(style=wx.DEFAULT_FRAME_STYLE|wx.NO_FULL_REPAINT_ON_RESIZE)
    scherm_breedte, scherm_hoogte = wx.GetDisplaySize()
    # geef de grote van het window
    self.SetSize((1000, scherm_hoogte-50))
    # geef de titel van het hoofd window
    self.SetTitle('%10s' %(self.XML_dir))
    # bepaal de minimum grootte van het window
    self.SetMinSize((1000, 500))
    self.SetMaxSize((1000, scherm_hoogte))
    # als er een logo is plaats dit dan 
    logo = '%s%s%s.png' %(self.start_dir, os.sep, os.path.splitext(self.bestand)[0])
    if os.path.isfile(logo): self.SetIcon(wx.Icon(logo, wx.BITMAP_TYPE_PNG))
    # maak de bestandmenu
    bestandmenu = wx.Menu()
    self.MenuItem_xml_dir = bestandmenu.Append(101, 'Open XML-Map', 'Lees XML bestanden uit een locale map')
    self.MenuItem_xml_dir.Enable(True)
    self.MenuItem_stand_xml_dir = bestandmenu.Append(102, 'Standaard XML-Map', 'Lees XML bestanden uit de standaard map')
    self.MenuItem_stand_xml_dir.Enable(False)
    bestandmenu.Append(103, 'Export Bestandenlijst', 'Exporteer een overzicht van de inhoud')
    bestandmenu.Append(104, 'Export Contactgegevens', 'Exporteer de contact gegevens')
    bestandmenu.Append(105, 'Sluiten', 'Beeindig het programma')
    # maak het selectie menu
    selectiemenu = wx.Menu()
    self.SelectieItem_validatie = selectiemenu.Append(201, 'Validatie selectie', 'Valideer de geselecteerde gegevens')
    self.SelectieItem_validatie.Enable(True)
    self.SelectieItem_export = selectiemenu.Append(202, 'Export selectie', 'Export de geselecteerde gegevens')
    self.SelectieItem_export.Enable(True)
    self.SelectieItem_verwijder = selectiemenu.Append(203, 'Verwijder selectie', 'Verwijder de geselecteerde gegevens')
    self.SelectieItem_verwijder.Enable(True)        
    # maak het filtermenu
    filtermenu = wx.Menu()
    self.FilterItem_filter = filtermenu.Append(301, 'Filter tekst', 'Beperk de Titel en de Samenvatting met een filter')
    self.FilterItem_filter.Enable(True)
    self.FilterItem_kwaliteit = filtermenu.Append(302, 'Filter PGR kwaliteit', 'Beperk de resultaten met kwaliteits criteria')
    self.FilterItem_kwaliteit.Enable(True)    
    self.FilterItem_uniek = filtermenu.Append(303, 'Filter unieke waardes', 'Beperk de resultaten met unieke waardes')
    self.FilterItem_uniek.Enable(True)
    self.FilterItem_trefwoord = filtermenu.Append(304, 'Filter trefwoorden', 'Filter op trefwoorden die niet voorkomen in de thesaurs')
    self.FilterItem_trefwoord.Enable(True)     
    self.FilterItem_selected = filtermenu.Append(305, 'Filter selectie', 'Beperk de resultaten tot de geselecteerde metadata')
    self.FilterItem_selected.Enable(True)  
    self.FilterItem_no_selected = filtermenu.Append(306, 'Verwijder filters', 'Verwijder de selectie')
    self.FilterItem_no_selected.Enable(True)    
    # maak het repareer menu
    repareermenu = wx.Menu()
    self.RepareerItem_uniek = repareermenu.Append(401, 'Repareer unieke waardes', 'Repareer de data op basis van unieke waardes')
    self.RepareerItem_uniek.Enable(False)
    self.RepareerItem_contact = repareermenu.Append(402, 'Repareer Contactgegevens', 'Repareer de contact gegevens van de bron')
    self.RepareerItem_contact.Enable(False)
    self.RepareerItem_overigebeperkingen = repareermenu.Append(410, 'Repareer publicdomain', 'Repareer overige beperkingen creative commons')
    self.RepareerItem_overigebeperkingen.Enable(False) 
    self.RepareerItem_tijdperiode = repareermenu.Append(411, 'Repareer tijd periode', 'Repareer de tijd periode')
    self.RepareerItem_tijdperiode.Enable(False)
    self.RepareerItem_thesauri = repareermenu.Append(412, 'Repareer thesauri', 'Repareer thesauri')
    self.RepareerItem_thesauri.Enable(False)
    self.RepareerItem_legeregel = repareermenu.Append(413, 'Repareer layout XML', 'Verwijder lege en dergelijke regels uit de xml')
    self.RepareerItem_legeregel.Enable(False)   
    # maak het plugin menu
    plugin = False
    # kijk of er een plugins directorie is met daarin .py of .pyw bestanden
    if os.path.isdir(self.start_dir+os.sep+'plugins'):
      for bestand in os.listdir(self.start_dir+os.sep+'plugins'):
        if os.path.splitext(bestand)[-1] == '.py' or os.path.splitext(bestand)[-1] == '.pyw': plugin = True
    if plugin: pluginmenu = wx.Menu()
    #~ self.InstellingenItem_voorkeur = instellingenmenu.Append(501, 'Pas instellingen aan', 'Pas de instellingen aan')
    #~ self.InstellingenItem_voorkeur.Enable(False)    
    # maak het helpmenu
    helpmenu = wx.Menu()
    self.RapportItem_help = helpmenu.Append(601, 'Help', 'Applicatie beschrijving') 
    self.RapportItem_help.Enable(True)
    self.RapportItem_over = helpmenu.Append(602, 'Over', 'Over %s' %(self.bestand))
    self.RapportItem_over.Enable(True)
    # maak menubar
    menubar = wx.MenuBar()
    menubar.Append(bestandmenu, 'Bestand')
    menubar.Append(selectiemenu, 'Selectie')
    menubar.Append(filtermenu, 'Filters')
    menubar.Append(repareermenu, 'Repareer')
    if plugin: menubar.Append(pluginmenu, 'Plugins')
    menubar.Append(helpmenu, 'Help')
    # plaats de menu's
    self.SetMenuBar(menubar)    
    # creeer een status bar
    self.CreateStatusBar()
    # start een boxer verticaal
    box = wx.BoxSizer(wx.VERTICAL)  
    box.Add((1,1),0)
    self.SetSizer(box)  
    # maak een grid paneel
    self.sheet = wx.grid.Grid(self)
    # maak een grid met het aantal records en 1 kolom
    self.sheet.CreateGrid(100, 2)
    # alleen rijen kunnen geselecteerd worden
    self.sheet.SetSelectionMode(wx.grid.Grid.SelectRows)    
    # er kan niet geedit worden
    self.sheet.EnableEditing(False)
    # vul de header van de kolommen
    self.sheet.SetColLabelValue(0, 'Bestand')
    self.sheet.SetColLabelValue(1, 'Titel')
    # zet de hoogte en breedte van verschillende cellen
    self.sheet.SetDefaultRowSize(25, False)  
    self.sheet.SetColSize(0, 300)
    self.sheet.SetColSize(1, 600)  
    # alignment van de kolommen
    align1 = wx.grid.GridCellAttr()
    align1.SetAlignment(wx.ALIGN_LEFT, wx.ALIGN_BOTTOM)
    self.sheet.SetColAttr(0, align1)
    self.sheet.SetColAttr(1, align1)
    # vul het grid met data uit de xml directorie
    self.verwerk_XML_dir()  
    # voeg sheet toe aan de box
    box.Add(self.sheet, 1, wx.EXPAND)
    # afhandeling control (ctrl) met een letter
    self.SetAcceleratorTable(wx.AcceleratorTable([(wx.ACCEL_CTRL,  ord('a'), 901)]))    
    # zet alles op het scherm    
    self.Center(direction=wx.HORIZONTAL)
    self.Show(True)
    # werk de events af
    wx.EVT_MENU(self, 101, self.menuOpenDir)
    wx.EVT_MENU(self, 102, self.menuOpenStandDir)
    wx.EVT_MENU(self, 103, self.menuOverzicht)
    wx.EVT_MENU(self, 104, self.menuContactGegevens)
    wx.EVT_MENU(self, 105, self.menuExit)
    wx.EVT_MENU(self, 201, self.menuGeonovumVal)
    wx.EVT_MENU(self, 202, self.menuExportMetadata)
    wx.EVT_MENU(self, 203, self.menuVerwijderMetadata)
    wx.EVT_MENU(self, 301, self.menuFilterTekst)
    wx.EVT_MENU(self, 302, self.menuFilterKwaliteit)
    wx.EVT_MENU(self, 303, self.menuFilterUniek) 
    wx.EVT_MENU(self, 304, self.menuFilterTrefWoord) 
    wx.EVT_MENU(self, 305, self.menuFilterSelectie) 
    wx.EVT_MENU(self, 306, self.menuFilterOff)
    wx.EVT_MENU(self, 401, self.menuRepareerUniek)
    wx.EVT_MENU(self, 402, self.menuRepareerContact)
    wx.EVT_MENU(self, 410, self.menuRepareerPublicDomain)
    wx.EVT_MENU(self, 411, self.menuRepareerTijdPeriode)
    wx.EVT_MENU(self, 412, self.menuRepareerThesauri)
    wx.EVT_MENU(self, 413, self.menuRepareerLegeRegels)    
    wx.EVT_MENU(self, 601, self.onHelp)
    wx.EVT_MENU(self, 602, self.menuOver)
    # selecteer alles bij control A
    wx.EVT_MENU(self, 901, self.onCtrlA)
    # vang een linker klik op het labelvan de grid af
    self.sheet.Bind(wx.grid.EVT_GRID_CMD_LABEL_LEFT_CLICK, self.onLabelClick)
    # vang een linker dubbel muis klik af
    self.sheet.Bind(wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.onLeftDClick)    
    # vang een rechter muis klik af
    self.sheet.Bind(wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.onRightClick) 

# -----

  def menuOpenDir(self, event):
    """ Open een directorie met XML bestanden """
    # start de directorie dialoog op  
    fileDialoog = wx.DirDialog(self, message='Selecteer directorie', defaultPath=os.path.expanduser('~'))
    # als een directorie is aangeklikt geef dan oke
    if fileDialoog.ShowModal() == wx.ID_OK:
      # verander menu item
      self.MenuItem_stand_xml_dir.Enable(True)
      self.RepareerItem_uniek.Enable(True)
      self.RepareerItem_contact.Enable(True)
      self.RepareerItem_overigebeperkingen.Enable(True)
      self.RepareerItem_tijdperiode.Enable(True)
      self.RepareerItem_thesauri.Enable(True)
      self.RepareerItem_legeregel.Enable(True)            
      # bepaal de directorie met XML bestanden
      self.XML_dir = fileDialoog.GetPath()
      # verwerk de aangeklikte directorie
      self.verwerk_XML_dir()
    return
    
# -----

  def menuOpenStandDir(self, event):
    """ Open de standaard directorie met XML bestanden """
    # verander menu item
    self.MenuItem_stand_xml_dir.Enable(False)
    self.RepareerItem_uniek.Enable(False)
    self.RepareerItem_contact.Enable(False)
    self.RepareerItem_overigebeperkingen.Enable(False)
    self.RepareerItem_tijdperiode.Enable(False)
    self.RepareerItem_thesauri.Enable(False)
    self.RepareerItem_legeregel.Enable(False)
    # bepaal de directorie met XML bestanden
    self.XML_dir = self.cfg.get('dirs')['xml_dir']
    # verwerk de aangeklikte directorie
    self.verwerk_XML_dir()    

# -----

  def menuOverzicht(self, event):
    """ Maak een overzicht van de inhoud """
    # zet self.XML_bestand om naar tekst
    tekst = u'Bestandsnaam'+self.sep+u'Titel'+self.sep+u'Alter Titel\n\n'
    for regel in self.XML_bestanden: 
      tekst += regel[0].decode('utf-8')+self.sep
      if regel[1]: tekst += regel[1].decode('utf-8')+self.sep
      else: tekst += self.sep
      if self.XML_data[regel[0]]['bron titel alter'][0]: tekst += self.XML_data[regel[0]]['bron titel alter'][0].decode('utf-8')
      tekst += '\n'
    # start de File dialoog op
    csvDialoog = wx.FileDialog(self, 'Sla het csv bestand op', self.csv_dir, 'Metadata_Master_Overzicht.csv', '(*.csv; *.CSV)|*.csv; *.CSV', wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
    # lees de reactie uit
    if csvDialoog.ShowModal() == wx.ID_OK:
      # leg de huidige directorie vast
      self.csv_dir = csvDialoog.GetDirectory()
      # lees de bestandsnaam
      bestandsnaam = csvDialoog.GetFilename()
      # voeg als nodig '.csv' toe
      if bestandsnaam[-4:].lower() != '.csv': bestandsnaam += '.csv'
      # schrijf alles weg
      with open(self.csv_dir+os.sep+bestandsnaam, 'w') as outfile: outfile.write(tekst.encode('utf-8'))
    return

# -----

  def menuContactGegevens(self,event): 
    """ Genereer een cvs bestand met alle contact gegevens """
    # lees de contact gegevens uit en sorteer ze
    contact_tags = self.cfg.get('contact_gegevens')
    # maak een gesorteerde list van de keys
    contact_keys = sorted(contact_tags.keys())
    contact_list0 = contact_tags[contact_keys[0]].strip('/').split('/')
    # bepaal de eerste regel van het bestand
    tekst = ''
    for  item in contact_keys: tekst += '%s%s ' %(item[3:], self.sep)
    # plaats einde regel
    tekst += '\n\n'
    # start de File dialoog op
    csvDialoog = wx.FileDialog(self, 'Sla het csv bestand op', self.csv_dir, 'Metadata_Master_Contacten.csv', \
                               '(*.csv; *.CSV)|*.csv; *.CSV', wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
    # lees de reactie uit
    if csvDialoog.ShowModal() == wx.ID_OK:
      # leg de huidige directorie vast
      self.csv_dir = csvDialoog.GetDirectory()
      # lees de bestandsnaam
      bestandsnaam = csvDialoog.GetFilename()
      # voeg als nodig '.csv' toe
      if bestandsnaam[-4:].lower() != '.csv': bestandsnaam += '.csv'
      # maak een lege teller
      teller = 0
      # lees het aantal xml's
      aantal_xmls = len(self.XML_bestanden)
      # geef het minimale aantal xmls om een voortgangs scerm te laten zien
      min_xmls = 50
      # bouw het voortgangs scherm
      if aantal_xmls > min_xmls: VoortgangsScherm = wx.ProgressDialog("VERWERKEN XML's", 'Even geduld A.U.B.', maximum=len(self.XML_bestanden), parent=self)
      # loop door alle bestanden
      for XML in [self.XML_dir+os.sep+XML_bestand[0]+'.xml' for XML_bestand in self.XML_bestanden]:
        # parse de bestanden
        xmlObject = minidom.parse(XML)
        # als er geen name space is ingevuld verwijder die dan uit de email list
        if xmlObject.getElementsByTagName(contact_list0[0]) == []: contact_list0[0] = contact_list0[0].split(':')[-1]
        # zoek naar de eerste tag en loop en maak er een xml object van
        for xml_element in xmlObject.getElementsByTagName(contact_list0[0]):
          # lees alle contact gegevens uit
          contact_geg = contact_gegevens(xml_element, contact_tags)
          # loop door de gesorterde keys
          for sleutel in sorted(contact_geg.keys()): 
            # als een tag begint met ' sla ' dan over
            if contact_geg[sleutel].startswith('\''): contact_geg[sleutel] = contact_geg[sleutel][1:]
            # verzamel de teksten
            tekst += '%s' %(contact_geg[sleutel].decode('utf-8'))
            tekst += '%s ' %(self.sep)
          # sluit de regel af
          tekst += '\n'
        # verhoog de teller
        teller += 1
        # update het voortgangs scherm
        if aantal_xmls > min_xmls: VoortgangsScherm.Update(teller)
      # verwijder het voortgangs scherm
      if aantal_xmls > min_xmls: VoortgangsScherm.Destroy()
      # schrijf alles weg
      with open(self.csv_dir+os.sep+bestandsnaam, 'w') as outfile: outfile.write(tekst.encode('utf-8'))
    return

# -----

  def menuExit(self, event):
    """ sluit het frame, dus het programma """
    # beperk de omvang van de log file
    gzip_log_file(self.log_file) 
    # sluit het programma  
    self.Close(True) 

# -----

  def menuGeonovumVal(self, event):
    """ Valideer geselecteerde data """
    # als er geen records zijn geselecteerd
    if len(self.GetSelectedRows()) == 0:
      # open een message dialog
      MsgBox = wx.MessageDialog(None, 'Er zijn geen records geselecteerd.', 'SELECTIE MELDING', wx.OK|wx.ICON_INFORMATION)
      # als in de message dialog op ok wordt gedrukt, doe dan niets
      if MsgBox.ShowModal() == wx.ID_OK: pass
    # valideer de gegevens
    else: self.GeonovumVal()
    return

# -----

  def menuExportMetadata(self, event):
    """ Exporteer geselecteerde data """
    # als er geen records zijn geselecteerd
    if len(self.GetSelectedRows()) == 0:
      # open een message dialog
      MsgBox = wx.MessageDialog(None, 'Er zijn geen records geselecteerd.', 'SELECTIE MELDING', wx.OK|wx.ICON_INFORMATION)
      # als in de message dialog op ok wordt gedrukt, doe dan niets
      if MsgBox.ShowModal() == wx.ID_OK: pass
    # exporteer de gegevens
    else: self.ExportMetadata()
    return
    
# -----

  def  menuVerwijderMetadata(self, event):
    """ Verwijder geselecteerde data """
    # als er geen records zijn geselecteerd
    if len(self.GetSelectedRows()) == 0:
      # open een message dialog
      MsgBox = wx.MessageDialog(None, 'Er zijn geen records geselecteerd.', 'SELECTIE MELDING', wx.OK|wx.ICON_INFORMATION)
      # als in de message dialog op ok wordt gedrukt, doe dan niets
      if MsgBox.ShowModal() == wx.ID_OK: pass
    # verwijder de gegevens
    else: self.VerwijderMetadata()
    return

# -----

  def menuFilterTekst(self, event):
    """ plaats een filter """
    # zet de variabelen voor de menu filter leeg
    self.ortitel = self.orresume = ''
    # maak een object voor het filteren
    orfilter_obj = FilterDialog(None, -1, title='FILTER TEKST', titel=self.ortitel, resume=self.orresume)
    orfilter_obj.ShowModal()
    # lees de verschillende waardes uit het object
    # geef een lege string als het venster wordt weggeklikt
    if type(orfilter_obj.titel) is unicode: self.ortitel = orfilter_obj.titel
    else: self.ortitel = ''
    if type(orfilter_obj.resume) is unicode: self.orresume = orfilter_obj.resume
    else: self.resume = ''
    # verwijder het object
    orfilter_obj.Destroy()
    # maak een lege list
    XML_rows = []
    # loop door de huidige XML bestanden
    for XML_row in [regel[0] for regel in self.XML_bestanden]:
      # voeg de titel toe
      titel = self.XML_data[XML_row]['bron titel'][0]
      # verwijder de \n
      if titel: titel = titel.rstrip()
      # log als er geen titel is
      else: logging.info('%s heeft geen titel' %(XML_row))
      # voeg de samenvatting toe en de lengte van de samenvatting
      samenvatting = self.XML_data[XML_row]['samenvatting'][0]
      # verwijder de \n
      if samenvatting: samenvatting = samenvatting.rstrip()
      # log als er geen samenvatting is
      else: logging.info('%s heeft geen samenvatting' %(XML_row))
      # als de titel en samenvatting
      if titel and samenvatting: 
        # Filter de resultaten en voeg een True toe aan XML_rows
        if self.VoegtoeFilter(titel, samenvatting): XML_rows.append(XML_row)
    # stel de nieuwe XML bestanden vast
    self.XML_bestanden = sorted([[result, self.XML_data[result]['bron titel'][0]] for result in XML_rows])
    # vul de data met de XML bestanden
    self.vul_data()
    return
 
# ----
 
  def menuFilterKwaliteit(self, event):
    """ Filter voor onvoldoende kwaliteits eisen """
    # geef de titel balk
    title = 'PGR KWALITEIT ONVOLDOENDE'
    # geef de header van de ctrl list
    header = (('Aantal', 70), ('Kwaliteits eisen', 550))
    # maak een teller voor de kwaliteit
    kwaliteit_teller = dict([(tag, [0, []]) for tag in self.cfg.get('kwaliteit').keys()])
    # geef de criteria zoals ze in het cfg bestand moeten staan
    titel_criteria = 'de titel heeft minder dan 3 of meer dan 75 letters'
    abstract_criteria = 'de samenvatting heeft minder als 25 of meer als 2000 letters'
    trefwoord_criteria = 'de xml bevat meer dan 5 trefwoorden'
    image_criteria = 'de URL van het voorbeeld plaatje begint niet met "http"'   
    thesaurus_criteria = 'heeft geen combi: datum "2010-11-05" en "interprovinciale thesaurus"'
    overige_beperkingen_criteria = 'heeft geen combi: "geen beperkingen" en creativecommons licentie'
    OGC_criteria = 'heeft geen combi: "OGC:WMS" en "OGC:WFS" en URL begint niet met "http://"'
    extend_criteria = 'buiten extend: X_min = 3, Y_min = 50, X_max = 8, Y_max = 54'
    # loop door de huidige XML bestanden
    for XML_row in [regel[0] for regel in self.XML_bestanden]:
      # als een limiet wordt overschreden verhoog dan de bijbehorende teller
      # als de titel korter of langer is als max_titel
      titel_len = len(self.XML_data[XML_row]['bron titel'][0])
      if titel_len < self.cfg.get('kwaliteit')[titel_criteria][0] or titel_len > self.cfg.get('kwaliteit')[titel_criteria][1]: 
        kwaliteit_teller[titel_criteria][0] += 1
        kwaliteit_teller[titel_criteria][1].append(XML_row)
      # als de samenvatting korter of langer is als max_tekst
      if self.XML_data[XML_row]['samenvatting'][0]: 
        abstract_len = len(self.XML_data[XML_row]['samenvatting'][0])
        if abstract_len < self.cfg.get('kwaliteit')[abstract_criteria][0] or abstract_len > self.cfg.get('kwaliteit')[abstract_criteria][1]: 
          kwaliteit_teller[abstract_criteria][0] += 1
          kwaliteit_teller[abstract_criteria][1].append(XML_row)
      # als het aantal trefwoorden meer is als max_tref
      if len(self.XML_data[XML_row]['trefwoorden']) > self.cfg.get('kwaliteit')[trefwoord_criteria][0]: 
        kwaliteit_teller[trefwoord_criteria][0] += 1
        kwaliteit_teller[trefwoord_criteria][1].append(XML_row)
      # als het image niet is ingevuld
      if not self.XML_data[XML_row]['image'][0]:
        kwaliteit_teller[image_criteria][0] += 1
        kwaliteit_teller[image_criteria][1].append(XML_row)
      # als het begin van de link naar het image niet gelijk is aan limiet voorbeeld               
      elif not self.XML_data[XML_row]['image'][0].startswith(self.cfg.get('kwaliteit')[image_criteria][0]): 
        kwaliteit_teller[image_criteria][0] += 1
        kwaliteit_teller[image_criteria][1].append(XML_row)
      # als de thesaurus datum niet voorkomt en de thesaurus naam komt niet voor
      # zet eerst alles naar kleine letters
      thesaurussen = [thesaurus.lower() for thesaurus in self.XML_data[XML_row]['thesaurus']]
      # controle thesaurus
      if self.cfg.get('kwaliteit')[thesaurus_criteria][0] not in self.XML_data[XML_row]['thesaurus datum'] or \
      self.cfg.get('kwaliteit')[thesaurus_criteria][1] not in thesaurussen:
        kwaliteit_teller[thesaurus_criteria][0] += 1
        kwaliteit_teller[thesaurus_criteria][1].append(XML_row)
      # overige beperkingen
      # zet eerst om naar kleine letters
      overige_beperkingen = [overige_beperking.lower() for overige_beperking in self.XML_data[XML_row]['overige beperkingen']]
      # controle overige beperkingen
      if self.cfg.get('kwaliteit')[overige_beperkingen_criteria][0] not in overige_beperkingen or \
      self.cfg.get('kwaliteit')[overige_beperkingen_criteria][1] not in overige_beperkingen:
        kwaliteit_teller[overige_beperkingen_criteria][0] += 1
        kwaliteit_teller[overige_beperkingen_criteria][1].append(XML_row) 
      # WMS-WFS
      wms_wfs = False
      # Als OGC:WFS of OGC:WMS niet voorkomen
      if self.cfg.get('kwaliteit')[OGC_criteria][0] not in self.XML_data[XML_row]['OGC-service']: wms_wfs = True
      if self.cfg.get('kwaliteit')[OGC_criteria][1] not in self.XML_data[XML_row]['OGC-service']: wms_wfs = True
      # loop door de URLs
      for url in self.XML_data[XML_row]['WMS-WFS']:
        # als de url niet met http begint
        if not url.startswith(self.cfg.get('kwaliteit')[OGC_criteria][2]): wms_wfs = True
        # als er een ? in de url zit en de url niet eindigd met een ?
        if self.cfg.get('kwaliteit')[OGC_criteria][3] in url and not url.endswith(self.cfg.get('kwaliteit')[OGC_criteria][3]): wms_wfs = True
      # als wms_wfs is omgezet naar True
      if wms_wfs:    
        kwaliteit_teller[OGC_criteria][0] += 1
        kwaliteit_teller[OGC_criteria][1].append(XML_row)  
      # min_max_extend
      XY_min_max = False
      # probeer of XY_min_max een getal is, anders klopt de extend niet
      for coord in ('X_min', 'X_min', 'X_max', 'Y_max'):
        try: float(self.XML_data[XML_row][coord][0])
        except: XY_min_max = True
      # als XY_min_max een getal is
      if not XY_min_max:
        if float(self.XML_data[XML_row]['X_min'][0]) < float(self.cfg.get('kwaliteit')[extend_criteria][0]): XY_min_max = True
        if float(self.XML_data[XML_row]['Y_min'][0]) < float(self.cfg.get('kwaliteit')[extend_criteria][1]): XY_min_max = True
        if float(self.XML_data[XML_row]['X_max'][0]) > float(self.cfg.get('kwaliteit')[extend_criteria][2]): XY_min_max = True
        if float(self.XML_data[XML_row]['Y_max'][0]) > float(self.cfg.get('kwaliteit')[extend_criteria][3]): XY_min_max = True
      # als XY_min_max verhoog dan de teller en voeg de XML_row toe
      if XY_min_max: 
        kwaliteit_teller[extend_criteria][0] += 1
        kwaliteit_teller[extend_criteria][1].append(XML_row)         
    # stel de lijst samen voor de ctrl list
    lijst = [[kwaliteit_teller[sleutel][0], sleutel] for sleutel in sorted(kwaliteit_teller.keys())]
    # maak een list control object
    combo_obj = ListCtrlDialog(None, -1, title=title,  header=header, lijst=lijst)
    # zet het object op het scherm
    combo_obj.ShowModal()
    # lees de verschillende waardes uit het object
    response = combo_obj.response
    # verwijder het object
    combo_obj.Destroy()
    # verwerkt de geselecteerde resultaten 
    if response is not False: 
      if len(kwaliteit_teller[response[1]][1]) > 0:
        # stel de nieuwe XML bestanden vast
        self.XML_bestanden = sorted([[result, self.XML_data[result]['bron titel'][0]] for result in kwaliteit_teller[response[1]][1]])
        # vul de data met de XML bestanden
        self.vul_data()
    return
       
# -----

  def menuFilterUniek(self, event):
    """ Maak een filter met de unieke waardes van een veld """ 
    # geef de titel balk
    title = 'GEEF UNIEKE WAARDES'
    # geef de header van de ctrl list
    header = (('XML item', 250),)
    # stel de lijst samen voor de ctrl list
    lijst = [[tag] for tag in self.cfg.get('single_tags').keys()]
    lijst.extend([[tag] for tag in self.cfg.get('multi_tags').keys()])
    lijst = sorted(lijst)
    # maak een list control object
    combo_obj = ListCtrlDialog(None, -1, title=title,  header=header, lijst=lijst)
    # zet het object op het scherm
    combo_obj.ShowModal()
    # lees de verschillende waardes uit het object
    response_01 = combo_obj.response
    # verwijder het object
    combo_obj.Destroy()
    # verwerkt de geselecteerde resultaten 
    if response_01 is not False: 
      tag_results = []
      # loop door de huidige XML bestanden
      for XML_row in [regel[0] for regel in self.XML_bestanden]:
        # als het geselecteerde item zich in XML data bevind voeg dit dan toe aan de lijst
        for item in self.XML_data[XML_row][response_01[0]]:
          # als item bestaat voeg hem dan toe, behalve \n
          if item and item.strip() != '\\n': tag_results.append(item)
      # geef de titel van de list ctrl
      title = 'UNIEKE WAARDES'
      # geef de header van de list ctrl
      header = (('Aantal', 70), ('Omschrijving', 500))
      # stel de lijst samen voor de list ctrl
      lijst = sorted([[tag_results.count(item), item.decode('utf-8')] for item in set(tag_results)], key=lambda kolom: kolom[1])
      # maak een list control object
      combo_obj = ListCtrlDialog(None, -1, title=title,  header=header, lijst=lijst)
      # zet het object op het scherm
      combo_obj.ShowModal()
      # lees de verschillende waardes uit het object
      response_02 = combo_obj.response
      # verwijder het object
      combo_obj.Destroy()
      # verwerk de geselecteerde resultaten
      if response_02 is not False: 
        xml_results = []
        # loop door de huidige XML bestanden  
        for XML_row in [regel[0] for regel in self.XML_bestanden]:
          # loop door de geselecteerde items 
          for item in self.XML_data[XML_row][response_01[0]]:
            # als de response in het item is voeg dit dan toe aan de list
            if response_02[1] == item: xml_results.append(XML_row)
        # stel de nieuwe XML bestanden vast
        self.XML_bestanden = sorted([[result, self.XML_data[result]['bron titel'][0]] for result in xml_results])
        # vul de data met de XML bestanden
        self.vul_data()
    return
    
# -----

  def menuFilterTrefWoord(self, event):
    """  """
    # geef de titel balk
    title = 'THESAURI'
    # geef de header van de ctrl list
    header = (('datum', 100), ('thesauri', 300),)
    # stel de lijst samen voor de ctrl list
    lijst = [tag.split(' ', 1) for tag in self.cfg.get('trefwoorden').keys()]
    lijst = sorted(lijst)
    # maak een list control object
    combo_obj = ListCtrlDialog(None, -1, title=title,  header=header, lijst=lijst)
    # zet het object op het scherm
    combo_obj.ShowModal()
    # lees de verschillende waardes uit het object
    response_01 = combo_obj.response
    # verwijder het object
    combo_obj.Destroy()
    # verwerkt de geselecteerde resultaten 
    if response_01 is not False: 
      print(response_01)
    
    # !!! nog verder uitwerken
    # open een message dialog
    MsgBox = wx.MessageDialog(None, 'Trefwoorden moet nog verder uitgewerkt worden.', 'THESAURI', wx.OK|wx.ICON_INFORMATION)
    # als in de message dialog op ok wordt gedrukt, doe dan niets
    if MsgBox.ShowModal() == wx.ID_OK: pass
    return

# -----    
    
  def menuFilterSelectie(self, event):
    """ Filter de geselecteerde bestanden """
    # verzamel de metadata xmls
    self.XML_bestanden = sorted([[self.sheet.GetCellValue(row, 0), self.sheet.GetCellValue(row, 1)] for row in self.GetSelectedRows()])
    # bepaal het aantal xml bestanden
    if len(self.XML_bestanden) != 0: self.vul_data()

# -----

  def menuFilterOff(self, event):
    """ Verwijder de filter """ 
    # sorteer de data
    self.XML_bestanden = sorted([[result, self.XML_data[result]['bron titel'][0]] for result in self.XML_data.keys()])
    # vul het grid met data
    self.vul_data() 

# -----

  def menuRepareerUniek(self, event):
    """ Repareer de unieke gegevens """
    # geef de titel balk
    title = 'REPAREER UNIEKE WAARDES'
    # lees de single en multi tags
    single_tags = self.cfg.get('single_tags')
    multi_tags = self.cfg.get('multi_tags')
    # geef de header van de ctrl list
    header = (('XML item', 250),)
    # stel de lijst samen voor de ctrl list
    lijst = [[tag] for tag in self.cfg.get('single_tags').keys()]
    lijst.extend([[tag] for tag in self.cfg.get('multi_tags').keys()])
    lijst = sorted(lijst)
    # maak een list control object
    combo_obj = ListCtrlDialog(None, -1, title=title,  header=header, lijst=lijst)
    # zet het object op het scherm
    combo_obj.ShowModal()
    # lees de verschillende waardes uit het object
    response_01 = combo_obj.response
    # verwijder het object
    combo_obj.Destroy()
    # verwerkt de geselecteerde resultaten 
    if response_01 is not False: 
      tag_results = []
      # loop door de huidige XML bestanden
      for XML_row in [regel[0] for regel in self.XML_bestanden]:
        # als het geselecteerde item zich in XML data bevind voeg dit dan toe aan de lijst
        for item in self.XML_data[XML_row][response_01[0]]: 
          # als item bestaat voeg hem dan toe, behalve \n
          if item and item.strip() != '\\n': tag_results.append(item)
      # geef de titel van de list ctrl
      title = 'UNIEKE WAARDES'
      # geef de header van de list ctrl
      header = (('Aantal', 70), ('Omschrijving', 500))
      # stel de lijst samen voor de list ctrl
      lijst = sorted([[tag_results.count(item), item] for item in set(tag_results)], key=lambda kolom: kolom[1])
      # maak een list control object
      combo_obj = ListCtrlDialog(None, -1, title=title,  header=header, lijst=lijst)
      # zet het object op het scherm
      combo_obj.ShowModal()
      # lees de verschillende waardes uit het object
      response_02 = combo_obj.response
      # verwijder het object
      combo_obj.Destroy()
      # verwerk de geselecteerde resultaten
      if response_02 is not False: 
        xml_results = []
        # loop door de huidige XML bestanden  
        for XML_row in [regel[0] for regel in self.XML_bestanden]:
          # loop door de geselecteerde items 
          for item in self.XML_data[XML_row][response_01[0]]:
            # als de response in het item is voeg dit dan toe aan de list
            if response_02[1] == item: xml_results.append(XML_row)
        # maak een object voor het repareren
        repare_obj = RepareDialog(None, -1, title='VERVANG UNIEK', text_old=response_02)
        repare_obj.ShowModal()
        if repare_obj.text_new is not False: 
          # lees de verschillende waardes uit het object
          # geef een lege string als het venster wordt weggeklikt
          if type(repare_obj.text_new) is unicode: self.repare = repare_obj.text_new
          else: self.repare = ''
          # verwijder het object
          repare_obj.Destroy()
          # verzamel de oude en nieuwe tekst
          repare_data = {'old_text' : response_02[1], 'new_text' : self.repare}
          # loop door de bestanden
          for XML in [self.XML_dir+os.sep+XML+'.xml'for XML in xml_results]: 
            # parse de XML
            xmlObject = minidom.parse(XML)
            # maak een dictionarie voor de dateStamp
            repare_dateStamp = {'old_text' : self.XML_data[os.path.splitext(os.path.split(XML)[1])[0]]['metadata datum'][0], \
                                'new_text' : datetime.date.today().isoformat(), 'tags' : single_tags['metadata datum']}
            # pas de dateStamp aan aan vandaag
            repare_single_tag(xmlObject, repare_dateStamp)
            # kijk of het een single of multi tag is
            if response_01[0] in single_tags.keys():
              # lees de single tags uit
              repare_data['tags'] = single_tags[response_01[0]]
              # repareer de single tag
              repare_single_tag(xmlObject, repare_data)
            elif response_01[0] in multi_tags.keys():
              # lees de multi tags uit
              repare_data['tags'] = multi_tags[response_01[0]]
              # repareer multi tag
              repare_multi_tag(xmlObject, repare_data)
            # schrijf alles weg in het XML bestand  
            with open(XML, 'w') as bestand: bestand.write(xmlObject.toxml(encoding='utf-8'))        
            # aanpassen self.XML_data (vervang old tekst door new tekst in de list)
            self.XML_data[os.path.splitext(os.path.split(XML)[1])[0]][response_01[0]] = \
              [self.repare if item == response_02[1] else item for item in self.XML_data[os.path.splitext(os.path.split(XML)[1])[0]][response_01[0]]]
            # dateStamp in self.XML_data aanpassen
            self.XML_data[os.path.splitext(os.path.split(XML)[1])[0]]['metadata datum'][0] = datetime.date.today().isoformat()
          # open een message dialog
          MsgBox = wx.MessageDialog(None, 'Repareer unieke waardes zijn verwerkt.', 'REPAREER UNIEKE WAARDES', wx.OK|wx.ICON_INFORMATION)
          # als in de message dialog op ok wordt gedrukt, doe dan niets
          if MsgBox.ShowModal() == wx.ID_OK: pass  
    return
    
# -----

  def menuRepareerContact(self, event):            
    """ 
    Repareer de contact gegevens 
    """
    # bepaal csv bestand
    csv_bestand = self.start_dir+os.sep+os.path.splitext(self.bestand)[0]+'.csv'
    # als de csv niet bestaat
    if not os.path.isfile(csv_bestand):
      # open een message dialog
      MsgBox = wx.MessageDialog(None, 'CSV bestand is niet aanwezig', 'CSV BESTAND AFWEZIG', wx.OK|wx.ICON_INFORMATION)
      # als in de message dialog op ok wordt gedrukt, doe dan niets
      if MsgBox.ShowModal() == wx.ID_OK: pass
       # geef een melding in de logging
      logging.info('%s bestaat niet' %(csv_bestand))
      return
    # maak een object van de csv data open de file en lees de regels
    with open(csv_bestand, 'r') as csvfile: csv_regels = csvfile.readlines()
    # genereer een list uit de lines
    csv_list = [csv_regel.strip().split(self.sep) for csv_regel in csv_regels]
    # lees de header 
    csv_header = csv_list[:1][0][1:]
    # maak een lege dictionarie
    csv_dict = {}
    # vul de dictionarie met keys in kleine letters
    for csv in csv_list[1:]: csv_dict[csv[0].lower()] = csv
    # maak een lege list voor contacten die niet voorkomen in de csv
    csv_onbekend = []
    # lees de contact gegevens uit en sorteer ze
    contact_tags = self.cfg.get('contact_gegevens')
    # maak een gesorteerde list van de keys
    contact_keys = sorted(contact_tags.keys())
    # lees de mail tags uit
    mail_tags = contact_tags[contact_keys[0]]
    # bepaal de eerste tag om het element te zoeken
    first_tag = mail_tags.strip('/').split('/')[0]
    # loop door de self.XML_bestanden
    for XML in [self.XML_dir+os.sep+XML_bestand[0]+'.xml' for XML_bestand in self.XML_bestanden]:
      # parse de bestanden
      xmlObject = minidom.parse(XML)
      # als er geen name space is ingevuld verwijder die dan uit de email list
      if xmlObject.getElementsByTagName(first_tag) == []: first_tag = first_tag.split(':')[-1]
      # zoek naar de eerste tag en loop en maak er een xml object van
      for xml_element in xmlObject.getElementsByTagName(first_tag):
        # lees mail gegevens uit
        mail_geg = zoek_tag(xml_element, mail_tags)
        # als de mail gegevens voorkomen in de csv, vervang dan de data
        if mail_geg.lower() in csv_dict.keys():
          # loop door de contact keys
          for sleutel in contact_keys:
            # zoek de benodigde gegevens bij elkaar
            old_text = zoek_tag(xml_element, contact_tags[contact_keys[int(sleutel[0:2])-1]])
            new_text = csv_dict[mail_geg.lower()][int(sleutel[0:2])-1]
            tags = contact_tags[contact_keys[int(sleutel[0:2])-1]]
            # stel de dictionarie samen
            repare_data = {'old_text' : old_text, 'new_text' : new_text, 'tags' : tags}
            # pas de data aan
            repare_single_tag(xml_element, repare_data)
          # haal de oude en nieuwe mail gegevens op
          old_text = mail_geg
          new_text = csv_dict[mail_geg.lower()][0]
          # pas de mail gegevens aan in self.XML_data (metadata email)
          metadata_mail_list = self.XML_data[os.path.splitext(os.path.split(XML)[1])[0]]['metadata email']
          # loop door de metadata_mail_list
          metadata_mail_list = [item if not item == old_text else new_text for item in metadata_mail_list]
          # vervang de list 
          self.XML_data[os.path.splitext(os.path.split(XML)[1])[0]]['metadata email'] = metadata_mail_list
          # pas de mail gegevens aan in self.XML_data (metadata email, bron email, distributie email)
          bron_mail_list =  self.XML_data[os.path.splitext(os.path.split(XML)[1])[0]]['bron email']
          # loop door de bron_mail_list
          bron_mail_list = [item if item != old_text else new_text for item in bron_mail_list]
          # vervang de list
          self.XML_data[os.path.splitext(os.path.split(XML)[1])[0]]['bron email'] = bron_mail_list
          # pas de mail gegevens aan in self.XML_data (bron email)
          distributie_mail_list = self.XML_data[os.path.splitext(os.path.split(XML)[1])[0]]['distributie email']
          # loop door de distributie_mail_list
          distributie_mail_list = [item if not item == old_text else new_text for item in distributie_mail_list]
          # vervang de list
          self.XML_data[os.path.splitext(os.path.split(XML)[1])[0]]['distributie email'] = distributie_mail_list
          # pas dateStamp date aan, maak een dictionarie voor de dateStamp
          repare_dateStamp = {'old_text' : self.XML_data[os.path.splitext(os.path.split(XML)[1])[0]]['metadata datum'][0], \
                            'new_text' : datetime.date.today().isoformat(), 'tags' : self.cfg.get('single_tags')['metadata datum']}
          # pas de dateStamp aan aan vandaag
          repare_single_tag(xmlObject, repare_dateStamp)
          # pas de dateStamp aan in self.XML_data aan
          self.XML_data[os.path.splitext(os.path.split(XML)[1])[0]]['metadata datum'][0] = datetime.date.today().isoformat()
          # schrijf alles weg in het XML bestand  
          with open(XML, 'w') as bestand: bestand.write(xmlObject.toxml(encoding='utf-8'))
        # als de mail gegevens niet bekend zijn 
        else:
          # voeg ze dan toe aan de csv onbekend list
          if mail_geg not in csv_onbekend: csv_onbekend.append(mail_geg) 
    # open een message dialog
    MsgBox = wx.MessageDialog(None, 'Repareer contact gegevens zijn verwerkt.', 'REPAREER CONTACT GEGEVENS', wx.OK|wx.ICON_INFORMATION)
    # als in de message dialog op ok wordt gedrukt, doe dan niets
    if MsgBox.ShowModal() == wx.ID_OK: pass  
    # verwerk de onbekende csv gegevens in de logging
    if len(csv_onbekend) > 0: logging.info('Mail gegevens niet bekend %s' %(csv_onbekend))
    return

# -----

  def menuRepareerPublicDomain(self, event):
    """ Zet alles naar Public Domain """
    # maak een message dialog
    MsgBox = wx.MessageDialog(None, 'De structuur van de bestanden wordt aangepast.', 'VERVANG CREATIVE COMMON LICENTIE', wx.CANCEL|wx.OK|wx.ICON_EXCLAMATION)
    # als in de message dialog op ok wordt gedrukt
    if MsgBox.ShowModal() == wx.ID_OK:
      # maak een list met de volledige bestandsnamen
      metadata_xmls = [self.XML_dir+os.sep+XML[0]+'.xml' for XML in self.XML_bestanden]
      # bepaal het aantal xml bestanden
      aantal_xmls = len(metadata_xmls)
      # bepaal het aantal stappen
      stap = 100
      # maak een lege resultaten list
      results = []
      # loop door de gegevens in stappen
      for aantal in range(0, aantal_xmls, stap):
        # maak een pool voor het aantal request
        pool = multiprocessing.Pool(processes=stap)
        # map metadata xmls naar de correct_xml en vang de resultaten af
        results.extend(pool.map(vervang_creative_commons, metadata_xmls[aantal:aantal+stap]))
        # geen processen meer toevoegen
        pool.close()
        # wacht tot alles verwerkt is
        pool.join()
      # wijzig de datestamp en overige beperkingen in self.XML_data
      for metadata_xml in metadata_xmls:
        # lees de metadata xml uit 
        with open(metadata_xml, 'r') as bestand: xml = bestand.read()
        if 'http://creativecommons.org/publicdomain/mark/1.0/deed.nl' in xml:
          # dateStamp in self.XML_data aanpassen
          self.XML_data[os.path.splitext(os.path.split(metadata_xml)[1])[0]]['metadata datum'][0] = datetime.date.today().isoformat()
          # overige beperkingen aanpassen
          self.XML_data[os.path.splitext(os.path.split(metadata_xml)[1])[0]]['overige beperkingen'] = ['geen beperkingen', 'http://creativecommons.org/publicdomain/mark/1.0/deed.nl']
      # open een message dialog
      MsgBox = wx.MessageDialog(None, 'Repareer publicdomain is verwerkt.', 'VERVANG CREATIVE COMMON LICENTIE', wx.OK|wx.ICON_INFORMATION)
      # als in de message dialog op ok wordt gedrukt, doe dan niets
      if MsgBox.ShowModal() == wx.ID_OK: pass  
    return

# -----

  def menuRepareerTijdPeriode(self,event):
    """ 
    Repareer de tijd periode:
    - als de begin datum ontbreekt verwijder de gehele tag
    - als de eind datum ontbreekt vervang die door de waarde uit het config bestand
    """
    # maak een message dialog
    MsgBox = wx.MessageDialog(None, 'De structuur van de bestanden wordt aangepast.', 'REPAREER TIJD PERIODE', wx.CANCEL|wx.OK|wx.ICON_EXCLAMATION)
    # als in de message dialog op ok wordt gedrukt
    if MsgBox.ShowModal() == wx.ID_OK:
      # lees de eind tijd uit
      time_period_eind_datum = self.cfg.get('time_period_eind_datum')
      # loop door alle XMLs
      for XML in [self.XML_dir+os.sep+XML[0]+'.xml' for XML in self.XML_bestanden]:
        # open de xml bestanden
        with open(XML, 'r') as bestand: xml = bestand.read().strip()
        # lees de TimePeriod begin en eind datum uit de xml
        begin_datum = zoek_tekst_waarde(xml, ['begin>', 'timePosition'])
        eind_datum = zoek_tekst_waarde(xml, ['end>', 'timePosition'])
        # als de begin datum bestaat en de eind datum niet pas dan de eind datum aan
        if begin_datum and not eind_datum:
          # vervang de eind datum door de config eind datum
          eind_datum = time_period_eind_datum
          xml = vervang_time_period(xml, [begin_datum, eind_datum])
          # wijzig de datestamp
          xml = vervang_datestamp(xml)
          # schrijf alles weg
          with open(XML, 'w') as bestand: bestand.write(xml)
          # dateStamp in self.XML_data aanpassen
          self.XML_data[os.path.splitext(os.path.split(XML)[1])[0]]['metadata datum'][0] = datetime.date.today().isoformat()
        # als de begin datum niet bestaat en de eind datum wel verwijder dan de gehele TimePeriod
        elif not begin_datum and eind_datum:
          xml = verwijder_time_period(xml)
          # wijzig de date stamp
          xml = vervang_datestamp(xml)
          # schrijf alles weg
          with open(XML, 'w') as bestand: bestand.write(xml)
          # dateStamp in self.XML_data aanpassen
          self.XML_data[os.path.splitext(os.path.split(XML)[1])[0]]['metadata datum'][0] = datetime.date.today().isoformat()
      # open een message dialog
      MsgBox = wx.MessageDialog(None, 'Repareer tijd periode is verwerkt.', 'REPAREER TIJD PERIODE', wx.OK|wx.ICON_INFORMATION)
      # als in de message dialog op ok wordt gedrukt, doe dan niets
      if MsgBox.ShowModal() == wx.ID_OK: pass        
    return    

# -----

  def menuRepareerThesauri(self,event):
    """ Repareer Thesauri """
    strings = ['descriptiveKeywords>']
    # geef de titel balk
    title = 'VERWIJDER THESAURUS INCLUSIEF TREFWOORDEN'
    # geef de header van de ctrl list
    header = (('thesauri', 400),)
    # stel de lijst samen voor de ctrl list
    temp_lijst = [self.XML_data[xml_naam[0]]['thesaurus'] for xml_naam in self.XML_bestanden if self.XML_data[xml_naam[0]]['thesaurus'] != []]
    # maak een platte lijst met unieke waarden
    # zie: http://treyhunner.com/2015/12/python-list-comprehensions-now-in-color/   (nested loops)
    lijst = set([item for items in temp_lijst for item in items])
    lijst = sorted([[item] for item in lijst])
    # maak een list control object
    combo_obj = ListCtrlDialog(None, -1, title=title,  header=header, lijst=lijst)
    # zet het object op het scherm
    combo_obj.ShowModal()
    # lees de verschillende waardes uit het object
    response_01 = combo_obj.response
    # verwijder het object
    combo_obj.Destroy()
    # verwerkt de geselecteerde resultaten 
    if response_01 is not False: 
      # maak een message dialog
      MsgBox = wx.MessageDialog(None, 'Thesaurus "%s" wordt verwijderd inclusief de bijbehorende trefwoorden.' %(response_01[0]), \
                       'VERWIJDER THESAURUS INCLUSIEF TREFWOORDEN', wx.CANCEL|wx.OK|wx.ICON_EXCLAMATION)
      # als in de message dialog op ok wordt gedrukt
      if MsgBox.ShowModal() == wx.ID_OK:
        # voeg de response toe aan de strings
        strings.extend(response_01)
        # loop door de self.XML_bestanden
        for metadata_xml in [self.XML_dir+os.sep+XML[0]+'.xml' for XML in self.XML_bestanden]:
          # roep remove xml data op
          remove_xml_data(metadata_xml, strings)
        # schoon self.XML_data op voor self.XML_bestanden
        for XML in self.XML_bestanden:
          if response_01[0] in self.XML_data[XML[0]]['thesaurus']: 
            self.XML_data[XML[0]]['thesaurus'].remove(response_01[0])
            # dateStamp in self.XML_data aanpassen
            self.XML_data[XML[0]]['metadata datum'][0] = datetime.date.today().isoformat()
        # open een message dialog
        MsgBox = wx.MessageDialog(None, 'Repareer thesauri is verwerkt.', 'VERWIJDER THESAURUS INCLUSIEF TREFWOORDEN', wx.OK|wx.ICON_INFORMATION)
        # als in de message dialog op ok wordt gedrukt, doe dan niets
        if MsgBox.ShowModal() == wx.ID_OK: pass           
    return
        
# -----

  def menuRepareerLegeRegels(self, event):
    """ Verwijder alle lege regels """
    # maak een message dialog
    MsgBox = wx.MessageDialog(None, 'De structuur van de bestanden wordt aangepast.', 'REPAREER LAYOUT XML', wx.CANCEL|wx.OK|wx.ICON_EXCLAMATION)
    # als in de message dialog op ok wordt gedrukt
    if MsgBox.ShowModal() == wx.ID_OK:
      # W3C prolog
      W3Cprolog = '<?xml version="1.0"'
      # loop door alle XMLs
      for XML in [self.XML_dir+os.sep+XML[0]+'.xml' for XML in self.XML_bestanden]: 
        # begin en eind te verwijderen commentaar
        begin_skip = '<!--'
        end_skip = '-->'
        # open de xml en lees de data
        with open(XML, 'r') as infile: tekst = infile.read()
        # verwijder begin en eind spaties
        tekst = tekst.strip()
        # als de tekst met de W3C prolog begint plaats het begin van de tekst
        if W3Cprolog in tekst: regels = []
        else: regels = ['<?xml version="1.0" encoding="UTF-8"?>\n']
        # loop door het aantal te verwijderen teksten
        for num in range(tekst.count(begin_skip)):
          # verwijder van begin skip tot eind skip
          tekst = tekst[:tekst.find(begin_skip)]+tekst[tekst.find(end_skip)+len(end_skip):]
        # sla alles op
        with open(XML, 'w') as outfile: outfile.write(tekst)
        # open de file en lees de regels
        with open(XML, 'r') as infile: temp_regels = infile.readlines()
        # maak lege variabelen
        vorige_regel = ''
        tekst = ''
        spaties = 0
        # loop door de tijdelijke regels
        for temp_regel in temp_regels:
          # als '>   <' zich in de regel bevind
          if re.compile(r'>\s*<').search(temp_regel):
            # vervang '>  <' door '>~<'
            split_regels = re.compile(r'>\s*<').sub('>~<', temp_regel)
            # split op de tilde
            split_regels = split_regels.split('~')
            # voeg een \n toe
            split_regels = [split_regel+'\n' for split_regel in split_regels]
            # voeg de split regels toe aan regels
            regels.extend(split_regels)
          # voeg de temp_regel toe aan regels  
          else: regels.append(temp_regel)
        # lees alle regels in
        for regel in regels:
          # lees alleen de gevulde regels
          if not re.compile(r'^\s*$').match(regel):
            # verwijder lege stuk begin regel
            regel = regel.lstrip()
            # verwijder spaties aan het einde van de regel
            regel = regel.rstrip(' ')
            # zet in het begin de spaties op 0
            if regel.startswith('<gmd:MD_Metadata') or regel.startswith('<MD_Metadata') or regel.startswith('<?xml'): spaties = 0
            elif regel.startswith('</') and vorige_regel.startswith('<'): spaties += -2
            elif vorige_regel.startswith('</') or vorige_regel.endswith('/>'): spaties += 0
            elif regel.startswith('<') and vorige_regel.startswith('<'): spaties += 2
            # verzamel de regels in tekst
            tekst += '%s%s' %(' '*spaties, regel)
            # lees de huidige tag als vorige tag
            vorige_regel = regel[regel.find('<') : regel.find('>')+1]
        # sla alles op
        with open(XML, 'w') as outfile: outfile.write(tekst)
      # open een message dialog
      MsgBox = wx.MessageDialog(None, 'Repareer layout xml zijn verwerkt.', 'REPAREER LAYOUT XML', wx.OK|wx.ICON_INFORMATION)
      # als in de message dialog op ok wordt gedrukt, doe dan niets
      if MsgBox.ShowModal() == wx.ID_OK: pass       
    return

# -----

  def menuInstellingenVoorkeur(self,event):
    """ Pas de instellingen aan """
    pass
         
# -----

  def onHelp(self,event):
    """ Help menu """
    # open het help bestand
    if sys.platform == 'linux2': os.system('firefox "%s"' %(self.cfg.get('dirs')['help']))
    elif sys.platform == 'win32': os.startfile('"%s"' %(self.cfg.get('dirs')['help']))
    return

# -----

  def menuOver(self, event):
    """ Gegevens over de ontwikkeling van de applicatie """
    # maak de beschrijving
    description = '%s is een programma voor het beheren van GEO metadata, ' %os.path.splitext(self.bestand)[0]
    description += 'die voldoet aan de door geonovum vastgestelde normen' 
    description += ' '*20
    # maak een wx.AboutDialogInfo object
    info = wx.AboutDialogInfo()
    # vul de Aboutdialog met gegevens
    info.SetName(os.path.splitext(self.bestand)[0])
    info.SetVersion('%s' %( __version__))
    info.SetDescription(description)
    info.SetCopyright('(C) 2016 %s' %(__author__))
    info.SetWebSite('http://www.provinciaalgeoregister.nl/georegister/pgr.do')
    info.SetLicence('\n%s wordt verspreid onder GNU GPL3 licentie. \n\nhttps://www.gnu.org/licenses/gpl.html' %os.path.splitext(self.bestand)[0])
    info.AddDeveloper('binaries:  https://osgeo.nl/geonetwork-gebruikersgroep/best-practices\nsource code:  https://github.com/provincies\n\n%s' %(__author__))
    info.AddDocWriter('%s' %('Carel Stortelder'))
    info.AddArtist('%s' %(__author__))
    # maak de wx.AboutBox widget
    wx.AboutBox(info)
    return

# -----

  def onLabelClick(self, event):
    """ sorteer de data op aangeklikte kolom """
    # sorteer de xml bestanden op de geselecteerde kolom
    self.XML_bestanden = sorted(self.XML_bestanden, key=lambda bestand: bestand[event.GetCol()], reverse = self.sorteer_richting)
    # verander de sorteer richting
    if self.sorteer_richting == True : self.sorteer_richting = False
    else: self.sorteer_richting = True
    # vul de data opnieuw
    self.vul_data()
    return

# -----

  def onLeftDClick(self, event):
    """ Bij dubbel klik links open de xml """
    # bepaal de xml naam 
    metadata_xml = self.sheet.GetCellValue(event.GetRow(), 0)
    # open een message dialog
    MsgBox = wx.MessageDialog(None, 'Lees bij aanpassingen de XML directorie opnieuw in\nen pas <MD_Metadata><dateStamp><gco:Date> aan.', 'EDIT XML', wx.OK|wx.ICON_INFORMATION)
    # als in de message dialog op ok wordt gedrukt, doe dan niets
    if MsgBox.ShowModal() == wx.ID_OK: pass
    # open het bestand
    if sys.platform == 'linux2': os.system('geany "%s.xml"' %(self.XML_dir+os.sep+metadata_xml))
    elif sys.platform == 'win32': os.startfile('"%s.xml"' %(self.XML_dir+os.sep+metadata_xml))
    return  
      
# -----

  def onRightClick(self, event):
    """ Rechts klik menu """
    # begin pas als er iets geselecteerd is
    if len(self.GetSelectedRows()) > 0:
      # geef alle items voor het Rechts Click menu
      self.RCitems={80 : 'Validatie geselecteerde metadata', \
                    81 : 'Export geselecteerde metadata', \
                    82 : 'Verwijder geselecteerde metadata'}
      # maak een RC menu
      RCmenu = wx.Menu()
      # vul het RC menu met de items en maak de events
      for id, RCitem in self.RCitems.items(): 
        RCmenu.Append(id, RCitem)
        wx.EVT_MENU(RCmenu, id, self.RC_Export)
      # laat het RC menu zien  
      self.PopupMenu(RCmenu)
      # verwijder het RC menu om te verkomen dat er mem leaks ontstaat  
      RCmenu.Destroy() 
    return

# -----

  def onCtrlA(self, event):
    """ selecteer alle records """
    # als niet alle records geselecteerd zijn: selecteer dan alle records
    if len(self.GetSelectedRows()) < len(self.XML_bestanden): self.sheet.SelectAll()
    # anders deselecteer alle records
    else: [self.sheet.DeselectRow(row) for row in range(len(self.XML_bestanden))]
    return
              
# -----

  def RC_Export(self, event):
    """ Uitvoeren rechts klik menu """
    # loop door de mogelijk geselecteerde items
    if event.GetId() == 80: self.GeonovumVal()
    elif event.GetId() == 81: self.ExportMetadata()
    elif event.GetId() == 82: self.VerwijderMetadata()
      
# -----

  def GeonovumVal(self):
    """ voer de Geonovum validatie uit """ 
    # lees de validatie_code uit
    val_codes = self.cfg.get('validatie_codes')
    # verzamel de metadata xmls
    metadata_xmls = [[str(self.XML_dir+os.sep+self.sheet.GetCellValue(row, 0)+'.xml'), val_codes] for row in self.GetSelectedRows()]            
    # bepaal het aantal xml bestanden
    aantal_xmls = len(metadata_xmls)
    # bepaal de stap grootte
    stap = 10
    # maak een lege resultaten list
    results = []
    #~ results.append(metadata_validatie(metadata_xmls[0]))
    # loop door de gegevens in stappen
    for aantal in range(0, aantal_xmls, stap):
      # maak een pool voor het aantal request
      pool = multiprocessing.Pool(processes=stap)
      # map metadata xmls naar de metadata_validatie en vang de resultaten af
      results.extend(pool.map(metadata_validatie, metadata_xmls[aantal:aantal+stap]))
      # geen processen meer toevoegen
      pool.close()
      # wacht tot alles verwerkt is
      pool.join()
    # verwerk de resultaten
    eind_results = verwerking_results(results)
    # zet de titel
    title = 'XML VALIDATIE'
    # header
    header = (('Aantal', 70), ('Omschrijving', 200))
    # resultaten
    lijst = []
    val_lijst = ["goed gekeurde xml's", "afgekeurde xml's", 'bestanden voldoen niet']
    # bepaal het aantal goed gekeurde metadata xmls
    if len(eind_results[0]) > 0: lijst.append([len(eind_results[0]), val_lijst[0], '#98FF98'])
    # bepaal het aantal afgekeurde metadata xmls
    if len(eind_results[1]) > 0: lijst.append([len(eind_results[1]), val_lijst[1], '#FFA500'])
    # bepaal het aantal bestanden dat niet voldoet
    if aantal_xmls-len(eind_results[0])-len(eind_results[1]) > 0: 
      lijst.append([aantal_xmls-len(eind_results[0])-len(eind_results[1]), val_lijst[2], '#F75D59'])
    # maak een list control object
    combo_obj = ListCtrlDialog(None, -1, title=title,  header=header, lijst=lijst)
    # zet het object op het scherm
    combo_obj.ShowModal()
    # lees de verschillende waardes uit het object
    response = combo_obj.response
    # verwijder het object
    combo_obj.Destroy()
    # verwerk de resultaten
    if response is not False:
      # als het de goed gekeurde xmls zijn
      if response[1] == val_lijst[0]:
        # vul self. XML bestanden (onder windows 'metadata_master\\' uit eind_results[0] verwijderen)
        self.XML_bestanden = [[os.path.splitext(str(result))[0], self.XML_data[os.path.splitext(str(result))[0]]['bron titel'][0]] \
                               for result in [result.split('\\')[-1] for result in eind_results[0]]]
        # vul de data
        self.vul_data()
      # als het geen valide xmls zijn
      elif response[1] == val_lijst[1]:
        # start de File dialoog op
        csvDialoog = wx.FileDialog(self, 'Sla het csv bestand op', self.csv_dir, \
                    'Metadata_Master_Validatie_Errors.csv', '(*.csv; *.CSV)|*.csv; *.CSV', wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
        # lees de reactie uit
        if csvDialoog.ShowModal() == wx.ID_OK:
          # leg de huidige directorie vast
          self.csv_dir = csvDialoog.GetDirectory()
          # lees de bestandsnaam
          bestandsnaam = csvDialoog.GetFilename()
          # voeg als nodig '.csv' toe
          if bestandsnaam[-4:].lower() != '.csv': bestandsnaam += '.csv'
          # schrijf alles weg
          with open(self.csv_dir+os.sep+bestandsnaam, 'w') as outfile: 
            for result in eind_results[1].keys():
              outfile.write('%s' %(result))
              for item in eind_results[1][result]:
                outfile.write('|%s\n' %(item.encode('utf_8', errors='ignore')))           
          # vul self. XML bestanden
          self.XML_bestanden = [[os.path.splitext(str(result))[0], self.XML_data[os.path.splitext(str(result))[0]]['bron titel'][0]] \
                               for result in eind_results[1].keys()]
          # vul de data
          self.vul_data()
      # als bestand niet gevalideerd kan worden        
      elif response[1] == val_lijst[2]: 
        # bepaal de lijst met valide xmls
        XMLs = [str(self.XML_dir+os.sep+result) for result in eind_results[0]]
        # bepaal de lijst met niet valide xmls
        XMLs.extend([str(self.XML_dir+os.sep+result) for result in eind_results[1].keys()])
        XMLs = sorted(XMLs, reverse=True)
        # verwijder overbodige data uit metadata_xmls (alleen xml[0]) en verwijder de xmllen die in XMLs staan
        metadata_xmls = sorted([os.path.splitext(os.path.split(xml[0])[1])[0] for xml in metadata_xmls if xml[0] not in XMLs])
        # zet self.XML_bestanden
        self.XML_bestanden = [[xml, self.XML_data[xml]['bron titel'][0]] for xml in metadata_xmls]
        # vul de data
        self.vul_data()
    return

# -----

  def ExportMetadata(self):
    """ Exporteer de geselecteerde metadata """
    # als het export path niet bestaat ga dan naar de home dir
    if not hasattr(self,'export_pad'): self.export_pad = os.path.expanduser('~')
    # start de File dialoog op
    exp_dlg = wx.DirDialog(self, 'Selecteer export directorie','/')
    # zet het export pad    
    exp_dlg.SetPath(self.export_pad) 
    if exp_dlg.ShowModal() == wx.ID_OK:
      # leg de huidige directorie vast
      self.export_pad = exp_dlg.GetPath()
      # verzamel de metadata xmls
      metadata_xmls = [self.sheet.GetCellValue(row, 0)+'.xml' for row in self.GetSelectedRows()]    
      # loop door de geselecteerde xmls
      for metadata_xml in metadata_xmls:
        # open een output file en een input file
        with open(self.export_pad+os.sep+metadata_xml, 'w') as outfile, open(self.XML_dir+os.sep+metadata_xml, 'r') as infile:
          # schrijf de data naar de output file
          outfile.write(infile.read())
    return

# -----

  def VerwijderMetadata(self):
    """ Verwijder de geselecteerd metadata """
    # maak een message dialog
    MsgBox = wx.MessageDialog(None, 'De geselecteerde metadata wordt definitief verwijderd.', \
                             'DELETE METADATA', wx.CANCEL|wx.OK|wx.ICON_EXCLAMATION)
    # als in de message dialog op ok wordt gedrukt
    if MsgBox.ShowModal() == wx.ID_OK:
      # maak een lege index
      XML_bestanden_indexen = []
      # verzamel de metadata xmls 
      for metadata_xml in [str(self.sheet.GetCellValue(row, 0)) for row in self.GetSelectedRows()]:
        # leg de indexen van self.XML_bestanden vast
        XML_bestanden_indexen.append([XML_bestand[0] for XML_bestand in self.XML_bestanden].index(metadata_xml))
        # verwijder de data uit self.XML_data
        del self.XML_data[metadata_xml]
        # verwijder de file
        os.remove(self.XML_dir+os.sep+metadata_xml+'.xml')
      # verwijder de self.XML_bestanden met reverse gesorteerde indexen
      for index in sorted(XML_bestanden_indexen, reverse=True): del self.XML_bestanden[index]
      # vul de data
      self.vul_data()
    return
    
# -----

  def GetSelectedRows(self):
    """
    ivm bug "GetSelectedRows()" zie:
    http://wxpython-users.1045709.n5.nabble.com/BUG-wx-Grid-GetSelectedRows-broken-td2303648.html
    """
    if sys.platform == 'win32': return self.sheet.GetSelectedRows()
    else:
      rows=[]
      set1=self.sheet.GetSelectionBlockTopLeft()
      set2=self.sheet.GetSelectionBlockBottomRight()
      if len(set1):
        assert len(set1)==len(set2)
        for i in range(len(set1)):
          for row in range(set1[i][0], set2[i][0]+1):
            # range in wx is inclusive of last element
            if row not in rows: rows.append(row)
      return rows

# -----

  def verwerk_XML_dir(self):
    """ verwerk een directorie met xml's """
    # maak een lege xml bestanden lists
    self.XML_bestanden = []
    temp_bestanden = []
    # maak een lege resultaten dictionarie
    self.XML_data = {}
    # lees de single en multi tags uit
    single_tags = self.cfg.get('single_tags')
    multi_tags = self.cfg.get('multi_tags')
    # hernoem eventueel de extensie .XML naar kleine letters
    [os.rename(self.XML_dir+os.sep+metadata_xml, self.XML_dir+os.sep+metadata_xml[:-3]+'xml') \
    for metadata_xml in os.listdir(self.XML_dir) if os.path.splitext(metadata_xml)[1].upper() == '.XML' \
    and not os.path.splitext(metadata_xml)[1] == '.xml']
    # loop door de uit te lezen directorie
    for metadata_xml in os.listdir(self.XML_dir):
      # kijk of het een XML bestand is
      if os.path.splitext(metadata_xml)[1] == '.xml':
        # open het bestand en plaats het in de xml veriablele
        with open(self.XML_dir+os.sep+metadata_xml, 'r') as bestand: xml = bestand.read().strip()
        # loop door de ISO profielen
        for iso_profiel in self.ISO_profielen:
          # als in de xml een iso profiel aanwezig is voeg dan de metadata toe aan de temp bestanden list
          if iso_profiel in xml: temp_bestanden.append(self.XML_dir+os.sep+metadata_xml)
    # maak een lege teller
    teller = 0
    # lees het aantal xml's
    aantal_xmls = len(temp_bestanden)
    # geef het minimale aantal xmls om een voortgangs scerm te laten zien
    min_xmls = 50
    # bouw het voortgangs scherm
    if aantal_xmls > min_xmls: VoortgangsScherm = wx.ProgressDialog("INLEZEN XML's", 'Even geduld A.U.B.', maximum=len(temp_bestanden), parent=self)
    # loop door de gegevens in stappen
    for metadata_xml in temp_bestanden:
      try: xmlObject = minidom.parse(metadata_xml)
      except Exception, foutmelding: logging.error('%s geeft een xml foutmelding: %s' %(metadata_xml, foutmelding))
      else:
        # maak een lege dictionarie voor de tags van dit record
        xml_data = {}
        # voeg de waardes van alle single tags toe aan de dictionarie 
        for single_tag_key in single_tags.keys():
          xml_data[single_tag_key] = [zoek_tag(xmlObject, single_tags[single_tag_key])]
        # voeg de waardes van alle multi tags toe aan de dictionarie
        for multi_tag_key in multi_tags.keys():
          xml_data[multi_tag_key] = zoek_tag_waarde(xmlObject, multi_tags[multi_tag_key])
        self.XML_data[os.path.splitext(os.path.split(metadata_xml)[1])[0]] = xml_data
      # verhoog de teller
      teller += 1
      # update het voortgangs scherm
      if aantal_xmls > min_xmls: VoortgangsScherm.Update(teller)
    # verwijder het voortgangs scherm
    if aantal_xmls > min_xmls: VoortgangsScherm.Destroy()
    # sorteer de data
    self.XML_bestanden = sorted([[result, self.XML_data[result]['bron titel'][0]] for result in self.XML_data.keys()])
    # vul het grid met data
    self.vul_data()
    return

# -----

  def vul_data(self):
    """ Vul alle grids met data """  
    # deselect de geselecteerde regels
    [self.sheet.DeselectRow(row) for row in self.GetSelectedRows()]
    # verwijder eventuele dubbele XML bestanden
    temp_bestanden = []
    [temp_bestanden.append(bestand) for bestand in self.XML_bestanden if bestand not in temp_bestanden]
    self.XML_bestanden = temp_bestanden
    # lees het aantal xml bestanden
    stuks_XML = len(self.XML_bestanden)
    # verander de status tekst
    self.SetStatusText("aantal actieve xml\'s: %s stuks" %(stuks_XML), number=0)
    # pas het aantal regels  in de grid eventueel aan de lengte van de xml bestanden 
    if self.sheet.GetNumberRows() > stuks_XML:
      self.sheet.DeleteRows(pos=0, numRows=self.sheet.GetNumberRows()-stuks_XML)
    elif self.sheet.GetNumberRows() < stuks_XML:
      self.sheet.AppendRows(numRows=stuks_XML-self.sheet.GetNumberRows())
    # vul het grid met de xml data uit de xml bestanden
    for rownum in range(len(self.XML_bestanden)):
      # zet de fonts voor de eerste 2 cellen
      self.sheet.SetCellFont(rownum, 0, wx.Font(9, wx.SWISS, wx.NORMAL, wx.NORMAL))        
      self.sheet.SetCellFont(rownum, 1, wx.Font(9, wx.SWISS, wx.NORMAL, wx.NORMAL))
      # vul de eerste 2 cellen
      self.sheet.SetCellValue(rownum, 0, self.XML_bestanden[rownum][0])
      # kijk of de title gevuld is
      if self.XML_bestanden[rownum][1]: 
        self.sheet.SetCellValue(rownum, 1, self.XML_bestanden[rownum][1].decode('utf-8'))
      # geef anders een lege title
      else: self.sheet.SetCellValue(rownum, 1, ' ')
    # geef de titel van het hoofd window
    self.SetTitle('%10s' %(self.XML_dir))
    # refresh de window
    self.Refresh()
    return
    
# -----

  def VoegtoeFilter(self, titel, tekst):
    """   """
    # maak een variabele voegtoe
    voegtoe = False
    # als er geen filter is voeg alles toe
    if self.ortitel == '' and self.orresume == '': voegtoe = True
    else:
      # kijk of het filter self.ortitel niet leeg is 
      if self.ortitel != '':
        # split het filter self.titel op ;
        for item in self.ortitel.split(self.sep):
          # kijk of het filter voorkomt in de ortitel
          if item.encode('utf_8').strip(' ').upper() in titel.upper(): voegtoe = True
      # kijk of het filter self.orresume niet leeg is 
      if self.orresume != '':
        # split het filter self.resume op ;
        for item in self.orresume.split(self.sep):
          # kijk of het filter voorkomt in de samenvatting
          if item.encode('utf_8').strip(' ').upper() in tekst.upper(): voegtoe = True
    if voegtoe: return True
    else: return False          
    
# ----- HOOFD PROGRAMMA ------------------------------------------------

if __name__ == '__main__':
  """
  """
  #start het hoofd window
  app = wx.App(False)
  # http://stackoverflow.com/questions/33505916/wx-image-is-throwing-pyassertionerror
  app.locale = wx.Locale(wx.LANGUAGE_ENGLISH)
  # https://github.com/pyinstaller/pyinstaller/wiki/Recipe-Multiprocessing
  multiprocessing.freeze_support()
  frame = MainWindow(None,-1)
  frame.Show()
  app.MainLoop()

# ----- EINDE PROGRAMMA ------------------------------------------------
