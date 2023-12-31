#!/usr/bin/awk -f
##
##  SPDX-FileCopyrightText: © 2007-2023 Benedict Verhegghe <bverheg@gmail.com>
##  SPDX-License-Identifier: GPL-3.0-or-later
##
##  This file is part of pyFormex 3.3  (Sun Mar 26 20:16:15 CEST 2023)
##  pyFormex is a tool for generating, manipulating and transforming 3D
##  geometrical models by sequences of mathematical operations.
##  Home page: https://pyformex.org
##  Project page: https://savannah.nongnu.org/projects/pyformex/
##  Development: https://gitlab.com/bverheg/pyformex
##  Distributed under the GNU General Public License version 3 or later.
##
##  This program is free software: you can redistribute it and/or modify
##  it under the terms of the GNU General Public License as published by
##  the Free Software Foundation, either version 3 of the License, or
##  (at your option) any later version.
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License
##  along with this program.  If not, see http://www.gnu.org/licenses/.
##

#
# (c) 2009-2012 Benedict Verhegghe
# This is an embryonal awk script to extract information from an Abaqus(tm)
# format input file (.inp) and write it in a format that can be loaded
# easily into pyFormex. Note that the .inp format is also used by Calculix.
#
# Usage: awk -f read_abq.awk INPUT_FILE
#
# In most cases however, the user will call this command from the pyFormex
# GUI, using the Mesh plugin menu ("Convert Abaqus .inp file"), after which
# the model can be imported with the "Import converted model" menu item.
#
# Currently it reads nodes, elements and elsets and stores them in a series
# of files:
#   partname.nodes: contrains the nodal coordinates
#   partname.elems: contains the element connectivity
#   partname.esets: contains element sets
# There may be multiple nodes and elems files.
# An index file partname.mesh keeps record of the created files.
# nodes/elems defined before the first part get a default part name.
#
# The nodes should be numbered consecutively in each of the parts,
# but not necessarily over the different parts.
#
#

######## scanner #######################

# initialisation: set default part name
BEGIN { IGNORECASE=1; mode=0; start_part("DEFAULT_PART"); }

# start a new part
#/^\*\* PART INSTANCE:/ { start_part($4); print "**PART "$4; next; }
/^\*Part,/ { sub(".*name=",""); sub(" .*",""); start_part($0); print "*Part "$0; next; }
/^\*Instance,/ { sub(".*name=",""); sub(", .*",""); start_instance($0); print "*Instance "$0; next; }

# skip all other comment lines
/^\*\*/ { next; }

# start a node block: record the number of the first node
/^\*Node/ {
    start_mode(1)
    getline; gsub(","," "); header = "# nodes "outfile " offset "$1
}

# start an element block
/^\*Element,/ {
    start_mode(2)
    getline; gsub(","," "); header = "# elems "outfile " nplex "NF-1

}

# start an elset block
/^\*Elset, *elset=.*, *generate/ {
    start_mode(3)
    sub(".*elset=","");sub(",.*",""); setname=$0;
    getline; gsub(","," ");
}

# start an nset block
/^\*Nset, *nset=.*, *generate/ {
    start_mode(4)
    sub(".*nset=","");sub(",.*",""); setname=$0;
    getline; gsub(","," ");
}

# skip a step block
/^\*Step/ {
    print "*Step"
    skip_block("^*End Step")
    next
}

# skip other commands
/^\*/ { print "Unknown command: "$0;  end_mode(); next;}

# output data according to output mode
{
    gsub(","," ");
    if (mode==1) print_node();
    else if (mode==2) print_elem();
    else if (mode==3) print_elset();
}

END { end_mode(); fflush(""); close(meshfile) }

######## functions #####################

# skip input until endcmd
function skip_block(endcmd) {
    print "  Skipping until " endcmd
    do {
	getline;
	done = match($0,endcmd);
    } while (done == 0);
    print;
}

# start a new part with name pname
function start_part(pname) {
    print "Starting part "pname
    partname = pname
    meshfile = partname".mesh"
    printf("") > meshfile
    nodesblk = -1
    elemsblk = -1
    esetsblk = -1
}

# start a new instance with name pname
function start_instance(pname) {
    print "Starting instance "pname
    start_part(pname)
}


# start a new output file with given name and type
function start_mode(mod) {
    end_mode()

    mode = mod
    if (mode==1) {
	nodesblk = start_blocked_file("nodes",nodesblk)
    }
    else if (mode==2) {
	elemsblk = start_blocked_file("elems",elemsblk)
    }
    else if (mode==3) {
	esetsblk = start_unique_file("eset",esetsblk)
    }
    else if (mode==4) {
	esetsblk = start_unique_file("nsets",esetsblk)
    }
    print "Starting mode "mode" to file "outfile
    count = 0
}


# Start a file for a blocked type
function start_blocked_file(type,blk) {
    outfile = partname"."type
    blk += 1
    if (blk > 0) outfile = outfile""blk
    printf("") > outfile
    return (blk)
}

# Start a file for a unique type
function start_unique_file(type,blk) {
    outfile = partname"."type
    if (blk < 0) print "# "type" "outfile >> meshfile
    printf("") > outfile
    return 0
}

# stop writing to the current file
function end_mode() {
    if (mode>0) {
	print "Ending mode "mode
	close(outfile)
	mode = 0
	if (count > 0) print header" count "count >> meshfile
    }
}

# print a node
function print_node() {
    gsub(",",""); print $2," ",$3," ",$4 >> outfile;
    count += 1;
}

# print an element
function print_elem() {
    gsub(",",""); print $2" "$3" "$4" "$5" "$6" "$7" "$8" "$9 >> outfile;
    count += 1;
}

# print an elset
function print_elset() {
    print setname
    print $0
    gsub(",",""); print setname" "$1" "$2" "$3 >> outfile;
}

# End
