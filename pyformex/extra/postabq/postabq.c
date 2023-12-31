/* */
//
//  SPDX-FileCopyrightText: © 2007-2023 Benedict Verhegghe <bverheg@gmail.com>
//  SPDX-License-Identifier: GPL-3.0-or-later
//
//  This file is part of pyFormex 3.3  (Sun Mar 26 20:16:15 CEST 2023)
//  pyFormex is a tool for generating, manipulating and transforming 3D
//  geometrical models by sequences of mathematical operations.
//  Home page: https://pyformex.org
//  Project page: https://savannah.nongnu.org/projects/pyformex/
//  Development: https://gitlab.com/bverheg/pyformex
//  Distributed under the GNU General Public License version 3 or later.
//
//  This program is free software: you can redistribute it and/or modify
//  it under the terms of the GNU General Public License as published by
//  the Free Software Foundation, either version 3 of the License, or
//  (at your option) any later version.
//
//  This program is distributed in the hope that it will be useful,
//  but WITHOUT ANY WARRANTY; without even the implied warranty of
//  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//  GNU General Public License for more details.
//
//  You should have received a copy of the GNU General Public License
//  along with this program.  If not, see http://www.gnu.org/licenses/.
//

/*
  Scanner for ABAQUS .fil results files
  (C) 2008 Benedict Verhegghe
  Distributed under the GNU GPL version 3 or higher
  THIS PROGRAM COMES WITHOUT ANY WARRANTY
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>


char* copyright = "postabq 0.2 (C) 2008,2014 Benedict Verhegghe";

FILE * fil;

/* Blocks and records
  A block consists of :
  - lead : 4 byte word with value 4096  (RECSIZE in bytes)
  - data : RECSIZE double words (512 * 8 = 4096 bytes)
  - tail : as lead

  A record consists of
  - NW (1)  : number of (double) words
  - KEY (1) : record type
  - DATA (NW-2) : the data

  !!! Records may span the block boundary !!!
  Reading from file is done block by block. If we want to process records as
  a whole, we need to buffer at least 2 blocks.
*/

#define RECSIZE 512
#define BUFSIZE 2*RECSIZE

int64_t recnr = 0;
int64_t blknr = 0;
int64_t err = 0;

int32_t lead,tail;
union {
  double d[BUFSIZE];
  int64_t i[BUFSIZE];
  char   c[8*BUFSIZE];
} data;

int64_t nw,key;

int64_t
  j,    /* Pointer to current data */
  jend, /* Pointer behind current record */
  jmax; /* Pointer behind currently filled buffer */

#define STRINGBUFSIZE 256
char s[STRINGBUFSIZE];

int explicit = 0;  /* assume standard unless specified/detected */
int verbose = 0;
int fake = 0;

/* Copy character data into the string buffer */
/*
  Copies character data from the current data buffer to the string buffer s.
  k : start position of the data (in 8-byte words)
  n : number of data to copy (in 8-byte words)
  strip: if 1, trailing blanks will be stripped of. If 0, the length of the
    resulting string will always be a multiple of 8 (padded with blanks at
    the end).
*/
char* stripn(int64_t k,int64_t n,int strip) {
  s[0] = '\0';
  int64_t m = 8*n;
  if (m > STRINGBUFSIZE) m = STRINGBUFSIZE;
  memmove(s,data.c + (8*k),m);
  while (s[--m] == ' ') {}
  s[++m] = '\0';
  char* p = s;
  if (strip) {
    while (*p==' ') p++;
  }
  return p;
}

/* Copy n words of character data into the string buffer */
/* This is like stripn but without the stripping option */
char* strn(int64_t k,int64_t n) {
  return stripn(k,n,0);
}

/* Copy one word of character data into the string buffer */
/* This is like strn but copying a single 8-byte word only */
char* str(int64_t k) {
  return strn(k,1);
}

