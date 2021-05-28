'''
PyMOL R2D2 Plugin

Plugin for GROMACS FF visualization

License: BSD-2-Clause

Łukasz Radziński, Justyna Replin

lukasz.radzinski@gmail.com
'''

from pymol import cmd, plugins

# Avoid importing "expensive" modules here (e.g. scipy), since this code is
# executed on PyMOL's startup. Only import such modules inside functions.

import os

# Function to convert   
def listToString(s):  
    
    # initialize an empty string 
    str1 = ""  
    
    # traverse in the string   
    for ele in s:  
        str1 += (ele + "/") 
    
    # return string   
    return str1 

def charge_to_color(charge):
    '''
    Convert charge of an atom to RGB color in hex
    Charge: color
    -1.00: blue
    -0.25: cyan
     0.00: white
     0.25: yellow
     1.00: red
    arguments: charge (float)
    returns: RGB color in hex (string)
    '''
    R = 0xFF
    G = 0xFF
    B = 0xFF

    if(charge>0):
        if(charge > 1):
            charge = 1

        B -= round(4*charge*0xFF)
        if(B<0):
            B = 0

        G -= round((4/3)*(charge-0.25)*0xFF)

        if(G>0xFF):
            G = 0xFF

    if(charge<0):
        if(charge < -1):
            charge = -1
        charge = -charge

        R -= round(4*charge*0xFF)
        if(R<0):
            R = 0

        G -= round(4/3*(charge-0.25)*0xFF)

        if(G>0xFF):
            G = 0xFF

    RGB = "0x" + bytearray([R, G, B]).hex()

    return RGB

def process(topology_filename, topology_path, ff_topology_path):

    topology_file = ""

    includes = []

    try:
        #print(topology_path + topology_filename)
        topology_file = open(topology_path + topology_filename, "r")
        print("File " + topology_filename + " loaded")
    except IOError:
        try:
            topology_file = open(ff_topology_path + topology_filename, "r")
            print("File " + topology_filename + " loaded")
        except IOError:
            print("File " + topology_filename + " does not exist!")
            return -1

    is_atoms_section = False
    
    should_skip = False

    for i in topology_file:
        i = i.split()

        if(len(i) >= 2 and i[0] == "#ifdef"):
            should_skip = True
        elif(len(i) >= 1 and i[0] == "#endif"):
            should_skip = False

        if(should_skip == True):
            continue

        if(len(i) >= 2 and i[0] == "#include"):
            includes.append(i[1][1:-1])

        if(len(i) >= 3 and i[0] == '[' and i[1] == 'atoms' and i[2] == ']'):
            is_atoms_section = True
        elif(len(i) >= 3 and i[0] == '[' and i[2] == ']'):
            is_atoms_section = False

        if(is_atoms_section == True and len(i)>=7 and i[0].isdigit() == True):
            if(len(i[4]) == 4 and i[4][0] == 'H'):
                i[4] = i[4][3] + i[4][0:3]

            residue_name = i[3]
            atom_name = i[4]
            charge = float(i[6])

            atom_selection = "resn " + residue_name + " and name " + atom_name
            #print(charge_to_color(charge), atom_selection)
            cmd.color(charge_to_color(charge), atom_selection)

    topology_file.close()

    #print(includes)

    for i in includes:

        i = i.split('/')

        topology_subfilename = i[-1]

        topology_subpath = topology_path + listToString(i[:-1])

        ff_topology_subpath = ff_topology_path + listToString(i[:-1])

        process(topology_subfilename, topology_subpath, ff_topology_subpath)

    return 0


def __init_plugin__(app=None):
    '''
    Add an entry to the PyMOL "Plugin" menu
    '''
    from pymol.plugins import addmenuitemqt
    addmenuitemqt('R2D2 Plugin', run_plugin_gui)


# global reference to avoid garbage collection of our dialog
dialog = None

def run_plugin_gui():
    '''
    Open our custom dialog
    '''
    global dialog

    if dialog is None:
        dialog = make_dialog()

    dialog.show()


def open_ff_location(file_path):
    ff_location_path = open(file_path, "r")
    file_contents = ff_location_path.read()
    return file_contents


def make_dialog():

    # pymol.Qt provides the PyQt5 interface, but may support PyQt4
    # and/or PySide as well
    from pymol.Qt import QtWidgets
    from pymol.Qt.utils import loadUi

    # create a new Window
    dialog = QtWidgets.QDialog()

    # populate the Window from our *.ui file which was created with the Qt Designer
    uifile = os.path.join(os.path.dirname(__file__), 'demowidget.ui')
    form = loadUi(uifile, dialog)
    #ff_location_path = open("ff_location.txt", "r")
    #file_contents = ff_location_path.read()
    file_content = open_ff_location("ff_location.txt")
    form.ff_location.setText(file_content)

    # callback for the "Ray" button
    def run():

        cmd.ramp_new(name='color_bar', map_name='none', range=[-1, -0.25, 0, 0.25, 1], color=['blue', 'cyan', 'white', 'yellow', 'red'])

        ff_location = form.ff_location.text()
        ff_location += "/"

        file_contents = open_ff_location("ff_location.txt")
        form.ff_location.setText(file_contents)


        pdb_filename = form.pdb_filename.text()

        if(pdb_filename):

            cmd.load(pdb_filename)
            cmd.hide("everything")
            cmd.show("sticks")

        topology_filepath = form.topology_filename.text()

        if(topology_filepath):

            topology_filepath = topology_filepath.split('/')

            topology_filename = topology_filepath[-1]

            topology_path = listToString(topology_filepath[:-1])

            process(topology_filename, topology_path, ff_location)
        else:
            print("No topology file!")
            

    def browse_ff_dir():
      
        dirname = QtWidgets.QFileDialog.getExistingDirectory(dialog)

        if dirname:
            form.ff_location.setText(dirname)
            f = open("ff_location.txt", "w")
            f.write(dirname)
            f.close()

    def browse_filename_pdb():
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(dialog, 'Open...', filter='PDB file (*.pdb)')
        if filename:
            form.pdb_filename.setText(filename)

    def browse_filename_topology():
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(dialog, 'Open...', filter='Topology file (*.top *.itp)')
        if filename:
            form.topology_filename.setText(filename)

    # hook up button callbacks
    form.button_ray.clicked.connect(run)
    form.button_browse_ff.clicked.connect(browse_ff_dir)
    form.button_browse_pdb.clicked.connect(browse_filename_pdb)
    form.button_browse_topology.clicked.connect(browse_filename_topology)
    form.button_close.clicked.connect(dialog.close)

    return dialog