void do_element() {
  printf("D.Element(%d,",(int)data.i[j++]);
  printf("'%s',[",str(j++));
  while (j < jend) printf("%d,",(int)data.i[j++]);
  printf("])\n");
}

void do_node() {
  printf("D.Node(%d,[",(int)data.i[j++]);
  int64_t j3 = j+3;
  if (j3 > jend) j3 = jend;
  while (j < j3) printf("%e,",data.d[j++]);
  if (j < jend) {
    printf("],normal=[");
    while (j < jend) printf("%e,",data.d[j++]);
  }
  printf("])\n");
}

void do_dofs() {
  printf("D.Dofs([");
  while (j < jend) printf("%d,",(int)data.i[j++]);
  printf("])\n");
}

void do_outreq() {
  int64_t * ip = data.i + j++;
  int flag = ip[0];
  printf("D.OutputRequest(flag=%d,set='%s'",flag,str(j++));
  if (flag==0) printf(",eltyp='%s',",str(j++));
  printf(")\n");
}

void do_abqver() {
  printf("D.Abqver('%s')\n",str(j++));
  /* BEWARE ! Do not call str() multiple times in the same printf instruction */
  printf("D.Date('%s',",strn(j,2)); j += 2;
  printf("'%s')\n",str(j++));
  printf("D.Size(nelems=%d,nnodes=%d,length=%f)\n",(int)data.i[j],(int)data.i[j+1],data.d[j+2]);
}

void do_heading() {
  printf("D.Heading('%s')\n",strn(j,jend-j));
}

void do_nodeset() {
  printf("D.Nodeset('%s',[",stripn(j++,1,1));
  while (j<jend) printf("%d,",(int)data.i[j++]);
  printf("])\n");
}

void add_nodeset() {
  printf("D.NodesetAdd([");
  while (j<jend) printf("%d,",(int)data.i[j++]);
  printf("])\n");
}

void do_elemset() {
  printf("D.Elemset('%s',[",stripn(j++,1,1));
  while (j<jend) printf("%d,",(int)data.i[j++]);
  printf("])\n");
}

void add_elemset() {
  printf("D.ElemsetAdd([");
  while (j<jend) printf("%d,",(int)data.i[j++]);
  printf("])\n");
}

void do_label() {
  printf("D.Label(tag='%d',value='",(int)data.i[j++]);
  printf("%s",strn(j,jend-j));
  printf("')\n");
}

void do_increment() {
  int64_t * ip = data.i + j;
  double * dp = data.d + j;
  int64_t type = ip[4];
  explicit = (type==17 || type == 74);
  printf("D.Increment(");
  printf("step=%ld,",ip[5]);
  printf("inc=%ld,",ip[6]);
  printf("tottime=%e,",dp[0]);
  printf("steptime=%e,",dp[1]);
  printf("timeinc=%e,",dp[10]);
  printf("type=%ld,",type);
  printf("heading='%s',",stripn(j+11,10,1));
  if (!explicit) {
    printf("maxcreep=%e,",dp[2]);
    printf("solamp=%e,",dp[3]);
    printf("linpert=%ld,",ip[7]);
    printf("loadfactor=%e,",dp[8]);
    printf("frequency=%e,",dp[9]);
  }
  printf(")\n");
}

void end_increment() {
  printf("D.EndIncrement()\n");
}

char* output_location[] = { "gp", "ec", "en", "rb", "na", "el" };

void do_elemheader() {
  int64_t * ip = data.i + j;
  int loc = ip[3];
  printf("D.ElemHeader(loc='%s',",output_location[loc]);
  printf("i=%d,",(int)ip[0]);
  if (loc==0)
    printf("gp=%d,",(int)ip[1]);
  else if (loc==2)
    printf("np=%d,",(int)ip[1]);
  else if (ip[1]!=0)
    printf("ip=%d,",(int)ip[1]);
  if (ip[2]!=0)
    printf("sp=%d,",(int)ip[2]);
  if (loc==3)
    printf("rb='%s',",stripn(j+4,1,1));
  printf("ndi=%d,",(int)ip[5]);
  printf("nshr=%d,",(int)ip[6]);
  printf("nsfc=%d,",(int)ip[8]);
  if (explicit)
      printf("ndir=%d,",(int)ip[7]);
  printf(")\n");
}

void do_elemout(char* text) {
  printf("D.ElemOutput('%s',[",text);
  while (j < jend) printf("%e,",data.d[j++]);
  printf("])\n");
}

void do_nodeout(char* text) {
  printf("D.NodeOutput('%s',%d,[",text,(int)data.i[j++]);
  while (j < jend) printf("%e,",data.d[j++]);
  printf("])\n");
}

void do_total_energies() {
  double * dp = data.d + j;
  printf("D.TotalEnergies(");
  printf("ALLKE=%f,",dp[0]);
  printf("ALLSE=%f,",dp[1]);
  printf("ALLWK=%f,",dp[2]);
  printf("ALLPD=%f,",dp[3]);
  printf("ALLCD=%f,",dp[4]);
  printf("ALLVD=%f,",dp[5]);
  printf("ALLAE=%f,",dp[7]);
  printf("ALLIE=%f,",dp[10]);
  printf("ETOTAL=%f,",dp[11]);
  printf("ALLFD=%f,",dp[12]);
  printf("ALLDMD=%f,",dp[16]);
  if (explicit) {
    printf("ALLDC=%f,",dp[8]);
    printf("ALLIHE=%f,",dp[16]);
    printf("ALLHF=%f,",dp[17]);
  } else {
    printf("ALLKL=%f,",dp[6]);
    printf("ALLQB=%f,",dp[8]);
    printf("ALLEE=%f,",dp[9]);
    printf("ALLJD=%f,",dp[13]);
    printf("ALLSD=%f,",dp[14]);
  }
  printf(")\n");
}

/* Process the data of a record */
int process_data() {
  /* nw and key have been set, j points to data*/
  if (verbose) fprintf(stderr,"Record %ld Offset %ld Length %ld Type %ld End %ld max %ld\n",recnr,j,nw,key,jend,jmax);
  if (fake) return 0;
  switch(key) {
  case 1900: do_element(); break;
  case 1901: do_node(); break;
  case 1902: do_dofs();  break;
  case 1911: do_outreq(); break;
  case 1921: do_abqver(); break;
  case 1922: do_heading(); break;
  case 1931: do_nodeset(); break;
  case 1932: add_nodeset(); break;
  case 1933: do_elemset(); break;
  case 1934: add_elemset(); break;
  case 1940: do_label(); break;
  case 2000: do_increment(); break;
  case 2001: end_increment(); break;

  case 1:   do_elemheader(); break;
  case 11:  do_elemout("S"); break;
  case 12:  do_elemout("SINV"); break;
  case 13:  do_elemout("SF"); break;
  case 101: do_nodeout("U"); break;
  case 102: do_nodeout("V"); break;
  case 103: do_nodeout("A"); break;
  case 104: do_nodeout("RF"); break;
  case 105: do_nodeout("EPOT"); break;
  case 106: do_nodeout("CF"); break;
  case 107: do_nodeout("COORD"); break;
  case 108: do_nodeout("POR"); break;
  case 109: do_nodeout("RVF"); break;
  case 110: do_nodeout("RVT"); break;

  case 1999: do_total_energies(); break;
  default: printf("D.Unknown(%ld)\n",key);
  }
  return err;
}


/* read the next block from file */
int read_block() {
  if (j < jmax) {
    /* Move the remaining data to the start of the buffer */
    int64_t nm = jmax-j;
    if (verbose) fprintf(stderr,"Moving %ld words to start of buffer\n",nm);
    memmove(data.d,data.d+j,8*nm);
    j = 0;
    jmax = j+nm;
  } else {
    j = 0;
    jmax = 0;
  }
  blknr++;
  if (verbose)
    fprintf(stderr,"Reading block at filepos %ld, %d\n",ftell(fil),feof(fil));
  if ( (fread(&lead,sizeof(lead),1,fil) != 1 && !feof(fil)) ||
       (!feof(fil) && fread(data.d+jmax,RECSIZE*8,1,fil) != 1) ||
       (!feof(fil) && fread(&tail,sizeof(tail),1,fil) != 1) ) {
    fprintf(stderr,"ERROR while reading block nr %ld at filepos %ld\n",blknr,ftell(fil));
    return 1;
  }
  if (feof(fil)) return 1;
  jmax += RECSIZE;
  if (verbose) {
    fprintf(stderr,"** Block %ld size %d lead %d tail %d\n",blknr,8*RECSIZE,lead,tail);
    fprintf(stderr,"** Buffer Start %ld End %ld size %ld\n",j,jmax,jmax-j);
  }
  return 0;
}

/* Process a single file */
int process_file(const char* fn) {
  fprintf(stderr,"Processing file '%s'\n",fn);
  fil = fopen(fn,"r");
  if (fil == NULL) return 1;

  printf("#!/usr/bin/env pyformex\n");
  printf("# Created by %s\n",copyright);
  printf("from plugins.fe_post import FeResult\n");
  printf("D = FeResult()\n");
  j = jmax = 0; /* start with empty buffer */
  while (!feof(fil)) {
    if (read_block()) break;
    while (j < jmax) { /* we have data : process them */
      nw = data.i[j];
      if (nw <= 0) {
	/* this must be block padding */
	if (verbose) fprintf(stderr,"Skipping rest of block(padding)\n)");
	j = jmax;
	break;
      }
      if (j+nw > jmax) {
	/* record spans block boundary */
	if (verbose) fprintf(stderr,"Record exceeds block boundary\n");
	break;
      }
      jend = j+nw;
      if (jend > jmax) {
	fprintf(stderr,"ERROR: record seems to span more than 2 blocks\n");
	return 1;
      }
      key = data.i[j+1];
      recnr++;
      j += 2;
      if (process_data()) return 1;
      j = jend; /* in case the process_data did not process everything */
    }
  }
  printf("D.Export()\n");
  printf("# End\n");
  fclose(fil);
  return 0;
}

void print_copyright() {
  fprintf(stderr,"%s\n",copyright);
}

void print_usage() {
  fprintf(stderr,"\nUsage: postabq [options] output.fil\n\
Converts an ABAQUS output file (.fil) into a Python script.\n\
The output goes to stdout.\n\
\n\
Options:\n\
  -v : Be verbose (mostly for debugging)\n\
  -e : Force EXPLICIT from the start (default is to autodetect)\n\
  -n : Dry run: run through the file but do not produce conversion\n\
  -h : Print this help text\n\
  -V : Print version and exit\n\
\n");
}

/* The main program loops over the files specified in the command line */
int main(int argc, char *argv[]) {
  int i,nerr,res,nfiles;
  char c;

  print_copyright();

  /* Process command line options */
  for (i=1; i<argc; i++) {
    if (argv[i][0] != '-') continue;
    c = argv[i][1];
    switch (c) {
    case 'v': verbose=1; break;
    case 'e': explicit=1; break;
    case 'n': fake=1; break;
    case 'h': print_usage();
    case 'V': return 0;
    default: fprintf(stderr,"Invalid option '%c'; use '-h' for help\n",c);
      return 1;
    }
  }

  /* Loop over non-option arguments */
  nerr = 0;
  nfiles = 0;
  for (i=1; i<argc; i++) {
    if (argv[i][0] == '-') continue;
    nfiles ++;
    res = process_file(argv[i]);
    if (res != 0) {
      fprintf(stderr,"ERROR %d\n",res);
      nerr++;
    }
  }

  /* Cleanup */
  fprintf(stderr,"Processed %d files, %d errors\n",nfiles,nerr);
  return 0;
}

/* End */
